# LangGraph Architecture Diagrams

## Current Architecture (Before Refactoring)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Agent Service                            │
│  (Manual State Management with if/else routing)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  execute_task()  │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Planner Node    │
                    │  (manual call)   │
                    └──────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ Store in _pending_executions  │
              │ (in-memory dictionary)        │
              └───────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Send Approval    │
                    │ Request          │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Wait for User    │
                    │ (manual check)   │
                    └──────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ resume_after_approval()       │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ if next_agent == "invoice":   │
              │     invoice_agent_node()      │
              │ elif next_agent == "closing": │
              │     closing_agent_node()      │
              │ elif next_agent == "audit":   │
              │     audit_agent_node()        │
              │ elif next_agent == "salesforce": │
              │     salesforce_agent_node()   │
              │ elif next_agent == "zoho":    │
              │     zoho_agent_node()         │
              └───────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Manual HITL      │
                    │ Handling         │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Manual Revision  │
                    │ Loop             │
                    └──────────────────┘
```

## Proposed Architecture (After Refactoring)

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Execution Engine                    │
│              (Stateful, Persistent, Declarative)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  graph.invoke()  │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph Workflow                          │
│                                                                   │
│  ┌─────────────┐                                                │
│  │   Planner   │                                                │
│  │    Node     │                                                │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │  Approval   │ ◄─── INTERRUPT (wait for human)               │
│  │    Node     │                                                │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────┐                   │
│  │      Conditional Edge (supervisor)       │                   │
│  │  ┌─────────┬─────────┬─────────┬──────┐│                   │
│  │  │ Invoice │ Closing │  Audit  │ etc. ││                   │
│  │  └────┬────┴────┬────┴────┬────┴──────┘│                   │
│  └───────┼─────────┼─────────┼─────────────┘                   │
│          │         │         │                                  │
│          ▼         ▼         ▼                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │ Invoice  │ │ Closing  │ │  Audit   │                       │
│  │  Agent   │ │  Agent   │ │  Agent   │                       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                       │
│       │            │            │                               │
│       └────────────┴────────────┘                               │
│                    │                                             │
│                    ▼                                             │
│            ┌──────────────┐                                     │
│            │  Tool Nodes  │ (optional)                          │
│            │  - Zoho      │                                     │
│            │  - Salesforce│                                     │
│            └──────┬───────┘                                     │
│                   │                                              │
│                   ▼                                              │
│            ┌──────────────┐                                     │
│            │  HITL Node   │ ◄─── INTERRUPT (wait for human)    │
│            └──────┬───────┘                                     │
│                   │                                              │
│                   ▼                                              │
│       ┌───────────────────────┐                                │
│       │  Conditional Edge     │                                │
│       │  ┌─────────┬────────┐│                                │
│       │  │Approved │Revision││                                │
│       │  └────┬────┴───┬────┘│                                │
│       └───────┼────────┼─────┘                                │
│               │        │                                        │
│               ▼        │                                        │
│            ┌─────┐     │                                        │
│            │ END │     │                                        │
│            └─────┘     │                                        │
│                        │                                        │
│                        └──────► Loop back to Agent             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Checkpointer    │
                    │  (MongoDB/SQLite)│
                    │  - Persistent    │
                    │  - Resumable     │
                    └──────────────────┘
```

## State Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                      Initial State                            │
│  {                                                            │
│    messages: [],                                              │
│    plan_id: "...",                                            │
│    task_description: "...",                                   │
│    current_agent: "",                                         │
│    next_agent: null,                                          │
│    approved: null,                                            │
│    iteration_count: 0                                         │
│  }                                                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                   After Planner Node                          │
│  {                                                            │
│    messages: ["Task analyzed..."],                            │
│    current_agent: "Planner",                                  │
│    next_agent: "invoice",  ◄─── Planner decides routing      │
│    ...                                                        │
│  }                                                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼ INTERRUPT (wait for approval)
┌──────────────────────────────────────────────────────────────┐
│                   After Approval                              │
│  {                                                            │
│    ...                                                        │
│    approved: true,  ◄─── User approved                       │
│    ...                                                        │
│  }                                                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                After Specialized Agent                        │
│  {                                                            │
│    messages: [..., "Invoice processed..."],                   │
│    current_agent: "Invoice",                                  │
│    final_result: "Invoice data extracted",                    │
│    ...                                                        │
│  }                                                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼ INTERRUPT (wait for HITL)
┌──────────────────────────────────────────────────────────────┐
│                   After HITL Decision                         │
│  {                                                            │
│    ...                                                        │
│    user_response: "Please fix X",  ◄─── User revision        │
│    iteration_count: 1,                                        │
│    ...                                                        │
│  }                                                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼ Loop back to agent OR complete
```

## Comparison: Code Complexity

### Before (Manual State Management)

```python
# 830 lines in agent_service.py
class AgentService:
    _pending_executions = {}  # Manual state storage
    _execution_contexts = {}  # Manual context storage
    
    async def execute_task(...):
        # 100+ lines of manual orchestration
        planner_result = planner_node(state)
        AgentService._pending_executions[plan_id] = {...}
        await websocket_manager.send_message(...)
        await PlanRepository.update_status(...)
        # ... more manual management
    
    async def resume_after_approval(...):
        # 150+ lines of if/else routing
        if next_agent == "invoice":
            result = await invoice_agent_node(state)
        elif next_agent == "closing":
            result = closing_agent_node(state)
        # ... 5 more elif blocks
        
        if require_hitl:
            # ... 50+ lines of HITL logic
        # ... more manual management
    
    async def handle_user_clarification(...):
        # 100+ lines of revision loop logic
        if is_approval:
            # ... complete task
        else:
            # ... route back to agent
            if current_agent == "invoice":
                result = await invoice_agent_node(state)
            # ... more if/else
