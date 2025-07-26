"""Unit tests for ConfigLoader."""

import pytest
import json
import tempfile
from pathlib import Path

from orchestrator.core.config_loader import ConfigLoader, ContainerConfig, OrchestratorConfig


class TestConfigLoader:
    """Test cases for ConfigLoader."""
    
    def test_init_default_path(self):
        """Test ConfigLoader initialization with default path."""
        loader = ConfigLoader()
        assert loader.config_dir == Path("configs")
        
    def test_init_custom_path(self):
        """Test ConfigLoader initialization with custom path."""
        loader = ConfigLoader("/custom/path")
        assert loader.config_dir == Path("/custom/path")
        
    def test_load_orchestrator_config_default(self):
        """Test loading orchestrator config with defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ConfigLoader(tmpdir)
            config = loader.load_orchestrator_config()
            
            assert isinstance(config, OrchestratorConfig)
            assert config.api_host == "0.0.0.0"
            assert config.api_port == 8000
            assert config.max_sessions == 50
            
    def test_load_orchestrator_config_from_file(self):
        """Test loading orchestrator config from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_data = {
                "api_host": "127.0.0.1",
                "api_port": 9000,
                "max_sessions": 100,
                "log_level": "DEBUG"
            }
            
            config_file = Path(tmpdir) / "orchestrator.json"
            with open(config_file, "w") as f:
                json.dump(config_data, f)
                
            loader = ConfigLoader(tmpdir)
            config = loader.load_orchestrator_config()
            
            assert config.api_host == "127.0.0.1"
            assert config.api_port == 9000
            assert config.max_sessions == 100
            assert config.log_level == "DEBUG"
            
    def test_load_container_configs(self):
        """Test loading container configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            containers_dir = Path(tmpdir) / "containers"
            containers_dir.mkdir()
            
            # Create test container configs
            python_config = {
                "name": "python-dev",
                "image": "python:3.9-slim",
                "command": "/bin/bash",
                "volumes": ["./workspace:/workspace"]
            }
            
            node_config = {
                "name": "node-dev",
                "image": "node:16",
                "command": "/bin/bash",
                "environment": {"NODE_ENV": "development"}
            }
            
            with open(containers_dir / "python.json", "w") as f:
                json.dump(python_config, f)
                
            with open(containers_dir / "node.json", "w") as f:
                json.dump(node_config, f)
                
            loader = ConfigLoader(tmpdir)
            configs = loader.load_container_configs()
            
            assert len(configs) == 2
            assert "python-dev" in configs
            assert "node-dev" in configs
            
            python = configs["python-dev"]
            assert python.image == "python:3.9-slim"
            assert python.volumes == ["./workspace:/workspace"]
            
            node = configs["node-dev"]
            assert node.image == "node:16"
            assert node.environment == {"NODE_ENV": "development"}
            
    def test_load_container_configs_empty_dir(self):
        """Test loading container configs from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ConfigLoader(tmpdir)
            configs = loader.load_container_configs()
            assert configs == {}
            
    def test_get_container_config(self):
        """Test getting specific container configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            containers_dir = Path(tmpdir) / "containers"
            containers_dir.mkdir()
            
            config_data = {
                "name": "test-container",
                "image": "ubuntu:22.04"
            }
            
            with open(containers_dir / "test.json", "w") as f:
                json.dump(config_data, f)
                
            loader = ConfigLoader(tmpdir)
            config = loader.get_container_config("test-container")
            
            assert config is not None
            assert config.name == "test-container"
            assert config.image == "ubuntu:22.04"
            
    def test_get_container_config_not_found(self):
        """Test getting non-existent container config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ConfigLoader(tmpdir)
            config = loader.get_container_config("nonexistent")
            assert config is None
            
    def test_reload_configs(self):
        """Test reloading configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            containers_dir = Path(tmpdir) / "containers"
            containers_dir.mkdir()
            
            # Initial config
            config_data = {
                "name": "test-container",
                "image": "python:3.8"
            }
            
            config_file = containers_dir / "test.json"
            with open(config_file, "w") as f:
                json.dump(config_data, f)
                
            loader = ConfigLoader(tmpdir)
            loader.load_container_configs()
            
            # Update config
            config_data["image"] = "python:3.9"
            with open(config_file, "w") as f:
                json.dump(config_data, f)
                
            # Reload
            loader.reload_configs()
            config = loader.get_container_config("test-container")
            
            assert config.image == "python:3.9"
            
    def test_container_config_validation(self):
        """Test ContainerConfig model validation."""
        # Valid config
        config = ContainerConfig(
            name="test",
            image="python:3.9"
        )
        assert config.name == "test"
        assert config.command is None
        assert config.privileged is False
        
        # Config with all fields
        config = ContainerConfig(
            name="full-test",
            image="ubuntu:22.04",
            command="/bin/bash",
            volumes=["/host:/container"],
            environment={"KEY": "value"},
            working_dir="/app",
            ports={"8080": 80},
            privileged=True,
            readonly=True,
            resources={"memory": "512m"}
        )
        
        assert config.privileged is True
        assert config.readonly is True
        assert config.resources["memory"] == "512m"