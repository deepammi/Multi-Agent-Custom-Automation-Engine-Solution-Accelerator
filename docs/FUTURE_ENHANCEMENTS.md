# Future Enhancements & Technical Debt

## Overview

This document tracks architectural improvements and features to implement after MVP completion.

---

## 1. LangGraph Integration (High Priority)

### Current State
- **Architecture:** Direct agent execution via `agent_service.py`
- **Routing:** Hardcoded if/elif statements in agent_service
- **Graph:** LangGraph graph is defined but not actively used for execution
- **Status:** ⚠️ Technical Debt

### Issue
The backend has two parallel execution paths:
1. **LangGraph workflow** (`app/agents/graph.py`) - Defined but not used
2. **Direct execution** (`app/services/agent_service.py`) - Currently active

The agent_service.py directly calls agent nodes instead of using the compiled LangGraph:

```python
# Current (Direct Execution)
if next_agent == "invoice":
    result = await invoice_agent_node(state)
elif next_agent == "zoho":
    result = await zoho_agent_node(state)
# ... etc

# Desired (LangGraph Execution)
result = await agent_graph.ainvoke(state)
```

### Benefits of LangGraph Integration

1. **Automatic Routing:** Graph handles agent routing via supervisor
2. **State Management:** Built-in state persistence and checkpointing
3. **Visualization:** Can visualize agent workflows
4. **Flexibility:** Easy to add new agents without modifying service code
5. **Debugging:** Better observability of agent transitions
6. **Scalability:** Support for complex multi-agent workflows

### Implementation Plan

#### Phase 1: Refactor Agent Service
- [ ] Replace direct agent calls with graph invocation
- [ ] Remove hardcoded if/elif agent routing
- [ ] Use `agent_graph.ainvoke()` for execution
- [ ] Maintain backward compatibility during transition

#### Phase 2: State Management
- [ ] Implement proper state serialization
- [ ] Add checkpointing for HITL workflows
- [ ] Handle state persistence across requests

#### Phase 3: Testing
- [ ] Test all agent routing through graph
- [ ] Verify HITL workflows work correctly
- [ ] Ensure WebSocket streaming still functions
- [ ] Performance testing

#### Phase 4: Cleanup
- [ ] Remove legacy direct execution code
- [ ] Update documentation
- [ ] Add graph visualization tools

### Files to Modify

```
backend/app/services/agent_service.py  # Main refactor
backend/app/agents/graph.py            # Already defined, needs integration
backend/app/agents/supervisor.py      # Already updated
backend/app/agents/nodes.py            # Already updated
```

### Estimated Effort
- **Time:** 4-6 hours
- **Risk:** Medium (requires careful testing of HITL flows)
- **Priority:** High (reduces technical debt)

### Current Workaround
✅ All agents (Invoice, Closing, Audit, Salesforce, Zoho) are manually registered in agent_service.py
✅ Routing works but requires code changes for new agents
✅ Functional for MVP

---

## 2. Zoho OAuth Scope Issues (Medium Priority)

### Current State
- **Status:** ⚠️ OAuth working but with scope limitations
- **Workaround:** Using mock data for Zoho integration
- **Issue:** Refresh token has insufficient scopes

### Problem
The Zoho refresh token was generated with incomplete scopes, causing 401 errors when accessing certain API endpoints.

### Required Scopes
```
ZohoInvoice.invoices.ALL
ZohoInvoice.contacts.ALL
ZohoInvoice.items.ALL
ZohoInvoice.settings.ALL
```

### Solution
1. Generate new grant token with all required scopes
2. Exchange for new refresh token
3. Update `.env` with new refresh token
4. Test all API endpoints

### Documentation
- See: `docs/ZOHO_FIX_SCOPES.md`
- See: `backend/regenerate_zoho_token.py`

### Estimated Effort
- **Time:** 30 minutes (once scopes are understood)
- **Risk:** Low
- **Priority:** Medium (mock data works for MVP)

---

## 3. MCP Server Implementation (Low Priority)

### Current State
- **Status:** 📋 Planned but not implemented
- **Phase:** Phase 4-5 of implementation plan
- **Current:** Direct API integration working

### Plan
Create FastMCP server for Zoho Invoice to follow MCP protocol standards.

### Benefits
- Standardized tool interface
- Reusable across projects
- Better separation of concerns
- Follows MCP best practices

### Implementation Plan
See: `docs/ZOHO_MCP_IMPLEMENTATION_PLAN.md` (Phases 4-5)

### Estimated Effort
- **Time:** 2-3 hours
- **Risk:** Low
- **Priority:** Low (direct integration works)

---

## 4. Additional Enhancements

### 4.1 Error Handling Improvements
- [ ] Add retry logic for API failures
- [ ] Better error messages for users
- [ ] Graceful degradation when services unavailable

### 4.2 Performance Optimization
- [ ] Cache frequently accessed data
- [ ] Implement connection pooling
- [ ] Optimize database queries

### 4.3 Testing Coverage
- [ ] Add unit tests for all agents
- [ ] Integration tests for workflows
- [ ] End-to-end tests for UI flows

### 4.4 Monitoring & Logging
- [ ] Structured logging
- [ ] Performance metrics
- [ ] Error tracking
- [ ] Usage analytics

### 4.5 Security Enhancements
- [ ] Token encryption at rest
- [ ] Rate limiting
- [ ] Input validation
- [ ] Audit logging

---

## Priority Matrix

| Enhancement | Priority | Effort | Impact | Status |
|-------------|----------|--------|--------|--------|
| LangGraph Integration | High | 4-6h | High | 📋 Planned |
| Zoho OAuth Fix | Medium | 30m | Medium | ⚠️ Workaround |
| MCP Server | Low | 2-3h | Low | 📋 Planned |
| Error Handling | Medium | 2h | Medium | 📋 Planned |
| Testing Coverage | Medium | 4h | High | 📋 Planned |
| Performance | Low | 3h | Medium | 📋 Planned |
| Monitoring | Low | 2h | Medium | 📋 Planned |
| Security | High | 3h | High | 📋 Planned |

---

## MVP Completion Checklist

### Current MVP Status: ✅ Functional

- [x] Salesforce integration (mock mode)
- [x] Zoho integration (mock mode)
- [x] File upload feature
- [x] Invoice extraction
- [x] Multi-agent routing
- [x] WebSocket streaming
- [x] Frontend UI working
- [ ] LangGraph integration (post-MVP)
- [ ] Real OAuth for Zoho (post-MVP)
- [ ] MCP server (post-MVP)

---

## Post-MVP Roadmap

### Phase 1: Stabilization (Week 1)
1. Fix LangGraph integration
2. Resolve Zoho OAuth issues
3. Add comprehensive error handling

### Phase 2: Enhancement (Week 2)
1. Implement MCP server
2. Add testing coverage
3. Performance optimization

### Phase 3: Production Ready (Week 3)
1. Security hardening
2. Monitoring & logging
3. Documentation completion

---

## Notes

- **Current Focus:** MVP completion with working features
- **Technical Debt:** Acceptable for MVP, documented for future
- **Architecture:** Functional but can be improved
- **Decision:** Ship MVP first, refactor later ✅

---

## References

- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- Zoho API Docs: https://www.zoho.com/invoice/api/v3/
- MCP Protocol: https://modelcontextprotocol.io/
- Implementation Plan: `docs/ZOHO_MCP_IMPLEMENTATION_PLAN.md`
- Architecture Analysis: `docs/BACKEND_ARCHITECTURE_ANALYSIS.md`