```

### After (LangGraph)

```python
# ~200 lines total
class AgentService:
    async def execute_task(...):
        # 20 lines - just invoke graph
        graph = get_agent_graph()
        config = {"configurable": {"thread_id": f"plan_{plan_id}"}}
        result = await graph.ainvoke(initial_state, config)
        return {"status": "pending_approval"}
    
    async def resume_after_approval(...):
        # 15 lines - update state and resume
        graph = get_agent_graph()
        state = await graph.aget_state(config)
        state.values["approved"] = approved
        result = await graph.ainvoke(None, config)
        return {"status": result.get("status")}
    
    async def handle_user_clarification(...):
        # 15 lines - update state and resume
        graph = get_agent_graph()
        state = await graph.aget_state(config)
        state.values["user_response"] = answer
        result = await graph.ainvoke(None, config)
        return {"status": result.get("status")}
```

**Result**: ~75% reduction in code complexity!

## Memory and Context Management

```
┌─────────────────────────────────────────────────────────────┐
│                    Conversation Memory                       │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Iteration 1:                                           │ │
│  │   User: "Process invoice"                              │ │
│  │   Planner: "Routing to Invoice Agent"                  │ │
│  │   Invoice: "Invoice processed"                         │ │
│  │   HITL: "Please approve"                               │ │
│  │   User: "Fix the date"                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Iteration 2:                                           │ │
│  │   Invoice: "Date fixed, invoice reprocessed"           │ │
│  │   HITL: "Please approve"                               │ │
│  │   User: "OK"                                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  All stored in AgentState["chat_history"]                   │
│  Persisted via Checkpointer                                 │
│  Available to all agents for context                        │
└─────────────────────────────────────────────────────────────┘
```

## Tool Integration Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Node                              │
│  (e.g., Zoho Agent)                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ Should use tools?     │
         │ (conditional edge)    │
         └───────┬───────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
   ┌─────────┐      ┌──────────┐
   │Continue │      │Tool Node │
   │to HITL  │      │          │
   └─────────┘      └────┬─────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Execute Tools│
                  │ - list_invoices
                  │ - get_invoice
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Loop back to │
                  │ Agent Node   │
                  └──────────────┘
```

## Persistence and Recovery

```
┌─────────────────────────────────────────────────────────────┐
│                    Execution Timeline                        │
│                                                               │
│  T0: User submits task                                       │
│      └─► State saved to checkpointer                         │
│                                                               │
│  T1: Planner analyzes                                        │
│      └─► State updated and saved                             │
│                                                               │
│  T2: Interrupt for approval                                  │
│      └─► State saved (waiting for user)                      │
│                                                               │
│  ⚡ SERVER RESTART ⚡                                         │
│                                                               │
│  T3: User approves                                           │
│      └─► State loaded from checkpointer                      │
│      └─► Execution resumes seamlessly                        │
│                                                               │
│  T4: Agent processes                                         │
│      └─► State updated and saved                             │
│                                                               │
│  T5: Interrupt for HITL                                      │
│      └─► State saved (waiting for user)                      │
│                                                               │
│  T6: User provides revision                                  │
│      └─► State loaded and execution continues                │
│                                                               │
└─────────────────────────────────────────────────────────────┘

All state transitions are persisted!
No data loss on restart!
```

## Key Improvements Summary

| Aspect | Before | After |
|--------|--------|-------|
| **State Management** | Manual dictionaries | LangGraph checkpointer |
| **Persistence** | In-memory only | MongoDB/SQLite |
| **Agent Routing** | if/else statements | Graph edges |
| **Code Lines** | ~830 lines | ~200 lines |
| **Complexity** | High (manual) | Low (declarative) |
| **Observability** | Logs only | LangGraph Studio |
| **Recovery** | Lost on restart | Automatic resume |
| **Testing** | Hard to test | Easy to test |
| **Extensibility** | Add if/else | Add graph node |

