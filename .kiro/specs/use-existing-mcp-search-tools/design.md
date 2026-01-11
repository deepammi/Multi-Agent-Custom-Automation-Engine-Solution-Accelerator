# Design: Use Existing MCP Search Tools for Keyword-Based Queries

## Overview

This design addresses the confirmed issue where agents call general listing MCP tools instead of search tools when users provide specific keywords. The solution involves updating agent logic to detect keywords and route to appropriate search tools while maintaining backward compatibility.

## Architecture

### Current Flow (Problematic)
```
User: "check emails with TBI Corp"
  ↓
Gmail Agent LLM Analysis (unclear tool descriptions)
  ↓
Action: "list" (❌ Wrong choice due to poor guidance)
  ↓
list_messages(max_results=10) 
  ↓
Returns: Latest 10 emails (❌ Not filtered)
```

### Proposed Flow (AI-Guided)
```
User: "check emails with TBI Corp"
  ↓
Gmail Agent LLM Analysis (crystal clear tool descriptions)
  ↓
Action: "search" (✅ Correct choice with better guidance)
Query: "TBI Corp" (✅ LLM preserves keywords naturally)
  ↓
search_messages(query="TBI Corp", max_results=10)
  ↓
Returns: Only emails containing "TBI Corp" (✅ Filtered)
```

## Components and Interfaces

### 1. Enhanced Tool Descriptions for LLM Guidance

**Gmail Agent Tool Descriptions:**
```python
GMAIL_TOOL_DESCRIPTIONS = {
    "search_messages": {
        "name": "search_messages",
        "description": "Search messages using semantic search. Use this when the user asks about specific topics, content, people, companies, invoice numbers, or timeframes. Examples: 'messages about TBI Corp', 'emails containing INV-001', 'what did John say about the deadline', 'emails from last week about budget'. ALWAYS use this for keyword-based queries.",
        "parameters": {
            "query": "Search query with keywords, company names, invoice numbers, or topics",
            "max_results": "Maximum number of results (default: 15)"
        }
    },
    "list_messages": {
        "name": "list_messages", 
        "description": "List recent messages in chronological order. Use this ONLY when the user wants to see recent/latest messages without any specific topic, keyword, or search criteria. Examples: 'show my recent messages', 'latest emails', 'what are my newest emails'. DO NOT use this for keyword searches.",
        "parameters": {
            "max_results": "Maximum number of recent messages (default: 10)"
        }
    }
}
```

**Salesforce Agent Tool Descriptions:**
```python
SALESFORCE_TOOL_DESCRIPTIONS = {
    "search_records": {
        "name": "search_records",
        "description": "Search across accounts, contacts, and opportunities using keywords. Use this when the user mentions specific company names, contact names, or any search terms. Examples: 'find TBI Corp', 'search for Acme accounts', 'look up John Smith contact'. ALWAYS use this for keyword-based queries.",
        "parameters": {
            "search_term": "Company name, contact name, or keywords to search for",
            "objects": "Object types to search (default: Account, Contact, Opportunity)"
        }
    },
    "get_accounts": {
        "name": "get_accounts",
        "description": "List recent accounts in the system. Use this ONLY when the user wants to see general account listings without specific search criteria. Examples: 'show me accounts', 'list recent accounts'. DO NOT use this for company name searches.",
        "parameters": {
            "limit": "Maximum number of accounts (default: 5)"
        }
    }
}
```

**Bill.com Agent Tool Descriptions:**
```python
BILLCOM_TOOL_DESCRIPTIONS = {
    "search_bills": {
        "name": "search_bills",
        "description": "Search bills and invoices using keywords. Use this when the user mentions specific invoice numbers, vendor names, or any search terms. Examples: 'find invoice TBI-001', 'search for Acme bills', 'look up INV-123'. ALWAYS use this for keyword-based queries.",
        "parameters": {
            "search_term": "Invoice number, vendor name, or keywords to search for"
        }
    },
    "list_bills": {
        "name": "list_bills",
        "description": "List recent bills in chronological order. Use this ONLY when the user wants to see recent/latest bills without specific search criteria. Examples: 'show recent bills', 'latest invoices'. DO NOT use this for invoice number or vendor searches.",
        "parameters": {
            "limit": "Maximum number of recent bills (default: 10)"
        }
    }
}
```

