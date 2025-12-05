# Design Document

## Overview

This design addresses a critical race condition in the invoice extraction workflow where the Invoice Agent returns with an extraction approval request before sending its agent message via WebSocket. This causes the frontend to timeout waiting for the expected agent message, resulting in a poor user experience with a 30-second spinner timeout.

The fix ensures that the Invoice Agent sends its processing message via WebSocket before returning control to the agent service, which then sends the extraction approval request. This maintains the correct message chronology expected by the frontend.

## Architecture

### Current Flow (Broken)
```
1. User approves plan
2. AgentService.resume_after_approval() calls invoice_agent_node()
3. invoice_agent_node() performs extraction
4. invoice_agent_node() returns with requires_extraction_approval=True
5. AgentService sends extraction_approval_request via WebSocket
6. Frontend receives extraction_approval_request (but never got agent message)
7. Frontend times out after 30 seconds
```

### Fixed Flow
```
1. User approves plan
2. AgentService.resume_after_approval() calls invoice_agent_node()
3. invoice_agent_node() sends agent_message via WebSocket ("Processing invoice extraction...")
4. invoice_agent_node() performs extraction
5. invoice_agent_node() sends agent_message via WebSocket ("Extraction complete")
6. invoice_agent_node() returns with requires_extraction_approval=True
7. AgentService sends extraction_approval_request via WebSocket
8. Frontend receives messages in correct order and displays extraction approval dialog
```

## Components and Interfaces

### Modified Components

#### 1. invoice_agent_node (backend/app/agents/nodes.py)

**Current Signature:**
```python
async def invoice_agent_node(state: AgentState) -> Dict[str, Any]
```

**Changes Required:**
- Add WebSocket message sending before extraction
- Add WebSocket message sending after extraction completes
- Ensure messages are sent before returning with extraction approval flag

**New Behavior:**
```python
async def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    plan_id = state.get("plan_id")
    task = state.get("task_description", "")
    websocket_manager = state.get("websocket_manager")
    
    # Send initial processing message
    if websocket_manager:
        await websocket_manager.send_message(plan_id, {
            "type": "agent_message",
            "data": {
                "agent_name": "Invoice",
                "content": "📊 Processing invoice extraction...",
                "status": "in_progress",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    # Perform extraction
    extraction_result = await LangExtractService.extract_invoice_data(...)
    
    # Send completion message
    if websocket_manager:
        await websocket_manager.send_message(plan_id, {
            "type": "agent_message",
            "data": {
                "agent_name": "Invoice",
                "content": "✅ Invoice extraction complete. Awaiting approval...",
                "status": "in_progress",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    # Return with extraction approval flag
    return {
        "messages": [structured_response],
        "current_agent": "Invoice",
        "final_result": structured_response,
        "extraction_result": extraction_result,
        "requires_extraction_approval": True
    }
```

#### 2. AgentService.resume_after_approval (backend/app/services/agent_service.py)

**Current Behavior:**
- Calls invoice_agent_node()
- Immediately checks for requires_extraction_approval
- Sends extraction approval request

**Changes Required:**
- No changes needed - the invoice_agent_node will handle message sending
- The existing flow will work correctly once invoice_agent_node sends messages first

**Verification:**
- Add logging to confirm messages are sent in correct order
- Log timestamps of each message for debugging

## Data Models

No new data models required. Existing models are sufficient:

### AgentState (existing)
```python
class AgentState(TypedDict):
    messages: List[str]
    plan_id: str
    session_id: str
    task_description: str
    current_agent: str
    next_agent: Optional[str]
    final_result: str
    websocket_manager: Any
    extraction_result: Optional[Any]
    requires_extraction_approval: bool
```

### WebSocket Message Format (existing)
```python
{
    "type": "agent_message",
    "data": {
        "agent_name": str,
        "content": str,
        "status": str,  # "in_progress", "completed", "error"
        "timestamp": str  # ISO format with Z suffix
    }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Message Ordering Invariant

*For any* invoice extraction workflow, the agent message SHALL be sent via WebSocket before the extraction approval request is sent.

**Validates: Requirements 1.1, 1.2**

### Property 2: Message Delivery Completeness

*For any* invoice extraction that requires approval, the system SHALL send exactly two agent messages (processing start and completion) before sending the extraction approval request.

**Validates: Requirements 1.3, 1.5**

### Property 3: WebSocket Manager Availability

*For any* invoice agent execution, if the websocket_manager is available in state, then agent messages SHALL be sent via WebSocket.

**Validates: Requirements 1.4**

### Property 4: Timestamp Monotonicity

*For any* sequence of messages sent during invoice extraction, the timestamps SHALL be monotonically increasing (later messages have later timestamps).

**Validates: Requirements 1.3**

## Error Handling

### WebSocket Unavailable
- **Scenario**: websocket_manager is None or not available in state
- **Handling**: Log warning and continue without sending messages (fallback behavior)
- **Impact**: Frontend may not receive real-time updates but extraction will still complete

### Message Send Failure
- **Scenario**: WebSocket send_message() raises exception
- **Handling**: Log error but continue with extraction process
- **Impact**: Frontend may miss some messages but extraction approval will still be sent

### Extraction Failure
- **Scenario**: LangExtractService.extract_invoice_data() raises exception
- **Handling**: Send error message via WebSocket, return with error status
- **Impact**: Frontend displays error message, no extraction approval requested

## Testing Strategy

### Unit Tests

#### Test 1: Message Sending Order
```python
async def test_invoice_agent_sends_messages_before_approval():
    """Verify agent messages are sent before returning with approval flag."""
    mock_websocket = Mock()
    state = {
        "plan_id": "test-plan",
        "task_description": "Invoice: ...",
        "websocket_manager": mock_websocket
    }
    
    result = await invoice_agent_node(state)
    
    # Verify messages were sent
    assert mock_websocket.send_message.call_count >= 2
    
    # Verify first message is processing
    first_call = mock_websocket.send_message.call_args_list[0]
    assert "Processing invoice extraction" in first_call[0][1]["data"]["content"]
    
    # Verify second message is completion
    second_call = mock_websocket.send_message.call_args_list[1]
    assert "extraction complete" in second_call[0][1]["data"]["content"].lower()
    
    # Verify result has approval flag
    assert result["requires_extraction_approval"] is True
