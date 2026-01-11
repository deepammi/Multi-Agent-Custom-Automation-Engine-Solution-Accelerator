# LangGraph Orchestrator Simplification Design

## Overview

This design document outlines the transformation of the current complex conditional routing system to a simplified linear orchestrator using LangGraph's built-in patterns. The key innovation is replacing hardcoded workflow logic with an AI-driven Planner that intelligently generates optimal agent sequences for any given task.

The system eliminates infinite loops by removing all conditional routing and implementing strict linear execution with Human-in-the-Loop (HITL) approval at critical decision points.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Task Input    │───▶│   AI Planner     │───▶│  HITL Approval  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │  GenAI Analysis  │    │ Sequence Review │
                    └──────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Final Results   │◀───│ Linear Execution │◀───│ Approved Plan   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│ HITL Approval   │    │ Agent Sequence   │
└─────────────────┘    └──────────────────┘
```

### Component Architecture

1. **AI Planner**: Enhanced planner with embedded GenAI agent for sequence generation
2. **Linear Executor**: LangGraph workflow with static agent connections
3. **HITL Interface**: WebSocket-based approval system for plan and result review
4. **Agent Nodes**: Existing agent implementations (unchanged)
5. **State Manager**: Simplified state management without routing fields

## Components and Interfaces

### AI Planner Component

```python
class AIPlanner:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.available_agents = ["gmail", "invoice", "salesforce", "zoho", "audit", "closing"]
    
    async def analyze_task(self, task: str) -> TaskAnalysis:
        """Use GenAI to analyze task and suggest agent sequence."""
        
    async def generate_sequence(self, analysis: TaskAnalysis) -> AgentSequence:
        """Generate optimal agent sequence with reasoning."""
        
    def create_linear_graph(self, sequence: AgentSequence) -> StateGraph:
        """Create static LangGraph with linear connections."""
```

### Linear Executor Interface

```python
class LinearExecutor:
    def __init__(self, graph: StateGraph):
        self.graph = graph
        self.checkpointer = MemorySaver()
    
    async def execute_workflow(self, state: AgentState) -> ExecutionResult:
        """Execute agents in predetermined linear sequence."""
        
    async def handle_agent_failure(self, agent: str, error: Exception) -> None:
        """Handle agent failures gracefully."""
```

### HITL Interface

```python
class HITLInterface:
    async def request_plan_approval(self, sequence: AgentSequence) -> ApprovalResult:
        """Request HITL approval for agent sequence."""
        
    async def request_result_approval(self, results: Dict[str, Any]) -> ApprovalResult:
        """Request HITL approval for final results."""
        
    async def send_progress_update(self, step: int, total: int, agent: str) -> None:
        """Send real-time progress updates."""
```

## Data Models

### AgentSequence Model

```python
@dataclass
class AgentSequence:
    agents: List[str]
    reasoning: Dict[str, str]  # agent -> reason for inclusion
    estimated_duration: int   # seconds
    complexity_score: float   # 0.0 to 1.0
    
    def to_linear_graph(self) -> StateGraph:
        """Convert sequence to LangGraph with linear connections."""
```

### TaskAnalysis Model

```python
@dataclass
class TaskAnalysis:
    complexity: Literal["simple", "medium", "complex"]
    required_systems: List[str]  # ["email", "erp", "crm", etc.]
    business_context: str
    data_sources_needed: List[str]
    estimated_agents: List[str]
    confidence_score: float
```

### Simplified AgentState

```python
class AgentState(TypedDict, total=False):
    # Core identification
    plan_id: str
    session_id: str
    task_description: str
    
    # Linear execution tracking
    agent_sequence: List[str]
    current_step: int
    total_steps: int
    
    # Data collection
    collected_data: Dict[str, Any]
    execution_results: List[Dict[str, Any]]
    
    # HITL state
    plan_approved: Optional[bool]
    result_approved: Optional[bool]
    hitl_feedback: Optional[str]
    
    # Execution metadata
    start_time: datetime
    current_agent: str
    final_result: Optional[str]
    
    # WebSocket manager
    websocket_manager: Optional[Any]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: AI Sequence Generation
*For any* valid task input, the GenAI agent should produce a valid agent sequence with reasoning for each included agent
**Validates: Requirements 1.2, 5.2**

### Property 2: HITL Approval Enforcement
*For any* workflow execution, no agents should execute without explicit HITL approval of the generated plan
**Validates: Requirements 2.4**

### Property 3: Linear Execution Fidelity
*For any* approved agent sequence, the system should execute agents in the exact order specified without deviation
**Validates: Requirements 3.1**

