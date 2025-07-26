"""Container lifecycle management."""

import logging
from typing import Dict, List, Optional, Any

import docker
from docker.models.containers import Container
from docker.errors import NotFound, APIError

from orchestrator.core.config_loader import ContainerConfig


logger = logging.getLogger(__name__)


class ContainerManager:
    """Manages Docker container lifecycle operations."""
    
    def __init__(self, docker_socket: Optional[str] = None):
        """Initialize container manager.
        
        Args:
            docker_socket: Path to Docker socket
        """
        self.docker_socket = docker_socket or "/var/run/docker.sock"
        self.client = docker.DockerClient(base_url=f"unix://{self.docker_socket}")
        self.containers: Dict[str, Container] = {}
        
    def create_container(self, config: ContainerConfig) -> str:
        """Create and start a new container.
        
        Args:
            config: Container configuration
            
        Returns:
            Container ID
            
        Raises:
            APIError: If container creation fails
        """
        try:
            # Prepare container parameters
            params = {
                "image": config.image,
                "name": config.name,
                "command": config.command,
                "detach": True,
                "tty": True,
                "stdin_open": True,
                "auto_remove": False,
                "privileged": config.privileged,
                "read_only": config.readonly,
            }
            
            # Add volumes if specified
            if config.volumes:
                params["volumes"] = config.volumes
                
            # Add environment variables
            if config.environment:
                params["environment"] = config.environment
                
            # Add working directory
            if config.working_dir:
                params["working_dir"] = config.working_dir
                
            # Add port mappings
            if config.ports:
                params["ports"] = config.ports
                
            # Add resource limits
            if config.resources:
                if "memory" in config.resources:
                    params["mem_limit"] = config.resources["memory"]
                if "cpu_shares" in config.resources:
                    params["cpu_shares"] = config.resources["cpu_shares"]
            
            # Create container
            container = self.client.containers.create(**params)
            
            # Start container
            container.start()
            
            # Store reference
            self.containers[container.id] = container
            
            logger.info(f"Created and started container {config.name} ({container.id})")
            return container.id
            
        except APIError as e:
            logger.error(f"Failed to create container {config.name}: {e}")
            raise
            
    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a running container.
        
        Args:
            container_id: Container ID
            timeout: Timeout in seconds
            
        Returns:
            True if successful
        """
        try:
            container = self._get_container(container_id)
            container.stop(timeout=timeout)
            logger.info(f"Stopped container {container_id}")
            return True
            
        except NotFound:
            logger.warning(f"Container {container_id} not found")
            return False
        except APIError as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False
            
    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """Remove a container.
        
        Args:
            container_id: Container ID
            force: Force removal even if running
            
        Returns:
            True if successful
        """
        try:
            container = self._get_container(container_id)
            container.remove(force=force)
            
            # Remove from internal tracking
            if container_id in self.containers:
                del self.containers[container_id]
                
            logger.info(f"Removed container {container_id}")
            return True
            
        except NotFound:
            logger.warning(f"Container {container_id} not found")
            return False
        except APIError as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False
            
    def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get container resource usage statistics.
        
        Args:
            container_id: Container ID
            
        Returns:
            Dictionary with container statistics
        """
        try:
            container = self._get_container(container_id)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = 0.0
            if system_delta > 0.0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
            
            # Calculate memory usage
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            return {
                "cpu_percent": cpu_percent,
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
                "memory_percent": memory_percent,
                "network_rx": stats["networks"]["eth0"]["rx_bytes"],
                "network_tx": stats["networks"]["eth0"]["tx_bytes"],
            }
            
        except (NotFound, KeyError) as e:
            logger.error(f"Failed to get stats for container {container_id}: {e}")
            return {}
            
    def list_containers(self, all: bool = False) -> List[Dict[str, Any]]:
        """List containers.
        
        Args:
            all: Include stopped containers
            
        Returns:
            List of container information
        """
        containers = self.client.containers.list(all=all)
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else c.image.id,
                "status": c.status,
                "created": c.attrs["Created"],
            }
            for c in containers
        ]
        
    def get_container_logs(
        self, 
        container_id: str, 
        tail: int = 100,
        timestamps: bool = True
    ) -> str:
        """Get container logs.
        
        Args:
            container_id: Container ID
            tail: Number of lines to retrieve
            timestamps: Include timestamps
            
        Returns:
            Container logs as string
        """
        try:
            container = self._get_container(container_id)
            logs = container.logs(
                tail=tail,
                timestamps=timestamps,
                decode=True
            )
            return logs
            
        except NotFound:
            logger.error(f"Container {container_id} not found")
            return ""
            
    def _get_container(self, container_id: str) -> Container:
        """Get container object by ID.
        
        Args:
            container_id: Container ID
            
        Returns:
            Container object
            
        Raises:
            NotFound: If container doesn't exist
        """
        # Check cache first
        if container_id in self.containers:
            return self.containers[container_id]
            
        # Fetch from Docker
        container = self.client.containers.get(container_id)
        self.containers[container_id] = container
        return container
        
    def cleanup(self) -> None:
        """Cleanup resources and close connections."""
        try:
            self.client.close()
        except Exception as e:
            logger.error(f"Error closing Docker client: {e}")