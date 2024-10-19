from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_container():
    response = client.post("/containers", json={"name": "test-container", "db_type": "mongodb"})
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == "test-container"
    assert response.json()["status"] == "running"

def test_list_containers():
    response = client.get("/containers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_delete_container():
    # First, create a container
    create_response = client.post("/containers", json={"name": "test-delete-container", "db_type": "mongodb"})
    container_id = create_response.json()["id"]

    # Then, delete it
    delete_response = client.delete(f"/containers/{container_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Container deleted successfully"}