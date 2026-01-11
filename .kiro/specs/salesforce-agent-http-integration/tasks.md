# Implementation Plan: Salesforce Agent HTTP Integration

## Overview

This implementation plan applies the successful Bill.com HTTP MCP integration patterns to the Salesforce/CRM agent. The approach focuses on validation and testing of existing HTTP components, followed by comprehensive integration testing to achieve 100% reliability.

## Tasks

- [x] 1. Environment and Server Validation
  - Validate Salesforce MCP server HTTP mode operation
  - Verify Salesforce CLI authentication and org access
  - Test server startup and tool registration
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 1.1 Validate Salesforce MCP Server HTTP Startup
  - Start Salesforce MCP server in HTTP mode on port 9001
  - Verify server responds to health check requests
  - Confirm all 6 Salesforce tools are registered and accessible
  - _Requirements: 2.1, 2.2_

- [ ]* 1.2 Write property test for server startup
  - **Property 4: Server Port Binding**
  - **Validates: Requirements 2.1, 2.2**

- [x] 1.3 Validate Salesforce CLI Authentication
  - Test Salesforce CLI connectivity with configured org
  - Verify SALESFORCE_ORG_ALIAS environment variable
  - Execute sample SOQL query to confirm authentication
  - _Requirements: 2.3, 2.5_

- [ ]* 1.4 Write unit tests for CLI authentication
  - Test authentication success and failure scenarios
  - Test org alias validation and error handling
  - _Requirements: 2.3, 2.5_

- [x] 2. HTTP Agent Architecture Validation
  - Review CRM HTTP agent implementation against Bill.com pattern
  - Validate HTTP MCP client usage and tool mapping
  - Test FastMCP CallToolResult processing
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2.1 Review CRM HTTP Agent Implementation
  - Compare CRM agent with successful Bill.com agent pattern
  - Verify usage of `app.services.mcp_http_client` not `mcp_client_service`
  - Validate tool mapping configuration for Salesforce operations
  - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 2.2 Write property test for HTTP transport consistency
  - **Property 1: HTTP Transport Consistency**
  - **Validates: Requirements 1.1, 1.2**

- [x] 2.3 Validate FastMCP CallToolResult Processing
  - Test `_process_mcp_result()` method with various response formats
  - Verify structured_content extraction from FastMCP responses
  - Test fallback handling for different result types
  - _Requirements: 1.3_

- [ ]* 2.4 Write property test for FastMCP result processing
  - **Property 2: FastMCP Result Processing**
  - **Validates: Requirements 1.3**

- [x] 3. Tool Mapping and Parameter Validation
  - Test all CRM operations with correct tool name mapping
  - Validate parameter passing and validation logic
  - Ensure optional parameter handling works correctly
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 3.1 Test Individual CRM Operations
  - Test get_accounts operation with account name filtering and limits
  - Test get_opportunities operation with stage filtering and limits
  - Test get_contacts operation with account name filtering and limits
  - Test search_records operation across multiple Salesforce objects
  - Test run_soql_query operation with custom SOQL queries
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 3.2 Write property test for tool name mapping
  - **Property 5: Tool Name Mapping Accuracy**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [ ]* 3.3 Write property test for parameter validation
  - **Property 6: Parameter Validation**
  - **Validates: Requirements 3.6, 3.7**

- [ ]* 3.4 Write property test for multi-operation support
  - **Property 10: Multi-Operation Support**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

- [x] 4. Real Data Retrieval Testing
  - Execute all CRM operations with real Salesforce org
  - Validate data format and content accuracy
  - Test data formatting for monetary amounts and dates
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [x] 4.1 Test Real Salesforce Data Retrieval
  - Execute get_accounts and verify real account data with names, industries, revenue
  - Execute get_opportunities and verify real opportunity data with amounts, stages, dates
  - Execute get_contacts and verify real contact data with emails, titles, accounts
  - Execute SOQL queries and verify actual query results
  - Execute search operations and verify real search results
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 4.2 Write property test for real data retrieval
  - **Property 7: Real Data Retrieval**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [ ]* 4.3 Write property test for data formatting
  - **Property 8: Data Formatting Consistency**
  - **Validates: Requirements 4.6, 4.7**

