# Salesforce Agent HTTP Integration Specification

## Overview

This specification defines the requirements for applying the successful Bill.com HTTP MCP integration improvements to the Salesforce/CRM agent. The goal is to achieve the same level of reliability and functionality that was accomplished with the Bill.com agent, ensuring 100% success rate with real data retrieval from Salesforce.

## Context

The Bill.com agent integration has been successfully completed with the following achievements:
- ✅ 100% HTTP MCP transport reliability (vs 0% with STDIO transport)
- ✅ Real data retrieval from Bill.com sandbox (Acme Marketing, invoices 1001/1002)
- ✅ Complete AI Planner + HTTP AP Agent integration working
- ✅ Robust error handling and parameter validation
- ✅ FastMCP CallToolResult format processing

The Salesforce agent currently exists in HTTP form but needs validation and potential improvements to match the Bill.com success pattern.

## User Stories

### User Story 1: Salesforce Data Retrieval
**As a business user**, I want to query Salesforce data through the CRM agent, so that I can get real-time information about accounts, opportunities, and contacts.

**Acceptance Criteria:**
- CRM agent successfully connects to Salesforce MCP server via HTTP transport
- Real Salesforce data is retrieved and processed correctly
- Query responses include actual account names, opportunity amounts, and contact details
- Error handling provides clear feedback when Salesforce is unavailable

### User Story 2: AI Planner Integration
**As a business user**, I want the AI Planner to automatically route CRM queries to the Salesforce agent, so that I can get CRM insights without specifying technical details.

**Acceptance Criteria:**
- AI Planner correctly identifies CRM-related queries
- Planner selects CRM agent with high confidence (>90%)
- Complete workflow from user query → AI Planner → CRM Agent → Salesforce works end-to-end
- Results are formatted in business-friendly language

### User Story 3: Multi-Operation Support
**As a business user**, I want to perform various CRM operations (accounts, opportunities, contacts, SOQL queries), so that I can access comprehensive Salesforce data.

**Acceptance Criteria:**
- All CRM operations work: get_accounts, get_opportunities, get_contacts, search_records, run_soql_query
- Parameters are correctly validated and passed to Salesforce MCP server
- Results are consistently formatted regardless of operation type
- Complex SOQL queries execute successfully

## Technical Requirements

### Requirement 1: HTTP MCP Transport Validation
**Priority: High**

The Salesforce agent must use HTTP MCP transport exclusively, following the same pattern as the successful Bill.com agent.

**Acceptance Criteria:**
- ✅ CRM agent uses `app.services.mcp_http_client` (not `mcp_client_service`)
- ✅ All tool calls go through HTTP MCP manager
- ✅ FastMCP CallToolResult format is properly processed
- ✅ Connection pooling and error handling match Bill.com agent pattern

### Requirement 2: Salesforce MCP Server Validation
**Priority: High**

The Salesforce MCP server must be running in HTTP mode and properly configured.

**Acceptance Criteria:**
- ✅ Salesforce MCP server starts on designated port (9001)
- ✅ Health check endpoint responds correctly
- ✅ All Salesforce tools are registered and accessible
- ✅ Salesforce CLI integration works properly
- ✅ Authentication with Salesforce org is successful

### Requirement 3: Tool Name and Parameter Mapping
**Priority: High**

Tool names and parameters must be correctly mapped between the CRM agent and Salesforce MCP server.

**Acceptance Criteria:**
- ✅ Tool name mapping is accurate (e.g., `salesforce_get_accounts` not `get_salesforce_accounts`)
- ✅ Parameter names match server expectations (e.g., `limit`, `account_name`, `query`)
- ✅ Optional parameters are handled correctly
- ✅ Error messages indicate specific parameter issues

### Requirement 4: Real Data Retrieval Testing
**Priority: High**

The integration must successfully retrieve real data from a configured Salesforce org.

**Acceptance Criteria:**
- ✅ Salesforce credentials are properly configured in `.env`
- ✅ Test queries return actual Salesforce data (not mock data)
- ✅ Account, opportunity, and contact data is retrieved successfully
- ✅ SOQL queries execute and return real results
- ✅ Search operations find existing records

### Requirement 5: AI Planner Integration
**Priority: Medium**

The AI Planner must correctly route CRM queries to the Salesforce agent.

**Acceptance Criteria:**
- ✅ Planner identifies CRM-related queries with >90% accuracy
- ✅ CRM agent is selected for appropriate queries
- ✅ Complete workflow executes without errors
- ✅ Results are properly formatted for business users

### Requirement 6: Error Handling and Validation
**Priority: Medium**

Error handling must be robust and provide clear feedback.

**Acceptance Criteria:**
- ✅ Connection errors are handled gracefully
- ✅ Invalid parameters are validated before MCP calls
- ✅ Salesforce API errors are properly translated
- ✅ Timeout handling works correctly
- ✅ Error messages are user-friendly

## Implementation Tasks

### Phase 1: Environment and Server Validation
1. **Verify Salesforce MCP Server Configuration**
   - Check if Salesforce MCP server can start in HTTP mode
   - Validate Salesforce CLI authentication
   - Test basic tool registration and health checks

2. **Validate Environment Configuration**
   - Ensure Salesforce credentials are properly set in `.env`
   - Verify `SALESFORCE_ORG_ALIAS` points to accessible org
   - Test Salesforce CLI connectivity

