# Design Document: Multi-Agent Loop with Human-in-the-Loop

## Overview

This design implements a multi-agent workflow with human-in-the-loop approval and revision capability. The system allows specialized agents to process tasks, then routes results to a HITL agent that requests human approval. If the human provides feedback, the task loops directly back to the specialized agent for re-processing with the revision context.

## Architecture

```
User Task
    ↓
Planner Agent (analyzes & routes)
    ↓
Specialized Agent (Invoice/Closing/Audit)
    ↓
HITL Agent (requests approval/revision)
    ↓
User Clarification
    ├→ Approve → Complete
    └→ Revise → Loop back to Specialized Agent (directly, with context)
```

## Components and Interfaces

### Backend Components

1. **HITL Agent Node** (`hitl_agent_node`)
   - Receives specialized agent result
   - Formats clarification request
   - Returns structured message for user

2. **Context Manager**
   - Stores original task description
   - Maintains execution history
   - Passes context through loops

3. **Loop Handler**
   - Detects revision responses
   - Routes back to Planner with context
   - Tracks iteration count

4. **Clarification Handler** (in agent_service.py)
   - Processes user clarification responses
   - Determines if approval or revision
   - Initiates loop or completion

### Frontend Components

1. **Clarification UI**
   - Displays agent result
   - Text input for user response
   - "Retry" button for submission
   - "OK" button for approval

2. **Clarification Message Handler**
   - Listens for `user_clarification_request` messages
   - Displays clarification UI
   - Captures user input

3. **Retry Logic**
   - Sends user response back to backend
   - Clears UI after submission
   - Waits for next agent message

## Data Models

### Clarification Request Message
```python
{
    "type": "user_clarification_request",
    "data": {
        "request_id": "uuid",
        "plan_id": "uuid",
        "agent_result": "string",  # Result from specialized agent
        "question": "Please approve or provide revision",
        "timestamp": "ISO8601"
    }
}
```

### Clarification Response (from frontend)
```python
{
    "request_id": "uuid",
    "plan_id": "uuid",
    "answer": "string",  # "OK" for approval or revision text
    "is_approval": "boolean"
}
```

### Execution Context
```python
{
    "original_task": "string",
    "execution_history": [
        {
            "iteration": 1,
            "agent": "Planner",
            "result": "string"
        },
        {
            "iteration": 1,
            "agent": "Invoice",
            "result": "string"
        },
        {
            "iteration": 1,
            "agent": "HITL",
            "user_feedback": "string"
        }
    ]
}
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: HITL Routing
*For any* specialized agent result, when the HITL agent is enabled, the system SHALL send a clarification request to the user before completing the task.
**Validates: Requirements 1.1, 1.2**

### Property 2: Context Preservation
*For any* task that loops back to the Planner, the original task description SHALL be preserved and accessible in the execution history.
**Validates: Requirements 2.1, 2.2**

### Property 3: Approval Completion
*For any* clarification request, when the user responds with approval, the system SHALL mark the task as completed without looping back.
**Validates: Requirements 1.3**

### Property 4: Revision Loop
*For any* clarification request, when the user provides a revision, the system SHALL send the revised task directly back to the specialized agent with full context retained.
**Validates: Requirements 1.4, 2.3**

### Property 5: Optional HITL
*For any* task configured to skip HITL, the system SHALL complete after the specialized agent finishes without sending a clarification request.
**Validates: Requirements 3.1, 3.2**

### Property 6: Unlimited Iterations
*For any* number of revisions provided by the user, the system SHALL process each revision and loop back to the specialized agent without limit.
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

## Error Handling

- If clarification request fails to send: Log error and complete task with agent result
- If user response is malformed: Treat as approval (default safe behavior)
- If Planner fails on revised task: Send error message and allow user to revise again
- If HITL agent fails: Skip HITL and complete with agent result

## Testing Strategy

### Unit Tests
- Test HITL agent node with various agent results
- Test context preservation across loops
- Test clarification message formatting
- Test approval vs revision detection

### Property-Based Tests
- Property 1: HITL routing for all agent types
- Property 2: Context preservation across multiple loops
- Property 3: Approval completion without looping
- Property 4: Revision loop with context
- Property 5: Optional HITL behavior
- Property 6: Unlimited iteration handling

### Integration Tests
- End-to-end flow: Task → Planner → Specialized Agent → HITL → Approval → Complete
- End-to-end flow: Task → Planner → Specialized Agent → HITL → Revision → Specialized Agent (direct) → HITL → Complete
- Multiple revision loops with direct specialized agent routing
- Mixed approval and revision scenarios

### Testing Framework
- Backend: pytest with property-based testing using Hypothesis
- Frontend: Vitest with React Testing Library
- Minimum 100 iterations per property test
