"""Session management API routes."""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestrator.api.app import orchestrator


router = APIRouter()


class SessionCreateRequest(BaseModel):
    """Session creation request model."""
    container_id: str
    command: Optional[str] = None
    use_automation: bool = False


class SessionInputRequest(BaseModel):
    """Session input request model."""
    data: str


class SessionResizeRequest(BaseModel):
    """Session resize request model."""
    rows: int
    cols: int


@router.get("/", response_model=List[Dict[str, Any]])
async def list_sessions():
    """List all active sessions.
    
    Returns:
        List of sessions
    """
    return orchestrator.session_manager.list_sessions()


@router.post("/", response_model=Dict[str, Any])
async def create_session(request: SessionCreateRequest):
    """Create a new terminal session.
    
    Args:
        request: Session creation request
        
    Returns:
        Session creation result
    """
    try:
        result = await orchestrator.create_session(
            container_id=request.container_id,
            command=request.command,
            use_automation=request.use_automation
        )
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Get session details.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session details
    """
    session = orchestrator.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return {
        "session_id": session.session_id,
        "container_id": session.container_id,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "active": session.active,
    }


@router.delete("/{session_id}")
async def close_session(session_id: str):
    """Close a session.
    
    Args:
        session_id: Session ID
        
    Returns:
        Closure result
    """
    success = orchestrator.session_manager.close_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return {"success": True, "session_id": session_id}


@router.post("/{session_id}/input")
async def send_input(session_id: str, request: SessionInputRequest):
    """Send input to session.
    
    Args:
        session_id: Session ID
        request: Input request
        
    Returns:
        Success result
    """
    session = orchestrator.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.send_input(request.data)
    return {"success": True}


@router.post("/{session_id}/resize")
async def resize_session(session_id: str, request: SessionResizeRequest):
    """Resize terminal session.
    
    Args:
        session_id: Session ID
        request: Resize request
        
    Returns:
        Success result
    """
    session = orchestrator.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.resize(request.rows, request.cols)
    return {"success": True}


@router.get("/{session_id}/output")
async def get_output_buffer(session_id: str, lines: Optional[int] = None):
    """Get session output buffer.
    
    Args:
        session_id: Session ID
        lines: Number of lines to retrieve
        
    Returns:
        Output buffer contents
    """
    session = orchestrator.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # For now, return empty as we don't have a built-in buffer
    # In production, this would integrate with IOManager
    return {
        "session_id": session_id,
        "output": [],
        "lines": lines or 0
    }