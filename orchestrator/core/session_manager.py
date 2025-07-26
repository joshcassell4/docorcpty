"""Terminal session management."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable

from orchestrator.terminal.pty_handler import PTYHandler
from orchestrator.terminal.pexpect_handler import PexpectHandler


logger = logging.getLogger(__name__)


class Session:
    """Represents a terminal session."""
    
    def __init__(
        self,
        session_id: str,
        container_id: str,
        pty_handler: PTYHandler,
        pexpect_handler: Optional[PexpectHandler] = None
    ):
        """Initialize session.
        
        Args:
            session_id: Unique session identifier
            container_id: Associated container ID
            pty_handler: PTY handler instance
            pexpect_handler: Optional pexpect handler
        """
        self.session_id = session_id
        self.container_id = container_id
        self.pty_handler = pty_handler
        self.pexpect_handler = pexpect_handler
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.active = True
        self._output_callbacks: list[Callable[[str], None]] = []
        
    def add_output_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for output data.
        
        Args:
            callback: Function to call with output data
        """
        self._output_callbacks.append(callback)
        
    def remove_output_callback(self, callback: Callable[[str], None]) -> None:
        """Remove output callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._output_callbacks:
            self._output_callbacks.remove(callback)
            
    def send_input(self, data: str) -> None:
        """Send input to terminal.
        
        Args:
            data: Input data to send
        """
        self.last_activity = datetime.utcnow()
        if self.pexpect_handler:
            self.pexpect_handler.send(data)
        else:
            self.pty_handler.write(data.encode())
            
    def resize(self, rows: int, cols: int) -> None:
        """Resize terminal.
        
        Args:
            rows: Number of rows
            cols: Number of columns
        """
        self.pty_handler.resize(rows, cols)
        
    def close(self) -> None:
        """Close the session."""
        self.active = False
        if self.pexpect_handler:
            self.pexpect_handler.close()
        self.pty_handler.close()


class SessionManager:
    """Manages terminal sessions."""
    
    def __init__(self, max_sessions: int = 50, timeout_seconds: int = 3600):
        """Initialize session manager.
        
        Args:
            max_sessions: Maximum concurrent sessions
            timeout_seconds: Session timeout in seconds
        """
        self.max_sessions = max_sessions
        self.timeout_seconds = timeout_seconds
        self.sessions: Dict[str, Session] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def create_session(
        self,
        container_id: str,
        command: Optional[str] = None,
        use_pexpect: bool = False
    ) -> str:
        """Create a new terminal session.
        
        Args:
            container_id: Container ID to attach to
            command: Optional command to execute
            use_pexpect: Whether to use pexpect for automation
            
        Returns:
            Session ID
            
        Raises:
            RuntimeError: If max sessions reached
        """
        if len(self.sessions) >= self.max_sessions:
            raise RuntimeError(f"Maximum sessions ({self.max_sessions}) reached")
            
        session_id = str(uuid.uuid4())
        
        # Create PTY handler
        pty_handler = PTYHandler(container_id)
        await pty_handler.connect(command)
        
        # Optionally create pexpect handler
        pexpect_handler = None
        if use_pexpect:
            pexpect_handler = PexpectHandler(pty_handler)
            
        # Create session
        session = Session(
            session_id=session_id,
            container_id=container_id,
            pty_handler=pty_handler,
            pexpect_handler=pexpect_handler
        )
        
        self.sessions[session_id] = session
        
        # Start output reader
        asyncio.create_task(self._read_output(session))
        
        logger.info(f"Created session {session_id} for container {container_id}")
        return session_id
        
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session or None
        """
        return self.sessions.get(session_id)
        
    def close_session(self, session_id: str) -> bool:
        """Close a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session was closed
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
            
        session.close()
        del self.sessions[session_id]
        
        logger.info(f"Closed session {session_id}")
        return True
        
    def list_sessions(self) -> list[Dict[str, Any]]:
        """List all active sessions.
        
        Returns:
            List of session information
        """
        return [
            {
                "session_id": s.session_id,
                "container_id": s.container_id,
                "created_at": s.created_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
                "active": s.active,
            }
            for s in self.sessions.values()
        ]
        
    async def _read_output(self, session: Session) -> None:
        """Read output from session PTY.
        
        Args:
            session: Session to read from
        """
        try:
            while session.active:
                data = await session.pty_handler.read()
                if data:
                    # Notify callbacks
                    for callback in session._output_callbacks:
                        try:
                            callback(data)
                        except Exception as e:
                            logger.error(f"Error in output callback: {e}")
                else:
                    # No data, sleep briefly
                    await asyncio.sleep(0.01)
                    
        except Exception as e:
            logger.error(f"Error reading session output: {e}")
            session.active = False
            
    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            
    async def _cleanup_loop(self) -> None:
        """Background task to cleanup timed out sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.utcnow()
                timeout_delta = timedelta(seconds=self.timeout_seconds)
                
                # Find timed out sessions
                timed_out = [
                    sid for sid, session in self.sessions.items()
                    if now - session.last_activity > timeout_delta
                ]
                
                # Close timed out sessions
                for session_id in timed_out:
                    logger.info(f"Closing timed out session {session_id}")
                    self.close_session(session_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                
    def cleanup(self) -> None:
        """Cleanup all sessions."""
        for session_id in list(self.sessions.keys()):
            self.close_session(session_id)