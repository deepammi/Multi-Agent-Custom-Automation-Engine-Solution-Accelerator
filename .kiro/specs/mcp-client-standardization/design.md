# MCP Client Architecture Standardization Design

## Overview

This design document outlines the standardization of Model Context Protocol (MCP) client implementation across the Multi-Agent Custom Automation Engine (MACAE) system. The current system has inconsistent MCP usage where some services use proper MCP protocol while others bypass it entirely with direct API calls. This design establishes a unified architecture that ensures all external service integrations use proper MCP protocol for consistency, reliability, and maintainability.

The solution builds upon the existing correct MCP implementation in `mcp_client_service.py` and extends it to replace the incorrect implementations in Salesforce, Gmail, and Zoho services. It provides a standardized base class, unified tool registry, proper error handling, and comprehensive testing framework.

## Architecture

### Current State Analysis

**Correct Implementation (mcp_client_service.py):**
- Uses official MCP SDK with stdio transport
- Proper protocol initialization and handshake
- Tool discovery and capability negotiation
- Async context manager for lifecycle management

**Incorrect Implementations:**
- **Salesforce Service**: Bypasses MCP, calls Salesforce CLI directly
- **Gmail Service**: Uses Google API client directly instead of MCP
- **Zoho Service**: Makes direct HTTP requests instead of MCP protocol

### Target Architecture

```mermaid
graph TB
    subgraph "Category-Based Agent Layer"
        A[CRM Agent]
        B[AccountsPayable Agent]
        C[Email Agent]
        D[Audit Agent]
        E[Invoice Agent]
    end
    
    subgraph "Service Layer"
        F[Unified MCP Client Manager]
        G[Tool Registry with Service Routing]
        H[Connection Pool]
    end
    
    subgraph "MCP Protocol Layer"
        I[Base MCP Client]
        J[Service-Agnostic MCP Clients]
        K[Error Handler]
        L[Health Monitor]
    end
    
    subgraph "MCP Servers"
        M[Bill.com MCP Server]
        N[Salesforce MCP Server]
        O[Gmail MCP Server]
        P[Zoho MCP Server]
    end
    
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    
    F --> G
    F --> H
    
    G --> I
    H --> I
    I --> J
    I --> K
    I --> L
    
    J --> M
    J --> N
    J --> O
    J --> P
    
    note1[CRM Agent calls: get_accounts(service='salesforce')]
    note2[Email Agent calls: send_email(service='gmail')]
    note3[AccountsPayable calls: get_invoices(service='zoho')]
```

**Key Architectural Improvements:**

1. **Category-Based Agents**: Replace brand-specific agents (SalesforceAgent, GmailAgent) with functional agents (CRMAgent, EmailAgent, AccountsPayableAgent)

2. **Service-Parameterized Tool Calls**: Tools accept service parameters to route to appropriate backends:
   ```python
   # Instead of: salesforce_agent.get_accounts()
   crm_agent.get_accounts(service='salesforce')
   
   # Instead of: gmail_agent.send_email()
   email_agent.send_email(service='gmail')
   
   # Instead of: zoho_agent.get_invoices()
   accounts_payable_agent.get_invoices(service='zoho')
   ```

3. **Unified Tool Registry**: Single registry maps functional operations to service-specific implementations

## Components and Interfaces

### 1. Base MCP Client (Enhanced)

Extends the existing `MCPClientService` with additional standardization features:

```python
class BaseMCPClient:
    """Enhanced base MCP client with standardized features."""
    
    async def connect(self) -> None:
        """Connect with retry logic and health checks."""
        
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool with standardized error handling."""
        
    async def list_available_tools(self) -> List[ToolInfo]:
        """Get tools with metadata and descriptions."""
        
    async def health_check(self) -> HealthStatus:
        """Comprehensive health monitoring."""
```

### 2. Unified MCP Client Manager

Central coordinator for all MCP connections:

```python
class MCPClientManager:
    """Manages all MCP client connections and routing."""
    
    def __init__(self):
        self.clients: Dict[str, BaseMCPClient] = {}
        self.tool_registry = ToolRegistry()
        self.connection_pool = ConnectionPool()
    
    async def get_client(self, service_name: str) -> BaseMCPClient:
        """Get or create MCP client for service."""
        
    async def call_tool(self, service: str, tool: str, args: Dict) -> Dict:
        """Route tool calls to appropriate MCP client."""
        
    async def discover_tools(self) -> Dict[str, List[ToolInfo]]:
        """Discover all available tools across services."""
```