### 2. Enhanced LLM Prompts with Clear Guidance

**Updated Gmail Agent Intent Analysis Prompt:**
```python
intent_prompt = f"""
Analyze this Gmail request and determine the action to take:

Request: "{user_request}"

TOOL SELECTION RULES:
1. If the request contains ANY specific keywords, company names, invoice numbers, people names, or topics → use "search"
2. If the request asks for "recent", "latest", "newest" emails with NO other criteria → use "list"
3. When in doubt, prefer "search" over "list"

EXAMPLES:
✅ SEARCH: "emails about TBI Corp" → search_messages(query="TBI Corp")
✅ SEARCH: "find INV-001" → search_messages(query="INV-001") 
✅ SEARCH: "messages from John about budget" → search_messages(query="from:John budget")
✅ LIST: "show my recent emails" → list_messages(max_results=10)
✅ LIST: "latest messages" → list_messages(max_results=10)

RESPOND WITH RAW JSON:
{{
    "action": "search|list|send|get",
    "query": "search terms if action=search",
    "max_results": 15
}}
"""
```

### 3. Simple Validation Check (Optional Warning System)

**Post-Decision Validation:**
```python
def validate_tool_choice(user_request: str, action_analysis: Dict[str, Any]) -> Optional[str]:
    """
    Simple check to warn if AI made a potentially incorrect tool choice.
    Returns warning message if suspicious, None if looks good.
    """
    user_lower = user_request.lower()
    action = action_analysis.get("action", "")
    
    # Check for obvious keyword queries that chose "list"
    keyword_indicators = ["corp", "inc", "ltd", "inv-", "po-", "bill-", "about", "containing", "from:", "subject:"]
    has_keywords = any(indicator in user_lower for indicator in keyword_indicators)
    
    if has_keywords and action == "list":
        return f"⚠️ WARNING: Query contains keywords but chose 'list' action. Consider 'search' instead."
    
    # Check for obvious recent queries that chose "search"
    recent_indicators = ["recent", "latest", "newest", "last few"]
    wants_recent = any(indicator in user_lower for indicator in recent_indicators)
    no_specific_terms = not has_keywords
    
    if wants_recent and no_specific_terms and action == "search":
        return f"⚠️ WARNING: Query asks for recent items but chose 'search'. Consider 'list' instead."
    
    return None  # Looks good
```

## Data Models

### Tool Description Schema
```python
@dataclass
class ToolDescription:
    name: str
    description: str  # Crystal clear usage guidance
    parameters: Dict[str, str]  # Parameter descriptions
    examples: List[str]  # Usage examples
    avoid_when: List[str]  # When NOT to use this tool
```