### Property 4: Single Agent Execution
*For any* workflow instance, each agent in the sequence should execute exactly once
**Validates: Requirements 3.4**

### Property 5: Automatic Progression
*For any* agent completion, the system should automatically proceed to the next agent in sequence without manual intervention
**Validates: Requirements 3.2**

### Property 6: Workflow Termination
*For any* workflow where the final agent completes, the system should automatically terminate the workflow
**Validates: Requirements 3.3**

### Property 7: Routing Logic Elimination
*For any* agent connection in the graph, it should use LangGraph's add_edge() method and not conditional routing
**Validates: Requirements 4.2**

### Property 8: Data Preservation
*For any* agent execution, the collected_data should persist and be available to subsequent agents
**Validates: Requirements 7.2**

### Property 9: Error Termination
*For any* agent failure, the workflow should terminate gracefully and notify HITL
**Validates: Requirements 8.1**

### Property 10: Timeout Enforcement
*For any* workflow execution, it should terminate within 15 minutes regardless of state
**Validates: Requirements 9.1**

### Property 11: Progress Reporting
*For any* agent transition, the system should send appropriate WebSocket status updates
**Validates: Requirements 10.2**

## Error Handling

### Agent Failure Handling

1. **Immediate Termination**: When any agent fails, terminate the entire workflow
2. **HITL Notification**: Send failure details to HITL via WebSocket
3. **State Preservation**: Maintain execution state for debugging
4. **Resource Cleanup**: Release all allocated resources

### Timeout Management

1. **Global Timeout**: 15-minute maximum execution time per workflow
2. **Agent Timeout**: 3-minute maximum per individual agent
3. **Graceful Shutdown**: Allow current agent to complete before timeout
4. **Status Reporting**: Notify HITL of timeout conditions

### Approval Rejection Handling

1. **Plan Rejection**: Terminate workflow without executing any agents
2. **Result Rejection**: Mark workflow as requiring revision
3. **Modification Support**: Allow HITL to modify sequences before approval
4. **Audit Trail**: Log all approval decisions and modifications

## Testing Strategy

### Unit Testing Approach

- **AI Planner Tests**: Test sequence generation with various task types
- **Linear Executor Tests**: Test workflow execution with mock agents
- **HITL Interface Tests**: Test approval workflows and WebSocket messaging
- **State Management Tests**: Test state transitions and data preservation
- **Error Handling Tests**: Test failure scenarios and recovery

### Property-Based Testing Approach

The system will use **Hypothesis** for Python property-based testing with a minimum of 100 iterations per property test.

Each property-based test will be tagged with comments referencing the design document:
- Format: `# Feature: langgraph-orchestrator-simplification, Property X: [property description]`
- Each correctness property will be implemented by a single property-based test
- Tests will generate random task inputs, agent sequences, and execution scenarios

### Integration Testing

- **End-to-End Workflow Tests**: Complete task submission to result approval
- **Multi-Agent Coordination Tests**: Verify data flow between agents
- **HITL Integration Tests**: Test approval workflows with simulated user input
- **WebSocket Communication Tests**: Verify real-time updates and messaging
- **Error Recovery Tests**: Test system behavior under various failure conditions

### Test Data Generation

- **Task Generators**: Generate diverse business task descriptions
- **Sequence Generators**: Create valid and invalid agent sequences
- **State Generators**: Generate various workflow states for testing
- **Failure Generators**: Simulate different types of agent failures

## Implementation Notes

### LangGraph Integration

1. **Static Graph Creation**: Create graphs at startup, not runtime
2. **Linear Connections**: Use only add_edge() for agent connections
3. **No Conditional Routing**: Eliminate all conditional edge logic
4. **Built-in Checkpointing**: Use LangGraph's MemorySaver for state persistence

### AI Integration

1. **LLM Service Integration**: Use existing LLMService for GenAI calls
2. **Prompt Engineering**: Design prompts for optimal sequence generation
3. **Fallback Logic**: Provide default sequences when AI is unavailable
4. **Response Validation**: Validate AI-generated sequences before use

### Performance Considerations

1. **Graph Caching**: Cache compiled graphs for reuse
2. **Concurrent Execution**: Support multiple workflows simultaneously
3. **Resource Limits**: Enforce per-user workflow limits
4. **Memory Management**: Clean up completed workflow state

### Migration Strategy

1. **Backward Compatibility**: Maintain existing agent interfaces
2. **Gradual Rollout**: Support both old and new routing during transition
3. **Data Migration**: Convert existing state to new format
4. **Testing Coverage**: Ensure all existing functionality is preserved