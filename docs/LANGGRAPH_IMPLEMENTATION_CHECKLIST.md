# LangGraph Refactoring Implementation Checklist

Use this checklist to track progress through the 6-week refactoring plan.

## Pre-Implementation

- [ ] Team review of refactoring plan
- [ ] Timeline approved
- [ ] Resources allocated
- [ ] Development environment set up
- [ ] Feature branch created: `feature/langgraph-refactor`

---

## Week 1: Infrastructure Setup

### Dependencies
- [ ] Add `langgraph>=0.0.40` to requirements.txt
- [ ] Add `langchain>=0.1.0` to requirements.txt
- [ ] Add `langchain-openai>=0.0.5` to requirements.txt
- [ ] Add `langchain-anthropic>=0.1.0` to requirements.txt
- [ ] Run `pip install -r requirements.txt`
- [ ] Verify all imports work

### Checkpointer
- [ ] Create `backend/app/agents/checkpointer.py`
- [ ] Choose checkpointer type (MongoDB or SQLite)
- [ ] Implement `get_checkpointer()` function
- [ ] Test checkpointer connection
- [ ] Verify state can be saved and loaded

### State Schema
- [ ] Update `backend/app/agents/state.py`
- [ ] Add `messages` field with `add_messages` annotation
- [ ] Add all required fields (see plan)
- [ ] Add type hints for all fields
- [ ] Test state creation and serialization

### Testing
- [ ] Create `backend/tests/test_checkpointer.py`
- [ ] Test checkpointer save/load
- [ ] Test state persistence
- [ ] All tests passing

**Week 1 Deliverable**: ✅ Working checkpointer with persistent state

---

## Week 2: Graph Structure

### Router Functions
- [ ] Create `backend/app/agents/routers.py`
- [ ] Implement `approval_router()`
- [ ] Implement `hitl_router()`
- [ ] Implement `supervisor_router()`
- [ ] Add logging to all routers
- [ ] Test router logic

### Graph Definition
- [ ] Create `backend/app/agents/graph_v2.py`
- [ ] Define all nodes (planner, agents, approval, hitl)
- [ ] Add entry point
- [ ] Add edges between nodes
- [ ] Add conditional edges with routers
- [ ] Configure interrupts (`interrupt_before`)
- [ ] Compile graph with checkpointer

### Node Functions
- [ ] Create `create_approval_node()`
- [ ] Create `create_hitl_node()`
- [ ] Update existing agent nodes if needed
- [ ] Add proper logging to all nodes

### Testing
- [ ] Create `backend/tests/test_graph_v2.py`
- [ ] Test graph compilation
- [ ] Test node execution
- [ ] Test routing logic
- [ ] Test interrupts
- [ ] All tests passing

**Week 2 Deliverable**: ✅ Complete LangGraph workflow with interrupts

---

## Week 3: Agent Service Refactoring

### New Service
- [ ] Create `backend/app/services/agent_service_v2.py`
- [ ] Implement `execute_task()` using graph.ainvoke()
- [ ] Implement `resume_after_approval()` using graph state
- [ ] Implement `handle_user_clarification()` using graph state
- [ ] Add WebSocket message sending
- [ ] Add database status updates
- [ ] Add comprehensive logging

### Helper Methods
- [ ] Implement `_send_approval_request()`
- [ ] Implement `_send_hitl_request()`
- [ ] Implement `_send_extraction_approval()` (if needed)
- [ ] Add error handling

### Feature Flag
- [ ] Add `USE_LANGGRAPH_V2` to `.env`
- [ ] Update `backend/app/api/v3/routes.py`
- [ ] Add conditional routing based on feature flag
- [ ] Test both implementations work

### Testing
- [ ] Create `backend/tests/test_agent_service_v2.py`
- [ ] Test basic execution flow
- [ ] Test approval flow
- [ ] Test clarification flow
- [ ] Test revision loop
- [ ] Test error handling
- [ ] All tests passing

**Week 3 Deliverable**: ✅ Working AgentServiceV2 with feature flag

---

## Week 4: Tool Integration

### Tool Definitions
- [ ] Create `backend/app/agents/tool_nodes.py`
- [ ] Define Zoho tools (list_invoices, get_invoice, etc.)
- [ ] Define Salesforce tools (query_accounts, etc.)
- [ ] Create ToolNode instances
- [ ] Test tool execution

### Graph Integration
- [ ] Add tool nodes to graph
- [ ] Add conditional edges for tool calling
- [ ] Add loop-back edges after tool execution
- [ ] Implement `should_use_tools()` router
- [ ] Test tool calling flow

### Agent Updates
- [ ] Update agents to request tools when needed
- [ ] Add tool result handling
- [ ] Test agents with tools