- [x] 5. Checkpoint - Validate Core Functionality
  - Ensure all individual CRM operations work with real data
  - Verify HTTP transport and tool mapping are functioning correctly
  - Confirm error handling provides clear feedback

- [x] 6. AI Planner Integration Testing
  - Test AI Planner CRM query recognition and routing
  - Validate complete workflow from user query to Salesforce response
  - Test LLM-based intent analysis and parameter extraction
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6.1 Test AI Planner CRM Query Recognition
  - Submit various CRM-related queries to AI Planner
  - Measure CRM query identification accuracy (target >90%)
  - Verify CRM agent selection for appropriate queries
  - Test planner reasoning and agent sequence generation
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 6.2 Write property test for AI planner CRM recognition
  - **Property 9: AI Planner CRM Recognition**
  - **Validates: Requirements 5.1, 5.2, 5.3**

- [x] 6.3 Test Complete Workflow Integration
  - Test end-to-end workflow: user query → AI Planner → CRM Agent → Salesforce
  - Verify WebSocket streaming for real-time responses
  - Test LLM-based result analysis and formatting
  - _Requirements: 5.5_

- [ ]* 6.4 Write integration tests for complete workflow
  - Test multiple workflow scenarios with different query types
  - Test error handling in complete workflow
  - _Requirements: 5.5_

- [x] 7. Comprehensive Integration Test Suite
  - Create Salesforce integration test script following Bill.com pattern
  - Implement multiple test scenarios covering all CRM operations
  - Include performance and reliability testing
  - _Requirements: All_

- [x] 7.1 Create Salesforce Integration Test Script
  - Follow the pattern of `test_planner_ap_integration.py`
  - Implement test scenarios for account retrieval, opportunity search, contact lookup
  - Include SOQL query execution and general CRM search scenarios
  - Add real-time tracing and comprehensive result validation
  - _Requirements: All_

- [x] 7.2 Implement Test Scenarios
  - **Scenario 1**: "Show me recent account updates from Salesforce"
  - **Scenario 2**: "Find opportunities in closing stage"
  - **Scenario 3**: "Get contacts for [specific account]"
  - **Scenario 4**: "Run SOQL query to get top accounts by revenue"
  - **Scenario 5**: "Search for [company name] in our CRM"
  - _Requirements: All_

- [ ]* 7.3 Write property tests for error handling
  - **Property 11: Error Message Clarity**
  - **Property 12: Retry Logic Robustness**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.7, 8.3**

- [ ]* 8. Performance and Reliability Testing
  - Test response times and concurrent request handling
  - Validate retry logic and error recovery
  - Measure success rates and reliability metrics
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 8.1 Test Performance Requirements
  - Measure CRM operation response times (target <2 seconds average)
  - Test concurrent request handling without performance degradation
  - Validate connection pooling efficiency and reuse
  - _Requirements: 8.1, 8.2, 8.5_

- [ ]* 8.2 Write property tests for performance
  - **Property 13: Performance Requirements**
  - **Property 14: Concurrent Request Handling**
  - **Property 15: Reliability Threshold**
  - **Validates: Requirements 8.1, 8.2, 8.4**

- [ ]* 8.3 Test Error Recovery and Reliability
  - Test temporary failure handling and retry logic
  - Simulate various error conditions and measure recovery
  - Validate >95% success rate over extended testing period
  - _Requirements: 8.3, 8.4_

- [ ]* 8.4 Write unit tests for error recovery
  - Test retry logic for temporary failures
  - Test timeout handling and graceful degradation
  - _Requirements: 8.3_

- [ ]* 9. Final Integration Validation
  - Run complete test suite and validate 100% success rate
  - Compare results with Bill.com integration success metrics
  - Document performance and reliability achievements
  - _Requirements: All_

- [ ]* 9.1 Execute Complete Test Suite
  - Run all test scenarios with real Salesforce data
  - Validate 100% HTTP MCP transport success rate
  - Confirm AI Planner integration with >90% accuracy
  - Measure and document performance metrics
  - _Requirements: All_

- [ ]* 9.2 Document Integration Success
  - Create success summary comparing with Bill.com achievements
  - Document configuration requirements and setup instructions
  - Provide troubleshooting guide for common issues
  - _Requirements: All_

- [ ]* 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate complete workflows
- The approach follows the proven Bill.com integration pattern for maximum reliability