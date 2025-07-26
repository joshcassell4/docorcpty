"""Configuration loader and management."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ContainerConfig(BaseModel):
    """Container configuration model."""
    
    name: str
    image: str
    command: Optional[str] = None
    volumes: Optional[list[str]] = None
    environment: Optional[Dict[str, str]] = None
    working_dir: Optional[str] = None
    ports: Optional[Dict[str, int]] = None
    privileged: bool = False
    readonly: bool = False
    resources: Optional[Dict[str, Any]] = None


class OrchestratorConfig(BaseModel):
    """Main orchestrator configuration model."""
    
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    docker_socket: str = Field(default="/var/run/docker.sock")
    docker_network: str = Field(default="cto_network")
    max_sessions: int = Field(default=50)
    session_timeout: int = Field(default=3600)
    log_level: str = Field(default="INFO")


class ConfigLoader:
    """Configuration loader for the orchestrator."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration loader.
        
        Args:
            config_dir: Path to configuration directory
        """
        self.config_dir = Path(config_dir or os.getenv("CTO_CONFIG_DIR", "configs"))
        self._configs: Dict[str, Any] = {}
        self._container_configs: Dict[str, ContainerConfig] = {}
        
    def load_orchestrator_config(self) -> OrchestratorConfig:
        """Load main orchestrator configuration.
        
        Returns:
            OrchestratorConfig instance
        """
        config_path = self.config_dir / "orchestrator.json"
        
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
                return OrchestratorConfig(**data)
        
        # Return default configuration
        return OrchestratorConfig()
    
    def load_container_configs(self) -> Dict[str, ContainerConfig]:
        """Load all container configurations.
        
        Returns:
            Dictionary of container configurations
        """
        containers_dir = self.config_dir / "containers"
        
        if not containers_dir.exists():
            return {}
        
        configs = {}
        for config_file in containers_dir.glob("*.json"):
            with open(config_file) as f:
                data = json.load(f)
                config = ContainerConfig(**data)
                configs[config.name] = config
                
        self._container_configs = configs
        return configs
    
    def get_container_config(self, name: str) -> Optional[ContainerConfig]:
        """Get specific container configuration.
        
        Args:
            name: Container name
            
        Returns:
            Container configuration or None
        """
        if not self._container_configs:
            self.load_container_configs()
            
        return self._container_configs.get(name)
    
    def reload_configs(self) -> None:
        """Reload all configurations from disk."""
        self._configs.clear()
        self._container_configs.clear()
        self.load_container_configs()