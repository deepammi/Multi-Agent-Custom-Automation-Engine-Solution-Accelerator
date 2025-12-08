# LangGraph Refactoring Plan

## Executive Summary

This document outlines a comprehensive plan to refactor the backend from using if/else statements in `agent_service.py` to using proper LangGraph graphs with stateful execution, memory persistence, and conditional routing.

## Current Architecture Analysis

### Problems with Current Implementation

1. **Manual State Management**: `agent_service.py` manually manages execution state using dictionaries (`_pending_executions`, `_execution_contexts`)
2. **If/Else Agent Routing**: Lines 244-253 use if/else to route to agents instead of graph edges
3. **No Persistence**: State is stored in memory only - lost on server restart
4. **Complex Flow Control**: Manual handling of approval, clarification, and revision loops
5. **Tight Coupling**: Service layer tightly coupled to specific agent implementations
6. **Limited Observability**: Hard to visualize execution flow and debug issues

### Current Flow

```
User Request → AgentService.execute_task()
    ↓
Planner Node (manual call)
    ↓
Store state in _pending_executions
    ↓
Send approval request
    ↓
Wait for approval (manual state check)
    ↓
AgentService.resume_after_approval()
    ↓
If/else routing to specialized agent
    ↓
Manual HITL handling
    ↓
Manual revision loop
```

## Proposed Architecture

### Goals

1. **True LangGraph Execution**: Use LangGraph's built-in execution engine
2. **Persistent State**: Use LangGraph checkpointers for state persistence
3. **Declarative Routing**: Define agent routing as graph edges, not if/else
4. **Human-in-the-Loop**: Use LangGraph's interrupt mechanism for approvals
5. **Memory Management**: Leverage LangGraph's memory for conversation history
6. **Tool Integration**: Connect agents to tools via LangGraph tool nodes
7. **Observability**: Enable LangGraph Studio visualization

### New Flow

```
User Request → LangGraph.invoke()
    ↓
Planner Node (graph node)
    ↓
Conditional Edge (supervisor_router)
    ↓
Specialized Agent Node (graph node)
    ↓
Interrupt for Approval (graph interrupt)
    ↓
Resume with approval (graph.invoke with state)
    ↓
HITL Node (graph node)
    ↓
Conditional Edge (approval vs revision)
    ↓
Loop back to agent OR Complete
```

## Implementation Plan

### Phase 1: Setup Infrastructure (Week 1)

#### 1.1 Add LangGraph Dependencies
```python
# requirements.txt additions
langgraph>=0.0.40
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0
```

#### 1.2 Configure Checkpointer
Create persistent state storage using MongoDB or SQLite:

```python
# backend/app/agents/checkpointer.py
from langgraph.checkpoint.mongodb import MongoDBSaver
from app.db.mongodb import MongoDB

def get_checkpointer():
    """Get MongoDB checkpointer for persistent state."""
    db = MongoDB.get_database()
    return MongoDBSaver(
        db=db,
        collection_name="langgraph_checkpoints"
    )
```

**Alternative**: Use SQLite for simpler setup:
```python
from langgraph.checkpoint.sqlite import SqliteSaver

def get_checkpointer():
    return SqliteSaver.from_conn_string("checkpoints.db")
```

#### 1.3 Update State Schema
Enhance `AgentState` to include all necessary fields:

```python
# backend/app/agents/state.py
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import add_messages

class AgentState(TypedDict):
    # Core fields
    messages: Annotated[Sequence[dict], add_messages]
    plan_id: str
    session_id: str
    task_description: str
    
    # Agent routing
    current_agent: str
    next_agent: str | None
    
    # Execution state
    final_result: str
    iteration_count: int
    execution_history: list[dict]
    
    # HITL state
    approval_required: bool
    approved: bool | None
    clarification_request_id: str | None
    awaiting_user_input: bool
    
    # Extraction state
    requires_extraction_approval: bool
    extraction_result: dict | None
    extraction_approved: bool | None
    
    # Configuration
    websocket_manager: Any
    llm_provider: str | None
    llm_temperature: float | None
```

### Phase 2: Refactor Graph Structure (Week 2)

