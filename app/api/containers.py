from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.container import Container
from app.services.docker_service import DockerService
from app.api.auth import get_current_user
from pydantic import BaseModel
from typing import Dict
from app.models.user import User
router = APIRouter()
docker_service = DockerService()

class ContainerCreate(BaseModel):
    name: str
    db_type: str
    env: Dict[str, str]
@router.post("/containers")
def create_container(container_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Extract necessary fields from the container data
    name = container_data.get("name")
    db_type = container_data.get("db_type")
    port = container_data.get("user_port", 27017)  # Default port if not provided
    internal_port = container_data.get("internal_port", 27017)  # Default internal port
    env_vars = container_data.get("env_vars", {})

    # Ensure necessary fields are present
    if not name or not db_type or not env_vars:
        raise HTTPException(status_code=400, detail="Missing required fields: 'name', 'db_type', or 'env_vars'")

    # Create the container record in the database with 'creating' status
    db_container = Container(
        name=name,
        db_type=db_type,
        status="creating",
        env=env_vars,
        port=port
    )
    db.add(db_container)
    db.commit()

    try:
        # Create the Docker container using the provided details
        docker_service.create_container(name, db_type, env_vars, internal_port)

        # Update container status to 'running' and generate the connection string
        db_container.status = "running"
        db_container.connection_string = generate_connection_string(db_type, env_vars, port)
        db.commit()
    except Exception as e:
        # If there's an error, mark the container status as 'failed'
        db_container.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    # Return the container details after creation
    return {
        "id": db_container.id,
        "name": db_container.name,
        "status": db_container.status,
        "connection_string": db_container.connection_string
    }

@router.get("/containers")
def list_containers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    containers = db.query(Container).all()
    return containers

@router.delete("/containers/{container_id}")
def delete_container(container_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    container = db.query(Container).filter(Container.id == container_id).first()
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    
    try:
        docker_service.delete_container(container.name)
        db.delete(container)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"message": "Container deleted successfully"}

@router.put("/containers/{container_id}")
def update_container(container_id: int, container: ContainerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_container = db.query(Container).filter(Container.id == container_id).first()
    if not db_container:
        raise HTTPException(status_code=404, detail="Container not found")
    
    db_container.env = container.env
    db_container.connection_string = generate_connection_string(db_container.db_type, container.env, db_container.port)
    db.commit()
    
    # Restart the container with new environment variables
    try:
        docker_service.delete_container(db_container.name)
        docker_service.create_container(db_container.name, db_container.db_type, container.env, db_container.port)
        db_container.status = "running"
        db.commit()
    except Exception as e:
        db_container.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "id": db_container.id, 
        "name": db_container.name, 
        "status": db_container.status,
        "connection_string": db_container.connection_string
    }

@router.get("/get-free-ports/{port}")
def get_free_ports(port: int, current_user: User = Depends(get_current_user)):
    free_ports = docker_service.get_free_ports(port)
    return {"free_ports": free_ports}