### Testing
- [ ] Create `backend/tests/test_tool_nodes.py`
- [ ] Test tool execution
- [ ] Test tool integration with agents
- [ ] Test tool error handling
- [ ] All tests passing

**Week 4 Deliverable**: ✅ Agents can call tools via LangGraph

---

## Week 5: Memory and Context

### Memory Implementation
- [ ] Create `backend/app/agents/memory.py`
- [ ] Implement `AgentMemory` class
- [ ] Add conversation buffer
- [ ] Add context retrieval methods
- [ ] Test memory operations

### State Integration
- [ ] Add `chat_history` to AgentState
- [ ] Add `memory` instance to state
- [ ] Update nodes to use memory
- [ ] Update agents to access context

### Context Management
- [ ] Implement context formatting
- [ ] Add execution history tracking
- [ ] Add iteration tracking
- [ ] Test context persistence

### Testing
- [ ] Create `backend/tests/test_memory.py`
- [ ] Test memory storage
- [ ] Test context retrieval
- [ ] Test multi-turn conversations
- [ ] All tests passing

**Week 5 Deliverable**: ✅ Conversation memory and context management

---

## Week 6: Testing and Migration

### Comprehensive Testing
- [ ] Create `backend/tests/test_langgraph_integration.py`
- [ ] Test complete end-to-end flows
- [ ] Test all agent types
- [ ] Test approval scenarios
- [ ] Test revision loops
- [ ] Test error scenarios
- [ ] Test state persistence across restarts
- [ ] Test concurrent executions
- [ ] All tests passing

### Performance Testing
- [ ] Benchmark old vs new implementation
- [ ] Test with high load
- [ ] Optimize checkpointer if needed
- [ ] Verify no performance regression

### Migration Script
- [ ] Create migration script for in-flight tasks
- [ ] Test migration with sample data
- [ ] Document migration process

### Documentation
- [ ] Update API documentation
- [ ] Update developer guide
- [ ] Create troubleshooting guide
- [ ] Update deployment docs

### Rollout Plan
- [ ] Define rollout stages (10%, 50%, 100%)
- [ ] Set up monitoring and alerts
- [ ] Create rollback procedure
- [ ] Get approval for rollout

### Gradual Rollout
- [ ] Enable for 10% of traffic
- [ ] Monitor for 48 hours
- [ ] Enable for 50% of traffic
- [ ] Monitor for 48 hours
- [ ] Enable for 100% of traffic
- [ ] Monitor for 1 week

### Cleanup
- [ ] Remove old agent_service.py code
- [ ] Remove feature flag
- [ ] Update all references
- [ ] Clean up unused code
- [ ] Final code review

**Week 6 Deliverable**: ✅ Production deployment complete

---

## Post-Implementation

### Monitoring
- [ ] Set up dashboards for LangGraph metrics
- [ ] Monitor execution times
- [ ] Monitor error rates
- [ ] Monitor state persistence
- [ ] Set up alerts

### Team Training
- [ ] Conduct training session on LangGraph
- [ ] Share documentation
- [ ] Pair programming sessions
- [ ] Q&A session

### Retrospective
- [ ] Team retrospective meeting
- [ ] Document lessons learned
- [ ] Identify improvements
- [ ] Update process for future refactorings

### Celebration
- [ ] Announce completion to team
- [ ] Share metrics and improvements
- [ ] Celebrate success! 🎉

---

## Success Criteria

- [ ] All existing functionality works with new implementation
- [ ] State persists across server restarts
- [ ] Code is 30%+ simpler (fewer lines)
- [ ] Performance is equal or better
- [ ] All tests pass (100% coverage of critical paths)
- [ ] Can visualize execution in LangGraph Studio
- [ ] Zero downtime migration
- [ ] Team is trained and comfortable with new system

---

## Rollback Criteria

If any of these occur, consider rollback:

- [ ] Critical bugs affecting >5% of users
- [ ] Performance degradation >20%
- [ ] Data loss or corruption
- [ ] Unable to resume tasks after restart
- [ ] Team unable to debug issues

**Rollback Process**: Set `USE_LANGGRAPH_V2=false` in environment

---

## Notes

Use this space to track issues, decisions, and important notes during implementation:

```
Date: ___________
Note: ___________________________________________________________
_________________________________________________________________

Date: ___________
Note: ___________________________________________________________
_________________________________________________________________

Date: ___________
Note: ___________________________________________________________
_________________________________________________________________
```

---

## Sign-off

- [ ] Technical Lead Approval: _________________ Date: _______
- [ ] Product Owner Approval: _________________ Date: _______
- [ ] QA Approval: _________________ Date: _______
- [ ] DevOps Approval: _________________ Date: _______

---

**Version**: 1.0  
**Last Updated**: December 8, 2024  
**Status**: Ready for Implementation