#### 2.1 Create Proper Graph with Interrupts

```python
# backend/app/agents/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
from app.agents.checkpointer import get_checkpointer

def create_agent_graph():
    """Create stateful multi-agent graph with HITL."""
    
    # Use persistent checkpointer
    checkpointer = get_checkpointer()
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("invoice", invoice_agent_node)
    workflow.add_node("closing", closing_agent_node)
    workflow.add_node("audit", audit_agent_node)
    workflow.add_node("salesforce", salesforce_agent_node)
    workflow.add_node("zoho", zoho_agent_node)
    workflow.add_node("hitl", hitl_node)  # New HITL node
    workflow.add_node("approval", approval_node)  # New approval node
    
    # Entry point
    workflow.set_entry_point("planner")
    
    # Planner → Approval (always require approval first)
    workflow.add_edge("planner", "approval")
    
    # Approval → Specialized Agent (conditional)
    workflow.add_conditional_edges(
        "approval",
        approval_router,  # Check if approved
        {
            "approved": supervisor_router,  # Route to agent
            "rejected": END
        }
    )
    
    # Specialized Agents → HITL
    workflow.add_edge("invoice", "hitl")
    workflow.add_edge("closing", "hitl")
    workflow.add_edge("audit", "hitl")
    workflow.add_edge("salesforce", "hitl")
    workflow.add_edge("zoho", "hitl")
    
    # HITL → Decision (conditional)
    workflow.add_conditional_edges(
        "hitl",
        hitl_router,  # Check approval vs revision
        {
            "approved": END,
            "revision": supervisor_router,  # Loop back to agent
        }
    )
    
    # Compile with checkpointer and interrupts
    graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["approval", "hitl"]  # Pause for human input
    )
    
    return graph
```

#### 2.2 Create Router Functions

```python
# backend/app/agents/routers.py

def approval_router(state: AgentState) -> str:
    """Route based on plan approval."""
    if state.get("approved"):
        return "approved"
    return "rejected"

def hitl_router(state: AgentState) -> str:
    """Route based on HITL decision."""
    user_response = state.get("user_response", "").upper()
    
    if user_response in ["OK", "YES", "APPROVE", "APPROVED"]:
        return "approved"
    else:
        return "revision"

def supervisor_router(state: AgentState) -> str:
    """Route to appropriate specialized agent."""
    next_agent = state.get("next_agent")
    
    if next_agent in ["invoice", "closing", "audit", "salesforce", "zoho"]:
        return next_agent
    
    # Default to invoice
    return "invoice"
```

### Phase 3: Refactor Agent Service (Week 3)

#### 3.1 Simplify Agent Service

Replace complex manual state management with LangGraph invocations:

```python
# backend/app/services/agent_service.py (refactored)

class AgentService:
    """Service for agent orchestration using LangGraph."""
    
    @staticmethod
    async def execute_task(
        plan_id: str,
        session_id: str,
        task_description: str,
        require_hitl: bool = True
    ) -> Dict[str, Any]:
        """Execute task using LangGraph."""
        
        # Create initial state
        initial_state = {
            "messages": [],
            "plan_id": plan_id,
            "session_id": session_id,
            "task_description": task_description,
            "current_agent": "",
            "next_agent": None,
            "final_result": "",
            "iteration_count": 0,
            "execution_history": [],
            "approval_required": True,
            "approved": None,
            "websocket_manager": websocket_manager,
        }
        
        # Get graph
        graph = get_agent_graph()
        
        # Create thread ID for this execution
        thread_id = f"plan_{plan_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke graph - will stop at first interrupt (approval)
        result = await graph.ainvoke(initial_state, config)
        
        # Graph stopped at approval node
        return {
            "status": "pending_approval",
            "thread_id": thread_id,
            "state": result
        }
    
    @staticmethod
    async def resume_after_approval(
        plan_id: str,
        approved: bool,
        feedback: str = None
    ) -> Dict[str, Any]:
        """Resume execution after approval."""
        
        thread_id = f"plan_{plan_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state from checkpointer
        graph = get_agent_graph()
        state = await graph.aget_state(config)
        
        # Update state with approval decision
        state.values["approved"] = approved
        if feedback:
            state.values["feedback"] = feedback
        
        # Resume execution - will stop at next interrupt (HITL)
        result = await graph.ainvoke(None, config)
        
        # Check where we stopped
        current_node = result.get("current_node")
        
        if current_node == "hitl":
            return {
                "status": "pending_clarification",
                "thread_id": thread_id
            }
        else:
            return {
                "status": "completed",
                "result": result.get("final_result")
            }
    
    @staticmethod
    async def handle_user_clarification(
        plan_id: str,
        answer: str
    ) -> Dict[str, Any]:
        """Handle user clarification."""
        
        thread_id = f"plan_{plan_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get current state
        graph = get_agent_graph()
        state = await graph.aget_state(config)
        
        # Update state with user response
        state.values["user_response"] = answer
        
        # Resume execution
        result = await graph.ainvoke(None, config)
        
        # Check if we're done or looping
        current_node = result.get("current_node")
        
        if current_node == "hitl":
            # Looped back for another revision
            return {
                "status": "pending_clarification",
                "iteration": state.values.get("iteration_count", 0)
            }
        else:
            # Completed
            return {
                "status": "completed",
                "result": result.get("final_result")
            }
```

