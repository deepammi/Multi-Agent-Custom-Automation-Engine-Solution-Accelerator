# Zoho Invoice MCP Integration - Implementation Plan

## Overview

Build Zoho Invoice MCP server and backend integration incrementally with testing at each stage. Start with mock data, then integrate real OAuth when ready.

---

## Phase 1: Mock Zoho Service (Backend Only)

**Goal:** Create a working Zoho service with mock data to test the integration pattern.

### Tasks:
- [ ] 1.1 Create `zoho_mcp_service.py` with mock data
- [ ] 1.2 Implement basic methods (list_invoices, get_invoice, list_customers)
- [ ] 1.3 Create test script to verify mock service
- [ ] 1.4 Test: Run `test_zoho_mock_service.py`

**Success Criteria:**
- Service returns mock invoice data
- All methods work without OAuth
- Test script passes

**Estimated Time:** 30 minutes

---

## Phase 2: Zoho Agent Node (LangGraph Integration)

**Goal:** Add Zoho agent to LangGraph workflow.

### Tasks:
- [ ] 2.1 Create `zoho_agent_node.py`
- [ ] 2.2 Implement invoice listing and display logic
- [ ] 2.3 Update `graph.py` to include Zoho agent
- [ ] 2.4 Update `supervisor.py` routing
- [ ] 2.5 Update `planner_node` with Zoho keywords
- [ ] 2.6 Test: Run `test_zoho_agent.py`

**Success Criteria:**
- Planner routes "invoice" tasks to Zoho agent
- Zoho agent returns formatted mock data
- Agent integrates with existing workflow

**Estimated Time:** 45 minutes

---

## Phase 3: Frontend Testing (Mock Mode)

**Goal:** Test Zoho agent through the UI with mock data.

### Tasks:
- [ ] 3.1 Start backend server
- [ ] 3.2 Submit test task: "Show me recent invoices from Zoho"
- [ ] 3.3 Verify planner routes to Zoho agent
- [ ] 3.4 Verify mock invoice data displays correctly
- [ ] 3.5 Test different queries (customers, specific invoice)

**Success Criteria:**
- UI displays Zoho agent responses
- Mock data shows correctly formatted
- WebSocket streaming works

**Estimated Time:** 20 minutes

---

## Phase 4: Zoho MCP Server (FastMCP)

**Goal:** Create standalone MCP server for Zoho Invoice.

### Tasks:
- [ ] 4.1 Create `src/mcp_server/services/zoho_service.py`
- [ ] 4.2 Implement MCP tools (list_invoices, get_invoice, create_invoice)
- [ ] 4.3 Add OAuth handling (with fallback to mock)
- [ ] 4.4 Register tools with FastMCP
- [ ] 4.5 Test: Run MCP server standalone
- [ ] 4.6 Test: Call tools via MCP protocol

**Success Criteria:**
- MCP server starts successfully
- Tools are registered and discoverable
- Can call tools (mock mode)

**Estimated Time:** 1 hour

---

## Phase 5: MCP Client Integration

**Goal:** Connect backend to Zoho MCP server.

### Tasks:
- [ ] 5.1 Update `zoho_mcp_service.py` to use MCP client
- [ ] 5.2 Configure MCP server in `.kiro/settings/mcp.json`
- [ ] 5.3 Test MCP client → server communication
- [ ] 5.4 Verify tools are callable from backend
- [ ] 5.5 Test: Run `test_zoho_mcp_integration.py`

**Success Criteria:**
- Backend can call MCP server tools
- Mock data flows through MCP protocol
- Error handling works

**Estimated Time:** 45 minutes

---

## Phase 6: OAuth Integration (When Ready)

**Goal:** Replace mock data with real Zoho API calls.

### Tasks:
- [ ] 6.1 Fix OAuth scope issues
- [ ] 6.2 Update MCP server to use real API
- [ ] 6.3 Add token refresh logic
- [ ] 6.4 Test with real Zoho account
- [ ] 6.5 Verify real invoice data retrieval

**Success Criteria:**
- Real invoices retrieved from Zoho
- OAuth tokens refresh automatically
- Error handling for API failures

**Estimated Time:** 1 hour (after OAuth is fixed)

---

## Phase 7: Advanced Features

**Goal:** Add create/update capabilities.

