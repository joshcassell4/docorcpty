"""Unit tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock

from orchestrator.api.app import app


class TestApp:
    """Test cases for main FastAPI application."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
        
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Container Terminal Orchestrator"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"
        
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        with patch("orchestrator.api.app.orchestrator") as mock_orchestrator:
            mock_orchestrator.get_system_stats.return_value = {
                "orchestrator": {
                    "running": True,
                    "sessions": 5,
                    "max_sessions": 50
                },
                "system": {
                    "cpu": {"percent": 25.0},
                    "memory": {"percent": 45.0}
                }
            }
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "orchestrator" in data
            assert "system" in data
            
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/")
        
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        
    @pytest.mark.asyncio
    async def test_websocket_connection_no_session(self):
        """Test WebSocket connection with invalid session."""
        with TestClient(app) as client:
            with patch("orchestrator.api.app.orchestrator") as mock_orchestrator:
                mock_orchestrator.session_manager.get_session.return_value = None
                
                with client.websocket_connect("/ws/invalid-session") as websocket:
                    data = websocket.receive_json()
                    assert data["type"] == "error"
                    assert "not found" in data["message"]
                    
    @pytest.mark.asyncio
    async def test_websocket_input_handling(self):
        """Test WebSocket input handling."""
        with TestClient(app) as client:
            with patch("orchestrator.api.app.orchestrator") as mock_orchestrator:
                # Mock session
                mock_session = Mock()
                mock_session.send_input = Mock()
                mock_session.resize = Mock()
                mock_session.add_output_callback = Mock()
                mock_session.remove_output_callback = Mock()
                
                mock_orchestrator.session_manager.get_session.return_value = mock_session
                
                with client.websocket_connect("/ws/test-session") as websocket:
                    # Send input
                    websocket.send_json({
                        "type": "input",
                        "data": "test command"
                    })
                    
                    # Allow some time for processing
                    import time
                    time.sleep(0.1)
                    
                    mock_session.send_input.assert_called_with("test command")
                    
                    # Send resize
                    websocket.send_json({
                        "type": "resize",
                        "rows": 24,
                        "cols": 80
                    })
                    
                    time.sleep(0.1)
                    
                    mock_session.resize.assert_called_with(24, 80)