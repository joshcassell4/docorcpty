"""Unit tests for SessionManager."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from orchestrator.core.session_manager import SessionManager, Session


class TestSession:
    """Test cases for Session class."""
    
    def test_session_init(self, mock_pty_handler, mock_pexpect_handler):
        """Test Session initialization."""
        session = Session(
            session_id="test-123",
            container_id="container-456",
            pty_handler=mock_pty_handler,
            pexpect_handler=mock_pexpect_handler
        )
        
        assert session.session_id == "test-123"
        assert session.container_id == "container-456"
        assert session.pty_handler == mock_pty_handler
        assert session.pexpect_handler == mock_pexpect_handler
        assert session.active is True
        assert isinstance(session.created_at, datetime)
        
    def test_send_input_with_pexpect(self, mock_pty_handler, mock_pexpect_handler):
        """Test sending input with pexpect handler."""
        session = Session(
            session_id="test-123",
            container_id="container-456",
            pty_handler=mock_pty_handler,
            pexpect_handler=mock_pexpect_handler
        )
        
        session.send_input("test command")
        mock_pexpect_handler.send.assert_called_once_with("test command")
        
    def test_send_input_without_pexpect(self, mock_pty_handler):
        """Test sending input without pexpect handler."""
        session = Session(
            session_id="test-123",
            container_id="container-456",
            pty_handler=mock_pty_handler,
            pexpect_handler=None
        )
        
        session.send_input("test command")
        mock_pty_handler.write.assert_called_once_with(b"test command")
        
    def test_resize(self, mock_pty_handler):
        """Test terminal resize."""
        session = Session(
            session_id="test-123",
            container_id="container-456",
            pty_handler=mock_pty_handler
        )
        
        session.resize(24, 80)
        mock_pty_handler.resize.assert_called_once_with(24, 80)
        
    def test_close(self, mock_pty_handler, mock_pexpect_handler):
        """Test session close."""
        session = Session(
            session_id="test-123",
            container_id="container-456",
            pty_handler=mock_pty_handler,
            pexpect_handler=mock_pexpect_handler
        )
        
        session.close()
        
        assert session.active is False
        mock_pexpect_handler.close.assert_called_once()
        mock_pty_handler.close.assert_called_once()


class TestSessionManager:
    """Test cases for SessionManager."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, mock_session_manager):
        """Test creating a terminal session."""
        with patch("orchestrator.core.session_manager.PTYHandler") as mock_pty_class:
            mock_pty = AsyncMock()
            mock_pty_class.return_value = mock_pty
            
            session_id = await mock_session_manager.create_session("container-123")
            
            assert session_id in mock_session_manager.sessions
            assert len(mock_session_manager.sessions) == 1
            mock_pty.connect.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_create_session_max_limit(self, mock_session_manager):
        """Test session creation when max limit reached."""
        # Fill up sessions
        for i in range(mock_session_manager.max_sessions):
            mock_session_manager.sessions[f"session-{i}"] = Mock()
            
        with pytest.raises(RuntimeError, match="Maximum sessions"):
            await mock_session_manager.create_session("container-123")
            
    def test_get_session(self, mock_session_manager):
        """Test getting session by ID."""
        mock_session = Mock()
        mock_session_manager.sessions["test-123"] = mock_session
        
        session = mock_session_manager.get_session("test-123")
        assert session == mock_session
        
        # Test non-existent session
        assert mock_session_manager.get_session("nonexistent") is None
        
    def test_close_session(self, mock_session_manager):
        """Test closing a session."""
        mock_session = Mock()
        mock_session_manager.sessions["test-123"] = mock_session
        
        result = mock_session_manager.close_session("test-123")
        
        assert result is True
        assert "test-123" not in mock_session_manager.sessions
        mock_session.close.assert_called_once()
        
    def test_close_nonexistent_session(self, mock_session_manager):
        """Test closing non-existent session."""
        result = mock_session_manager.close_session("nonexistent")
        assert result is False
        
    def test_list_sessions(self, mock_session_manager, mock_pty_handler):
        """Test listing all sessions."""
        session1 = Session(
            session_id="session-1",
            container_id="container-1",
            pty_handler=mock_pty_handler
        )
        session2 = Session(
            session_id="session-2",
            container_id="container-2",
            pty_handler=mock_pty_handler
        )
        
        mock_session_manager.sessions = {
            "session-1": session1,
            "session-2": session2
        }
        
        sessions = mock_session_manager.list_sessions()
        
        assert len(sessions) == 2
        assert sessions[0]["session_id"] == "session-1"
        assert sessions[1]["session_id"] == "session-2"
        
    @pytest.mark.asyncio
    async def test_cleanup_loop(self, mock_session_manager):
        """Test cleanup of timed out sessions."""
        # Create an old session
        old_session = Mock()
        old_session.last_activity = datetime.utcnow() - timedelta(hours=2)
        mock_session_manager.sessions["old-session"] = old_session
        
        # Create a recent session
        new_session = Mock()
        new_session.last_activity = datetime.utcnow()
        mock_session_manager.sessions["new-session"] = new_session
        
        # Mock close_session
        mock_session_manager.close_session = Mock()
        
        # Run one iteration of cleanup
        await mock_session_manager._cleanup_loop()
        
        # Only old session should be closed
        mock_session_manager.close_session.assert_called_once_with("old-session")