### Phase 2: HTTP Agent Validation
1. **Review CRM HTTP Agent Implementation**
   - Compare with successful Bill.com HTTP agent pattern
   - Validate HTTP MCP client usage
   - Check tool name mappings and parameter handling

2. **Test Individual CRM Operations**
   - Test each operation: accounts, opportunities, contacts, search, SOQL
   - Validate parameter passing and result processing
   - Ensure FastMCP CallToolResult format handling

### Phase 3: Integration Testing
1. **Create Salesforce Integration Test Script**
   - Follow the pattern of `test_planner_ap_integration.py`
   - Test AI Planner → CRM Agent → Salesforce workflow
   - Include multiple test scenarios for different CRM operations

2. **Validate Real Data Retrieval**
   - Test with actual Salesforce org data
   - Verify account, opportunity, and contact retrieval
   - Test SOQL query execution with real queries

### Phase 4: Performance and Reliability
1. **Performance Testing**
   - Measure response times for different operations
   - Test concurrent request handling
   - Validate connection pooling efficiency

2. **Reliability Testing**
   - Test error scenarios (network issues, auth failures)
   - Validate retry logic and timeout handling
   - Test recovery from temporary failures

## Success Criteria

The Salesforce agent integration is considered successful when:

1. **100% HTTP MCP Transport Success Rate**
   - All MCP calls succeed without STDIO transport issues
   - Connection pooling works efficiently
   - No subprocess management conflicts

2. **Real Data Retrieval Achievement**
   - Actual Salesforce data is retrieved and processed
   - All CRM operations return real results
   - SOQL queries execute successfully

3. **AI Planner Integration Success**
   - Planner correctly routes CRM queries (>90% accuracy)
   - Complete workflow executes end-to-end
   - Results are properly formatted

4. **Comprehensive Test Coverage**
   - All CRM operations tested with real data
   - Error scenarios handled gracefully
   - Performance meets acceptable thresholds

## Test Scenarios

### Scenario 1: Account Retrieval
- **Query**: "Show me recent account updates from Salesforce"
- **Expected**: AI Planner → CRM Agent → Salesforce accounts retrieved
- **Validation**: Real account data with names, industries, revenue

### Scenario 2: Opportunity Search
- **Query**: "Find opportunities in closing stage"
- **Expected**: AI Planner → CRM Agent → Salesforce opportunities filtered by stage
- **Validation**: Real opportunity data with amounts, stages, close dates

### Scenario 3: Contact Lookup
- **Query**: "Get contacts for [specific account]"
- **Expected**: AI Planner → CRM Agent → Salesforce contacts for account
- **Validation**: Real contact data with emails, titles, account associations

### Scenario 4: SOQL Query Execution
- **Query**: "Run SOQL query to get top accounts by revenue"
- **Expected**: AI Planner → CRM Agent → Custom SOQL query execution
- **Validation**: Real query results with proper data formatting

### Scenario 5: General CRM Search
- **Query**: "Search for [company name] in our CRM"
- **Expected**: AI Planner → CRM Agent → Salesforce search across objects
- **Validation**: Real search results across accounts, contacts, opportunities

## Dependencies

- Salesforce CLI installed and configured
- Valid Salesforce org credentials in `.env`
- Salesforce MCP server implementation
- HTTP MCP client infrastructure
- AI Planner service
- LLM service (Gemini) for query analysis

## Risks and Mitigations

### Risk 1: Salesforce Authentication Issues
- **Mitigation**: Validate credentials and org access before testing
- **Fallback**: Use Salesforce sandbox or developer org

### Risk 2: Salesforce CLI Dependencies
- **Mitigation**: Ensure Salesforce CLI is properly installed and configured
- **Fallback**: Consider direct Salesforce API integration if CLI fails

### Risk 3: MCP Server Compatibility
- **Mitigation**: Follow FastMCP patterns used in Bill.com server
- **Fallback**: Update server implementation to match working patterns

### Risk 4: Data Access Limitations
- **Mitigation**: Use test org with known data for validation
- **Fallback**: Create test data if org is empty

## Deliverables

1. **Validated Salesforce HTTP Agent**
   - Working CRM agent with HTTP MCP transport
   - All operations tested and validated

2. **Salesforce MCP Server (HTTP Mode)**
   - Server running in HTTP mode on designated port
   - All tools registered and accessible

3. **Integration Test Suite**
   - Comprehensive test script following Bill.com pattern
   - Multiple scenarios covering all CRM operations

4. **Documentation Updates**
   - Configuration guide for Salesforce integration
   - Troubleshooting guide for common issues

5. **Performance Metrics**
   - Response time measurements
   - Success rate statistics
   - Reliability test results

## Definition of Done

- [ ] Salesforce MCP server starts successfully in HTTP mode
- [ ] CRM HTTP agent connects to Salesforce server without errors
- [ ] All CRM operations (accounts, opportunities, contacts, search, SOQL) work with real data
- [ ] AI Planner correctly routes CRM queries to Salesforce agent
- [ ] Integration test suite passes with 100% success rate
- [ ] Performance meets acceptable thresholds (< 2 seconds per operation)
- [ ] Error handling provides clear, actionable feedback
- [ ] Documentation is complete and accurate