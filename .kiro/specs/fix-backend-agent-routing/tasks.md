# Implementation Plan: Fix Backend Agent Routing

## Overview

Fix the backend agent routing system to ensure all user queries go through the Planner agent first, instead of bypassing it and going directly to domain-specific agents like Invoice.

## Tasks

- [x] 1. Update AI Planner Service Configuration
  - Add "planner" to available_agents list in AIPlanner class
  - Add planner capabilities to agent_capabilities mapping
  - Define planner agent role and responsibilities
  - _Requirements: 1.3, 3.1, 3.2_

- [ ] 2. Fix Sequence Generation Logic
  - [x] 2.1 Update sequence generation prompt to require planner-first routing
    - Modify `_create_sequence_prompt()` to emphasize planner as first agent
    - Update prompt instructions to always start with planner agent
    - _Requirements: 2.1, 2.2_

  - [x] 2.2 Add sequence validation for planner-first requirement
    - Update `_parse_sequence_response()` to validate planner is first agent
    - Reject sequences that don't start with "planner"
    - _Requirements: 2.4, 4.4_

- [ ] 3. Update Fallback Sequence Logic
  - [x] 3.1 Fix fallback sequence generation to include planner
    - Modify `get_fallback_sequence()` to always start with "planner"
    - Update all fallback scenarios to include planner agent
    - _Requirements: 2.5, 4.2_

  - [x] 3.2 Update mock mode sequence generation
    - Modify `_get_mock_sequence()` to start with planner agent
    - Update `_get_mock_analysis()` to include planner in estimated agents
    - _Requirements: 4.3, 6.4_

- [ ] 4. Add Sequence Validation and Error Handling
  - [x] 4.1 Implement agent sequence validation
    - Create validation function to check planner-first requirement
    - Add logging for validation failures
    - _Requirements: 4.4, 4.5_

  - [ ] 4.2 Update error handling to preserve planner routing
    - Ensure all error recovery includes planner agent
    - Log when sequences bypass planner agent
    - _Requirements: 4.5, 6.5_

- [ ] 5. Testing and Verification
  - [ ] 5.1 Add unit tests for AI Planner service updates
    - Test available_agents includes "planner"
    - Test agent_capabilities includes planner definition
    - Test sequence generation starts with planner
    - _Requirements: 6.1, 6.2_

  - [ ] 5.2 Add integration tests for planner-first routing
    - Test end-to-end workflow with planner agent
    - Test WebSocket messages include planner execution
    - Test database persistence with planner sequences
    - _Requirements: 6.3, 6.5_

- [ ] 6. Checkpoint - Verify planner routing is working
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Deploy and Monitor
  - [ ] 7.1 Deploy changes with enhanced logging
    - Add logging for agent sequence generation
    - Monitor planner agent usage in production
    - _Requirements: 6.5_

  - [ ] 7.2 Verify backward compatibility
    - Test existing API endpoints continue to work
    - Verify WebSocket message formats unchanged
    - Confirm frontend integration remains functional
    - _Requirements: 5.1, 5.2, 5.3_

## Notes

- Tasks focus on fixing the core routing issue without breaking existing functionality
- All changes maintain backward compatibility with current API and WebSocket interfaces
- Testing ensures the Planner agent is properly integrated into all workflows
- Monitoring verifies the fix works correctly in production