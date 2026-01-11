# Use Existing MCP Search Tools for Keyword-Based Queries

## Overview
Ensure agents use the existing search capabilities in MCP servers instead of general data retrieval when specific keywords are present in user queries.

## Problem Statement
**CONFIRMED ISSUE:** Agents call general listing tools (`list_messages`, `get_accounts`, `list_bills`) even when users specify keywords like "TBI Corp" or "TBI-001". All MCP servers already have search tools that accept keyword parameters, but agents aren't using them.

**Test Results:**
- ✅ MCP servers have proper search tools: `gmail_search_messages`, `salesforce_search_records`, `search_bill_com_bills`
- ❌ Gmail agent chooses 'list' action instead of 'search' for keyword queries
- ❌ Query parameter is empty: '' instead of "TBI Corp OR TBI-001"
- ❌ Result: Returns latest 10 emails instead of filtered results

## User Stories

### US1: Gmail Agent Uses Search Instead of List
**As a** user requesting email data with specific keywords  
**I want** the Gmail agent to use `search_messages` with my keywords  
**So that** I get targeted results instead of all emails  

**Acceptance Criteria:**
1. WHEN user query contains keywords like "TBI Corp" or "TBI-001", THE Gmail Agent SHALL call `search_messages` tool
2. THE search query parameter SHALL include the extracted keywords
3. THE results SHALL be filtered to only relevant emails
4. THE agent SHALL fall back to `list_messages` only when no keywords are specified

### US2: Salesforce Agent Uses Search Instead of General Queries
**As a** user requesting CRM data with specific keywords  
**I want** the Salesforce agent to use `search_records` with my keywords  
**So that** I get targeted CRM records instead of all accounts/opportunities  

**Acceptance Criteria:**
1. WHEN user query contains keywords, THE Salesforce Agent SHALL call `search_records` tool
2. THE search term parameter SHALL include the extracted keywords
3. THE results SHALL include accounts, opportunities, and contacts matching the keywords
4. THE agent SHALL fall back to general queries only when no keywords are specified

### US3: Bill.com Agent Uses Search Instead of List
**As a** user requesting invoice data with specific keywords  
**I want** the Bill.com agent to use `search_bills` with my keywords  
**So that** I get targeted invoices instead of all bills  

**Acceptance Criteria:**
1. WHEN user query contains keywords like "TBI-001", THE Bill.com Agent SHALL call `search_bills` tool
2. THE search term parameter SHALL include the extracted keywords
3. THE results SHALL be filtered to only relevant invoices
4. THE agent SHALL fall back to `list_bills` only when no keywords are specified

### US4: Keyword Extraction from User Queries
**As a** system processing user queries  
**I want** to extract relevant keywords from natural language  
**So that** agents can use them for targeted searches  

**Acceptance Criteria:**
1. THE system SHALL extract company names (e.g., "TBI Corp", "Acme Corp")
2. THE system SHALL extract invoice/reference numbers (e.g., "TBI-001", "INV-123")
3. THE system SHALL extract email subjects or sender names when specified
4. THE system SHALL pass extracted keywords to appropriate agents

## Existing MCP Tools to Use

### Gmail MCP Server (`src/mcp_server/gmail_mcp_server.py`)
```python
# Current: agents call this
list_messages(max_results=10)

# Should call this when keywords present
search_messages(query="TBI Corp OR TBI-001", max_results=10)
```

### Salesforce MCP Server (`src/mcp_server/salesforce_mcp_server.py`)
```python
# Current: agents call these
get_accounts()
get_opportunities()
get_contacts()

# Should call this when keywords present
search_records(search_term="TBI Corp")
# Or use SOQL for more precise queries
soql_query(query="SELECT Id, Name FROM Account WHERE Name LIKE '%TBI%'")
```

### Bill.com MCP Server (`src/mcp_server/billcom_mcp_server.py`)
```python
# Current: agents call this
list_bills()

# Should call this when keywords present
search_bills(search_term="TBI-001")
```

## Implementation Approach

### Phase 1: Update Agent Logic
1. **Modify Gmail Agent** (`backend/app/agents/gmail_agent_node.py`)
   - Add keyword extraction from task context
   - Use `search_messages` when keywords present
   - Fall back to `list_messages` when no keywords

2. **Modify Salesforce Agent** (`backend/app/agents/crm_agent.py`)
   - Add keyword extraction from task context
   - Use `search_records` when keywords present
   - Fall back to general queries when no keywords

3. **Modify Bill.com Agent** (`backend/app/agents/accounts_payable_agent_http.py`)
   - Add keyword extraction from task context
   - Use `search_bills` when keywords present
   - Fall back to `list_bills` when no keywords

### Phase 2: Keyword Extraction Utility
1. Create shared utility for extracting keywords from user queries
2. Support patterns like:
   - Company names: "TBI Corp", "Acme Corporation"
   - Reference numbers: "TBI-001", "INV-123", "PO-456"
   - Email patterns: "from:john@example.com", "subject:meeting"

### Phase 3: Testing
1. Test with query: "check all emails, bills and customer crm accounts with keywords TBI Corp or TBI-001"
2. Verify each agent uses search tools instead of listing tools
3. Confirm results are filtered and relevant

## Success Metrics
- Gmail agent returns only emails containing "TBI Corp" or "TBI-001" (not all 10 emails)
- Salesforce agent returns only CRM records matching keywords (not all accounts)
- Bill.com agent returns only invoices matching keywords (not all bills)
- Total execution time should be similar or faster due to targeted queries
- Analysis agent receives focused, relevant data for better insights

## Files to Modify
- `backend/app/agents/gmail_agent_node.py` - Use search_messages
- `backend/app/agents/crm_agent.py` - Use search_records
- `backend/app/agents/accounts_payable_agent_http.py` - Use search_bills
- Create keyword extraction utility
- Update `backend/test_multi_agent_coordination.py` to verify search behavior

## Non-Goals
- Do not create new MCP tools or servers
- Do not modify existing MCP server implementations
- Do not change the multi-agent coordination workflow
- Do not alter the WebSocket or HTTP transport mechanisms