```

#### Test 2: Message Content Validation
```python
async def test_invoice_agent_message_format():
    """Verify agent messages have correct format."""
    mock_websocket = Mock()
    state = {
        "plan_id": "test-plan",
        "task_description": "Invoice: ...",
        "websocket_manager": mock_websocket
    }
    
    await invoice_agent_node(state)
    
    for call in mock_websocket.send_message.call_args_list:
        message = call[0][1]
        assert message["type"] == "agent_message"
        assert "agent_name" in message["data"]
        assert message["data"]["agent_name"] == "Invoice"
        assert "content" in message["data"]
        assert "status" in message["data"]
        assert "timestamp" in message["data"]
        assert message["data"]["timestamp"].endswith("Z")
```

#### Test 3: Fallback Without WebSocket
```python
async def test_invoice_agent_works_without_websocket():
    """Verify agent works when websocket_manager is not available."""
    state = {
        "plan_id": "test-plan",
        "task_description": "Invoice: ...",
        "websocket_manager": None
    }
    
    # Should not raise exception
    result = await invoice_agent_node(state)
    
    # Should still return valid result
    assert "messages" in result
    assert "current_agent" in result
```

### Integration Tests

#### Test 4: End-to-End Message Flow
```python
async def test_full_extraction_approval_flow():
    """Test complete flow from plan approval to extraction approval."""
    # 1. Create plan and approve
    plan_id = await create_test_plan()
    await approve_plan(plan_id)
    
    # 2. Collect WebSocket messages
    messages = []
    async def collect_messages(plan_id, message):
        messages.append(message)
    
    # 3. Execute flow
    await AgentService.resume_after_approval(plan_id, True)
    
    # 4. Verify message order
    assert len(messages) >= 3
    assert messages[0]["type"] == "agent_message"  # Processing
    assert messages[1]["type"] == "agent_message"  # Complete
    assert messages[2]["type"] == "extraction_approval_request"
    
    # 5. Verify timestamps are ordered
    timestamps = [msg["data"]["timestamp"] for msg in messages]
    assert timestamps == sorted(timestamps)
```

### Manual Testing

#### Test 5: Frontend Integration
1. Start backend server
2. Open frontend and submit invoice extraction task
3. Approve plan
4. Verify in browser console:
   - Agent message "Processing invoice extraction..." appears
   - Agent message "Extraction complete..." appears
   - Extraction approval dialog appears
   - No spinner timeout occurs

#### Test 6: Logging Verification
1. Enable DEBUG logging
2. Submit invoice extraction task
3. Verify logs show:
   - "Invoice Agent processing task for plan {plan_id}"
   - "📊 Sending agent message: Processing invoice extraction"
   - "📊 Sending agent message: Extraction complete"
   - "📊 Sending extraction approval request"
4. Verify timestamps in logs are sequential

## Implementation Notes

### Message Content Guidelines

**Processing Message:**
- Should indicate extraction is starting
- Should be brief and informative
- Example: "📊 Processing invoice extraction..."

**Completion Message:**
- Should indicate extraction is complete
- Should mention awaiting approval
- Example: "✅ Invoice extraction complete. Awaiting approval..."

### Logging Guidelines

Add structured logging at key points:
```python
logger.info(f"📊 [Invoice Agent] Sending processing message for plan {plan_id}")
logger.info(f"📊 [Invoice Agent] Starting extraction for plan {plan_id}")
logger.info(f"📊 [Invoice Agent] Extraction completed in {elapsed:.2f}s for plan {plan_id}")
logger.info(f"📊 [Invoice Agent] Sending completion message for plan {plan_id}")
```

### Timing Considerations

- Add small delay (0.1s) between messages to ensure proper ordering
- Use `await asyncio.sleep(0.1)` between WebSocket sends
- This prevents race conditions in message delivery

### Backward Compatibility

- Changes are backward compatible
- Non-extraction invoice tasks continue to work as before
- WebSocket manager availability is checked before sending messages
- Fallback behavior maintains existing functionality

## Performance Considerations

### Message Overhead
- Two additional WebSocket messages per extraction
- Negligible impact: ~10ms per message
- Total overhead: ~20ms per extraction

### Extraction Time
- No change to extraction time
- Messages sent asynchronously
- No blocking operations added

## Security Considerations

- No new security concerns introduced
- WebSocket messages use existing authentication
- No sensitive data exposed in new messages
- Extraction data still requires approval before storage

## Deployment Notes

### Rollout Strategy
1. Deploy backend changes first
2. Verify logging shows correct message order
3. Test with frontend
4. Monitor for any timeout issues

### Rollback Plan
- If issues occur, revert backend changes
- Frontend will continue to work with old behavior
- No database migrations required

### Monitoring
- Monitor WebSocket message delivery rates
- Track extraction approval timeout rates
- Alert if timeout rate increases above baseline