### Phase 4: Add Tool Nodes (Week 4)

#### 4.1 Create Tool Nodes

```python
# backend/app/agents/tool_nodes.py
from langchain.tools import Tool
from langgraph.prebuilt import ToolNode

# Define tools
zoho_tools = [
    Tool(
        name="list_invoices",
        func=zoho_service.list_invoices,
        description="List invoices from Zoho"
    ),
    Tool(
        name="get_invoice",
        func=zoho_service.get_invoice,
        description="Get specific invoice details"
    ),
]

salesforce_tools = [
    Tool(
        name="query_accounts",
        func=salesforce_service.query_accounts,
        description="Query Salesforce accounts"
    ),
]

# Create tool nodes
zoho_tool_node = ToolNode(zoho_tools)
salesforce_tool_node = ToolNode(salesforce_tools)
```

#### 4.2 Integrate Tools into Graph

```python
# Add tool nodes to graph
workflow.add_node("zoho_tools", zoho_tool_node)
workflow.add_node("salesforce_tools", salesforce_tool_node)

# Add edges for tool calling
workflow.add_conditional_edges(
    "zoho",
    should_use_tools,
    {
        "tools": "zoho_tools",
        "continue": "hitl"
    }
)

workflow.add_edge("zoho_tools", "zoho")  # Loop back after tools
```

### Phase 5: Add Memory and Context (Week 5)

#### 5.1 Implement Conversation Memory

```python
# backend/app/agents/memory.py
from langchain.memory import ConversationBufferMemory

class AgentMemory:
    """Manage conversation memory for agents."""
    
    def __init__(self, plan_id: str):
        self.plan_id = plan_id
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
    
    async def add_message(self, role: str, content: str):
        """Add message to memory."""
        self.memory.chat_memory.add_message(
            {"role": role, "content": content}
        )
    
    async def get_context(self) -> str:
        """Get formatted context for agents."""
        history = self.memory.load_memory_variables({})
        return history.get("chat_history", [])
```

#### 5.2 Integrate Memory into State

```python
# Update AgentState
class AgentState(TypedDict):
    # ... existing fields ...
    chat_history: list[dict]  # Conversation history
    memory: AgentMemory  # Memory instance
```

### Phase 6: Testing and Migration (Week 6)

#### 6.1 Create Test Suite

```python
# backend/tests/test_langgraph_refactor.py

async def test_basic_execution():
    """Test basic task execution."""
    result = await AgentService.execute_task(
        plan_id="test-1",
        session_id="session-1",
        task_description="Test task"
    )
    assert result["status"] == "pending_approval"

async def test_approval_flow():
    """Test approval and execution."""
    # Execute
    result1 = await AgentService.execute_task(...)
    
    # Approve
    result2 = await AgentService.resume_after_approval(
        plan_id="test-1",
        approved=True
    )
    assert result2["status"] == "pending_clarification"

async def test_revision_loop():
    """Test revision loop."""
    # ... test multiple iterations ...

async def test_state_persistence():
    """Test state persists across restarts."""
    # Execute task
    result1 = await AgentService.execute_task(...)
    
    # Simulate server restart
    # ... restart services ...
    
    # Resume should work
    result2 = await AgentService.resume_after_approval(...)
    assert result2 is not None
```

