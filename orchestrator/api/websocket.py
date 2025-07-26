"""WebSocket connection management."""

import logging
from typing import Dict, Set

from fastapi import WebSocket


logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Accept and track WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
            
        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}")
        
    async def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """Remove WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                
        logger.info(f"WebSocket disconnected for session {session_id}")
        
    async def send_to_session(self, session_id: str, message: dict) -> None:
        """Send message to all connections for a session.
        
        Args:
            session_id: Session ID
            message: Message to send
        """
        if session_id in self.active_connections:
            # Send to all connections for this session
            disconnected = []
            
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    disconnected.append(websocket)
                    
            # Remove disconnected sockets
            for ws in disconnected:
                await self.disconnect(ws, session_id)
                
    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connections.
        
        Args:
            message: Message to broadcast
        """
        for session_id in list(self.active_connections.keys()):
            await self.send_to_session(session_id, message)