### Tasks:
- [ ] 7.1 Implement create_invoice tool
- [ ] 7.2 Implement update_invoice tool
- [ ] 7.3 Add customer management tools
- [ ] 7.4 Test CRUD operations
- [ ] 7.5 Add validation and error handling

**Success Criteria:**
- Can create invoices via agent
- Can update existing invoices
- Proper validation and errors

**Estimated Time:** 1.5 hours

---

## Phase 8: End-to-End Testing

**Goal:** Complete workflow testing.

### Tasks:
- [ ] 8.1 Test: List invoices via UI
- [ ] 8.2 Test: Create invoice via UI
- [ ] 8.3 Test: Update invoice via UI
- [ ] 8.4 Test: Error scenarios
- [ ] 8.5 Test: Multi-agent workflows (Invoice + Zoho)

**Success Criteria:**
- All operations work end-to-end
- Error handling is robust
- UI displays data correctly

**Estimated Time:** 45 minutes

---

## Implementation Strategy

### Start with Mock Data
- Build entire integration with mock data first
- Test all components independently
- Verify architecture before adding OAuth complexity

### Incremental Testing
- Test after each phase
- Don't proceed until current phase works
- Keep mock mode as fallback

### Parallel OAuth Debugging
- Continue debugging OAuth in parallel
- Switch to real API when OAuth works
- Mock mode remains as backup

---

## File Structure

```
backend/
├── app/
│   ├── agents/
│   │   ├── zoho_agent_node.py          # Phase 2
│   │   ├── graph.py                     # Phase 2 (update)
│   │   └── supervisor.py                # Phase 2 (update)
│   └── services/
│       └── zoho_mcp_service.py          # Phase 1
├── test_zoho_mock_service.py            # Phase 1
├── test_zoho_agent.py                   # Phase 2
└── test_zoho_mcp_integration.py         # Phase 5

src/mcp_server/
└── services/
    └── zoho_service.py                  # Phase 4

.kiro/settings/
└── mcp.json                             # Phase 5 (update)
```

---

## Testing Checklist

### Phase 1 Tests
- [ ] Mock service returns invoice list
- [ ] Mock service returns single invoice
- [ ] Mock service returns customers
- [ ] Error handling works

### Phase 2 Tests
- [ ] Planner routes to Zoho agent
- [ ] Zoho agent formats data correctly
- [ ] Agent integrates with graph
- [ ] WebSocket messages work

### Phase 3 Tests
- [ ] UI displays Zoho responses
- [ ] Multiple query types work
- [ ] Error messages display
- [ ] Real-time updates work

### Phase 4 Tests
- [ ] MCP server starts
- [ ] Tools are registered
- [ ] Tools can be called
- [ ] Mock data returns correctly

### Phase 5 Tests
- [ ] Backend connects to MCP server
- [ ] Tools are callable
- [ ] Data flows correctly
- [ ] Error handling works

### Phase 6 Tests
- [ ] OAuth authentication works
- [ ] Real API calls succeed
- [ ] Token refresh works
- [ ] Real data displays

---

## Current Status

**Phase:** Ready to start Phase 1
**OAuth Status:** Debugging in parallel
**Approach:** Mock-first implementation

---

## Next Steps

1. **Start Phase 1:** Create mock Zoho service
2. **Test Phase 1:** Verify mock data works
3. **Proceed to Phase 2:** Add agent node
4. **Continue incrementally:** Test after each phase

---

## Rollback Plan

If OAuth continues to fail:
- Keep mock mode as primary
- Document OAuth issues for later
- Complete integration with mock data
- Switch to real API when OAuth is resolved

---

## Success Metrics

- ✅ Mock integration works end-to-end
- ✅ All tests pass
- ✅ UI displays Zoho data
- ✅ Agent routing works correctly
- ⏳ OAuth integration (when ready)

---

## Estimated Total Time

- **Phases 1-3 (Mock):** 2 hours
- **Phases 4-5 (MCP):** 2 hours
- **Phase 6 (OAuth):** 1 hour (when ready)
- **Phases 7-8 (Advanced):** 2.5 hours

**Total:** ~7.5 hours (can be done incrementally)

---

## Ready to Start?

Let's begin with **Phase 1: Mock Zoho Service**!