#### 6.2 Migration Strategy

1. **Parallel Implementation**: Keep old code, add new code alongside
2. **Feature Flag**: Use environment variable to switch between old/new
3. **Gradual Rollout**: Test with subset of users first
4. **Monitoring**: Track execution metrics for both implementations
5. **Rollback Plan**: Keep old code for quick rollback if needed

```python
# Feature flag
USE_LANGGRAPH = os.getenv("USE_LANGGRAPH", "false").lower() == "true"

if USE_LANGGRAPH:
    # New LangGraph implementation
    result = await AgentService.execute_task_langgraph(...)
else:
    # Old implementation
    result = await AgentService.execute_task(...)
```

## Benefits of Refactoring

### 1. **Simplified Code**
- Remove 500+ lines of manual state management
- Declarative graph definition instead of imperative control flow
- Easier to understand and maintain

### 2. **Persistent State**
- State survives server restarts
- Can resume long-running tasks
- Better reliability

### 3. **Better Observability**
- Visualize execution flow in LangGraph Studio
- Track state transitions
- Debug issues more easily

### 4. **Scalability**
- LangGraph handles concurrency
- Can distribute across multiple workers
- Better performance under load

### 5. **Extensibility**
- Easy to add new agents (just add nodes)
- Easy to add new routing logic (just add edges)
- Easy to add tools (just add tool nodes)

### 6. **Standard Patterns**
- Use LangGraph's built-in patterns
- Leverage community examples
- Better documentation and support

## Risks and Mitigation

### Risk 1: Breaking Changes
**Mitigation**: Parallel implementation with feature flag, gradual rollout

### Risk 2: Learning Curve
**Mitigation**: Team training, documentation, pair programming

### Risk 3: Performance Impact
**Mitigation**: Benchmark both implementations, optimize as needed

### Risk 4: State Migration
**Mitigation**: Write migration script for existing in-flight tasks

### Risk 5: Debugging Complexity
**Mitigation**: Add comprehensive logging, use LangGraph Studio

## Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Infrastructure | Checkpointer, dependencies, state schema |
| 2 | Graph Structure | New graph definition, routers |
| 3 | Agent Service | Refactored service layer |
| 4 | Tool Integration | Tool nodes, tool calling |
| 5 | Memory | Conversation memory, context management |
| 6 | Testing | Test suite, migration, rollout |

**Total Duration**: 6 weeks

## Success Criteria

1. ✅ All existing functionality works with new implementation
2. ✅ State persists across server restarts
3. ✅ Code is 30%+ simpler (fewer lines, less complexity)
4. ✅ Performance is equal or better
5. ✅ All tests pass
6. ✅ Can visualize execution in LangGraph Studio
7. ✅ Zero downtime migration

## Next Steps

1. **Review and Approve Plan**: Get team buy-in
2. **Set Up Development Environment**: Install LangGraph, set up checkpointer
3. **Create Feature Branch**: `feature/langgraph-refactor`
4. **Start Phase 1**: Begin infrastructure setup
5. **Weekly Check-ins**: Review progress, adjust plan as needed

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [LangGraph Checkpointers](https://python.langchain.com/docs/langgraph/checkpointing)
- [LangGraph Human-in-the-Loop](https://python.langchain.com/docs/langgraph/how-tos/human_in_the_loop)
- [LangGraph Multi-Agent](https://python.langchain.com/docs/langgraph/tutorials/multi_agent)
- [LangGraph Studio](https://github.com/langchain-ai/langgraph-studio)

---

**Document Version**: 1.0  
**Last Updated**: December 8, 2024  
**Author**: AI Development Team  
**Status**: Proposed - Awaiting Approval
