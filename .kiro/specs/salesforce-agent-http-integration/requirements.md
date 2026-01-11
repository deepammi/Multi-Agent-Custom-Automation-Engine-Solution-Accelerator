# Salesforce Agent HTTP Integration Requirements

## Introduction

This specification defines the requirements for applying the successful Bill.com HTTP MCP integration improvements to the Salesforce/CRM agent. The goal is to achieve the same level of reliability and functionality that was accomplished with the Bill.com agent, ensuring 100% success rate with real data retrieval from Salesforce.

## Glossary

- **CRM_Agent**: Customer Relationship Management agent that handles Salesforce operations
- **HTTP_MCP_Transport**: HTTP-based Model Context Protocol communication method
- **Salesforce_MCP_Server**: MCP server that provides Salesforce tools via HTTP
- **AI_Planner**: Service that analyzes user queries and routes them to appropriate agents
- **SOQL_Query**: Salesforce Object Query Language for database queries
- **FastMCP_CallToolResult**: Result format returned by FastMCP servers
- **Tool_Mapping**: Configuration that maps agent operations to MCP server tools

## Requirements

### Requirement 1: HTTP MCP Transport Implementation

**User Story:** As a business user, I want to query Salesforce data through the CRM agent, so that I can get real-time information about accounts, opportunities, and contacts.

#### Acceptance Criteria

1. WHEN the CRM agent initializes, THE CRM_Agent SHALL use HTTP MCP transport exclusively
2. WHEN the CRM agent calls a tool, THE CRM_Agent SHALL use `app.services.mcp_http_client` not `mcp_client_service`
3. WHEN MCP responses are received, THE CRM_Agent SHALL process FastMCP CallToolResult format correctly
4. THE CRM_Agent SHALL maintain connection pooling for efficient resource usage
5. WHEN HTTP connections fail, THE CRM_Agent SHALL provide clear error messages and retry appropriately

### Requirement 2: Salesforce MCP Server Integration

**User Story:** As a system administrator, I want the Salesforce MCP server to run reliably in HTTP mode, so that multiple clients can connect without conflicts.

#### Acceptance Criteria

1. WHEN the Salesforce MCP server starts, THE Salesforce_MCP_Server SHALL listen on designated port (9001) for HTTP requests
2. WHEN health checks are requested, THE Salesforce_MCP_Server SHALL respond with server status and available tools
3. WHEN tool calls are received, THE Salesforce_MCP_Server SHALL execute Salesforce CLI commands and return results
4. THE Salesforce_MCP_Server SHALL handle concurrent requests without blocking
5. WHEN authentication fails, THE Salesforce_MCP_Server SHALL return clear error messages

### Requirement 3: Tool Mapping and Parameter Validation

**User Story:** As a developer, I want tool calls to be properly mapped and validated, so that Salesforce operations execute correctly.

#### Acceptance Criteria

1. WHEN CRM agent calls get_accounts, THE System SHALL map to `salesforce_get_accounts` tool
2. WHEN CRM agent calls get_opportunities, THE System SHALL map to `salesforce_get_opportunities` tool
3. WHEN CRM agent calls get_contacts, THE System SHALL map to `salesforce_get_contacts` tool
4. WHEN CRM agent calls search_records, THE System SHALL map to `salesforce_search_records` tool
5. WHEN CRM agent calls run_soql_query, THE System SHALL map to `salesforce_soql_query` tool
6. WHEN parameters are passed, THE System SHALL validate required parameters before MCP calls
7. WHEN optional parameters are provided, THE System SHALL include them in tool calls appropriately

### Requirement 4: Real Data Retrieval and Processing

**User Story:** As a business user, I want to see actual Salesforce data in query results, so that I can make informed business decisions.

#### Acceptance Criteria

1. WHEN accounts are requested, THE System SHALL return real Salesforce account data with names, industries, and revenue
2. WHEN opportunities are requested, THE System SHALL return real opportunity data with amounts, stages, and close dates
3. WHEN contacts are requested, THE System SHALL return real contact data with emails, titles, and account associations
4. WHEN SOQL queries are executed, THE System SHALL return actual query results from Salesforce
5. WHEN search operations are performed, THE System SHALL return real search results across Salesforce objects
6. THE System SHALL format monetary amounts with proper currency symbols
7. THE System SHALL format dates in readable format

### Requirement 5: AI Planner Integration

**User Story:** As a business user, I want the AI Planner to automatically route CRM queries to the Salesforce agent, so that I can get CRM insights without specifying technical details.

#### Acceptance Criteria

1. WHEN CRM-related queries are submitted, THE AI_Planner SHALL identify them with >90% accuracy
2. WHEN CRM queries are identified, THE AI_Planner SHALL select the CRM agent for execution
3. WHEN agent sequences are generated, THE AI_Planner SHALL include CRM agent for customer relationship queries
4. THE AI_Planner SHALL provide reasoning for agent selection decisions
5. WHEN CRM agent is selected, THE System SHALL execute the complete workflow without errors

### Requirement 6: Multi-Operation Support

**User Story:** As a business user, I want to perform various CRM operations, so that I can access comprehensive Salesforce data.

#### Acceptance Criteria

1. THE CRM_Agent SHALL support get_accounts operation with account name filtering and limits
2. THE CRM_Agent SHALL support get_opportunities operation with stage filtering and limits
3. THE CRM_Agent SHALL support get_contacts operation with account name filtering and limits
4. THE CRM_Agent SHALL support search_records operation across multiple Salesforce objects
5. THE CRM_Agent SHALL support run_soql_query operation for custom SOQL queries
6. WHEN invalid operations are requested, THE CRM_Agent SHALL return clear error messages
7. WHEN operations succeed, THE CRM_Agent SHALL return consistently formatted results

### Requirement 7: Error Handling and Validation

**User Story:** As a developer, I want robust error handling, so that I can identify and resolve issues quickly.

#### Acceptance Criteria

1. WHEN HTTP connections fail, THE System SHALL provide clear error messages indicating connectivity issues
2. WHEN Salesforce authentication fails, THE System SHALL return authentication-specific error messages
3. WHEN invalid parameters are provided, THE System SHALL validate and reject them with specific feedback
4. WHEN Salesforce API errors occur, THE System SHALL translate them into user-friendly messages
5. WHEN timeouts occur, THE System SHALL handle them gracefully with retry logic
6. THE System SHALL log all errors with sufficient context for debugging
7. WHEN errors are returned to users, THE System SHALL provide actionable guidance

### Requirement 8: Performance and Reliability

**User Story:** As a business user, I want CRM queries to execute quickly and reliably, so that I can work efficiently.

#### Acceptance Criteria

1. WHEN CRM operations are executed, THE System SHALL complete them within 2 seconds on average
2. WHEN multiple concurrent requests are made, THE System SHALL handle them without performance degradation
3. WHEN temporary failures occur, THE System SHALL retry operations automatically
4. THE System SHALL maintain >95% success rate for CRM operations
5. WHEN connection pooling is used, THE System SHALL reuse connections efficiently