### Validation Result
```python
@dataclass
class ToolChoiceValidation:
    is_valid: bool
    warning_message: Optional[str]
    confidence_score: float  # 0.0 to 1.0
    suggested_action: Optional[str]  # Alternative if invalid
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Clear Tool Descriptions Lead to Correct Choices
*For any* user query containing specific keywords or search terms, the LLM should choose "search" action over "list" action when provided with crystal clear tool descriptions
**Validates: Requirements 1.1, 2.1, 3.1**

### Property 2: Search Query Preservation
*For any* user query with specific terms, the LLM should preserve those terms in the search query parameter
**Validates: Requirements 1.2, 2.2, 3.2**

### Property 3: Appropriate Fallback to List Tools
*For any* user query asking for "recent" or "latest" items without specific search criteria, the LLM should choose "list" action
**Validates: Requirements 1.4, 2.4, 3.4**

### Property 4: Validation Warnings for Suspicious Choices
*For any* tool choice that seems inconsistent with the user query, the validation system should provide a helpful warning
**Validates: Requirements 4.1, 4.2, 4.3**

## Error Handling

### Keyword Extraction Failures
- **Empty Keywords:** Fall back to general listing tools
- **Invalid Patterns:** Log warning and use general terms
- **Service Mismatch:** Use generic search operators

### MCP Tool Call Failures
- **Search Tool Unavailable:** Fall back to listing tools
- **Query Too Complex:** Simplify query and retry
- **No Results:** Return empty result set with explanation

### Agent Decision Failures
- **LLM Analysis Error:** Use keyword-based decision
- **Invalid Action:** Default to search if keywords present
- **Missing Parameters:** Use extracted keywords as fallback

## Testing Strategy

### Unit Tests
- Test keyword extraction with various input patterns
- Test search query building for each service
- Test agent decision logic with different query types
- Test fallback behavior when search fails

### Property-Based Tests
- **Property 1 Test:** Generate random queries with known keywords, verify detection
- **Property 2 Test:** Generate keyword queries, verify search tool selection
- **Property 3 Test:** Generate keywords, verify preservation in MCP calls
- **Property 4 Test:** Generate non-keyword queries, verify fallback behavior
- **Property 5 Test:** Generate search queries, verify result filtering

### Integration Tests
- Test end-to-end workflow with "TBI Corp" query
- Test multi-agent coordination with keyword queries
- Test performance comparison: search vs listing tools
- Test error scenarios and fallback behavior

### Test Configuration
- Use property-based testing library (Hypothesis for Python)
- Run minimum 100 iterations per property test
- Tag each test with feature and property reference:
  - **Feature: use-existing-mcp-search-tools, Property 1: Keyword Detection Accuracy**
  - **Feature: use-existing-mcp-search-tools, Property 2: Search Tool Selection**

## Implementation Plan

### Phase 1: Keyword Extraction Utility (2 hours)
1. Create `KeywordExtractor` class with regex patterns
2. Implement company name detection (e.g., "TBI Corp", "Acme Inc")
3. Implement reference number detection (e.g., "TBI-001", "INV-123")
4. Add service-specific query builders
5. Write unit tests for extraction accuracy

### Phase 2: Gmail Agent Updates (1 hour)
1. Modify `_determine_and_execute_action` to check keywords first
2. Force search action when keywords detected
3. Update LLM prompt to prefer search over list
4. Test with "TBI Corp" query

### Phase 3: CRM Agent Updates (1 hour)
1. Add `get_crm_data_with_keywords` method
2. Route to `search_records` when keywords present
3. Maintain backward compatibility
4. Test with "TBI Corp" query

### Phase 4: Bill.com Agent Updates (1 hour)
1. Add `get_bills_with_keywords` method
2. Route to `search_bills` when keywords present
3. Maintain backward compatibility
4. Test with "TBI-001" query

### Phase 5: Integration and Testing (1 hour)
1. Update multi-agent coordination to use new methods
2. Run end-to-end test with full query
3. Verify performance improvements
4. Document changes and usage

## Backward Compatibility

### Existing Code Compatibility
- All existing method signatures remain unchanged
- New methods are additive, not replacing existing ones
- Fallback behavior ensures no breaking changes
- Legacy code continues to work without modification

### Configuration Options
```python
# Optional configuration for keyword detection sensitivity
KEYWORD_EXTRACTION_CONFIG = {
    'min_confidence': 0.7,
    'enable_company_detection': True,
    'enable_reference_detection': True,
    'max_query_terms': 10,
    'fallback_to_listing': True
}
```

## Performance Considerations

### Expected Improvements
- **Reduced Data Transfer:** Search returns only relevant records
- **Faster Processing:** Less data for analysis agent to process
- **Better User Experience:** More accurate results
- **Lower API Costs:** Fewer unnecessary API calls

### Potential Concerns
- **Keyword Extraction Overhead:** ~10ms per query (negligible)
- **Search Query Complexity:** Limited by max_terms parameter
- **False Positives:** Mitigated by confidence scoring

## Security Considerations

### Input Validation
- Sanitize extracted keywords to prevent injection attacks
- Limit query complexity to prevent DoS
- Validate search terms against allowed patterns

### Data Privacy
- Keywords are processed in-memory only
- No persistent storage of extracted terms
- Existing MCP security model unchanged

## Monitoring and Logging

### Key Metrics
- Keyword detection accuracy rate
- Search vs listing tool usage ratio
- Query response time improvements
- User satisfaction with result relevance

### Logging Strategy
```python
logger.info(
    "Keyword extraction completed",
    extra={
        "user_query": user_query,
        "keywords_found": len(keywords),
        "has_searchable_content": has_keywords,
        "confidence_score": confidence,
        "tool_selected": "search" if has_keywords else "list"
    }
)
```