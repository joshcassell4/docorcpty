"""I/O stream management for terminal sessions."""

import asyncio
import logging
from typing import Optional, Callable, Any
from collections import deque


logger = logging.getLogger(__name__)


class IOManager:
    """Manages input/output streams for terminal sessions."""
    
    def __init__(self, buffer_size: int = 10000):
        """Initialize I/O manager.
        
        Args:
            buffer_size: Maximum buffer size for output
        """
        self.buffer_size = buffer_size
        self._output_buffer = deque(maxlen=buffer_size)
        self._input_queue: asyncio.Queue = asyncio.Queue()
        self._output_callbacks: list[Callable[[str], Any]] = []
        self._closed = False
        
    def add_output_callback(self, callback: Callable[[str], Any]) -> None:
        """Add callback for output data.
        
        Args:
            callback: Function to call with output data
        """
        self._output_callbacks.append(callback)
        
    def remove_output_callback(self, callback: Callable[[str], Any]) -> None:
        """Remove output callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._output_callbacks:
            self._output_callbacks.remove(callback)
            
    async def write_output(self, data: str) -> None:
        """Write data to output buffer and notify callbacks.
        
        Args:
            data: Output data
        """
        if self._closed:
            return
            
        # Add to buffer
        self._output_buffer.append(data)
        
        # Notify callbacks
        for callback in self._output_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error in output callback: {e}")
                
    async def queue_input(self, data: str) -> None:
        """Queue input data.
        
        Args:
            data: Input data
        """
        if not self._closed:
            await self._input_queue.put(data)
            
    async def get_input(self) -> Optional[str]:
        """Get queued input data.
        
        Returns:
            Input data or None if closed
        """
        if self._closed:
            return None
            
        try:
            return await self._input_queue.get()
        except asyncio.CancelledError:
            return None
            
    def get_output_buffer(self, lines: Optional[int] = None) -> list[str]:
        """Get output buffer contents.
        
        Args:
            lines: Number of lines to retrieve (None for all)
            
        Returns:
            List of output lines
        """
        if lines is None:
            return list(self._output_buffer)
        else:
            return list(self._output_buffer)[-lines:]
            
    def clear_output_buffer(self) -> None:
        """Clear output buffer."""
        self._output_buffer.clear()
        
    async def pipe_streams(
        self,
        read_func: Callable[[], str],
        write_func: Callable[[bytes], None]
    ) -> None:
        """Pipe data between read and write functions.
        
        Args:
            read_func: Function to read data
            write_func: Function to write data
        """
        # Create tasks for input and output
        input_task = asyncio.create_task(
            self._handle_input(write_func)
        )
        output_task = asyncio.create_task(
            self._handle_output(read_func)
        )
        
        try:
            await asyncio.gather(input_task, output_task)
        except asyncio.CancelledError:
            pass
        finally:
            input_task.cancel()
            output_task.cancel()
            
    async def _handle_input(self, write_func: Callable[[bytes], None]) -> None:
        """Handle input stream.
        
        Args:
            write_func: Function to write data
        """
        while not self._closed:
            try:
                data = await self.get_input()
                if data:
                    write_func(data.encode())
            except Exception as e:
                logger.error(f"Error handling input: {e}")
                
    async def _handle_output(self, read_func: Callable[[], str]) -> None:
        """Handle output stream.
        
        Args:
            read_func: Function to read data
        """
        while not self._closed:
            try:
                data = read_func()
                if data:
                    await self.write_output(data)
                else:
                    await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error handling output: {e}")
                
    def close(self) -> None:
        """Close I/O manager."""
        self._closed = True
        self._output_callbacks.clear()