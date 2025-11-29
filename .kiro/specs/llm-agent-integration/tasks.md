# Implementation Plan

- [x] 1. Create LLM Service Module
  - Create `app/services/llm_service.py` with LLMService class
  - Implement `get_llm_instance()` method to initialize provider based on env vars
  - Implement `is_mock_mode()` method to check USE_MOCK_LLM flag
  - Implement `get_mock_response()` method for dummy responses
  - Add configuration reading from environment variables
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 8.1, 8.2_

- [ ]* 1.1 Write property test for LLM provider configuration
  - **Property 2: LLM Provider Configuration**
  - **Validates: Requirements 2.1**

- [ ]* 1.2 Write property test for mock mode behavior
  - **Property 4: Mock Mode Behavior**
  - **Validates: Requirements 8.2, 8.3**

- [x] 2. Create Prompt Templates Module
  - Create `app/agents/prompts.py` file
  - Define `INVOICE_AGENT_PROMPT` template with role, task, and instructions
  - Implement `build_invoice_prompt()` function to format template with task description
  - Add validation for prompt structure completeness
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 2.1 Write property test for prompt structure completeness
  - **Property 1: Prompt Structure Completeness**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

- [x] 3. Implement LLM Streaming Support
  - Add `call_llm_streaming()` method to LLMService
  - Implement WebSocket message sending for stream start, tokens, and stream end
  - Add token collection to build complete response
  - Implement timeout configuration (60 seconds)
  - Add error handling for streaming interruptions
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.1_

- [ ]* 3.1 Write property test for streaming message sequence
  - **Property 3: Streaming Message Sequence**
  - **Validates: Requirements 3.2, 3.3, 3.4**

- [ ]* 3.2 Write property test for timeout configuration
  - **Property 5: Timeout Configuration**
  - **Validates: Requirements 5.1**

- [x] 4. Update Invoice Agent Node
  - Modify `invoice_agent_node()` in `app/agents/nodes.py` to be async
  - Add mock mode check using `LLMService.is_mock_mode()`
  - Add prompt building using `build_invoice_prompt()`
  - Add LLM call using `LLMService.call_llm_streaming()`
  - Update return format to include final_result
  - Pass websocket_manager from state to LLM service
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 8.2, 8.3_

- [ ]* 4.1 Write property test for response flow integrity
  - **Property 10: Response Flow Integrity**
  - **Validates: Requirements 1.4**

- [x] 5. Implement Error Handling and Retry Logic
  - Add timeout error handling in LLMService
  - Implement retry logic for rate limit errors (max 2 retries with exponential backoff)
  - Add authentication error handling
  - Add network error handling
  - Create user-friendly error messages for each error type
  - _Requirements: 1.5, 5.2, 5.3, 5.4, 5.5_

- [ ]* 5.1 Write property test for retry logic
  - **Property 6: Retry Logic for Rate Limits**
  - **Validates: Requirements 5.3**

- [x] 6. Add Logging for LLM Interactions
  - Add logging for LLM API calls (prompt truncated if too long)
  - Add logging for LLM responses (length and completion time)
  - Add logging for LLM errors (type, message, context)
  - Include plan_id and agent name in all log entries
  - Add logging for mock mode usage
  - Ensure API keys are never logged
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 8.5_

- [ ]* 6.1 Write property test for logging completeness
  - **Property 7: Logging Completeness**
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.5**

- [ ]* 6.2 Write property test for API key security in logs
  - **Property 8: API Key Security in Logs**
  - **Validates: Requirements 6.4**

- [ ]* 6.3 Write property test for mock mode logging transparency
  - **Property 11: Mock Mode Logging Transparency**
  - **Validates: Requirements 8.5**

- [x] 7. Update Environment Configuration
  - Add LLM configuration variables to `.env.example`
  - Document all environment variables in README or docs
  - Add validation for required environment variables at startup
  - Set sensible defaults for optional variables
  - _Requirements: 2.1, 2.5, 8.1, 8.4_

- [x] 8. Update AgentState Type Definition
  - Add `websocket_manager` field to AgentState in `app/agents/state.py`
  - Add optional `llm_provider` field for provider override
  - Add optional `llm_temperature` field for temperature override
  - Update type hints and documentation
  - _Requirements: 3.1, 3.2_

- [x] 9. Update Agent Service to Pass WebSocket Manager
  - Modify `app/services/agent_service.py` to include websocket_manager in initial state
  - Ensure websocket_manager is available to all agent nodes
  - Test that WebSocket messages are delivered correctly
  - _Requirements: 3.2, 3.3, 3.4_

- [x] 10. Add Dependencies to Requirements
  - Add `langchain-anthropic` to requirements.txt if not present
  - Add `hypothesis` to requirements-dev.txt for property testing
  - Verify all LangChain dependencies are at correct versions
  - Update requirements documentation
  - _Requirements: 2.3, Testing Strategy_

- [ ]* 11. Write integration tests for end-to-end flow
  - Test complete flow from task submission to LLM response
  - Test WebSocket streaming delivery
  - Test database persistence of results
  - Test mock mode vs real mode switching
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.1, 3.2, 3.3, 3.4_

- [ ]* 12. Write integration tests for error scenarios
  - Test timeout handling with slow mock LLM
  - Test rate limit handling with mock 429 responses
  - Test auth error handling with invalid keys
  - Test network error handling with unreachable endpoints
  - _Requirements: 1.5, 5.2, 5.3, 5.4, 5.5_

- [x] 13. Create Documentation
  - Document LLM service usage in code comments
  - Create example .env file with all LLM variables
  - Document how to switch between providers
  - Document how to use mock mode for testing
  - Add troubleshooting guide for common LLM errors
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 13.1 Write property test for provider encapsulation
  - **Property 9: Provider Encapsulation**
  - **Validates: Requirements 7.5**

- [x] 14. Manual Testing and Validation
  - Test invoice task in mock mode, verify dummy response
  - Test invoice task with OpenAI, verify AI response
  - Test invoice task with Anthropic, verify AI response
  - Test invoice task with Ollama, verify AI response
  - Observe WebSocket streaming in browser DevTools
  - Verify logs contain proper information without API keys
  - Test error scenarios (timeout, rate limit, invalid key)
  - Verify other agents (Closing, Audit) still work
  - _Requirements: All_

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