### 3. Category-Based Agent Interfaces

Functional agents that accept service parameters:

```python
class CRMAgent:
    """Category-based agent for CRM operations across multiple services."""
    
    def __init__(self, mcp_manager: MCPClientManager):
        self.mcp_manager = mcp_manager
    
    async def get_accounts(self, service: str = 'salesforce', **kwargs) -> Dict[str, Any]:
        """Get accounts from specified CRM service."""
        tool_name = f"{service}_get_accounts"
        return await self.mcp_manager.call_tool(service, tool_name, kwargs)
    
    async def get_opportunities(self, service: str = 'salesforce', **kwargs) -> Dict[str, Any]:
        """Get opportunities from specified CRM service."""
        tool_name = f"{service}_get_opportunities"
        return await self.mcp_manager.call_tool(service, tool_name, kwargs)

class EmailAgent:
    """Category-based agent for email operations across multiple services."""
    
    def __init__(self, mcp_manager: MCPClientManager):
        self.mcp_manager = mcp_manager
    
    async def send_email(self, service: str = 'gmail', **kwargs) -> Dict[str, Any]:
        """Send email via specified email service."""
        tool_name = f"{service}_send_email"
        return await self.mcp_manager.call_tool(service, tool_name, kwargs)
    
    async def list_messages(self, service: str = 'gmail', **kwargs) -> Dict[str, Any]:
        """List messages from specified email service."""
        tool_name = f"{service}_list_messages"
        return await self.mcp_manager.call_tool(service, tool_name, kwargs)

class AccountsPayableAgent:
    """Category-based agent for accounts payable operations."""
    
    def __init__(self, mcp_manager: MCPClientManager):
        self.mcp_manager = mcp_manager
    
    async def get_invoices(self, service: str = 'zoho', **kwargs) -> Dict[str, Any]:
        """Get invoices from specified AP service."""
        tool_name = f"{service}_get_invoices"
        return await self.mcp_manager.call_tool(service, tool_name, kwargs)
    
    async def get_vendors(self, service: str = 'bill_com', **kwargs) -> Dict[str, Any]:
        """Get vendors from specified AP service."""
        tool_name = f"{service}_get_vendors"
        return await self.mcp_manager.call_tool(service, tool_name, kwargs)
```

### 4. Enhanced Tool Registry with Service Routing

Centralized tool discovery with category-to-service mapping:

```python
class ToolRegistry:
    """Registry for all available MCP tools with category-based routing."""
    
    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}
        self.service_tools: Dict[str, List[str]] = {}
        self.category_mappings: Dict[str, Dict[str, List[str]]] = {
            'crm': {
                'salesforce': ['get_accounts', 'get_opportunities', 'get_contacts'],
                'hubspot': ['get_accounts', 'get_deals', 'get_contacts']  # Future
            },
            'email': {
                'gmail': ['send_email', 'list_messages', 'search_messages'],
                'outlook': ['send_email', 'list_messages']  # Future
            },
            'accounts_payable': {
                'zoho': ['get_invoices', 'get_customers', 'get_payments'],
                'bill_com': ['get_invoices', 'get_vendors', 'get_audit_trail'],
                'quickbooks': ['get_invoices', 'get_vendors']  # Future
            }
        }
    
    async def register_service(self, service_name: str, client: BaseMCPClient):
        """Register all tools from an MCP service with category mapping."""
        
    def get_services_for_category(self, category: str) -> List[str]:
        """Get all available services for a functional category."""
        return list(self.category_mappings.get(category, {}).keys())
    
    def get_tools_for_category_service(self, category: str, service: str) -> List[str]:
        """Get available tools for a specific category-service combination."""
        return self.category_mappings.get(category, {}).get(service, [])
    
    def resolve_tool_name(self, category: str, service: str, operation: str) -> str:
        """Resolve functional operation to service-specific tool name."""
        return f"{service}_{operation}"
```

## Data Models

### Tool Information Model

```python
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
```

### Configuration Models

