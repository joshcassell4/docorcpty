"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, MagicMock
import docker
from fastapi.testclient import TestClient

from orchestrator.api.app import app
from orchestrator.core.config_loader import ContainerConfig, OrchestratorConfig
from orchestrator.core.container_manager import ContainerManager
from orchestrator.core.session_manager import SessionManager


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing."""
    client = Mock(spec=docker.DockerClient)
    
    # Mock container
    container = Mock()
    container.id = "test-container-123"
    container.name = "test-container"
    container.status = "running"
    container.image = Mock()
    container.image.tags = ["python:3.9-slim"]
    container.attrs = {
        "Created": "2024-01-01T00:00:00Z",
        "NetworkSettings": {"Ports": {}},
        "ExecIDs": []
    }
    
    # Mock methods
    client.containers.create.return_value = container
    client.containers.get.return_value = container
    client.containers.list.return_value = [container]
    
    return client


@pytest.fixture
def test_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_container_config():
    """Sample container configuration for tests."""
    return ContainerConfig(
        name="test-container",
        image="python:3.9-slim",
        command="/bin/bash",
        volumes=["./workspace:/workspace"],
        environment={"PYTHONPATH": "/workspace"},
        working_dir="/workspace"
    )


@pytest.fixture
def sample_orchestrator_config():
    """Sample orchestrator configuration."""
    return OrchestratorConfig(
        api_host="0.0.0.0",
        api_port=8000,
        docker_socket="/var/run/docker.sock",
        max_sessions=50,
        session_timeout=3600
    )


@pytest.fixture
def mock_container_manager(mock_docker_client):
    """Mock container manager."""
    manager = ContainerManager()
    manager.client = mock_docker_client
    return manager


@pytest.fixture
def mock_session_manager():
    """Mock session manager."""
    return SessionManager(max_sessions=10, timeout_seconds=300)


@pytest.fixture
def mock_pty_handler():
    """Mock PTY handler."""
    handler = Mock()
    handler.connect = MagicMock()
    handler.read = MagicMock(return_value="test output")
    handler.write = MagicMock()
    handler.resize = MagicMock()
    handler.close = MagicMock()
    return handler


@pytest.fixture
def mock_pexpect_handler():
    """Mock pexpect handler."""
    handler = Mock()
    handler.send = MagicMock()
    handler.sendline = MagicMock()
    handler.expect = MagicMock(return_value=0)
    handler.send_command = MagicMock(return_value="command output")
    handler.close = MagicMock()
    return handler