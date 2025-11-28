# Implementation Plan: Multi-Agent Loop with Human-in-the-Loop

- [x] 1. Implement HITL Agent Node
  - Create `hitl_agent_node` function in `backend/app/agents/nodes.py`
  - Takes specialized agent result as input
  - Formats clarification request message
  - Returns structured response for WebSocket
  - _Requirements: 1.1, 1.2_

- [ ]* 1.1 Write property test for HITL routing
  - **Property 1: HITL Routing**
  - **Validates: Requirements 1.1, 1.2**

- [x] 2. Implement Context Manager
  - Create context storage in `agent_service.py`
  - Store original task description with execution state
  - Maintain execution history list
  - Pass context through loop iterations
  - _Requirements: 2.1, 2.2_

- [ ]* 2.1 Write property test for context preservation
  - **Property 2: Context Preservation**
  - **Validates: Requirements 2.1, 2.2**

- [x] 3. Update Agent Service for HITL Routing
  - Modify `execute_task` to route specialized agent result to HITL
  - Add HITL agent invocation after specialized agent completes
  - Send clarification request via WebSocket
  - Store execution state for loop handling
  - _Requirements: 1.1, 1.2, 3.1_

- [ ]* 3.1 Write property test for approval completion
  - **Property 3: Approval Completion**
  - **Validates: Requirements 1.3**

- [x] 4. Implement Clarification Response Handler
  - Create `handle_user_clarification` function in `agent_service.py`
  - Parse user response (approval vs revision)
  - If approval: mark task complete and send final result
  - If revision: route directly to specialized agent with context
  - _Requirements: 1.3, 1.4, 2.3_

- [ ]* 4.1 Write property test for revision loop
  - **Property 4: Revision Loop**
  - **Validates: Requirements 1.4, 2.3**

- [x] 5. Add Optional HITL Configuration
  - Add `require_hitl` flag to task execution
  - Skip HITL agent if flag is false
  - Complete task directly after specialized agent if skipped
  - _Requirements: 3.1, 3.2_

- [ ]* 5.1 Write property test for optional HITL
  - **Property 5: Optional HITL**
  - **Validates: Requirements 3.1, 3.2**

- [x] 6. Implement Frontend Clarification UI
  - Create `ClarificationUI` component in `src/frontend/src/components/content/`
  - Display agent result in read-only section
  - Text input field for user response
  - "Retry" button for submission
  - "OK" button for quick approval
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 7. Add Clarification Message Handler in Frontend
  - Listen for `user_clarification_request` messages in `PlanPage.tsx`
  - Display clarification UI when message received
  - Hide approval buttons
  - Show input field and retry button
  - _Requirements: 4.1, 4.5_

- [x] 8. Implement Clarification Response Submission
  - Create `submitClarification` function in `apiService.tsx`
  - Send user response to backend via `/api/v3/user_clarification` endpoint
  - Handle response and wait for next message
  - _Requirements: 1.4, 4.3, 4.4_

- [ ]* 8.1 Write property test for unlimited iterations
  - **Property 6: Unlimited Iterations**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 9. Checkpoint - Ensure all tests pass
  - Run all property-based tests
  - Verify no regressions in existing tests
  - Ask the user if questions arise

- [x] 10. End-to-End Testing
  - Test complete flow: Task → Planner → Specialized Agent → HITL → Approval → Complete
  - Test revision loop: Task → Planner → Specialized Agent → HITL → Revision → Specialized Agent (direct) → HITL → Complete
  - Test multiple revision loops (3+ iterations)
  - Test optional HITL bypass
  - _Requirements: All_

- [ ]* 10.1 Write integration tests
  - Test end-to-end approval flow
  - Test end-to-end revision loop
  - Test multiple revision scenarios
  - _Requirements: All_

- [ ] 11. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise
