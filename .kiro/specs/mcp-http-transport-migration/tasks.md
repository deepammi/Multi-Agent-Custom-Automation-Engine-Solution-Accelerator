# Implementation Plan: MCP HTTP Transport Migration

## Overview

This implementation plan converts the existing STDIO-based MCP transport to HTTP transport using the FastMCP framework. The migration enables concurrent client connections, proper OAuth session management, and eliminates subprocess management conflicts.

## Tasks

- [x] 1. Set up FastMCP environment and dependencies
  - Install FastMCP SDK in backend requirements
  - Update environment configuration for HTTP transport
  - Create server configuration mapping for ports and scripts
  - _Requirements: 1.1, 1.2_

- [ ]* 1.1 Write property test for FastMCP tool registration
  - **Property 1: FastMCP Tool Registration**
  - **Validates: Requirements 1.1, 1.2**

- [ ] 2. Convert Gmail MCP server to FastMCP
- [x] 2.1 Migrate Gmail server to use @mcp.tool() decorators
  - Convert existing Gmail tools to FastMCP format
  - Implement OAuth token storage in server memory
  - Add HTTP transport startup with mcp.run()
  - _Requirements: 1.1, 8.1, 8.2_

- [ ]* 2.2 Write property test for OAuth token persistence
  - **Property 4: OAuth Token Persistence**
  - **Validates: Requirements 8.1, 8.2**

- [x] 2.3 Update Gmail agent to use FastMCP Client
  - Replace GmailStandardMCPClient with FastMCP Client
  - Implement proper connection management with context managers
  - Test tool calling via client.call_tool()
  - _Requirements: 2.1, 2.2_

- [ ]* 2.4 Write property test for FastMCP client connection
  - **Property 2: FastMCP Client Connection**
  - **Validates: Requirements 2.1**

- [ ] 3. Convert Salesforce MCP server to FastMCP
- [ ] 3.1 Migrate Salesforce server to use @mcp.tool() decorators
  - Convert existing Salesforce tools to FastMCP format
  - Implement OAuth token storage for Salesforce
  - Configure HTTP transport on port 9001
  - _Requirements: 1.1, 8.1_

- [ ] 3.2 Update Salesforce agent to use FastMCP Client
  - Replace STDIO client with FastMCP Client
  - Update tool calling interface to maintain compatibility
  - Test concurrent client connections
  - _Requirements: 2.1, 3.3_

- [ ]* 3.3 Write property test for concurrent client support
  - **Property 5: Concurrent Client Support**
  - **Validates: Requirements 1.5, 3.3**

- [ ] 4. Convert Bill.com MCP server to FastMCP
- [ ] 4.1 Migrate Bill.com server to use @mcp.tool() decorators
  - Convert existing Bill.com tools to FastMCP format
  - Implement OAuth token storage for Bill.com
  - Configure HTTP transport on port 9000
  - _Requirements: 1.1, 8.1_

- [ ] 4.2 Update Bill.com agent to use FastMCP Client
  - Replace STDIO client with FastMCP Client
  - Maintain existing tool calling interfaces
  - Test authentication and tool execution
  - _Requirements: 2.1, 2.2_

- [ ]* 4.3 Write property test for tool call protocol compliance
  - **Property 3: Tool Call Protocol Compliance**
  - **Validates: Requirements 2.2, 3.2**

- [ ] 5. Implement MCP Server Manager
- [ ] 5.1 Create server lifecycle management
  - Implement MCPServerManager class for subprocess control
  - Add methods for starting/stopping individual servers
  - Configure server startup with proper ports and scripts
  - _Requirements: 4.1, 4.2_

- [ ]* 5.2 Write property test for server process independence
  - **Property 6: Server Process Independence**
  - **Validates: Requirements 2.1, 3.1**

- [ ] 5.3 Create startup script for all MCP servers
  - Implement start_mcp_servers_http.py script
  - Add health check endpoints for server monitoring
  - Test server startup and shutdown procedures
  - _Requirements: 4.1, 4.2_

- [ ]* 5.4 Write property test for server manager process control
  - **Property 10: Server Manager Process Control**
  - **Validates: Requirements 4.1, 4.2**

- [ ] 6. Update remaining MCP servers (Audit, etc.)
- [ ] 6.1 Convert Audit MCP server to FastMCP
  - Migrate audit tools to use @mcp.tool() decorators
  - Configure HTTP transport on port 9003
  - Test tool registration and execution
  - _Requirements: 1.1, 1.2_

- [ ] 6.2 Update any remaining STDIO-based agents
  - Identify and convert remaining agents to FastMCP Client
  - Ensure consistent error handling across all agents
  - Test multi-service agent workflows
  - _Requirements: 2.1, 3.4_

- [ ]* 6.3 Write property test for transport layer abstraction
  - **Property 7: Transport Layer Abstraction**
  - **Validates: Requirements 3.4, 9.5**

- [ ] 7. Checkpoint - Test multi-service integration
  - Ensure all MCP servers start successfully via HTTP
  - Test concurrent connections from multiple agents
  - Verify OAuth flows work across all services
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement error handling and cleanup
- [ ] 8.1 Add proper session cleanup for client disconnections
  - Implement context manager cleanup in FastMCP clients
  - Test resource cleanup when clients disconnect
  - Add error recovery for connection failures
  - _Requirements: 2.5, 4.2_

- [ ]* 8.2 Write property test for session cleanup
  - **Property 8: Session Cleanup**
  - **Validates: Requirements 2.5, 4.2**

- [ ] 8.3 Implement consistent error handling
  - Create MCPTransportError exception hierarchy
  - Ensure all tool errors return strings instead of raising exceptions
  - Add retry logic for transient connection failures
  - _Requirements: 6.1, 6.2_

- [ ]* 8.4 Write property test for error handling consistency
  - **Property 9: Error Handling Consistency**
  - **Validates: Requirements 6.1, 6.2**

- [ ] 9. Integration testing and validation
- [ ] 9.1 Create comprehensive integration tests
  - Test complete OAuth flows with FastMCP servers
  - Test multi-client connections to same server
  - Test agent workflows using multiple MCP services
  - _Requirements: 1.5, 2.1, 8.1_

- [ ]* 9.2 Write integration tests for multi-service workflows
  - Test agents using Gmail, Salesforce, and Bill.com simultaneously
  - Verify proper connection management and cleanup
  - _Requirements: 3.3, 3.4_

- [ ] 9.3 Performance and load testing
  - Test server performance under concurrent client load
  - Verify memory usage and connection limits
  - Test server restart scenarios with client reconnection
  - _Requirements: 1.5, 4.2_

- [ ] 10. Final checkpoint and documentation
- [ ] 10.1 Update configuration and deployment scripts
  - Update environment variables for HTTP transport
  - Create production deployment configuration
  - Update documentation for new HTTP transport setup
  - _Requirements: 9.1, 9.2_

- [ ]* 10.2 Write end-to-end validation tests
  - Test complete migration from STDIO to HTTP transport
  - Verify all existing functionality works with new transport
  - _Requirements: 9.5_

- [ ] 10.3 Final validation and cleanup
  - Remove old STDIO transport code and dependencies
  - Ensure all tests pass with HTTP transport
  - Verify production readiness
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation of the migration
- Property tests validate universal correctness properties
- Integration tests validate complete workflows across services
- The migration maintains backward compatibility for existing agent interfaces