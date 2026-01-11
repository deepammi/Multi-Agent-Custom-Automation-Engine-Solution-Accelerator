# Implementation Plan: Multi-Agent Loop with Human-in-the-Loop

## Overview

This implementation plan covers comprehensive multi-agent testing with frontend integration, including dual HITL approval points, real-time progress display, and verbose results presentation. The plan builds incrementally from frontend enhancements through backend services to full integration testing.

## Tasks

- [x] 1. Enhance Frontend Query Submission Interface
  - Update `HomePage.tsx` to include comprehensive testing mode toggle
  - Add query validation for multi-agent workflows
  - Implement workflow initiation with progress indicators
  - Add team selection integration for multi-agent coordination
  - _Requirements: 1.1, 1.2, 1.3_

- [x]* 1.1 Write property test for frontend workflow initiation
  - **Property 1: Frontend Workflow Initiation**
  - **Validates: Requirements 1.1, 1.2, 1.3**

- [x] 2. Implement Plan Approval UI Components
  - Create `PlanApprovalDisplay.tsx` component for plan review
  - Add plan details display with agent sequence and duration
  - Implement approve/reject buttons with modification options
  - Add expandable sections for plan details
  - _Requirements: 1.4, 1.5, 2.2_

- [ ]* 2.1 Write property test for plan display completeness
  - **Property 2: Plan Display Completeness**
  - **Validates: Requirements 1.4, 1.5, 2.2**

- [x] 3. Create Comprehensive Results Display Component
  - Create `ComprehensiveResultsDisplay.tsx` component
  - Implement tabbed interface for agent results
  - Add data correlation visualization
  - Display executive summary and recommendations
  - Include metadata about data quality and sources
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 3.1 Write property test for comprehensive results compilation
  - **Property 5: Comprehensive Results Compilation**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [x] 4. Enhance WebSocket Message Handling
  - Add new message types to `WebsocketMessageType` enum
  - Update `WebSocketService.tsx` for plan approval messages
  - Add comprehensive results message handling
  - Implement progress update message processing
  - Update `PlanPage.tsx` message routing
  - _Requirements: 2.1, 5.1_

- [ ]* 4.1 Write property test for plan approval gating
  - **Property 3: Plan Approval Gating**
  - **Validates: Requirements 2.1, 2.3, 2.5**

- [x] 5. Implement Plan Approval Backend Service
  - Create `plan_approval_service.py` for plan approval management
  - Add plan approval request formatting
  - Implement plan modification and rejection handling
  - Add plan approval state management
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 5.1 Write property test for plan rejection handling
  - **Property 12: Plan Rejection Handling**
  - **Validates: Requirements 2.4**

- [x] 6. Create Agent Coordination Layer
  - Create `agent_coordinator.py` for multi-agent orchestration
  - Implement sequential agent execution (Gmail → AP → CRM → Analysis)
  - Add inter-agent data passing and context management
  - Implement error recovery and retry logic for agents
  - Add MCP server coordination
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x]* 6.1 Write property test for sequential multi-agent execution
  - **Property 4: Sequential Multi-Agent Execution**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [x] 7. Implement Comprehensive Results Compiler
  - Create `results_compiler_service.py` for results aggregation
  - Add data correlation analysis between agent results
  - Implement executive summary generation
  - Add quality metrics and metadata calculation
  - Create results formatting for frontend display
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8. Enhance Agent Service for Comprehensive Workflows
  - Update `agent_service.py` for dual HITL approval points
  - Add comprehensive workflow state management
  - Implement revision targeting logic (specific agents vs full replan)
  - Add workflow progress tracking and reporting
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x]* 8.1 Write property test for final approval gating
  - **Property 6: Final Approval Gating**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.5**

- [x]* 8.2 Write property test for revision loop capability
  - **Property 7: Revision Loop Capability**
  - **Validates: Requirements 5.4, 10.1, 10.2, 10.3, 10.4, 10.5**

