"""Main orchestration engine."""

import asyncio
import logging
from typing import Dict, Any, Optional

from orchestrator.core.config_loader import ConfigLoader, OrchestratorConfig
from orchestrator.core.container_manager import ContainerManager
from orchestrator.core.session_manager import SessionManager
from orchestrator.utils.monitoring import ResourceMonitor


logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestration engine coordinating all components."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize orchestrator.
        
        Args:
            config_dir: Configuration directory path
        """
        self.config_loader = ConfigLoader(config_dir)
        self.config = self.config_loader.load_orchestrator_config()
        
        self.container_manager = ContainerManager(self.config.docker_socket)
        self.session_manager = SessionManager(
            max_sessions=self.config.max_sessions,
            timeout_seconds=self.config.session_timeout
        )
        self.resource_monitor = ResourceMonitor()
        
        self._running = False
        self._tasks: list[asyncio.Task] = []
        
    async def start(self) -> None:
        """Start the orchestrator."""
        logger.info("Starting Container Terminal Orchestrator")
        
        self._running = True
        
        # Load container configurations
        self.config_loader.load_container_configs()
        
        # Start background tasks
        self._tasks.append(
            asyncio.create_task(self.session_manager.start_cleanup_task())
        )
        self._tasks.append(
            asyncio.create_task(self.resource_monitor.start_monitoring())
        )
        
        logger.info("Orchestrator started successfully")
        
    async def stop(self) -> None:
        """Stop the orchestrator."""
        logger.info("Stopping Container Terminal Orchestrator")
        
        self._running = False
        
        # Stop background tasks
        await self.session_manager.stop_cleanup_task()
        await self.resource_monitor.stop_monitoring()
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
        # Cleanup resources
        self.session_manager.cleanup()
        self.container_manager.cleanup()
        
        logger.info("Orchestrator stopped")
        
    async def create_container(self, container_name: str) -> Dict[str, Any]:
        """Create a container from configuration.
        
        Args:
            container_name: Name of container configuration
            
        Returns:
            Container creation result
        """
        config = self.config_loader.get_container_config(container_name)
        if not config:
            raise ValueError(f"Container configuration '{container_name}' not found")
            
        container_id = self.container_manager.create_container(config)
        
        return {
            "container_id": container_id,
            "name": config.name,
            "image": config.image,
            "status": "running"
        }
        
    async def create_session(
        self,
        container_id: str,
        command: Optional[str] = None,
        use_automation: bool = False
    ) -> Dict[str, Any]:
        """Create a terminal session.
        
        Args:
            container_id: Container ID
            command: Optional command to execute
            use_automation: Enable pexpect for automation
            
        Returns:
            Session creation result
        """
        session_id = await self.session_manager.create_session(
            container_id=container_id,
            command=command,
            use_pexpect=use_automation
        )
        
        return {
            "session_id": session_id,
            "container_id": container_id,
            "created": True
        }
        
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system resource statistics.
        
        Returns:
            System statistics
        """
        return {
            "orchestrator": {
                "running": self._running,
                "sessions": len(self.session_manager.sessions),
                "max_sessions": self.config.max_sessions,
            },
            "system": self.resource_monitor.get_current_stats(),
            "containers": len(self.container_manager.list_containers())
        }
        
    def reload_configurations(self) -> None:
        """Reload all configurations."""
        self.config_loader.reload_configs()
        self.config = self.config_loader.load_orchestrator_config()
        
        # Update components with new config
        self.session_manager.max_sessions = self.config.max_sessions
        self.session_manager.timeout_seconds = self.config.session_timeout
        
        logger.info("Configurations reloaded")