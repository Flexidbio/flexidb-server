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
def create_container(container: ContainerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    free_ports = docker_service.get_free_ports(8000)
    if not free_ports:
        raise HTTPException(status_code=500, detail="No free ports available")
    
    port = free_ports[0]
    
    db_container = Container(
        name=container.name, 
        db_type=container.db_type, 
        status="creating",
        env=container.env,
        port=port
    )
    db.add(db_container)
    db.commit()
    
    try:
        docker_service.create_container(container.name, container.db_type, container.env, port)
        db_container.status = "running"
        db_container.connection_string = generate_connection_string(container.db_type, container.env, port)
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

def generate_connection_string(db_type: str, env: dict, port: int) -> str:
    if db_type == "mongodb":
        return f"mongodb://{env.get('MONGO_INITDB_ROOT_USERNAME')}:{env.get('MONGO_INITDB_ROOT_PASSWORD')}@{settings.domain}:{port}"
    elif db_type == "postgres":
        return f"postgresql://{env.get('POSTGRES_USER')}:{env.get('POSTGRES_PASSWORD')}@{settings.domain}:{port}/{env.get('POSTGRES_DB')}"
    elif db_type in ["mysql", "mariadb"]:
        return f"mysql://{env.get('MYSQL_USER')}:{env.get('MYSQL_PASSWORD')}@{settings.domain}:{port}/{env.get('MYSQL_DATABASE')}"
    elif db_type == "redis":
        return f"redis://:{env.get('REDIS_PASSWORD')}@{settings.domain}:{port}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")