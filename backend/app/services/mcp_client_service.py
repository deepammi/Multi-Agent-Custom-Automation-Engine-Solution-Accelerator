"""
Enhanced MCP Client Service with standardization features.
Provides proper MCP protocol implementation with connection pooling,
health monitoring, standardized error handling, and comprehensive logging.
"""

import logging
import asyncio
import json
import time
import random
import os
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

# Import official MCP client SDK
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP SDK not available. Install with: pip install mcp")

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base exception for MCP-related errors."""
    def __init__(self, message: str, service: str, error_code: str = None):
        self.service = service
        self.error_code = error_code
        super().__init__(message)


class MCPConnectionError(MCPError):
    """MCP server connection failures."""
    pass


class MCPToolNotFoundError(MCPError):
    """Requested tool not available."""
    pass


class MCPAuthenticationError(MCPError):
    """Authentication/authorization failures."""
    pass


class MCPTimeoutError(MCPError):
    """Tool call timeout."""
    pass


@dataclass
class ToolInfo:
    """Metadata about an MCP tool."""
    name: str
    service: str
    description: str
    parameters: Dict[str, Any]
    return_type: str
    category: str
    requires_auth: bool
    rate_limit: Optional[int] = None
    timeout: Optional[int] = None


@dataclass
class HealthStatus:
    """Health status of MCP client/server."""
    is_healthy: bool
    last_check: datetime
    response_time_ms: int
    available_tools: int
    error_message: Optional[str] = None
    connection_status: str = "connected"
    consecutive_failures: int = 0
    last_successful_call: Optional[datetime] = None
    uptime_percentage: float = 100.0
    
    
@dataclass
class ConnectionRecoveryConfig:
    """Configuration for connection recovery behavior."""
    max_retry_attempts: int = 5
    base_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    jitter_enabled: bool = True
    timeout_detection_threshold: int = 3  # consecutive timeouts before recovery
    health_check_failure_threshold: int = 3  # consecutive health check failures
    auto_recovery_enabled: bool = True


@dataclass 
class DiagnosticInfo:
    """Diagnostic information for troubleshooting MCP issues."""
    service_name: str
    connection_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    total_tool_calls: int = 0
    successful_tool_calls: int = 0
    failed_tool_calls: int = 0
    timeout_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    recovery_attempts: int = 0
    successful_recoveries: int = 0
    connection_history: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class ConnectionStatus(Enum):
    """MCP connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class BaseMCPClient:
    """
    Enhanced base MCP client implementation with standardization features.
    
    This service provides proper MCP protocol implementation with:
    - Connection pooling and lifecycle management
    - Health monitoring and automatic recovery
    - Standardized error handling and logging
    - Tool discovery and metadata management
    """
    
    def __init__(
        self, 
        service_name: str,
        server_command: str = "python3", 
        server_args: List[str] = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        health_check_interval: int = 60,
        recovery_config: Optional[ConnectionRecoveryConfig] = None
    ):
        """
        Initialize enhanced MCP client service.
        
        Args:
            service_name: Name of the service (e.g., "salesforce", "gmail")
            server_command: Command to start MCP server (e.g., "python3", "node")
            server_args: Arguments for server command
            timeout: Default timeout for operations in seconds
            retry_attempts: Number of retry attempts for failed operations
            health_check_interval: Health check interval in seconds
            recovery_config: Configuration for connection recovery behavior
        """
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK not available. Install with: pip install mcp")
        
        self.service_name = service_name
        self.server_command = server_command
        self.server_args = server_args or ["src/mcp_server/mcp_server.py"]
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.health_check_interval = health_check_interval
        self.recovery_config = recovery_config or ConnectionRecoveryConfig()
        
        # Connection state
        self._session = None
        self._read = None
        self._write = None
        self._connection_status = ConnectionStatus.DISCONNECTED
        self._last_health_check = None
        self._health_status = None
        
        # Tool registry
        self._available_tools = []
        self._tool_metadata = {}
        
        # Performance metrics
        self._connection_time = None
        self._last_tool_call_time = None
        self._tool_call_count = 0
        self._error_count = 0
        
        # Enhanced recovery and monitoring
        self._consecutive_timeouts = 0
        self._consecutive_health_failures = 0
        self._recovery_in_progress = False
        self._diagnostic_info = DiagnosticInfo(service_name=service_name)
        self._health_check_task = None
        self._recovery_callbacks: List[Callable] = []
        
        logger.info(
            f"Enhanced MCP client initialized",
            extra={
                "service": self.service_name,
                "server_command": self.server_command,
                "server_args": self.server_args,
                "timeout": self.timeout,
                "retry_attempts": self.retry_attempts
            }
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Connect to MCP server with retry logic and health monitoring."""
        start_time = time.time()
        
        for attempt in range(self.retry_attempts):
            try:
                self._connection_status = ConnectionStatus.CONNECTING
                
                # Create server parameters
                server_params = StdioServerParameters(
                    command=self.server_command,
                    args=self.server_args,
                    env=None
                )
                
                logger.info(
                    f"Connecting to MCP server (attempt {attempt + 1}/{self.retry_attempts})",
                    extra={
                        "service": self.service_name,
                        "server_command": self.server_command,
                        "server_args": self.server_args,
                        "attempt": attempt + 1
                    }
                )
                
                # Connect to the MCP server with timeout
                connect_task = stdio_client(server_params).__aenter__()
                self._read, self._write = await asyncio.wait_for(connect_task, timeout=self.timeout)
                
                # Create client session
                session_task = ClientSession(self._read, self._write).__aenter__()
                self._session = await asyncio.wait_for(session_task, timeout=self.timeout)
                
                # Initialize the connection (required by MCP protocol)
                init_task = self._session.initialize()
                await asyncio.wait_for(init_task, timeout=self.timeout)
                
                # List available tools for capability negotiation
                tools_task = self._session.list_tools()
                tools_result = await asyncio.wait_for(tools_task, timeout=self.timeout)
                
                # Process tool metadata
                self._available_tools = []
                self._tool_metadata = {}
                
                for tool in tools_result.tools:
                    self._available_tools.append(tool.name)
                    self._tool_metadata[tool.name] = ToolInfo(
                        name=tool.name,
                        service=self.service_name,
                        description=getattr(tool, 'description', ''),
                        parameters=getattr(tool, 'inputSchema', {}).get('properties', {}),
                        return_type="dict",
                        category="external_api",
                        requires_auth=True  # Assume auth required by default
                    )
                
                self._connection_status = ConnectionStatus.CONNECTED
                self._connection_time = time.time() - start_time
                
                # Update diagnostic info
                self._diagnostic_info.connection_attempts += 1
                self._diagnostic_info.successful_connections += 1
                self._diagnostic_info.connection_history.append({
                    "timestamp": datetime.now(),
                    "status": "connected",
                    "attempt": attempt + 1,
                    "connection_time_ms": int(self._connection_time * 1000)
                })
                
                logger.info(
                    f"✅ MCP connection established successfully",
                    extra={
                        "service": self.service_name,
                        "available_tools": self._available_tools,
                        "tool_count": len(self._available_tools),
                        "connection_time_ms": int(self._connection_time * 1000),
                        "attempt": attempt + 1
                    }
                )
                
                # Perform initial health check
                await self._update_health_status()
                
                # Start continuous health monitoring
                if self._health_check_task is None or self._health_check_task.done():
                    self._health_check_task = asyncio.create_task(self._monitor_health_continuously())
                
                return
                
            except asyncio.TimeoutError:
                self._connection_status = ConnectionStatus.FAILED
                error_msg = f"Connection timeout after {self.timeout}s"
                logger.error(
                    f"❌ MCP connection timeout (attempt {attempt + 1})",
                    extra={
                        "service": self.service_name,
                        "error": error_msg,
                        "attempt": attempt + 1,
                        "timeout": self.timeout
                    }
                )
                if attempt == self.retry_attempts - 1:
                    raise MCPConnectionError(error_msg, self.service_name, "TIMEOUT")
                    
            except Exception as e:
                self._connection_status = ConnectionStatus.FAILED
                error_msg = f"Connection failed: {str(e)}"
                logger.error(
                    f"❌ MCP connection failed (attempt {attempt + 1})",
                    extra={
                        "service": self.service_name,
                        "error": error_msg,
                        "error_type": type(e).__name__,
                        "attempt": attempt + 1
                    }
                )
                if attempt == self.retry_attempts - 1:
                    raise MCPConnectionError(error_msg, self.service_name, "CONNECTION_FAILED")
            
            # Enhanced exponential backoff with jitter
            if attempt < self.retry_attempts - 1:
                backoff_time = self._calculate_backoff_time(attempt)
                logger.info(f"Retrying connection in {backoff_time:.2f}s...")
                await asyncio.sleep(backoff_time)
                
                # Update diagnostic info
                self._diagnostic_info.connection_attempts += 1
                self._diagnostic_info.failed_connections += 1
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server with proper cleanup."""
        try:
            self._connection_status = ConnectionStatus.DISCONNECTED
            
            # Stop health monitoring
            if self._health_check_task and not self._health_check_task.done():
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Update diagnostic info
            self._diagnostic_info.connection_history.append({
                "timestamp": datetime.now(),
                "status": "disconnected",
                "tool_calls_made": self._tool_call_count,
                "errors_encountered": self._error_count
            })
            
            if self._session:
                await self._session.__aexit__(None, None, None)
                self._session = None
            
            if self._read and hasattr(self._read, 'close'):
                await self._read.close()
                self._read = None
                
            if self._write and hasattr(self._write, 'close'):
                await self._write.close()
                self._write = None
            
            logger.info(
                "✅ MCP connection closed successfully",
                extra={
                    "service": self.service_name,
                    "tool_calls_made": self._tool_call_count,
                    "errors_encountered": self._error_count
                }
            )
            
        except Exception as e:
            logger.warning(
                f"⚠️ Error during MCP disconnect: {e}",
                extra={
                    "service": self.service_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def _update_health_status(self) -> None:
        """Update health status with current metrics."""
        start_time = time.time()
        
        try:
            # Test connection by listing tools
            if self._session:
                tools_result = await asyncio.wait_for(
                    self._session.list_tools(), 
                    timeout=5
                )
                response_time = int((time.time() - start_time) * 1000)
                
                self._health_status = HealthStatus(
                    is_healthy=True,
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    available_tools=len(tools_result.tools),
                    connection_status=self._connection_status.value,
                    consecutive_failures=0,
                    last_successful_call=datetime.now(),
                    uptime_percentage=self._calculate_uptime_percentage()
                )
                
                # Reset consecutive health failures on success
                self._consecutive_health_failures = 0
                
            else:
                self._health_status = HealthStatus(
                    is_healthy=False,
                    last_check=datetime.now(),
                    response_time_ms=0,
                    available_tools=0,
                    error_message="No active session",
                    connection_status=self._connection_status.value,
                    consecutive_failures=self._consecutive_health_failures,
                    uptime_percentage=self._calculate_uptime_percentage()
                )
                
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            self._consecutive_health_failures += 1
            
            self._health_status = HealthStatus(
                is_healthy=False,
                last_check=datetime.now(),
                response_time_ms=response_time,
                available_tools=0,
                error_message=str(e),
                connection_status=self._connection_status.value,
                consecutive_failures=self._consecutive_health_failures,
                uptime_percentage=self._calculate_uptime_percentage()
            )
        
        self._last_health_check = datetime.now()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool with enhanced error handling and logging.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result as dictionary
            
        Raises:
            MCPConnectionError: If session not initialized
            MCPToolNotFoundError: If tool not available
            MCPTimeoutError: If tool call times out
            MCPError: For other MCP-related errors
        """
        if not self._session:
            raise MCPConnectionError("MCP session not initialized", self.service_name, "NO_SESSION")
        
        if tool_name not in self._available_tools:
            error_msg = f"Tool '{tool_name}' not available. Available tools: {self._available_tools}"
            logger.warning(
                error_msg,
                extra={
                    "service": self.service_name,
                    "requested_tool": tool_name,
                    "available_tools": self._available_tools
                }
            )
            raise MCPToolNotFoundError(error_msg, self.service_name, "TOOL_NOT_FOUND")
        
        start_time = time.time()
        request_id = f"{self.service_name}_{tool_name}_{int(start_time * 1000)}"
        
        try:
            logger.info(
                f"Calling MCP tool: {tool_name}",
                extra={
                    "service": self.service_name,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "request_id": request_id
                }
            )
            
            # Call the tool using proper MCP protocol with timeout
            tool_call_task = self._session.call_tool(tool_name, arguments)
            result = await asyncio.wait_for(tool_call_task, timeout=self.timeout)
            
            # Parse result content
            if hasattr(result, 'content') and result.content:
                # Extract text content from MCP result
                content = result.content[0].text if result.content else "{}"
                try:
                    parsed_result = json.loads(content)
                except json.JSONDecodeError:
                    # If not JSON, return as text
                    parsed_result = {"result": content}
                
                execution_time = int((time.time() - start_time) * 1000)
                self._tool_call_count += 1
                self._last_tool_call_time = datetime.now()
                
                # Reset consecutive timeouts on successful call
                self._consecutive_timeouts = 0
                
                # Update diagnostic info
                self._diagnostic_info.successful_tool_calls += 1
                self._diagnostic_info.total_tool_calls += 1
                
                logger.info(
                    f"✅ MCP tool '{tool_name}' completed successfully",
                    extra={
                        "service": self.service_name,
                        "tool_name": tool_name,
                        "execution_time_ms": execution_time,
                        "request_id": request_id,
                        "result_size": len(str(parsed_result))
                    }
                )
                return parsed_result
            else:
                error_msg = f"MCP tool '{tool_name}' returned empty result"
                logger.warning(
                    error_msg,
                    extra={
                        "service": self.service_name,
                        "tool_name": tool_name,
                        "request_id": request_id
                    }
                )
                return {"error": error_msg}
                
        except asyncio.TimeoutError:
            self._error_count += 1
            self._consecutive_timeouts += 1
            self._diagnostic_info.timeout_count += 1
            self._diagnostic_info.failed_tool_calls += 1
            self._diagnostic_info.total_tool_calls += 1
            
            error_msg = f"Tool call '{tool_name}' timed out after {self.timeout}s"
            logger.error(
                error_msg,
                extra={
                    "service": self.service_name,
                    "tool_name": tool_name,
                    "timeout": self.timeout,
                    "request_id": request_id,
                    "consecutive_timeouts": self._consecutive_timeouts
                }
            )
            
            # Trigger timeout detection and recovery
            asyncio.create_task(self._detect_and_recover_from_timeouts())
            
            raise MCPTimeoutError(error_msg, self.service_name, "TIMEOUT")
            
        except json.JSONDecodeError as e:
            self._error_count += 1
            self._diagnostic_info.failed_tool_calls += 1
            self._diagnostic_info.total_tool_calls += 1
            self._diagnostic_info.last_error = str(e)
            self._diagnostic_info.last_error_time = datetime.now()
            
            error_msg = f"Failed to parse MCP tool result as JSON: {e}"
            logger.error(
                error_msg,
                extra={
                    "service": self.service_name,
                    "tool_name": tool_name,
                    "error": str(e),
                    "request_id": request_id
                }
            )
            raise MCPError(error_msg, self.service_name, "JSON_PARSE_ERROR")
            
        except Exception as e:
            self._error_count += 1
            self._diagnostic_info.failed_tool_calls += 1
            self._diagnostic_info.total_tool_calls += 1
            self._diagnostic_info.last_error = str(e)
            self._diagnostic_info.last_error_time = datetime.now()
            
            error_msg = f"MCP tool call failed: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "service": self.service_name,
                    "tool_name": tool_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "request_id": request_id
                }
            )
            raise MCPError(error_msg, self.service_name, "TOOL_CALL_FAILED")
    
    async def list_available_tools(self) -> List[str]:
        """Get list of available tools from MCP server."""
        if not self._session:
            raise MCPConnectionError("MCP session not initialized", self.service_name, "NO_SESSION")
        
        try:
            tools_result = await asyncio.wait_for(
                self._session.list_tools(), 
                timeout=self.timeout
            )
            return [tool.name for tool in tools_result.tools]
        except Exception as e:
            logger.error(
                f"Failed to list MCP tools: {e}",
                extra={
                    "service": self.service_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPError(f"Failed to list tools: {e}", self.service_name, "LIST_TOOLS_FAILED")
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolInfo]:
        """Get metadata for a specific tool."""
        return self._tool_metadata.get(tool_name)
    
    def get_all_tool_metadata(self) -> Dict[str, ToolInfo]:
        """Get metadata for all available tools."""
        return self._tool_metadata.copy()
    
    async def check_health(self) -> HealthStatus:
        """Check MCP server health and connectivity with comprehensive metrics."""
        # Update health status if needed
        if (not self._last_health_check or 
            datetime.now() - self._last_health_check > timedelta(seconds=self.health_check_interval)):
            await self._update_health_status()
        
        return self._health_status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the MCP client."""
        return {
            "service": self.service_name,
            "connection_status": self._connection_status.value,
            "connection_time_ms": int(self._connection_time * 1000) if self._connection_time else None,
            "tool_call_count": self._tool_call_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._tool_call_count, 1),
            "last_tool_call": self._last_tool_call_time.isoformat() if self._last_tool_call_time else None,
            "available_tools_count": len(self._available_tools),
            "health_status": self._health_status.__dict__ if self._health_status else None
        }
    
    async def reconnect(self) -> None:
        """Reconnect to MCP server with cleanup."""
        if self._recovery_in_progress:
            logger.info(f"Recovery already in progress for {self.service_name}")
            return
            
        logger.info(
            f"Reconnecting MCP client for service: {self.service_name}",
            extra={"service": self.service_name}
        )
        
        self._recovery_in_progress = True
        self._connection_status = ConnectionStatus.RECONNECTING
        self._diagnostic_info.recovery_attempts += 1
        
        try:
            # Clean disconnect first
            await self.disconnect()
            
            # Reset metrics
            self._error_count = 0
            self._tool_call_count = 0
            self._consecutive_timeouts = 0
            self._consecutive_health_failures = 0
            
            # Reconnect with enhanced retry logic
            await self.connect()
            
            # Mark successful recovery
            self._diagnostic_info.successful_recoveries += 1
            
            # Notify recovery callbacks
            await self._notify_recovery_callbacks("reconnected")
            
            logger.info(f"Successfully reconnected MCP client: {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to reconnect MCP client {self.service_name}: {e}")
            self._diagnostic_info.last_error = str(e)
            self._diagnostic_info.last_error_time = datetime.now()
            raise
        finally:
            self._recovery_in_progress = False
    
    def _calculate_backoff_time(self, attempt: int) -> float:
        """Calculate backoff time with exponential backoff and optional jitter."""
        base_time = min(
            self.recovery_config.base_backoff_seconds * (self.recovery_config.backoff_multiplier ** attempt),
            self.recovery_config.max_backoff_seconds
        )
        
        if self.recovery_config.jitter_enabled:
            # Add jitter to prevent thundering herd
            jitter = random.uniform(0, base_time * 0.1)
            return base_time + jitter
        
        return base_time
    
    async def _detect_and_recover_from_timeouts(self) -> None:
        """Detect consecutive timeouts and trigger recovery if needed."""
        if self._consecutive_timeouts >= self.recovery_config.timeout_detection_threshold:
            logger.warning(
                f"Detected {self._consecutive_timeouts} consecutive timeouts for {self.service_name}, triggering recovery"
            )
            
            if self.recovery_config.auto_recovery_enabled:
                try:
                    await self.reconnect()
                    self._consecutive_timeouts = 0
                except Exception as e:
                    logger.error(f"Auto-recovery failed for {self.service_name}: {e}")
    
    async def _monitor_health_continuously(self) -> None:
        """Continuously monitor health and trigger recovery if needed."""
        while self._connection_status != ConnectionStatus.DISCONNECTED:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                if self._connection_status == ConnectionStatus.CONNECTED:
                    health = await self.check_health()
                    
                    if not health.is_healthy:
                        self._consecutive_health_failures += 1
                        
                        if (self._consecutive_health_failures >= self.recovery_config.health_check_failure_threshold 
                            and self.recovery_config.auto_recovery_enabled):
                            
                            logger.warning(
                                f"Health check failures threshold reached for {self.service_name}, triggering recovery"
                            )
                            await self.reconnect()
                    else:
                        self._consecutive_health_failures = 0
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring for {self.service_name}: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    def add_recovery_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback to be notified of recovery events."""
        self._recovery_callbacks.append(callback)
    
    async def _notify_recovery_callbacks(self, event_type: str) -> None:
        """Notify all registered recovery callbacks."""
        for callback in self._recovery_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type)
                else:
                    callback(event_type)
            except Exception as e:
                logger.error(f"Error in recovery callback: {e}")
    
    def get_diagnostic_info(self) -> DiagnosticInfo:
        """Get comprehensive diagnostic information for troubleshooting."""
        # Update performance metrics
        if self._tool_call_count > 0:
            self._diagnostic_info.performance_metrics.update({
                "success_rate": (self._diagnostic_info.successful_tool_calls / self._diagnostic_info.total_tool_calls) * 100,
                "error_rate": (self._diagnostic_info.failed_tool_calls / self._diagnostic_info.total_tool_calls) * 100,
                "average_response_time": self._health_status.response_time_ms if self._health_status else 0,
                "uptime_percentage": self._calculate_uptime_percentage()
            })
        
        return self._diagnostic_info
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate uptime percentage based on connection history."""
        if not self._diagnostic_info.connection_history:
            return 100.0 if self._connection_status == ConnectionStatus.CONNECTED else 0.0
        
        total_time = 0
        connected_time = 0
        
        for i, event in enumerate(self._diagnostic_info.connection_history):
            if i < len(self._diagnostic_info.connection_history) - 1:
                next_event = self._diagnostic_info.connection_history[i + 1]
                duration = (next_event["timestamp"] - event["timestamp"]).total_seconds()
                total_time += duration
                
                if event["status"] == "connected":
                    connected_time += duration
        
        return (connected_time / total_time * 100) if total_time > 0 else 100.0
    
    async def run_diagnostic_tests(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic tests for troubleshooting."""
        diagnostic_results = {
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Connection status
        diagnostic_results["tests"]["connection_status"] = {
            "status": self._connection_status.value,
            "healthy": self._connection_status == ConnectionStatus.CONNECTED
        }
        
        # Test 2: Health check
        try:
            health = await self.check_health()
            diagnostic_results["tests"]["health_check"] = {
                "healthy": health.is_healthy,
                "response_time_ms": health.response_time_ms,
                "available_tools": health.available_tools,
                "error": health.error_message
            }
        except Exception as e:
            diagnostic_results["tests"]["health_check"] = {
                "healthy": False,
                "error": str(e)
            }
        
        # Test 3: Tool listing
        try:
            tools = await self.list_available_tools()
            diagnostic_results["tests"]["tool_listing"] = {
                "success": True,
                "tool_count": len(tools),
                "tools": tools
            }
        except Exception as e:
            diagnostic_results["tests"]["tool_listing"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test 4: Performance metrics
        diagnostic_results["tests"]["performance"] = self.get_performance_metrics()
        
        # Test 5: Diagnostic info
        diagnostic_results["diagnostic_info"] = self.get_diagnostic_info().__dict__
        
        return diagnostic_results
    
    def get_diagnostic_tools(self) -> "MCPDiagnosticTools":
        """Get diagnostic tools instance for this client."""
        return MCPDiagnosticTools(self)


# Maintain backward compatibility with original class name
MCPClientService = BaseMCPClient


class MCPDiagnosticTools:
    """
    Comprehensive diagnostic tools for troubleshooting MCP issues.
    
    Provides utilities for testing connections, analyzing performance,
    and generating diagnostic reports.
    """
    
    def __init__(self, client: BaseMCPClient):
        self.client = client
        self.logger = logging.getLogger(f"{__name__}.{client.service_name}")
    
    async def run_connection_test(self) -> Dict[str, Any]:
        """Run comprehensive connection test."""
        test_results = {
            "service": self.client.service_name,
            "timestamp": datetime.now().isoformat(),
            "connection_test": {}
        }
        
        try:
            # Test basic connectivity
            start_time = time.time()
            health = await self.client.check_health()
            connection_time = int((time.time() - start_time) * 1000)
            
            test_results["connection_test"] = {
                "success": health.is_healthy,
                "response_time_ms": connection_time,
                "available_tools": health.available_tools,
                "connection_status": health.connection_status,
                "error": health.error_message
            }
            
        except Exception as e:
            test_results["connection_test"] = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        return test_results
    
    async def run_performance_test(self, test_duration: int = 30) -> Dict[str, Any]:
        """Run performance test over specified duration."""
        test_results = {
            "service": self.client.service_name,
            "test_duration_seconds": test_duration,
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": {}
        }
        
        start_time = time.time()
        health_checks = []
        errors = []
        
        try:
            while time.time() - start_time < test_duration:
                try:
                    check_start = time.time()
                    health = await self.client.check_health()
                    check_time = int((time.time() - check_start) * 1000)
                    
                    health_checks.append({
                        "timestamp": datetime.now().isoformat(),
                        "healthy": health.is_healthy,
                        "response_time_ms": check_time,
                        "available_tools": health.available_tools
                    })
                    
                except Exception as e:
                    errors.append({
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                
                await asyncio.sleep(1)  # Check every second
            
            # Calculate metrics
            if health_checks:
                response_times = [check["response_time_ms"] for check in health_checks]
                healthy_checks = [check for check in health_checks if check["healthy"]]
                
                test_results["performance_metrics"] = {
                    "total_checks": len(health_checks),
                    "successful_checks": len(healthy_checks),
                    "failed_checks": len(health_checks) - len(healthy_checks),
                    "success_rate": (len(healthy_checks) / len(health_checks)) * 100,
                    "avg_response_time_ms": sum(response_times) / len(response_times),
                    "min_response_time_ms": min(response_times),
                    "max_response_time_ms": max(response_times),
                    "total_errors": len(errors)
                }
            
            test_results["health_checks"] = health_checks
            test_results["errors"] = errors
            
        except Exception as e:
            test_results["performance_metrics"] = {
                "error": str(e),
                "error_type": type(e).__name__
            }
        
        return test_results
    
    async def run_tool_availability_test(self) -> Dict[str, Any]:
        """Test availability and responsiveness of all tools."""
        test_results = {
            "service": self.client.service_name,
            "timestamp": datetime.now().isoformat(),
            "tool_tests": {}
        }
        
        try:
            # Get available tools
            tools = await self.client.list_available_tools()
            
            for tool_name in tools:
                tool_test = {
                    "available": True,
                    "metadata": None,
                    "test_call": None
                }
                
                # Get tool metadata
                try:
                    metadata = self.client.get_tool_metadata(tool_name)
                    if metadata:
                        tool_test["metadata"] = {
                            "description": metadata.description,
                            "parameters": list(metadata.parameters.keys()) if metadata.parameters else [],
                            "requires_auth": metadata.requires_auth,
                            "category": metadata.category
                        }
                except Exception as e:
                    tool_test["metadata_error"] = str(e)
                
                # Note: We don't actually call tools in diagnostic mode to avoid side effects
                # In a real implementation, you might want to have "test" versions of tools
                
                test_results["tool_tests"][tool_name] = tool_test
            
            test_results["summary"] = {
                "total_tools": len(tools),
                "available_tools": len([t for t in test_results["tool_tests"].values() if t["available"]])
            }
            
        except Exception as e:
            test_results["error"] = str(e)
            test_results["error_type"] = type(e).__name__
        
        return test_results
    
    def generate_diagnostic_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report."""
        diagnostic_info = self.client.get_diagnostic_info()
        performance_metrics = self.client.get_performance_metrics()
        
        report = {
            "service": self.client.service_name,
            "report_timestamp": datetime.now().isoformat(),
            "connection_status": self.client._connection_status.value,
            "health_status": self.client._health_status.__dict__ if self.client._health_status else None,
            "diagnostic_summary": {
                "total_connection_attempts": diagnostic_info.connection_attempts,
                "successful_connections": diagnostic_info.successful_connections,
                "failed_connections": diagnostic_info.failed_connections,
                "connection_success_rate": (
                    (diagnostic_info.successful_connections / diagnostic_info.connection_attempts * 100) 
                    if diagnostic_info.connection_attempts > 0 else 0
                ),
                "total_tool_calls": diagnostic_info.total_tool_calls,
                "successful_tool_calls": diagnostic_info.successful_tool_calls,
                "failed_tool_calls": diagnostic_info.failed_tool_calls,
                "tool_success_rate": (
                    (diagnostic_info.successful_tool_calls / diagnostic_info.total_tool_calls * 100)
                    if diagnostic_info.total_tool_calls > 0 else 0
                ),
                "timeout_count": diagnostic_info.timeout_count,
                "recovery_attempts": diagnostic_info.recovery_attempts,
                "successful_recoveries": diagnostic_info.successful_recoveries,
                "last_error": diagnostic_info.last_error,
                "last_error_time": diagnostic_info.last_error_time.isoformat() if diagnostic_info.last_error_time else None
            },
            "performance_metrics": performance_metrics,
            "connection_history": [
                {
                    **event,
                    "timestamp": event["timestamp"].isoformat() if isinstance(event["timestamp"], datetime) else event["timestamp"]
                }
                for event in diagnostic_info.connection_history
            ],
            "recommendations": self._generate_recommendations(diagnostic_info, performance_metrics)
        }
        
        return report
    
    def _generate_recommendations(self, diagnostic_info: DiagnosticInfo, performance_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on diagnostic data."""
        recommendations = []
        
        # Connection reliability recommendations
        if diagnostic_info.connection_attempts > 0:
            success_rate = diagnostic_info.successful_connections / diagnostic_info.connection_attempts
            if success_rate < 0.9:
                recommendations.append(
                    f"Connection success rate is {success_rate:.1%}. Consider checking network connectivity and server availability."
                )
        
        # Tool call performance recommendations
        if diagnostic_info.total_tool_calls > 0:
            tool_success_rate = diagnostic_info.successful_tool_calls / diagnostic_info.total_tool_calls
            if tool_success_rate < 0.95:
                recommendations.append(
                    f"Tool call success rate is {tool_success_rate:.1%}. Review error logs and consider increasing timeouts."
                )
        
        # Timeout recommendations
        if diagnostic_info.timeout_count > 0:
            timeout_rate = diagnostic_info.timeout_count / max(diagnostic_info.total_tool_calls, 1)
            if timeout_rate > 0.1:
                recommendations.append(
                    f"High timeout rate ({timeout_rate:.1%}). Consider increasing timeout values or checking server performance."
                )
        
        # Recovery recommendations
        if diagnostic_info.recovery_attempts > 0:
            recovery_success_rate = diagnostic_info.successful_recoveries / diagnostic_info.recovery_attempts
            if recovery_success_rate < 0.8:
                recommendations.append(
                    f"Recovery success rate is {recovery_success_rate:.1%}. Review recovery configuration and server stability."
                )
        
        # Performance recommendations
        if performance_metrics.get("health_status") and performance_metrics["health_status"].get("response_time_ms", 0) > 5000:
            recommendations.append(
                "High response times detected. Consider optimizing server performance or network connectivity."
            )
        
        if not recommendations:
            recommendations.append("No issues detected. System appears to be operating normally.")
        
        return recommendations


class BillComMCPClient:
    """
    Bill.com specific MCP client using proper FastMCP HTTP transport.
    
    This connects to the existing HTTP MCP server using the official FastMCP Client.
    """
    
    def __init__(self):
        self.base_url = "http://localhost:9000/mcp"
        self._client = None
        self._connected = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        try:
            from fastmcp import Client
            self._client = Client(self.base_url)
            await self._client.__aenter__()
            self._connected = True
            logger.info(f"✅ Bill.com MCP client connected to {self.base_url}")
            return self
        except ImportError:
            logger.error("FastMCP not available. Install with: pip install fastmcp")
            raise
        except Exception as e:
            logger.error(f"Failed to connect Bill.com MCP client: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client and self._connected:
            try:
                await self._client.__aexit__(exc_type, exc_val, exc_tb)
                self._connected = False
                logger.info("✅ Bill.com MCP client disconnected")
            except Exception as e:
                logger.warning(f"Error disconnecting Bill.com MCP client: {e}")
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via FastMCP Client."""
        if not self._client or not self._connected:
            raise Exception("Bill.com MCP client not connected")
        
        try:
            logger.info(f"Calling Bill.com MCP tool: {tool_name}")
            result = await self._client.call_tool(tool_name, arguments)
            
            # FastMCP Client returns the result directly
            if isinstance(result, dict):
                return {"success": True, "result": result}
            elif isinstance(result, str):
                return {"success": True, "result": result}
            else:
                return {"success": True, "result": str(result)}
                
        except Exception as e:
            logger.error(f"Bill.com MCP tool call failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_invoices(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        vendor_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get invoices from Bill.com using proper MCP protocol."""
        return await self._call_mcp_tool("get_bill_com_invoices", {
            "start_date": start_date,
            "end_date": end_date,
            "vendor_name": vendor_name,
            "status": status,
            "limit": limit
        })
    
    async def search_invoices(
        self,
        search_term: str,
        search_type: str = "invoice_number"
    ) -> Dict[str, Any]:
        """Search invoices using proper MCP protocol."""
        return await self._call_mcp_tool("search_bill_com_invoices", {
            "query": search_term,
            "search_type": search_type
        })
    
    async def get_vendors(self, limit: int = 15) -> Dict[str, Any]:
        """Get vendors using proper MCP protocol."""
        return await self._call_mcp_tool("get_bill_com_vendors", {
            "limit": limit
        })
    
    async def get_audit_trail(
        self,
        entity_id: str,
        entity_type: str = "invoice",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get audit trail using proper MCP protocol."""
        return await self._call_mcp_tool("get_audit_trail", {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        })
    
    async def detect_audit_exceptions(
        self,
        entity_type: str = "invoice",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        severity_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detect audit exceptions using proper MCP protocol."""
        return await self._call_mcp_tool("detect_audit_exceptions", {
            "entity_type": entity_type,
            "start_date": start_date,
            "end_date": end_date,
            "severity_filter": severity_filter
        })
    
    async def generate_audit_report(
        self,
        entity_ids: List[str],
        entity_type: str = "invoice",
        include_exceptions: bool = True,
        format_type: str = "summary"
    ) -> Dict[str, Any]:
        """Generate audit report using proper MCP protocol."""
        return await self._call_mcp_tool("generate_audit_report", {
            "entity_ids": entity_ids,
            "entity_type": entity_type,
            "include_exceptions": include_exceptions,
            "format_type": format_type
        })
    
    async def check_bill_com_health(self) -> Dict[str, Any]:
        """Check Bill.com service health using FastMCP Client."""
        try:
            if not self._client or not self._connected:
                # Try to connect if not already connected
                await self.__aenter__()
            
            logger.info("Bill.com health check via FastMCP Client")
            
            result = await self._client.call_tool("bill_com_health_check_tool", {"comprehensive": False})
            
            logger.info(f"Health check result: {result}")
            
            # Parse the result
            if isinstance(result, dict):
                health_data = result
            elif isinstance(result, str):
                try:
                    import json
                    health_data = json.loads(result)
                except:
                    health_data = {"status": result}
            else:
                health_data = {"status": str(result)}
            
            return {
                "success": True,
                "error": None,
                "response_time_ms": 0,
                "available_tools": 0,
                "connection_status": "connected",
                "health_data": health_data
            }
            
        except Exception as e:
            logger.error(f"Exception in Bill.com health check: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": 0,
                "available_tools": 0,
                "connection_status": "failed"
            }


# Global instance for backward compatibility
_bill_com_client = None

async def get_bill_com_service() -> BillComMCPClient:
    """
    Get Bill.com MCP client instance.
    
    This function provides backward compatibility while using proper MCP protocol.
    """
    global _bill_com_client
    
    if _bill_com_client is None:
        _bill_com_client = BillComMCPClient()
    
    return _bill_com_client


# Backward compatibility wrapper
class BillComIntegrationServiceLegacy:
    """
    Legacy wrapper that maintains the old interface but uses proper MCP protocol.
    
    This allows existing code to work without changes while using correct MCP implementation.
    """
    
    def __init__(self):
        self._client = None
    
    async def _get_client(self) -> BillComMCPClient:
        """Get or create MCP client."""
        if self._client is None:
            self._client = BillComMCPClient()
            await self._client.__aenter__()
        return self._client
    
    async def get_invoices(self, **kwargs) -> Dict[str, Any]:
        """Legacy interface for get_invoices."""
        client = await self._get_client()
        return await client.get_invoices(**kwargs)
    
    async def search_invoices(self, **kwargs) -> Dict[str, Any]:
        """Legacy interface for search_invoices."""
        client = await self._get_client()
        return await client.search_invoices(**kwargs)
    
    async def get_vendors(self, **kwargs) -> Dict[str, Any]:
        """Legacy interface for get_vendors."""
        client = await self._get_client()
        return await client.get_vendors(**kwargs)
    
    async def get_audit_trail(self, **kwargs) -> Dict[str, Any]:
        """Legacy interface for get_audit_trail."""
        client = await self._get_client()
        return await client.get_audit_trail(**kwargs)
    
    async def detect_audit_exceptions(self, **kwargs) -> Dict[str, Any]:
        """Legacy interface for detect_audit_exceptions."""
        client = await self._get_client()
        return await client.detect_audit_exceptions(**kwargs)
    
    async def generate_audit_report(self, **kwargs) -> Dict[str, Any]:
        """Legacy interface for generate_audit_report."""
        client = await self._get_client()
        return await client.generate_audit_report(**kwargs)
    
    async def check_bill_com_health(self) -> Dict[str, Any]:
        """Legacy interface for health check."""
        client = await self._get_client()
        return await client.check_bill_com_health()


class ToolRegistry:
    """
    Registry for all available MCP tools across services.
    
    Provides centralized tool discovery, metadata management,
    and conflict resolution for tools from multiple services.
    """
    
    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}
        self.service_tools: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()
        
        logger.info("Tool registry initialized")
    
    async def register_service(self, service_name: str, client: BaseMCPClient) -> None:
        """
        Register all tools from an MCP service.
        
        Args:
            service_name: Name of the service
            client: MCP client instance
        """
        async with self._lock:
            try:
                # Get tool metadata from client
                tool_metadata = client.get_all_tool_metadata()
                
                # Register each tool
                service_tool_names = []
                for tool_name, tool_info in tool_metadata.items():
                    # Handle naming conflicts
                    registered_name = self._resolve_tool_name_conflict(tool_name, service_name)
                    
                    # Update tool info with resolved name
                    resolved_tool_info = ToolInfo(
                        name=registered_name,
                        service=service_name,
                        description=tool_info.description,
                        parameters=tool_info.parameters,
                        return_type=tool_info.return_type,
                        category=tool_info.category,
                        requires_auth=tool_info.requires_auth,
                        rate_limit=tool_info.rate_limit,
                        timeout=tool_info.timeout
                    )
                    
                    self.tools[registered_name] = resolved_tool_info
                    service_tool_names.append(registered_name)
                
                self.service_tools[service_name] = service_tool_names
                
                logger.info(
                    f"Registered {len(service_tool_names)} tools for service: {service_name}",
                    extra={
                        "service": service_name,
                        "tools": service_tool_names,
                        "total_tools": len(self.tools)
                    }
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to register service tools: {e}",
                    extra={
                        "service": service_name,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                raise MCPError(f"Tool registration failed: {e}", service_name, "REGISTRATION_FAILED")
    
    def _resolve_tool_name_conflict(self, tool_name: str, service_name: str) -> str:
        """
        Resolve tool name conflicts by prefixing with service name if needed.
        
        Args:
            tool_name: Original tool name
            service_name: Service name
            
        Returns:
            Resolved tool name
        """
        if tool_name not in self.tools:
            return tool_name
        
        # Conflict detected - use service prefix
        prefixed_name = f"{service_name}_{tool_name}"
        
        logger.warning(
            f"Tool name conflict resolved: '{tool_name}' -> '{prefixed_name}'",
            extra={
                "original_name": tool_name,
                "resolved_name": prefixed_name,
                "service": service_name,
                "existing_service": self.tools[tool_name].service
            }
        )
        
        return prefixed_name
    
    def get_tools_by_service(self, service_name: str) -> List[ToolInfo]:
        """Get all tools for a specific service."""
        tool_names = self.service_tools.get(service_name, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def find_tool(self, tool_name: str) -> Optional[ToolInfo]:
        """Find tool by name across all services."""
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, ToolInfo]:
        """Get all registered tools."""
        return self.tools.copy()
    
    def get_services(self) -> List[str]:
        """Get list of registered services."""
        return list(self.service_tools.keys())
    
    def get_tool_count_by_service(self) -> Dict[str, int]:
        """Get tool count for each service."""
        return {service: len(tools) for service, tools in self.service_tools.items()}


class ConnectionPool:
    """
    Connection pool for managing MCP client connections.
    
    Provides connection reuse, lifecycle management, and automatic cleanup.
    """
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections: Dict[str, BaseMCPClient] = {}
        self.connection_usage: Dict[str, int] = {}
        self._lock = asyncio.Lock()
        
        logger.info(f"Connection pool initialized with max_connections: {max_connections}")
    
    async def get_connection(self, service_name: str, client_factory) -> BaseMCPClient:
        """
        Get or create a connection for a service.
        
        Args:
            service_name: Name of the service
            client_factory: Function to create new client if needed
            
        Returns:
            MCP client instance
        """
        async with self._lock:
            # Check if connection exists and is healthy
            if service_name in self.connections:
                client = self.connections[service_name]
                health = await client.check_health()
                
                if health.is_healthy:
                    self.connection_usage[service_name] += 1
                    logger.debug(f"Reusing connection for service: {service_name}")
                    return client
                else:
                    # Connection unhealthy, remove it
                    logger.warning(f"Removing unhealthy connection for service: {service_name}")
                    await self._remove_connection(service_name)
            
            # Create new connection if pool not full
            if len(self.connections) >= self.max_connections:
                # Remove least used connection
                await self._evict_connection()
            
            # Create new connection
            client = await client_factory()
            self.connections[service_name] = client
            self.connection_usage[service_name] = 1
            
            logger.info(f"Created new connection for service: {service_name}")
            return client
    
    async def _remove_connection(self, service_name: str) -> None:
        """Remove a connection from the pool."""
        if service_name in self.connections:
            client = self.connections[service_name]
            try:
                await client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting client: {e}")
            
            del self.connections[service_name]
            del self.connection_usage[service_name]
    
    async def _evict_connection(self) -> None:
        """Evict the least used connection."""
        if not self.connections:
            return
        
        # Find least used connection
        least_used_service = min(self.connection_usage, key=self.connection_usage.get)
        logger.info(f"Evicting least used connection: {least_used_service}")
        await self._remove_connection(least_used_service)
    
    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            for service_name in list(self.connections.keys()):
                await self._remove_connection(service_name)
            
            logger.info("All connections closed")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "active_connections": len(self.connections),
            "max_connections": self.max_connections,
            "connection_usage": self.connection_usage.copy(),
            "services": list(self.connections.keys())
        }


class MCPClientManager:
    """
    Unified manager for all MCP client connections and tool routing.
    
    Provides centralized management of MCP clients, tool discovery,
    connection pooling, and unified interface for tool execution.
    """
    
    def __init__(self, max_connections: int = 10):
        self.clients: Dict[str, BaseMCPClient] = {}
        self.tool_registry = ToolRegistry()
        self.connection_pool = ConnectionPool(max_connections)
        self._client_factories: Dict[str, callable] = {}
        self._lock = asyncio.Lock()
        
        logger.info("MCP Client Manager initialized")
    
    def register_service(
        self, 
        service_name: str, 
        client_factory: callable,
        auto_connect: bool = True
    ) -> None:
        """
        Register a service with its client factory.
        
        Args:
            service_name: Name of the service
            client_factory: Function that creates and connects the client
            auto_connect: Whether to connect immediately
        """
        self._client_factories[service_name] = client_factory
        
        logger.info(
            f"Service registered: {service_name}",
            extra={
                "service": service_name,
                "auto_connect": auto_connect
            }
        )
    
    async def get_client(self, service_name: str) -> BaseMCPClient:
        """
        Get or create MCP client for service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            MCP client instance
            
        Raises:
            MCPError: If service not registered or connection fails
        """
        if service_name not in self._client_factories:
            raise MCPError(f"Service '{service_name}' not registered", service_name, "SERVICE_NOT_REGISTERED")
        
        # Get connection from pool
        client_factory = self._client_factories[service_name]
        client = await self.connection_pool.get_connection(service_name, client_factory)
        
        # Register tools if not already done
        if service_name not in self.tool_registry.service_tools:
            await self.tool_registry.register_service(service_name, client)
        
        return client
    
    async def call_tool(
        self, 
        service: str, 
        tool: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route tool calls to appropriate MCP client.
        
        Args:
            service: Service name
            tool: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        try:
            client = await self.get_client(service)
            return await client.call_tool(tool, arguments)
            
        except Exception as e:
            logger.error(
                f"Tool call failed: {service}.{tool}",
                extra={
                    "service": service,
                    "tool": tool,
                    "arguments": arguments,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise
    
    async def discover_tools(self) -> Dict[str, List[ToolInfo]]:
        """
        Discover all available tools across services.
        
        Returns:
            Dictionary mapping service names to their tools
        """
        tools_by_service = {}
        
        for service_name in self._client_factories.keys():
            try:
                # Ensure client is connected and tools are registered
                await self.get_client(service_name)
                tools_by_service[service_name] = self.tool_registry.get_tools_by_service(service_name)
                
            except Exception as e:
                logger.error(
                    f"Failed to discover tools for service: {service_name}",
                    extra={
                        "service": service_name,
                        "error": str(e)
                    }
                )
                tools_by_service[service_name] = []
        
        return tools_by_service
    
    async def get_service_health(self, service_name: str) -> HealthStatus:
        """Get health status for a specific service."""
        try:
            client = await self.get_client(service_name)
            return await client.check_health()
        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                last_check=datetime.now(),
                response_time_ms=0,
                available_tools=0,
                error_message=str(e),
                connection_status="failed"
            )
    
    async def get_all_service_health(self) -> Dict[str, HealthStatus]:
        """Get health status for all registered services."""
        health_status = {}
        
        for service_name in self._client_factories.keys():
            health_status[service_name] = await self.get_service_health(service_name)
        
        return health_status
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get comprehensive manager statistics."""
        return {
            "registered_services": list(self._client_factories.keys()),
            "total_tools": len(self.tool_registry.get_all_tools()),
            "tools_by_service": self.tool_registry.get_tool_count_by_service(),
            "connection_pool": self.connection_pool.get_pool_stats()
        }
    
    async def shutdown(self) -> None:
        """Shutdown the manager and close all connections."""
        logger.info("Shutting down MCP Client Manager")
        
        # Close all connections
        await self.connection_pool.close_all()
        
        # Clear registries
        self.clients.clear()
        self._client_factories.clear()
        
        logger.info("MCP Client Manager shutdown complete")


# Global manager instance
_mcp_manager: Optional[MCPClientManager] = None


def get_mcp_manager() -> MCPClientManager:
    """Get or create global MCP client manager instance."""
    global _mcp_manager
    
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()
    
    return _mcp_manager


async def initialize_mcp_services() -> None:
    """Initialize all MCP services with the manager using configuration system."""
    from app.config.mcp_config import load_mcp_config
    
    manager = get_mcp_manager()
    config = load_mcp_config()
    
    logger.info(f"Initializing MCP services with configuration: {len(config.servers)} services")
    
    # Register services based on configuration
    for server_config in config.servers:
        service_name = server_config.service_name
        
        async def create_client(config=server_config):
            # Resolve environment variables in server environment
            resolved_env = {}
            for key, value in config.environment.items():
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    resolved_value = os.getenv(env_var, value)
                    resolved_env[key] = resolved_value
                else:
                    resolved_env[key] = value
            
            client = BaseMCPClient(
                service_name=config.service_name,
                server_command=config.server_command,
                server_args=config.server_args,
                timeout=config.timeout,
                retry_attempts=config.retry_attempts,
                health_check_interval=config.health_check_interval,
                recovery_config=ConnectionRecoveryConfig(
                    max_retry_attempts=config.retry_attempts,
                    auto_recovery_enabled=True
                )
            )
            
            # Set environment variables for the MCP server process
            if resolved_env:
                # Note: Environment variables will be passed to the MCP server process
                # This is handled by the MCP SDK when starting the server
                for key, value in resolved_env.items():
                    os.environ[key] = value
            
            await client.connect()
            return client
        
        manager.register_service(service_name, create_client)
        logger.info(f"Registered MCP service: {service_name}")
    
    logger.info(f"MCP services initialized: {[s.service_name for s in config.servers]}")