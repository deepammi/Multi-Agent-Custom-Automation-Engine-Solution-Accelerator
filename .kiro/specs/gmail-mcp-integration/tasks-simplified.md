# Gmail MCP Integration - Simplified Implementation Tasks

## Overview

This implementation plan integrates the existing Shinzo Labs Gmail MCP server with minimal new code. The approach leverages subprocess calls to the pre-built MCP server, reducing development time and complexity.

## Implementation Tasks

- [x] 1. Setup Gmail OAuth Authentication
  - Complete OAuth flow using existing client_secret.json
  - Verify Gmail MCP server can authenticate and access Gmail API
  - Test basic email reading functionality
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Create Gmail MCP Service Wrapper
  - Implement minimal service wrapper that calls Gmail MCP server via subprocess
  - Add methods for list_messages, send_message, and get_message
  - Handle JSON serialization/deserialization for MCP communication
  - _Requirements: 4.2_

- [x] 3. Implement Gmail Agent Node
  - Create LangGraph agent node for Gmail operations
  - Add task processing logic for "read emails" and "send email" commands
  - Integrate with existing agent state management pattern
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 4.1_

- [x] 4. Add Gmail Agent to LangGraph Workflow
  - Register Gmail agent in the main agent graph
  - Add routing logic to supervisor for Gmail-related tasks
  - Test integration with existing agent workflow
  - _Requirements: 4.1, 4.3_

- [ ] 5. Create OAuth Setup Script
  - Implement one-time setup script for OAuth authentication
  - Handle client_secret.json copying to expected location
  - Provide clear instructions for initial setup
  - _Requirements: 5.1, 5.2, 5.3_

- [ ]* 6. Write Basic Tests
  - Unit tests for Gmail MCP service wrapper
  - Integration tests for Gmail agent node
  - Test OAuth setup script functionality
  - _Requirements: All_

- [x] 7. Update Agent Registration
  - Add Gmail agent to existing agent factory/registry
  - Update supervisor routing to include Gmail capabilities
  - Test end-to-end workflow with Gmail integration
  - _Requirements: 4.1, 4.3_

- [x] 8. Documentation and Deployment
  - Create setup instructions for OAuth authentication
  - Document Gmail agent capabilities and usage
  - Test deployment with existing infrastructure
  - _Requirements: 5.1, 5.2, 5.3_

## Checkpoint Tasks

- [x] 4.1 Verify Gmail MCP server integration works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7.1 Verify end-to-end Gmail workflow
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- This implementation leverages the existing Gmail MCP server to minimize new code
- OAuth authentication is handled entirely by the Gmail MCP server
- No additional infrastructure or databases required
- Integration follows existing MCP service patterns used for Zoho/Salesforce