"""Pexpect handler for terminal automation."""

import logging
import re
from typing import Optional, Union, List

import pexpect


logger = logging.getLogger(__name__)


class PexpectHandler:
    """Handles terminal automation using pexpect."""
    
    def __init__(self, pty_handler):
        """Initialize pexpect handler.
        
        Args:
            pty_handler: PTY handler instance
        """
        self.pty_handler = pty_handler
        self._buffer = ""
        self._patterns: List[re.Pattern] = []
        
    def send(self, data: str) -> None:
        """Send data to terminal.
        
        Args:
            data: Data to send
        """
        self.pty_handler.write(data.encode())
        
    def sendline(self, line: str = "") -> None:
        """Send line to terminal with newline.
        
        Args:
            line: Line to send
        """
        self.send(f"{line}\n")
        
    def expect(
        self,
        pattern: Union[str, re.Pattern, List[Union[str, re.Pattern]]],
        timeout: float = 30.0
    ) -> int:
        """Wait for pattern in output.
        
        Args:
            pattern: Pattern(s) to match
            timeout: Timeout in seconds
            
        Returns:
            Index of matched pattern
            
        Raises:
            TimeoutError: If pattern not found within timeout
        """
        # Convert patterns to list
        if isinstance(pattern, (str, re.Pattern)):
            patterns = [pattern]
        else:
            patterns = pattern
            
        # Compile string patterns
        compiled_patterns = []
        for p in patterns:
            if isinstance(p, str):
                compiled_patterns.append(re.compile(re.escape(p)))
            else:
                compiled_patterns.append(p)
                
        # Wait for match
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Read more data
            new_data = self.pty_handler.read()
            if new_data:
                self._buffer += new_data
                
            # Check patterns
            for i, pattern in enumerate(compiled_patterns):
                match = pattern.search(self._buffer)
                if match:
                    # Clear buffer up to match
                    self._buffer = self._buffer[match.end():]
                    return i
                    
            # Small delay to avoid busy loop
            time.sleep(0.1)
            
        raise TimeoutError(f"Pattern not found within {timeout} seconds")
        
    def expect_exact(
        self,
        pattern_list: List[str],
        timeout: float = 30.0
    ) -> int:
        """Wait for exact string in output.
        
        Args:
            pattern_list: List of exact strings to match
            timeout: Timeout in seconds
            
        Returns:
            Index of matched pattern
        """
        # Use exact string matching
        patterns = [re.compile(re.escape(p)) for p in pattern_list]
        return self.expect(patterns, timeout)
        
    def send_command(
        self,
        command: str,
        expect_prompt: bool = True,
        prompt: str = "$"
    ) -> str:
        """Send command and wait for completion.
        
        Args:
            command: Command to execute
            expect_prompt: Whether to wait for prompt
            prompt: Prompt pattern to wait for
            
        Returns:
            Command output
        """
        # Clear buffer
        self._buffer = ""
        
        # Send command
        self.sendline(command)
        
        if expect_prompt:
            # Wait for prompt
            self.expect(prompt)
            
        # Return captured output
        return self._buffer
        
    def interact(self) -> None:
        """Enter interactive mode (not implemented for containers)."""
        logger.warning("Interactive mode not implemented for container sessions")
        
    def close(self) -> None:
        """Close pexpect handler."""
        # Clear buffer
        self._buffer = ""
        self._patterns.clear()