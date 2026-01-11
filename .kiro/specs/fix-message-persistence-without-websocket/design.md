# Design Document: Fix Message Persistence Without WebSocket

## Overview

This design addresses the message persistence issue where agent messages are not saved to the database when no WebSocket connection is active. The solution implements direct database persistence during agent execution while maintaining backward compatibility with existing WebSocket functionality.

## Architecture

The current architecture has a dependency where message persistence only occurs through the WebSocket service. We need to decouple message persistence from WebSocket connections by implementing direct database saving during agent execution.

### Current Flow (Problematic)
```
Agent Execution → WebSocket Manager → Database Persistence
                ↓ (if no WebSocket)
              Messages Lost
```

### New Flow (Fixed)
```
Agent Execution → Direct Database Save + WebSocket Manager → Database Persistence
                ↓                      ↓ (if WebSocket active)
            Always Saved           Real-time Broadcasting
```

## Components and Interfaces

### 1. Message Persistence Service

**Purpose**: Centralized service for saving agent messages to database

**Interface**:
```python
class MessagePersistenceService:
    async def save_agent_message(
        self, 
        plan_id: str, 
        agent_name: str, 
        content: str, 
        metadata: Dict[str, Any] = None
    ) -> bool
    
    async def save_messages_batch(
        self, 
        messages: List[AgentMessage]
    ) -> List[bool]
    
    async def get_messages_for_plan(
        self, 
        plan_id: str
    ) -> List[AgentMessage]
```

### 2. Enhanced Agent Nodes

**Purpose**: Agent nodes that save messages directly during execution

**Key Changes**:
- Add direct database persistence calls in agent nodes
- Maintain existing WebSocket broadcasting when available
- Handle persistence failures gracefully

### 3. Dual Persistence Manager

**Purpose**: Coordinates both database and WebSocket message persistence

**Interface**:
```python
class DualPersistenceManager:
    async def persist_message(
        self,
        message: AgentMessage,
        websocket_manager: Optional[WebSocketManager] = None
    ) -> PersistenceResult
```

## Data Models

### Enhanced AgentMessage Model

```python
@dataclass
class AgentMessage:
    plan_id: str
    agent_name: str
    agent_type: str
    content: str
    timestamp: datetime
    message_id: str  # New: unique identifier
    persistence_status: str  # New: tracking persistence state
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # New fields for tracking
    saved_to_db: bool = False
    sent_via_websocket: bool = False
    retry_count: int = 0
```

### PersistenceResult Model

```python
@dataclass
class PersistenceResult:
    database_saved: bool
    websocket_sent: bool
    errors: List[str] = field(default_factory=list)
    retry_needed: bool = False
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

<function_calls>
<invoke name="prework">
<parameter name="featureName">fix-message-persistence-without-websocket

### Property Reflection

After analyzing all acceptance criteria, I identified several areas where properties can be consolidated:

**Redundancy Analysis:**
- Properties 1.1, 2.1, and 3.1 all test message saving but from different angles - these can be combined into a comprehensive message persistence property
- Properties 1.4, 3.4, and 4.5 all test consistency across execution modes - these can be consolidated
- Properties 2.4 and 4.4 both test message format consistency - these can be combined
- Properties 4.1, 4.2, and 4.3 all test WebSocket backward compatibility - these can be consolidated

**Core Properties (Primary Focus):**

Property 1: Universal Message Persistence
*For any* agent execution that generates messages, all messages should be saved to the database regardless of WebSocket connection status
**Validates: Requirements 1.1, 1.2, 2.1, 3.1**

Property 2: Immediate Message Persistence
*For any* message generated during agent execution, the message should be available in the database immediately after generation
**Validates: Requirements 1.3**

Property 3: Execution Mode Consistency
*For any* task executed in both WebSocket and non-WebSocket modes, the database should contain identical message sets
**Validates: Requirements 1.4, 3.4, 4.5**

Property 4: Message Chronological Ordering
*For any* sequence of messages generated during execution, the database storage should maintain the same chronological order
**Validates: Requirements 1.5**

Property 5: Dual Persistence Operation
*For any* execution with active WebSocket connections, messages should be both saved to database and broadcast via WebSocket
**Validates: Requirements 2.2**

Property 6: Message Format Consistency
*For any* message, the structure should be identical whether retrieved from database or received via WebSocket
**Validates: Requirements 2.4, 4.4**

Property 7: Complete Message Retrieval
*For any* plan with saved messages, the GET /api/v3/plan endpoint should return all messages regardless of persistence method
**Validates: Requirements 3.3**

Property 8: WebSocket Backward Compatibility
*For any* WebSocket-enabled execution, the real-time message broadcasting should work identically to the previous implementation
**Validates: Requirements 4.1, 4.2, 4.3**

**Secondary Properties (Implementation Details):**

These properties address important system qualities but are secondary to the core message persistence functionality:

- Concurrent Message Safety: Database operations should handle concurrent access safely (Requirements 2.3)
- Execution Resilience: Agent execution should continue even if database saving fails (Requirements 2.5, 5.1, 5.4)  
- Error Recovery and Retry: System should retry failed saves and log errors (Requirements 5.2, 5.3)
- Persistence Monitoring: Success/failure rates should be tracked (Requirements 5.5)

## Error Handling

### Database Connection Failures
- Implement connection pooling with automatic retry
- Use circuit breaker pattern for database operations
- Graceful degradation: continue execution even if persistence fails
- Queue messages for retry when database becomes available

### Concurrent Access Handling
- Use database transactions for atomic message saving
- Implement optimistic locking for message updates
- Handle duplicate message prevention with unique constraints

### WebSocket Integration Errors
- Separate error handling for database vs WebSocket failures
- Continue database persistence even if WebSocket broadcasting fails
- Log WebSocket errors without affecting database operations

## Testing Strategy

### Dual Testing Approach
- **Unit tests**: Test specific message persistence scenarios, error conditions, and edge cases
- **Property tests**: Verify universal properties across all execution modes and conditions
- Both are complementary and necessary for comprehensive coverage

### Property-Based Testing Configuration
- Use pytest with Hypothesis for property-based testing
- Minimum 100 iterations per property test
- Each property test references its design document property
- Tag format: **Feature: fix-message-persistence-without-websocket, Property {number}: {property_text}**

### Unit Testing Focus
- Database connection handling and retry logic
- Message format validation and consistency
- Error scenarios and graceful degradation
- WebSocket integration edge cases

### Integration Testing
- End-to-end message persistence across execution modes
- REST API message retrieval validation
- Concurrent execution message safety
- Database and WebSocket coordination testing