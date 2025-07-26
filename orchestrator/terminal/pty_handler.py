"""PTY handler using dockerpty."""

import asyncio
import logging
from typing import Optional

import dockerpty
import docker


logger = logging.getLogger(__name__)


class PTYHandler:
    """Handles pseudo-terminal allocation for containers."""
    
    def __init__(self, container_id: str):
        """Initialize PTY handler.
        
        Args:
            container_id: Docker container ID
        """
        self.container_id = container_id
        self.client = docker.from_env()
        self.container = self.client.containers.get(container_id)
        self._stdin = None
        self._stdout = None
        self._stderr = None
        self._connected = False
        
    async def connect(self, command: Optional[str] = None) -> None:
        """Connect to container PTY.
        
        Args:
            command: Optional command to execute
        """
        try:
            # Create exec instance
            exec_command = command or "/bin/bash"
            
            # Use dockerpty to create PTY
            # Note: dockerpty.start_exec is synchronous, so we run it in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._connect_sync,
                exec_command
            )
            
            self._connected = True
            logger.info(f"Connected PTY to container {self.container_id}")
            
        except Exception as e:
            logger.error(f"Failed to connect PTY: {e}")
            raise
            
    def _connect_sync(self, command: str) -> None:
        """Synchronous connection helper.
        
        Args:
            command: Command to execute
        """
        # For now, we'll use docker exec API directly
        # In production, dockerpty.start_exec would be used
        exec_instance = self.container.exec_run(
            command,
            stdin=True,
            stdout=True,
            stderr=True,
            tty=True,
            stream=True,
            socket=True
        )
        
        self._socket = exec_instance.output
        
    async def read(self, size: int = 4096) -> str:
        """Read data from PTY.
        
        Args:
            size: Maximum bytes to read
            
        Returns:
            Data as string
        """
        if not self._connected:
            return ""
            
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                self._socket.recv,
                size
            )
            
            if data:
                return data.decode("utf-8", errors="replace")
            return ""
            
        except Exception as e:
            logger.error(f"Error reading from PTY: {e}")
            return ""
            
    def write(self, data: bytes) -> None:
        """Write data to PTY.
        
        Args:
            data: Data to write
        """
        if not self._connected:
            return
            
        try:
            self._socket.send(data)
        except Exception as e:
            logger.error(f"Error writing to PTY: {e}")
            
    def resize(self, rows: int, cols: int) -> None:
        """Resize terminal.
        
        Args:
            rows: Number of rows
            cols: Number of columns
        """
        try:
            # Docker API resize
            exec_info = self.container.client.api.exec_inspect(
                self.container.attrs["ExecIDs"][0]
            )
            
            if exec_info["Running"]:
                self.container.client.api.exec_resize(
                    exec_info["ID"],
                    height=rows,
                    width=cols
                )
                
        except Exception as e:
            logger.error(f"Error resizing PTY: {e}")
            
    def close(self) -> None:
        """Close PTY connection."""
        if self._socket:
            try:
                self._socket.close()
            except Exception as e:
                logger.error(f"Error closing PTY: {e}")
                
        self._connected = False