import docker
import random
import string
from app.core.config import settings

class DockerService:
    def __init__(self):
        self.client = docker.from_env()

    def create_container(self, name: str, db_type: str, env: dict, port: int):
        if db_type == "mongodb":
            image = "mongo:latest"
        elif db_type == "postgres":
            image = "postgres:latest"
        elif db_type == "mysql":
            image = "mysql:latest"
        elif db_type == "mariadb":
            image = "mariadb:latest"
        elif db_type == "redis":
            image = "redis:latest"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        labels = {
            "traefik.enable": "true",
            f"traefik.http.routers.{name}.rule": f"Host(`{settings.domain}`) && PathPrefix(`/{name}`)",
            f"traefik.http.services.{name}.loadbalancer.server.port": str(port)
        }

        self.client.containers.run(
            image, 
            name=name, 
            detach=True, 
            environment=env,
            ports={f"{port}/tcp": port},
            labels=labels,
            network="traefik_network"  # Make sure this network exists
        )

    def delete_container(self, name: str):
        container = self.client.containers.get(name)
        container.stop()
        container.remove()

    def get_free_ports(self, start_port: int, count: int = 5):
        used_ports = set()
        for container in self.client.containers.list():
            used_ports.update(int(port.split('/')[0]) for port in container.ports.keys())
        
        free_ports = []
        current_port = start_port
        while len(free_ports) < count:
            if current_port not in used_ports:
                free_ports.append(current_port)
            current_port += 1
        return free_ports