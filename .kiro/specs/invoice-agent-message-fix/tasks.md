# Implementation Plan

- [x] 1. Update invoice_agent_node to send WebSocket messages
  - Modify `invoice_agent_node()` in `backend/app/agents/nodes.py`
  - Add WebSocket message sending before extraction starts
  - Add WebSocket message sending after extraction completes
  - Ensure messages are sent before returning with extraction approval flag
  - Add proper error handling for WebSocket send failures
  - _Requirements: 1.1, 1.2, 1.4_

- [ ] 2. Add structured logging for message flow
  - Add log statements before sending processing message
  - Add log statements after sending completion message
  - Add log statements with timestamps for debugging
  - Include plan_id in all log messages
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 3. Add timing delay between messages
  - Add small delay (0.1s) between WebSocket messages
  - Use `asyncio.sleep()` to prevent race conditions
  - Ensure messages arrive in correct order at frontend
  - _Requirements: 1.3_

- [ ] 4. Test the fix with manual verification
  - Start backend server with updated code
  - Submit invoice extraction task via frontend
  - Approve plan and verify messages appear in correct order
  - Verify no spinner timeout occurs
  - Check browser console for message order
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [ ] 5. Verify logging output
  - Enable DEBUG logging in backend
  - Submit test invoice extraction
  - Verify log messages show correct sequence
  - Verify timestamps are sequential
  - _Requirements: 2.1, 2.2, 2.3, 2.4_