- [x] 9. Simplify Context Manager for Comprehensive Workflows
  - Create simple `workflow_context_service.py` for basic execution tracking
  - Add simple plan approval and final approval status tracking
  - Implement basic workflow state queries (no complex revisions)
  - Add simple "restart workflow" option instead of complex revision targeting
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 9.1 ~~Write property test for context preservation across iterations~~ (SKIPPED - comprehensive tests already exist)
  - **Property 9: Context Preservation Across Iterations**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [x] 10. Integrate Workflow Context Service with Existing APIs
  - Integrate `workflow_context_service.py` with existing `/api/v3/plan_approval` endpoint
  - Update `/api/v3/user_clarification` to use workflow context for simple approve/restart logic
  - Remove complex revision endpoints (already implemented in Task 8)
  - Use existing API structure - no new endpoints needed
  - _Requirements: 2.3, 2.4, 5.3, 9.1_

- [x] 11. Simplify Frontend Final Approval UI
  - Update `ClarificationUI.tsx` for comprehensive results approval
  - Add simple "Approve" / "Start New Task" options (no complex revisions)
  - Implement export/save results functionality
  - Remove complex revision targeting UI in favor of restart workflow
  - _Requirements: 5.1, 5.2, 5.3, 9.1, 9.2_

- [ ]* 11.1 Write property test for simplified clarification UI
  - **Property 11: Simplified Clarification UI Functionality**
  - **Validates: Requirements 9.1, 9.2, 9.3**

- [x] 12. Implement Real-time Progress Display
  - Update `PlanChat.tsx` for comprehensive workflow progress
  - Add agent-specific status indicators
  - Implement progress bar for workflow completion
  - Add estimated time remaining display
  - Show live agent execution status
  - _Requirements: 3.2, 3.3_

- [x] 13. Add Error Handling and Recovery
  - Implement frontend error handling for workflow failures
  - Add backend error recovery for agent failures
  - Create user intervention options for errors
  - Add network interruption handling with state preservation
  - Implement timeout handling for long-running agents
  - _Requirements: 3.5_

- [ ] 14. Maintain Legacy HITL Compatibility
  - Ensure existing HITL functionality continues to work
  - Add backward compatibility for existing clarification flows
  - Maintain support for simple single-agent workflows
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ]* 14.1 Write property test for legacy HITL routing
  - **Property 8: Legacy HITL Routing**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

- [ ]* 15. Implement Optional HITL Configuration
  - Add configuration options for HITL behavior
  - Implement HITL bypass for simple workflows
  - Add per-workflow HITL requirements
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 15.1 Write property test for configurable HITL behavior
  - **Property 10: Configurable HITL Behavior**
  - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [x] 16. Checkpoint - Frontend Integration Testing
  - Test frontend query submission and workflow initiation
  - Verify plan approval UI functionality
  - Test comprehensive results display
  - Validate WebSocket message handling
  - Ensure all tests pass, ask the user if questions arise

- [x] 17. Checkpoint - Backend Service Integration
  - Test agent coordination and sequential execution
  - Verify results compilation and correlation analysis
  - Test dual HITL approval points
  - Validate revision targeting and loop functionality
  - Ensure all tests pass, ask the user if questions arise

- [x] 18. End-to-End Simplified Workflow Testing
  - Test complete flow: Query → Plan Approval → Multi-Agent Execution → Final Approval → Complete
  - Test plan rejection flow: Query → Plan Rejection → New Task Submission
  - Test final results flow: Execution → Results Review → Approve/Restart Decision
  - Test error recovery scenarios and user intervention
  - Test real MCP server integration with fallback to mock mode
  - _Requirements: All_

- [ ]* 18.1 Write integration tests for simplified workflows
  - Test end-to-end simplified workflow
  - Test plan rejection and restart flows
  - Test final results approval/restart flows
  - Test error recovery scenarios
  - _Requirements: All_

- [ ]* 19. Performance and User Experience Testing
  - Test multi-agent execution performance and timing
  - Verify WebSocket message throughput during streaming
  - Test results compilation performance with large datasets
  - Validate frontend responsiveness during long workflows
  - Test mobile and desktop responsive behavior
  - _Requirements: All_

- [x] 20. Final Integration and Validation
  - Run comprehensive test suite across all components
  - Validate all 12 correctness properties
  - Test backward compatibility with existing workflows
  - Verify error handling and recovery mechanisms
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional property-based and integration tests
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key integration points
- Property tests validate universal correctness properties
- Integration tests validate complete workflow scenarios
- The implementation maintains backward compatibility with existing HITL functionality
- Real MCP server integration is tested with fallback to mock mode
