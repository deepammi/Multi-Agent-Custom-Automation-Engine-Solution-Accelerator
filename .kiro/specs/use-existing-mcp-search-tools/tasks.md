# Implementation Plan: Improve MCP Tool Selection with AI Guidance

## Overview

Fix the confirmed issue where agents choose listing tools instead of search tools by providing crystal clear tool descriptions and enhanced LLM prompts. This AI-guided approach is flexible and maintainable compared to rigid keyword extraction rules.

## Tasks

- [ ] 1. Update Gmail agent tool descriptions and prompts
  - [x] 1.1 Enhance LLM intent analysis prompt with clear tool selection rules
    - Update prompt in `backend/app/agents/gmail_agent_node.py` 
    - Add crystal clear examples of when to use "search" vs "list"
    - Emphasize that ANY keywords should trigger "search" action
    - _Requirements: 1.1, 1.2_

  - [ ]* 1.2 Add optional validation check for tool choices
    - Create simple validation function to warn about suspicious choices
    - Log warnings when keyword queries choose "list" action
    - _Requirements: 4.1_

- [ ]* 1.3 Write property test for Gmail tool selection
  - **Property 1: Clear Tool Descriptions Lead to Correct Choices**
  - **Validates: Requirements 1.1, 1.2**

- [x] 2. Update Salesforce agent tool selection logic
  - [x] 2.1 Enhance CRM agent to prefer search_records for keyword queries
    - Update agent logic in `backend/app/agents/crm_agent.py`
    - Add clear guidance about when to use search_records vs get_accounts
    - _Requirements: 2.1, 2.2_

  - [x] 2.2 Update CRM agent node to pass better context to LLM
    - Ensure user query context is preserved for decision making
    - _Requirements: 2.1_

- [ ]* 2.3 Write property test for CRM tool selection
  - **Property 2: CRM Search Tool Selection**
  - **Validates: Requirements 2.1, 2.2**

- [x] 3. Update Bill.com agent tool selection logic
  - [x] 3.1 Enhance Bill.com agent to prefer search_bills for keyword queries
    - Update agent logic in `backend/app/agents/accounts_payable_agent_http.py`
    - Add clear guidance about when to use search_bills vs list_bills
    - _Requirements: 3.1, 3.2_

  - [x] 3.2 Update Bill.com agent node to pass better context
    - Ensure user query context is preserved for decision making
    - _Requirements: 3.1_

- [ ]* 3.3 Write property test for Bill.com tool selection
  - **Property 3: Bill.com Search Tool Selection**
  - **Validates: Requirements 3.1, 3.2**

- [x] 4. Test and validate the AI-guided approach
  - [x] 4.1 Update test cases to verify improved tool selection
    - Modify `backend/test_multi_agent_coordination.py` to test keyword queries
    - Add test case: "check all emails, bills and customer crm accounts with keywords TBI Corp or TBI-001"
    - Verify each agent chooses search tools instead of listing tools
    - _Requirements: 1.1, 2.1, 3.1_

  - [x] 4.2 Test edge cases and fallback behavior
    - Test queries asking for "recent" items (should use list tools)
    - Test mixed queries with both keywords and recency requests
    - Verify validation warnings work correctly
    - _Requirements: 1.4, 2.4, 3.4, 4.1_

- [ ]* 4.3 Write integration property test
  - **Property 4: End-to-End Tool Selection Accuracy**
  - **Validates: Requirements 1.1, 2.1, 3.1**

- [x] 5. Checkpoint - Verify improved tool selection
  - Run updated test with keyword query
  - Confirm Gmail agent calls `search_messages` instead of `list_messages`
  - Confirm CRM agent calls `search_records` instead of `get_accounts`
  - Confirm Bill.com agent calls `search_bills` instead of `list_bills`
  - Check validation warnings appear for suspicious choices
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 6. Performance and compatibility validation
  - [ ]* 6.1 Measure improvement in tool selection accuracy
    - Compare before/after tool selection for various query types
    - Measure result relevance improvements
    - Document accuracy gains
    - _Requirements: Success Metrics_

  - [ ]* 6.2 Ensure backward compatibility
    - Verify non-keyword queries still work with listing tools
    - Ensure existing functionality is preserved
    - Test edge cases and error scenarios
    - _Requirements: 1.4, 2.4, 3.4_

- [ ]* 6.3 Write property test for fallback behavior
  - **Property 5: Appropriate Fallback to List Tools**
  - **Validates: Requirements 1.4, 2.4, 3.4**

- [ ]* 7. Final validation and documentation
  - [ ]* 7.1 Run comprehensive test suite
    - Execute all property tests (minimum 100 iterations each)
    - Run integration tests with real MCP servers
    - Verify validation warnings and edge cases
    - _Requirements: All_

  - [ ]* 7.2 Document the AI-guided approach
    - Document enhanced prompts and tool descriptions
    - Add examples of good vs bad tool choices
    - Create troubleshooting guide for tool selection issues
    - _Requirements: Documentation_

- [ ]* 8. Final checkpoint - Complete verification
  - Ensure agents return filtered results for keyword queries
  - Verify tool selection accuracy is significantly improved
  - Confirm validation system catches suspicious choices
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation of improved tool selection
- Property tests validate universal correctness properties across all inputs
- The AI-guided approach is flexible and doesn't require rigid keyword extraction rules

## Expected Outcomes

After completing these tasks:
- ✅ Gmail agent will choose "search" action for keyword queries like "TBI Corp"
- ✅ Salesforce agent will use `search_records` instead of `get_accounts` for company searches
- ✅ Bill.com agent will use `search_bills` instead of `list_bills` for invoice searches
- ✅ Validation system will warn about suspicious tool choices
- ✅ Backward compatibility maintained for "recent" and "latest" queries
- ✅ Overall tool selection accuracy significantly improved through better AI guidance