```python
@dataclass
class MCPServerConfig:
    """Configuration for MCP server connection."""
    service_name: str
    server_command: str
    server_args: List[str]
    environment: Dict[str, str]
    timeout: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 60

@dataclass
class MCPClientConfig:
    """Configuration for MCP client manager."""
    servers: List[MCPServerConfig]
    connection_pool_size: int = 10
    default_timeout: int = 30
    enable_health_monitoring: bool = True
    log_level: str = "INFO"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the prework analysis, the following properties ensure correct MCP protocol usage across all services:

**Property 1: MCP Protocol Compliance**
*For any* external service integration, all communication must use proper MCP protocol with stdio transport instead of direct HTTP requests or CLI calls
**Validates: Requirements 1.1, 1.3, 1.5**

**Property 2: Protocol Initialization Consistency**
*For any* MCP connection, proper handshake and capability negotiation must occur before any tool calls are made
**Validates: Requirements 1.2, 3.1**

**Property 3: Session Lifecycle Management**
*For any* MCP client session, proper connection establishment, tool calling, and resource cleanup must occur without leaks
**Validates: Requirements 1.4, 2.4, 3.4**

**Property 4: Base Client Inheritance**
*For any* service-specific MCP client, it must inherit from the base MCP client class while maintaining protocol compliance
**Validates: Requirements 2.1, 2.5**

**Property 5: Interface Consistency**
*For any* MCP service integration, it must expose the same standardized interface methods for tool discovery and execution
**Validates: Requirements 2.2, 4.1, 4.2**

**Property 6: Error Handling Standardization**
*For any* MCP error condition, the error response must follow standardized format with service context and detailed information
**Validates: Requirements 2.3, 4.5, 6.2**

**Property 7: Automatic Reconnection**
*For any* MCP connection failure, the system must implement automatic reconnection with exponential backoff pattern
**Validates: Requirements 3.2, 3.5**

**Property 8: Timeout Detection and Recovery**
*For any* unresponsive MCP server, the system must detect timeouts and attempt recovery procedures
**Validates: Requirements 3.3**

**Property 9: Tool Registry Consistency**
*For any* tool discovery request, the registry must return consistent results and prevent naming conflicts across services
**Validates: Requirements 4.1, 4.4**

**Property 10: Authentication Token Management**
*For any* service requiring authentication, token refresh and credential management must be handled transparently through MCP
**Validates: Requirements 4.3**

**Property 11: Logging Completeness**
*For any* MCP operation, appropriate log entries must be generated with proper detail levels and error context
**Validates: Requirements 6.1, 6.2**

**Property 12: Health Monitoring Accuracy**
*For any* MCP health check, the reported metrics must accurately reflect connection status, success rates, and response times
**Validates: Requirements 6.3, 6.5**

## Error Handling

### Standardized Error Types

```python
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
```

### Error Recovery Strategies

1. **Connection Failures**: Automatic reconnection with exponential backoff
2. **Tool Call Failures**: Retry with circuit breaker pattern
3. **Authentication Errors**: Automatic token refresh and retry
4. **Timeout Errors**: Graceful degradation with cached responses

### Logging Standards

```python
# Structured logging format
{
    "timestamp": "2025-01-15T10:30:00Z",
    "level": "ERROR",
    "service": "salesforce_mcp",
    "operation": "tool_call",
    "tool_name": "salesforce_soql_query",
    "error_type": "MCPTimeoutError",
    "error_message": "Tool call timed out after 30 seconds",
    "request_id": "req_123456",
    "session_id": "sess_789012"
}
```

## Testing Strategy

### Unit Testing

**Test Categories:**
- MCP protocol compliance verification
- Tool discovery and registration
- Error handling and recovery
- Connection lifecycle management
- Authentication token handling

**Key Test Cases:**
```python
class TestMCPClientStandardization:
    async def test_proper_protocol_initialization(self):
        """Verify MCP handshake and capability negotiation."""
        
    async def test_tool_call_with_proper_protocol(self):
        """Verify tools are called via MCP, not direct APIs."""
        
    async def test_error_handling_standardization(self):
        """Verify consistent error format across services."""
        
    async def test_connection_recovery(self):
        """Verify automatic reconnection on failures."""
