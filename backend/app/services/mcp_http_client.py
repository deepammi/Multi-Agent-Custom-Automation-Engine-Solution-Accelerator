"""
FastMCP HTTP Client Service - HTTP transport implementation for MCP.

This service replaces the STDIO-based MCP client with HTTP transport using FastMCP Client.
Enables concurrent client connections and proper OAuth session management with 
environment-controlled mock mode support.
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

# Import FastMCP client
try:
    from fastmcp import Client
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    logging.warning("FastMCP not available. Install with: pip install fastmcp")

from app.config.environment import get_environment_config

logger = logging.getLogger(__name__)


class MCPHTTPError(Exception):
    """Base exception for MCP HTTP-related errors."""
    def __init__(self, message: str, service: str, error_code: str = None):
        self.service = service
        self.error_code = error_code
        super().__init__(message)


class MCPHTTPConnectionError(MCPHTTPError):
    """MCP HTTP server connection failures."""
    pass


class MCPHTTPToolNotFoundError(MCPHTTPError):
    """Requested tool not available via HTTP."""
    pass


class MCPHTTPTimeoutError(MCPHTTPError):
    """HTTP tool call timeout."""
    pass


@dataclass
class HTTPHealthStatus:
    """Health status of HTTP MCP client/server."""
    is_healthy: bool
    last_check: datetime
    response_time_ms: int
    available_tools: int
    error_message: Optional[str] = None
    connection_status: str = "connected"
    server_url: str = ""


class FastMCPHTTPClient:
    """
    FastMCP HTTP client implementation for MCP protocol over HTTP.
    
    This client uses FastMCP's Client class to connect to MCP servers
    running with HTTP transport, enabling concurrent connections and
    proper session management.
    """
    
    def __init__(
        self, 
        service_name: str,
        server_url: str,
        timeout: int = 60,  # Increased timeout for Bill.com API calls
        retry_attempts: int = 5,  # Increased from 3 to 5 for better reliability
        health_check_interval: int = 60,
        max_backoff_time: int = 30,  # Maximum backoff time in seconds
        base_backoff_time: float = 1.0  # Base backoff time for exponential backoff
        ):
            """
            Initialize FastMCP HTTP client with enhanced retry logic.
            
            Args:
                service_name: Name of the service (e.g., "gmail", "salesforce")
                server_url: HTTP URL of the MCP server (e.g., "http://localhost:9002/mcp")
                timeout: Default timeout for operations in seconds
                retry_attempts: Number of retry attempts for failed operations
                health_check_interval: Health check interval in seconds
                max_backoff_time: Maximum backoff time for exponential backoff
                base_backoff_time: Base backoff time for exponential backoff
            """
            if not FASTMCP_AVAILABLE:
                raise ImportError("FastMCP not available. Install with: pip install fastmcp")
        
            self.service_name = service_name
            self.server_url = server_url
            self.timeout = timeout
            self.retry_attempts = retry_attempts
            self.health_check_interval = health_check_interval
            self.max_backoff_time = max_backoff_time
            self.base_backoff_time = base_backoff_time
        
            # FastMCP client instance
            self._client = None
            self._connected = False
            
            # Health monitoring
            self._last_health_check = None
            self._health_status = None
            
            # Performance metrics
            self._connection_time = None
            self._tool_call_count = 0
            self._error_count = 0
            self._retry_count = 0  # Track total retry attempts
            self._last_connection_attempt = None
        
            logger.info(
                f"FastMCP HTTP client initialized with enhanced retry logic",
                extra={
                    "service": self.service_name,
                    "server_url": self.server_url,
                    "timeout": self.timeout,
                    "retry_attempts": self.retry_attempts,
                    "max_backoff_time": self.max_backoff_time
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
        """Connect to FastMCP HTTP server with enhanced exponential backoff retry logic."""
        start_time = time.time()
        self._last_connection_attempt = datetime.now()
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(
                    f"Connecting to FastMCP HTTP server (attempt {attempt + 1}/{self.retry_attempts})",
                    extra={
                        "service": self.service_name,
                        "server_url": self.server_url,
                        "attempt": attempt + 1,
                        "total_retries_so_far": self._retry_count
                    }
                )
                
                # Create FastMCP client with proper headers
                # FastMCP Client expects both application/json and text/event-stream
                self._client = Client(self.server_url)
                
                # Connect using proper async context manager
                # Note: We don't use 'async with' here because we want to keep the connection open
                # The client will be closed in the disconnect() method
                await self._client.__aenter__()
                
                self._connected = True
                self._connection_time = time.time() - start_time
                
                logger.info(
                    f"✅ FastMCP HTTP connection established successfully",
                    extra={
                        "service": self.service_name,
                        "server_url": self.server_url,
                        "connection_time_ms": int(self._connection_time * 1000),
                        "attempt": attempt + 1,
                        "total_retries": self._retry_count
                    }
                )
                
                # Perform initial health check
                await self._update_health_status()
                
                return
                
            except asyncio.TimeoutError as e:
                self._retry_count += 1
                error_msg = f"Connection timeout after {self.timeout}s"
                logger.error(
                    f"❌ FastMCP HTTP connection timeout (attempt {attempt + 1})",
                    extra={
                        "service": self.service_name,
                        "server_url": self.server_url,
                        "timeout": self.timeout,
                        "attempt": attempt + 1,
                        "error_type": "timeout"
                    }
                )
                if attempt == self.retry_attempts - 1:
                    raise MCPHTTPConnectionError(error_msg, self.service_name, "CONNECTION_TIMEOUT")
                    
            except Exception as e:
                self._retry_count += 1
                error_msg = f"Connection failed: {str(e)}"
                logger.error(
                    f"❌ FastMCP HTTP connection failed (attempt {attempt + 1})",
                    extra={
                        "service": self.service_name,
                        "server_url": self.server_url,
                        "error": error_msg,
                        "error_type": type(e).__name__,
                        "attempt": attempt + 1
                    }
                )
                if attempt == self.retry_attempts - 1:
                    raise MCPHTTPConnectionError(error_msg, self.service_name, "CONNECTION_FAILED")
            
            # Enhanced exponential backoff with jitter and maximum backoff time
            if attempt < self.retry_attempts - 1:
                # Calculate exponential backoff: base_time * (2 ^ attempt)
                backoff_time = min(
                    self.base_backoff_time * (2 ** attempt),
                    self.max_backoff_time
                )
                
                # Add jitter to prevent thundering herd (±20% randomization)
                import random
                jitter = random.uniform(0.8, 1.2)
                final_backoff = backoff_time * jitter
                
                logger.info(
                    f"⏳ Retrying connection in {final_backoff:.1f}s (exponential backoff with jitter)",
                    extra={
                        "service": self.service_name,
                        "backoff_time": final_backoff,
                        "base_backoff": backoff_time,
                        "jitter_factor": jitter,
                        "attempt": attempt + 1,
                        "next_attempt": attempt + 2
                    }
                )
                await asyncio.sleep(final_backoff)
    
    async def disconnect(self) -> None:
        """Disconnect from FastMCP HTTP server."""
        try:
            if self._client and self._connected:
                await self._client.__aexit__(None, None, None)
                self._client = None
                self._connected = False
            
            logger.info(
                "✅ FastMCP HTTP connection closed successfully",
                extra={
                    "service": self.service_name,
                    "tool_calls_made": self._tool_call_count,
                    "errors_encountered": self._error_count
                }
            )
            
        except Exception as e:
            logger.warning(
                f"⚠️ Error during FastMCP HTTP disconnect: {e}",
                extra={
                    "service": self.service_name,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool via HTTP using FastMCP Client with enhanced retry logic and environment-controlled mock mode.
        
        This method implements NFR1.3 and NFR1.4 by respecting mock mode settings, ensuring
        real service failures propagate when mock mode is disabled, and providing robust
        retry logic with exponential backoff for transient connection failures.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result as dictionary
            
        Raises:
            MCPHTTPConnectionError: If client not connected and mock mode disabled
            MCPHTTPTimeoutError: If tool call times out and mock mode disabled
            MCPHTTPError: For other HTTP MCP-related errors when mock mode disabled
        """
        env_config = get_environment_config()
        
        # Check if mock mode is enabled before attempting real connection
        if env_config.is_mock_mode_enabled():
            logger.info(
                f"🎭 Mock mode enabled for MCP service '{self.service_name}' - returning mock data",
                extra={
                    "service": self.service_name,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "mock_mode_reason": "USE_MOCK_MODE=true in environment"
                }
            )
            return self._generate_mock_tool_response(tool_name, arguments)
        
        # Enhanced retry logic for tool calls with exponential backoff
        max_tool_retries = 3  # Separate retry count for tool calls
        
        for tool_attempt in range(max_tool_retries):
            # Initialize request_id for this attempt
            start_time = time.time()
            request_id = f"{self.service_name}_{tool_name}_{int(start_time * 1000)}"
            
            try:
                # Auto-reconnect if not connected (only when mock mode disabled)
                if not self._client or not self._connected:
                    logger.info(f"Client not connected, attempting to reconnect (tool attempt {tool_attempt + 1})...")
                    try:
                        await self.connect()
                    except Exception as e:
                        # If connection fails and mock mode is disabled, propagate the error
                        logger.error(
                            f"❌ MCP connection failed and mock mode disabled - error will propagate",
                            extra={
                                "service": self.service_name,
                                "error": str(e),
                                "mock_mode_status": "disabled",
                                "tool_attempt": tool_attempt + 1
                            }
                        )
                        if tool_attempt == max_tool_retries - 1:
                            raise MCPHTTPConnectionError(
                                f"Failed to connect to MCP server and mock mode disabled: {str(e)}",
                                self.service_name,
                                "CONNECTION_FAILED"
                            )
                        # Continue to retry with backoff
                        continue
                
                logger.info(
                    f"Calling MCP tool via HTTP: {tool_name} (attempt {tool_attempt + 1}/{max_tool_retries})",
                    extra={
                        "service": self.service_name,
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "request_id": request_id,
                        "server_url": self.server_url,
                        "mock_mode": "disabled",
                        "tool_attempt": tool_attempt + 1
                    }
                )
                
                # Call the tool using FastMCP Client with timeout
                tool_call_task = self._client.call_tool(tool_name, arguments)
                result = await asyncio.wait_for(tool_call_task, timeout=self.timeout)
                
                execution_time = int((time.time() - start_time) * 1000)
                self._tool_call_count += 1
                
                logger.info(
                    f"✅ FastMCP HTTP tool '{tool_name}' completed successfully",
                    extra={
                        "service": self.service_name,
                        "tool_name": tool_name,
                        "execution_time_ms": execution_time,
                        "request_id": request_id,
                        "result_type": type(result).__name__,
                        "tool_attempt": tool_attempt + 1
                    }
                )
                
                # FastMCP Client returns CallToolResult object
                # Extract the structured content or data from the result
                if hasattr(result, 'structured_content') and result.structured_content:
                    # Use structured_content if available (preferred)
                    return result.structured_content
                elif hasattr(result, 'data') and result.data:
                    # Fallback to data field
                    return result.data
                elif isinstance(result, dict):
                    # Already a dict, return as-is
                    return result
                elif isinstance(result, str):
                    return {"result": result}
                else:
                    # Convert to string and wrap
                    return {"result": str(result)}
                    
            except asyncio.TimeoutError:
                self._error_count += 1
                # Mark as disconnected after timeout
                self._connected = False
                error_msg = f"HTTP tool call '{tool_name}' timed out after {self.timeout}s"
                logger.error(
                    f"❌ {error_msg} - mock mode disabled (attempt {tool_attempt + 1}/{max_tool_retries})",
                    extra={
                        "service": self.service_name,
                        "tool_name": tool_name,
                        "timeout": self.timeout,
                        "request_id": request_id,
                        "server_url": self.server_url,
                        "mock_mode_status": "disabled",
                        "tool_attempt": tool_attempt + 1
                    }
                )
                if tool_attempt == max_tool_retries - 1:
                    raise MCPHTTPTimeoutError(error_msg, self.service_name, "TIMEOUT")
                
            except Exception as e:
                self._error_count += 1
                # Mark as disconnected on error
                self._connected = False
                error_msg = f"FastMCP HTTP tool call failed: {str(e)}"
                logger.error(
                    f"❌ {error_msg} - mock mode disabled (attempt {tool_attempt + 1}/{max_tool_retries})",
                    extra={
                        "service": self.service_name,
                        "tool_name": tool_name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "request_id": request_id,
                        "server_url": self.server_url,
                        "mock_mode_status": "disabled",
                        "tool_attempt": tool_attempt + 1
                    }
                )
                if tool_attempt == max_tool_retries - 1:
                    raise MCPHTTPError(error_msg, self.service_name, "TOOL_CALL_FAILED")
            
            # Exponential backoff for tool call retries
            if tool_attempt < max_tool_retries - 1:
                backoff_time = min(
                    self.base_backoff_time * (2 ** tool_attempt),
                    self.max_backoff_time
                )
                
                # Add jitter to prevent thundering herd
                import random
                jitter = random.uniform(0.8, 1.2)
                final_backoff = backoff_time * jitter
                
                logger.info(
                    f"⏳ Retrying tool call in {final_backoff:.1f}s (exponential backoff)",
                    extra={
                        "service": self.service_name,
                        "tool_name": tool_name,
                        "backoff_time": final_backoff,
                        "tool_attempt": tool_attempt + 1,
                        "next_attempt": tool_attempt + 2
                    }
                )
                await asyncio.sleep(final_backoff)
    
    def _generate_mock_tool_response(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate mock response for MCP tool calls when mock mode is enabled.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments
            
        Returns:
            Dict with mock response data appropriate for the tool
        """
        logger.info(
            f"🎭 Generating mock response for {self.service_name} tool '{tool_name}'",
            extra={
                "service": self.service_name,
                "tool_name": tool_name,
                "arguments": arguments,
                "mock_mode": "enabled"
            }
        )
        
        # Service-specific mock responses
        if self.service_name == "gmail":
            return self._generate_gmail_mock_response(tool_name, arguments)
        elif self.service_name == "salesforce":
            return self._generate_salesforce_mock_response(tool_name, arguments)
        elif self.service_name == "bill_com":
            return self._generate_bill_com_mock_response(tool_name, arguments)
        else:
            # Generic mock response
            return {
                "result": f"Mock response for {tool_name} on {self.service_name}",
                "status": "success",
                "mock_mode": True,
                "service": self.service_name,
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_gmail_mock_response(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Gmail-specific mock responses."""
        if tool_name == "search_messages":
            return {
                "messages": [
                    {
                        "id": "mock_msg_001",
                        "subject": f"Mock email for query: {arguments.get('query', 'test')}",
                        "from": "mock@example.com",
                        "snippet": "This is a mock email response for testing purposes",
                        "date": datetime.now().isoformat()
                    }
                ],
                "total_count": 1,
                "mock_mode": True
            }
        elif tool_name == "send_message":
            return {
                "message_id": "mock_sent_001",
                "status": "sent",
                "to": arguments.get("to", "unknown@example.com"),
                "subject": arguments.get("subject", "Mock Subject"),
                "mock_mode": True
            }
        else:
            return {"result": f"Mock Gmail response for {tool_name}", "mock_mode": True}
    
    def _generate_salesforce_mock_response(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Salesforce-specific mock responses."""
        if tool_name == "search_records":
            return {
                "records": [
                    {
                        "Id": "mock_account_001",
                        "Name": f"Mock Account for {arguments.get('search_term', 'test')}",
                        "Industry": "Technology",
                        "AnnualRevenue": 1000000
                    }
                ],
                "total_count": 1,
                "mock_mode": True
            }
        elif tool_name == "get_opportunities":
            return {
                "records": [
                    {
                        "Id": "mock_opp_001",
                        "Name": "Mock Opportunity",
                        "Amount": 50000,
                        "StageName": "Prospecting"
                    }
                ],
                "total_count": 1,
                "mock_mode": True
            }
        else:
            return {"result": f"Mock Salesforce response for {tool_name}", "mock_mode": True}
    
    def _generate_bill_com_mock_response(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Bill.com-specific mock responses."""
        if tool_name == "get_bill_com_bills":
            vendor_name = arguments.get("vendor_name", "Mock Vendor")
            return {
                "bills": [
                    {
                        "id": "mock_bill_001",
                        "vendor_name": vendor_name,
                        "amount": 15000.00,
                        "due_date": "2025-01-15",
                        "status": "Open",
                        "invoice_number": "INV-MOCK-001"
                    }
                ],
                "total_count": 1,
                "mock_mode": True
            }
        elif tool_name == "search_vendors":
            return {
                "vendors": [
                    {
                        "id": "mock_vendor_001",
                        "name": arguments.get("vendor_name", "Mock Vendor"),
                        "status": "Active"
                    }
                ],
                "total_count": 1,
                "mock_mode": True
            }
        else:
            return {"result": f"Mock Bill.com response for {tool_name}", "mock_mode": True}
    
    async def _update_health_status(self) -> None:
        """Update health status by testing connection."""
        start_time = time.time()
        
        try:
            if self._client and self._connected:
                # Test connection with a simple operation
                # Note: FastMCP Client doesn't have a list_tools method, so we'll just check connection
                response_time = int((time.time() - start_time) * 1000)
                
                self._health_status = HTTPHealthStatus(
                    is_healthy=True,
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    available_tools=0,  # We don't have a way to count tools with FastMCP Client
                    connection_status="connected",
                    server_url=self.server_url
                )
                
            else:
                self._health_status = HTTPHealthStatus(
                    is_healthy=False,
                    last_check=datetime.now(),
                    response_time_ms=0,
                    available_tools=0,
                    error_message="No active connection",
                    connection_status="disconnected",
                    server_url=self.server_url
                )
                
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            
            self._health_status = HTTPHealthStatus(
                is_healthy=False,
                last_check=datetime.now(),
                response_time_ms=response_time,
                available_tools=0,
                error_message=str(e),
                connection_status="error",
                server_url=self.server_url
            )
        
        self._last_health_check = datetime.now()
    
    async def check_health(self) -> HTTPHealthStatus:
        """Check HTTP MCP server health and connectivity."""
        # Update health status if needed
        if (not self._last_health_check or 
            datetime.now() - self._last_health_check > timedelta(seconds=self.health_check_interval)):
            await self._update_health_status()
        
        return self._health_status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the HTTP MCP client."""
        return {
            "service": self.service_name,
            "server_url": self.server_url,
            "connected": self._connected,
            "connection_time_ms": int(self._connection_time * 1000) if self._connection_time else None,
            "tool_call_count": self._tool_call_count,
            "error_count": self._error_count,
            "retry_count": self._retry_count,  # Total retry attempts across all operations
            "error_rate": self._error_count / max(self._tool_call_count, 1),
            "retry_rate": self._retry_count / max(self._tool_call_count + self._retry_count, 1),
            "last_connection_attempt": self._last_connection_attempt.isoformat() if self._last_connection_attempt else None,
            "health_status": self._health_status.__dict__ if self._health_status else None,
            "retry_configuration": {
                "max_retry_attempts": self.retry_attempts,
                "timeout_seconds": self.timeout,
                "max_backoff_time": self.max_backoff_time,
                "base_backoff_time": self.base_backoff_time
            }
        }


class MCPHTTPManager:
    """
    Manager for multiple FastMCP HTTP clients.
    
    Provides centralized management of HTTP MCP connections to multiple services,
    with connection pooling and health monitoring.
    """
    
    def __init__(self):
        self.clients: Dict[str, FastMCPHTTPClient] = {}
        self.service_urls = {
            "gmail": "http://localhost:9000/mcp",
            "salesforce": "http://localhost:9001/mcp", 
            "bill_com": "http://localhost:9002/mcp",
            "audit": "http://localhost:9003/mcp"
        }
        
        # Import environment config
        from app.config.environment import get_environment_config
        self._env_config = get_environment_config()
        
        logger.info(
            "FastMCP HTTP Manager initialized with environment-controlled mock mode support",
            extra={
                "mock_mode_enabled": self._env_config.is_mock_mode_enabled(),
                "services_configured": list(self.service_urls.keys())
            }
        )
    
    async def get_client(self, service_name: str) -> FastMCPHTTPClient:
        """
        Get or create HTTP MCP client for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            FastMCP HTTP client instance
            
        Raises:
            ValueError: If service not configured
            MCPHTTPConnectionError: If connection fails
        """
        if service_name not in self.service_urls:
            raise ValueError(f"Service '{service_name}' not configured. Available: {list(self.service_urls.keys())}")
        
        if service_name not in self.clients:
            server_url = self.service_urls[service_name]
            client = FastMCPHTTPClient(service_name, server_url)
            await client.connect()
            self.clients[service_name] = client
            
            logger.info(f"Created new HTTP MCP client for service: {service_name}")
        
        return self.clients[service_name]
    
    async def call_tool(self, service_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on a specific service via HTTP with enhanced automatic reconnection and environment-controlled mock mode.
        
        This method implements NFR1.3 and NFR1.4 by respecting mock mode settings, ensuring
        real service failures propagate when mock mode is disabled, and providing robust
        retry logic with exponential backoff for transient connection failures.
        
        Args:
            service_name: Name of the service
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
            
        Raises:
            ValueError: If service not configured
            MCPHTTPConnectionError: If connection fails and mock mode disabled
            MCPHTTPTimeoutError: If tool call times out and mock mode disabled
            MCPHTTPError: For other errors when mock mode disabled
        """
        env_config = get_environment_config()
        
        # Check if mock mode is enabled
        if env_config.is_mock_mode_enabled():
            logger.info(
                f"🎭 Mock mode enabled for service '{service_name}' - using mock response",
                extra={
                    "service": service_name,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "mock_mode_reason": "USE_MOCK_MODE=true in environment"
                }
            )
            
            # Create a temporary client just for mock response generation
            if service_name not in self.service_urls:
                raise ValueError(f"Service '{service_name}' not configured. Available: {list(self.service_urls.keys())}")
            
            temp_client = FastMCPHTTPClient(service_name, self.service_urls[service_name])
            return temp_client._generate_mock_tool_response(tool_name, arguments)
        
        # Enhanced retry logic for manager-level tool calls
        max_manager_retries = 3
        
        for manager_attempt in range(max_manager_retries):
            try:
                client = await self.get_client(service_name)
                return await client.call_tool(tool_name, arguments)
                
            except (MCPHTTPConnectionError, MCPHTTPTimeoutError) as e:
                logger.warning(
                    f"Tool call failed (manager attempt {manager_attempt + 1}/{max_manager_retries}) - mock mode disabled",
                    extra={
                        "service": service_name,
                        "tool_name": tool_name,
                        "attempt": manager_attempt + 1,
                        "max_retries": max_manager_retries,
                        "mock_mode_status": "disabled",
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                
                # Remove failed client to force reconnection
                if service_name in self.clients:
                    try:
                        await self.clients[service_name].disconnect()
                    except:
                        pass
                    del self.clients[service_name]
                
                if manager_attempt == max_manager_retries - 1:
                    logger.error(
                        f"❌ All manager retry attempts exhausted for {service_name} and mock mode disabled - error will propagate",
                        extra={
                            "service": service_name,
                            "tool_name": tool_name,
                            "error": str(e),
                            "mock_mode_status": "disabled",
                            "total_attempts": max_manager_retries
                        }
                    )
                    raise
                
                # Exponential backoff for manager-level retries
                backoff_time = min(2.0 * (2 ** manager_attempt), 16.0)  # Max 16 seconds
                
                # Add jitter
                import random
                jitter = random.uniform(0.8, 1.2)
                final_backoff = backoff_time * jitter
                
                logger.info(
                    f"⏳ Manager-level retry in {final_backoff:.1f}s",
                    extra={
                        "service": service_name,
                        "backoff_time": final_backoff,
                        "manager_attempt": manager_attempt + 1
                    }
                )
                await asyncio.sleep(final_backoff)
    
    async def get_service_health(self, service_name: str) -> HTTPHealthStatus:
        """Get health status for a specific service."""
        if service_name not in self.clients:
            # Create client to test connection
            await self.get_client(service_name)
        
        client = self.clients[service_name]
        return await client.check_health()
    
    async def get_all_services_health(self) -> Dict[str, HTTPHealthStatus]:
        """Get health status for all configured services."""
        health_results = {}
        
        for service_name in self.service_urls.keys():
            try:
                health_results[service_name] = await self.get_service_health(service_name)
            except Exception as e:
                health_results[service_name] = HTTPHealthStatus(
                    is_healthy=False,
                    last_check=datetime.now(),
                    response_time_ms=0,
                    available_tools=0,
                    error_message=str(e),
                    connection_status="failed",
                    server_url=self.service_urls[service_name]
                )
        
        return health_results
    
    async def disconnect_all(self) -> None:
        """Disconnect all HTTP MCP clients."""
        for service_name, client in self.clients.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected HTTP MCP client: {service_name}")
            except Exception as e:
                logger.warning(f"Error disconnecting {service_name}: {e}")
        
        self.clients.clear()
    
    def get_performance_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all clients."""
        return {
            service_name: client.get_performance_metrics()
            for service_name, client in self.clients.items()
        }


# Global HTTP manager instance
_http_manager: Optional[MCPHTTPManager] = None


def get_mcp_http_manager() -> MCPHTTPManager:
    """
    Get or create global HTTP MCP manager instance.
    
    Returns:
        MCPHTTPManager instance
    """
    global _http_manager
    
    if _http_manager is None:
        _http_manager = MCPHTTPManager()
    
    return _http_manager


# Backward compatibility wrapper for existing code
class MCPHTTPClientService:
    """
    Backward compatibility wrapper that maintains the old interface
    but uses FastMCP HTTP transport internally.
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._manager = get_mcp_http_manager()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool using HTTP transport."""
        return await self._manager.call_tool(self.service_name, tool_name, arguments)
    
    async def check_health(self) -> Dict[str, Any]:
        """Check service health using HTTP transport."""
        health = await self._manager.get_service_health(self.service_name)
        
        # Convert to legacy format
        return {
            "is_healthy": health.is_healthy,
            "last_check": health.last_check.isoformat(),
            "response_time_ms": health.response_time_ms,
            "available_tools": health.available_tools,
            "error_message": health.error_message,
            "connection_status": health.connection_status
        }