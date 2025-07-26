"""FastAPI application for Container Terminal Orchestrator."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from orchestrator.core.orchestrator import Orchestrator
from orchestrator.utils.logger import setup_logging
from orchestrator.api.routes import containers, sessions, automation
from orchestrator.api.websocket import WebSocketManager


# Load environment variables
load_dotenv()

# Setup logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_format=os.getenv("LOG_FORMAT", "json")
)

# Global orchestrator instance
orchestrator: Orchestrator = None
ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global orchestrator
    
    # Startup
    orchestrator = Orchestrator()
    await orchestrator.start()
    
    yield
    
    # Shutdown
    await orchestrator.stop()


# Create FastAPI app
app = FastAPI(
    title="Container Terminal Orchestrator",
    description="Python-based container orchestration platform for terminal applications",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(containers.router, prefix="/api/containers", tags=["containers"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(automation.router, prefix="/api/automation", tags=["automation"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Container Terminal Orchestrator",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    stats = orchestrator.get_system_stats() if orchestrator else {}
    
    return {
        "status": "healthy",
        "orchestrator": stats.get("orchestrator", {}),
        "system": stats.get("system", {})
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for terminal sessions."""
    await ws_manager.connect(websocket, session_id)
    
    try:
        # Get session
        session = orchestrator.session_manager.get_session(session_id)
        if not session:
            await websocket.send_json({
                "type": "error",
                "message": f"Session {session_id} not found"
            })
            await ws_manager.disconnect(websocket, session_id)
            return
            
        # Add output callback
        async def output_callback(data: str):
            await websocket.send_json({
                "type": "output",
                "data": data
            })
            
        session.add_output_callback(output_callback)
        
        # Handle input
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "input":
                session.send_input(data["data"])
            elif data["type"] == "resize":
                session.resize(data["rows"], data["cols"])
            elif data["type"] == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        session.remove_output_callback(output_callback)
        await ws_manager.disconnect(websocket, session_id)


# For running directly
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000))
    )