```

### Property-Based Testing

**Property Test Implementation:**
- Generate random tool calls and verify MCP protocol compliance
- Test connection lifecycle with various failure scenarios
- Validate error handling consistency across different error types
- Test authentication token management with expired/invalid tokens

**Test Configuration:**
- Minimum 100 iterations per property test
- Use hypothesis library for Python property testing
- Mock MCP servers for controlled testing scenarios

### Integration Testing

**End-to-End Scenarios:**
- Complete workflow from agent request to MCP tool execution
- Multi-service tool calls within single workflow
- Error recovery across service boundaries
- Performance testing with concurrent tool calls

### Mock MCP Server

```python
class MockMCPServer:
    """Mock MCP server for testing."""
    
    def __init__(self, tools: List[str], simulate_failures: bool = False):
        self.tools = tools
        self.simulate_failures = simulate_failures
    
    async def handle_tool_call(self, tool_name: str, args: Dict) -> Dict:
        """Simulate tool execution with configurable responses."""
```

## Migration Strategy

### Phase 1: Infrastructure Setup
1. Enhance existing `MCPClientService` with standardization features
2. Create `MCPClientManager` and `ToolRegistry` classes
3. Implement standardized error handling and logging
4. Set up comprehensive testing framework

### Phase 2: Service Migration
1. **Salesforce Service**: Replace CLI calls with proper MCP client
2. **Gmail Service**: Replace direct Google API with MCP client  
3. **Zoho Service**: Replace HTTP requests with MCP client
4. Update all service interfaces to maintain backward compatibility

### Phase 3: Integration and Testing
1. Integrate new MCP clients with existing agent nodes
2. Run comprehensive integration tests
3. Performance testing and optimization
4. Documentation and training materials

### Phase 4: Monitoring and Optimization
1. Deploy health monitoring and alerting
2. Performance optimization based on real usage
3. Additional error recovery mechanisms
4. Advanced features (caching, load balancing)

## Backward Compatibility

### Legacy Interface Preservation

```python
# Maintain existing service interfaces
class SalesforceMCPService:
    """Legacy interface wrapper using proper MCP client."""
    
    def __init__(self):
        self._mcp_client = SalesforceStandardMCPClient()
    
    async def run_soql_query(self, query: str) -> Dict[str, Any]:
        """Legacy method using new MCP implementation."""
        return await self._mcp_client.run_soql_query(query)
```

### Migration Validation

- All existing API contracts maintained
- Response formats unchanged
- Error handling behavior preserved
- Performance characteristics maintained or improved

## Performance Considerations

### Connection Pooling
- Reuse MCP connections across multiple tool calls
- Implement connection limits and timeout management
- Monitor connection health and automatically replace failed connections

### Caching Strategy
- Cache tool discovery results with TTL
- Cache authentication tokens with automatic refresh
- Optional response caching for idempotent operations

### Monitoring Metrics
- Tool call latency and success rates
- Connection establishment time
- Error rates by service and tool
- Resource usage (memory, CPU, connections)

## Security Considerations

### Authentication Management
- Secure storage of service credentials
- Automatic token refresh without exposing secrets
- Audit logging of all authentication events

### Input Validation
- Validate all tool parameters before MCP calls
- Sanitize responses from external services
- Rate limiting to prevent abuse

### Network Security
- Secure stdio transport for MCP communication
- TLS encryption for external service connections
- Network isolation for MCP servers

## Deployment and Configuration

### Environment Configuration

```yaml
# config/mcp_clients.yaml
mcp_clients:
  salesforce:
    server_command: "python3"
    server_args: ["src/mcp_server/salesforce_mcp_server.py"]
    environment:
      SALESFORCE_ORG_ALIAS: "${SALESFORCE_ORG_ALIAS}"
    timeout: 30
    retry_attempts: 3
    
  gmail:
    server_command: "python3" 
    server_args: ["src/mcp_server/gmail_mcp_server.py"]
    environment:
      GMAIL_CREDENTIALS_PATH: "${GMAIL_CREDENTIALS_PATH}"
    timeout: 20
    
  zoho:
    server_command: "python3"
    server_args: ["src/mcp_server/zoho_mcp_server.py"] 
    environment:
      ZOHO_CLIENT_ID: "${ZOHO_CLIENT_ID}"
      ZOHO_CLIENT_SECRET: "${ZOHO_CLIENT_SECRET}"
    timeout: 25
```

### Docker Configuration

```dockerfile
# Ensure MCP SDK is available
RUN pip install mcp>=1.0.0

# Copy MCP server implementations
COPY src/mcp_server/ /app/src/mcp_server/

# Set up proper permissions for stdio communication
RUN chmod +x /app/src/mcp_server/*.py
```

This design provides a comprehensive approach to standardizing MCP client implementation across all services while maintaining backward compatibility and ensuring robust error handling and testing.