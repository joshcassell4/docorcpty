"""Resource monitoring utilities."""

import asyncio
import logging
import psutil
from datetime import datetime
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitors system and container resources."""
    
    def __init__(self, interval: int = 5):
        """Initialize resource monitor.
        
        Args:
            interval: Monitoring interval in seconds
        """
        self.interval = interval
        self._monitoring = False
        self._current_stats: Dict[str, Any] = {}
        self._history: list[Dict[str, Any]] = []
        self._max_history = 100
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start_monitoring(self) -> None:
        """Start resource monitoring."""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info("Resource monitoring started")
            
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        if self._monitoring:
            self._monitoring = False
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            logger.info("Resource monitoring stopped")
            
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                stats = self._collect_stats()
                self._current_stats = stats
                
                # Add to history
                self._history.append(stats)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
                    
                await asyncio.sleep(self.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.interval)
                
    def _collect_stats(self) -> Dict[str, Any]:
        """Collect current system statistics.
        
        Returns:
            Dictionary of system statistics
        """
        try:
            # CPU stats
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory stats
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # Disk stats
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total
            
            # Network stats
            net_io = psutil.net_io_counters()
            net_sent = net_io.bytes_sent
            net_recv = net_io.bytes_recv
            
            # Process stats
            process = psutil.Process()
            process_memory = process.memory_info().rss
            process_cpu = process.cpu_percent()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                },
                "memory": {
                    "percent": memory_percent,
                    "used": memory_used,
                    "total": memory_total,
                },
                "disk": {
                    "percent": disk_percent,
                    "used": disk_used,
                    "total": disk_total,
                },
                "network": {
                    "sent": net_sent,
                    "received": net_recv,
                },
                "process": {
                    "memory": process_memory,
                    "cpu": process_cpu,
                },
            }
            
        except Exception as e:
            logger.error(f"Error collecting stats: {e}")
            return {}
            
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current statistics.
        
        Returns:
            Current system statistics
        """
        return self._current_stats
        
    def get_history(self, limit: Optional[int] = None) -> list[Dict[str, Any]]:
        """Get historical statistics.
        
        Args:
            limit: Number of entries to return
            
        Returns:
            List of historical statistics
        """
        if limit:
            return self._history[-limit:]
        return self._history
        
    def check_resource_limits(
        self,
        cpu_threshold: float = 90.0,
        memory_threshold: float = 90.0
    ) -> Dict[str, bool]:
        """Check if resources exceed thresholds.
        
        Args:
            cpu_threshold: CPU usage threshold percentage
            memory_threshold: Memory usage threshold percentage
            
        Returns:
            Dictionary of threshold violations
        """
        violations = {
            "cpu_exceeded": False,
            "memory_exceeded": False,
        }
        
        if self._current_stats:
            cpu_percent = self._current_stats.get("cpu", {}).get("percent", 0)
            memory_percent = self._current_stats.get("memory", {}).get("percent", 0)
            
            violations["cpu_exceeded"] = cpu_percent > cpu_threshold
            violations["memory_exceeded"] = memory_percent > memory_threshold
            
        return violations