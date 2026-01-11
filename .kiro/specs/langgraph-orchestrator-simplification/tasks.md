# Implementation Plan

- [x] 1. Create AI-Driven Planner Component
  - Implement GenAI agent for task analysis and sequence generation
  - Create TaskAnalysis and AgentSequence data models
  - Integrate with existing LLMService for AI-powered planning
  - _Requirements: 1.1, 1.2, 5.1, 5.2_

- [ ]* 1.1 Write property test for AI sequence generation
  - **Property 1: AI Sequence Generation**
  - **Validates: Requirements 1.2, 5.2**

- [x] 2. Simplify AgentState Structure
  - Remove next_agent and workflow_type routing fields from AgentState
  - Add agent_sequence, current_step, and total_steps for linear tracking
  - Preserve collected_data and execution_results for cross-agent data sharing
  - Update all agent implementations to use simplified state
  - _Requirements: 7.1, 7.2_

- [ ]* 2.1 Write property test for data preservation
  - **Property 8: Data Preservation**
  - **Validates: Requirements 7.2**

- [x] 3. Eliminate Supervisor Router Function
  - Remove supervisor_router function completely from graph_refactored.py
  - Remove all conditional routing logic from agent implementations
  - Clean up next_agent routing logic from all agent nodes
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 3.1 Write unit test to verify router elimination
  - Verify supervisor_router function is not present in codebase
  - Verify no conditional routing logic exists in agents

- [x] 4. Implement Linear Graph Builder
  - Create function to build static LangGraph from agent sequences
  - Use only add_edge() method for all agent connections
  - Implement automatic workflow termination after final agent
  - Support dynamic graph creation based on AI-generated sequences
  - Add graph caching mechanism for performance optimization
  - Support multiple graph types (default, ai_driven, simple, hitl_enabled)
  - Integrate with AI Planner for dynamic graph creation
  - _Requirements: 3.1, 3.2, 3.3, 4.2_

- [x]* 4.1 Write property test for linear execution fidelity
  - **Property 3: Linear Execution Fidelity**
  - **Validates: Requirements 3.1**

- [x]* 4.2 Write property test for single agent execution
  - **Property 4: Single Agent Execution**
  - **Validates: Requirements 3.4**

- [x]* 4.3 Write property test for automatic progression
  - **Property 5: Automatic Progression**
  - **Validates: Requirements 3.2**

- [x]* 4.4 Write property test for workflow termination
  - **Property 6: Workflow Termination**
  - **Validates: Requirements 3.3**

- [x] 5. Implement HITL Approval System
  - Create HITLInterface for plan and result approval workflows
  - Implement WebSocket messaging for approval requests and responses
  - Add approval state management to prevent execution without approval
  - Support plan modification by HITL before approval
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 5.1 Write property test for HITL approval enforcement
  - **Property 2: HITL Approval Enforcement**
  - **Validates: Requirements 2.4**

- [x] 6. Create Linear Workflow Executor
  - Implement LinearExecutor class for managing workflow execution
  - Add progress tracking and WebSocket status updates
  - Implement timeout management (15-minute global, 3-minute per agent)
  - Add concurrent workflow limits (10 per user)
  - _Requirements: 3.1, 9.1, 9.4, 10.1, 10.2_

- [x]* 6.1 Write property test for timeout enforcement
  - **Property 10: Timeout Enforcement**
  - **Validates: Requirements 9.1**

- [x]* 6.2 Write property test for progress reporting
  - **Property 11: Progress Reporting**
  - **Validates: Requirements 10.2**

- [x] 7. Implement Error Handling and Recovery
  - Add graceful workflow termination on agent failures
  - Implement HITL notification system for errors
  - Add basic logging for agent failures and workflow events
  - Ensure system stability when individual workflows fail
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x]* 7.1 Write property test for error termination
  - **Property 9: Error Termination**
  - **Validates: Requirements 8.1**

- [x] 8. Update Agent Implementations
  - Remove next_agent routing logic from all agent nodes
  - Update agents to work with simplified AgentState
  - Ensure agents preserve collected_data for subsequent agents
  - Maintain existing WebSocket messaging functionality
  - _Requirements: 4.3, 7.2_

- [x]* 8.1 Write property test for routing logic elimination
  - **Property 7: Routing Logic Elimination**
  - **Validates: Requirements 4.2**

- [x] 9. Create New Graph Factory
  - Replace get_agent_graph() with create_linear_graph(sequence)
  - Support multiple graph types based on agent sequences
  - Cache compiled graphs for performance
  - Integrate with AI Planner for dynamic graph creation
  - _Requirements: 1.3, 4.2, 6.1_

- [x] 10. Integration Testing and Validation
  - Test complete workflow from task submission to result approval
  - Verify AI-generated sequences work with linear execution
  - Test HITL approval workflows with WebSocket communication
  - Validate error handling and timeout scenarios
  - _Requirements: All requirements integration_

- [x]* 10.1 Write integration tests for end-to-end workflows
  - Test task submission → AI planning → HITL approval → execution → result approval
  - Test error scenarios and recovery mechanisms
  - Test concurrent workflow execution limits

- [x] 11. Update API Endpoints
  - Modify process_request endpoint to use AI Planner
  - Update WebSocket handlers for HITL approval workflows
  - Ensure backward compatibility with existing frontend
  - Add new endpoints for plan modification if needed
  - _Requirements: 1.4, 2.1, 2.2_

- [x] 12. Performance Optimization and Cleanup
  - Remove unused routing code and state fields
  - Optimize graph compilation and caching
  - Add basic performance monitoring and logging
  - Clean up deprecated functions and imports
  - _Requirements: 9.1, 9.2, 9.3, 10.1_

- [x] 13. Final Testing and Documentation
  - Run comprehensive test suite with all property tests
  - Update API documentation for new workflow patterns
  - Create migration guide for transitioning from old system
  - Verify all infinite loop issues are resolved
  - _Requirements: All requirements validation_

- [x] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.