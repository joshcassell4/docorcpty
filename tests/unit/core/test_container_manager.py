"""Unit tests for ContainerManager."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from docker.errors import NotFound, APIError

from orchestrator.core.container_manager import ContainerManager
from orchestrator.core.config_loader import ContainerConfig


class TestContainerManager:
    """Test cases for ContainerManager."""
    
    def test_init(self, mock_docker_client):
        """Test ContainerManager initialization."""
        with patch("docker.DockerClient", return_value=mock_docker_client):
            manager = ContainerManager()
            assert manager.docker_socket == "/var/run/docker.sock"
            assert manager.containers == {}
            
    def test_create_container(self, mock_container_manager, sample_container_config):
        """Test container creation with proper configuration."""
        container_id = mock_container_manager.create_container(sample_container_config)
        
        assert container_id == "test-container-123"
        assert container_id in mock_container_manager.containers
        mock_container_manager.client.containers.create.assert_called_once()
        
    def test_create_container_with_resources(self, mock_container_manager):
        """Test container creation with resource limits."""
        config = ContainerConfig(
            name="resource-test",
            image="python:3.9",
            resources={
                "memory": "512m",
                "cpu_shares": 1024
            }
        )
        
        mock_container_manager.create_container(config)
        
        call_args = mock_container_manager.client.containers.create.call_args[1]
        assert call_args["mem_limit"] == "512m"
        assert call_args["cpu_shares"] == 1024
        
    def test_create_container_failure(self, mock_container_manager, sample_container_config):
        """Test container creation failure."""
        mock_container_manager.client.containers.create.side_effect = APIError("Creation failed")
        
        with pytest.raises(APIError):
            mock_container_manager.create_container(sample_container_config)
            
    def test_stop_container(self, mock_container_manager):
        """Test stopping a running container."""
        # Add container to tracking
        container = Mock()
        container.stop = MagicMock()
        mock_container_manager.containers["test-123"] = container
        mock_container_manager.client.containers.get.return_value = container
        
        result = mock_container_manager.stop_container("test-123")
        
        assert result is True
        container.stop.assert_called_once_with(timeout=10)
        
    def test_stop_container_not_found(self, mock_container_manager):
        """Test stopping non-existent container."""
        mock_container_manager.client.containers.get.side_effect = NotFound("Not found")
        
        result = mock_container_manager.stop_container("nonexistent")
        assert result is False
        
    def test_remove_container(self, mock_container_manager):
        """Test removing a container."""
        container = Mock()
        container.remove = MagicMock()
        mock_container_manager.containers["test-123"] = container
        mock_container_manager.client.containers.get.return_value = container
        
        result = mock_container_manager.remove_container("test-123")
        
        assert result is True
        assert "test-123" not in mock_container_manager.containers
        container.remove.assert_called_once_with(force=False)
        
    def test_get_container_stats(self, mock_container_manager):
        """Test getting container statistics."""
        container = Mock()
        container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000},
                "system_cpu_usage": 2000
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 500},
                "system_cpu_usage": 1000
            },
            "memory_stats": {
                "usage": 100 * 1024 * 1024,
                "limit": 512 * 1024 * 1024
            },
            "networks": {
                "eth0": {
                    "rx_bytes": 1000,
                    "tx_bytes": 2000
                }
            }
        }
        
        mock_container_manager.client.containers.get.return_value = container
        stats = mock_container_manager.get_container_stats("test-123")
        
        assert "cpu_percent" in stats
        assert "memory_usage" in stats
        assert "memory_percent" in stats
        assert stats["memory_usage"] == 100 * 1024 * 1024
        
    def test_list_containers(self, mock_container_manager):
        """Test listing containers."""
        containers = mock_container_manager.list_containers(all=True)
        
        assert len(containers) == 1
        assert containers[0]["id"] == "test-container-123"
        assert containers[0]["name"] == "test-container"
        mock_container_manager.client.containers.list.assert_called_once_with(all=True)
        
    def test_get_container_logs(self, mock_container_manager):
        """Test getting container logs."""
        container = Mock()
        container.logs.return_value = "test log output"
        mock_container_manager.client.containers.get.return_value = container
        
        logs = mock_container_manager.get_container_logs("test-123", tail=50)
        
        assert logs == "test log output"
        container.logs.assert_called_once_with(
            tail=50,
            timestamps=True,
            decode=True
        )