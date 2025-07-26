"""Container management API routes."""

from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from orchestrator.api.app import orchestrator


router = APIRouter()


class ContainerCreateRequest(BaseModel):
    """Container creation request model."""
    name: str


class ContainerActionRequest(BaseModel):
    """Container action request model."""
    action: str  # start, stop, restart, remove


@router.get("/", response_model=List[Dict[str, Any]])
async def list_containers(all: bool = Query(False, description="Include stopped containers")):
    """List all containers.
    
    Args:
        all: Include stopped containers
        
    Returns:
        List of containers
    """
    return orchestrator.container_manager.list_containers(all=all)


@router.post("/", response_model=Dict[str, Any])
async def create_container(request: ContainerCreateRequest):
    """Create a new container.
    
    Args:
        request: Container creation request
        
    Returns:
        Container creation result
    """
    try:
        result = await orchestrator.create_container(request.name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{container_id}")
async def get_container(container_id: str):
    """Get container details.
    
    Args:
        container_id: Container ID
        
    Returns:
        Container details
    """
    try:
        container = orchestrator.container_manager._get_container(container_id)
        return {
            "id": container.id,
            "name": container.name,
            "image": container.image.tags[0] if container.image.tags else container.image.id,
            "status": container.status,
            "created": container.attrs["Created"],
            "ports": container.attrs.get("NetworkSettings", {}).get("Ports", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Container not found: {e}")


@router.post("/{container_id}/action")
async def container_action(container_id: str, request: ContainerActionRequest):
    """Perform action on container.
    
    Args:
        container_id: Container ID
        request: Action request
        
    Returns:
        Action result
    """
    action = request.action.lower()
    
    try:
        if action == "stop":
            success = orchestrator.container_manager.stop_container(container_id)
            return {"success": success, "action": action}
            
        elif action == "start":
            container = orchestrator.container_manager._get_container(container_id)
            container.start()
            return {"success": True, "action": action}
            
        elif action == "restart":
            container = orchestrator.container_manager._get_container(container_id)
            container.restart()
            return {"success": True, "action": action}
            
        elif action == "remove":
            success = orchestrator.container_manager.remove_container(container_id)
            return {"success": success, "action": action}
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{container_id}/stats")
async def get_container_stats(container_id: str):
    """Get container resource statistics.
    
    Args:
        container_id: Container ID
        
    Returns:
        Container statistics
    """
    stats = orchestrator.container_manager.get_container_stats(container_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Container not found or stats unavailable")
    return stats


@router.get("/{container_id}/logs")
async def get_container_logs(
    container_id: str,
    tail: int = Query(100, description="Number of lines to return"),
    timestamps: bool = Query(True, description="Include timestamps")
):
    """Get container logs.
    
    Args:
        container_id: Container ID
        tail: Number of lines to return
        timestamps: Include timestamps
        
    Returns:
        Container logs
    """
    logs = orchestrator.container_manager.get_container_logs(
        container_id,
        tail=tail,
        timestamps=timestamps
    )
    
    return {
        "container_id": container_id,
        "logs": logs,
        "tail": tail
    }