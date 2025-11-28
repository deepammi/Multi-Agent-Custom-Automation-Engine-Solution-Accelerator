# HITL Testing Guide - Invoice Agent with Human Verification

## Quick Summary
The HITL routing logic is correct. The issue is likely that:
1. The backend wasn't fully restarted after code changes
2. Python bytecode cache needs to be cleared
3. The `require_hitl` flag isn't being passed correctly

## Step-by-Step Testing Plan

### Phase 1: Clean Restart

**Step 1.1: Stop all services**
```bash
# Kill backend
pkill -f "uvicorn app.main"

# Kill frontend
pkill -f "npm run dev"
```

**Step 1.2: Clear Python cache**
```bash
# Remove all __pycache__ directories
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find backend -type f -name "*.pyc" -delete

# Remove any .pytest_cache
rm -rf backend/.pytest_cache
```

**Step 1.3: Start backend with fresh Python**
```bash
cd backend
python -m uvicorn app.main:app --reload --log-level info
```

**Step 1.4: In another terminal, start frontend**
```bash
cd src/frontend
npm run dev
```

### Phase 2: Test Invoice + HITL Flow

**Step 2.1: Submit Invoice Task**
1. Open http://localhost:5173 (or your frontend URL)
2. In the chat input, type: `Check invoice for accuracy and verify payment terms`
3. Click Send

**Step 2.2: Expected Output - Planner Phase**
You should see:
- ✅ Planner Agent message: "This appears to be an invoice-related task..."
- ✅ Plan approval request with steps
- ✅ Approve/Cancel buttons appear

**Step 2.3: Approve the Plan**
1. Click "Approve Task Plan" button
2. Watch the logs for: `🔍 DEBUG: Storing execution state with require_hitl=True`

**Step 2.4: Expected Output - Invoice Agent Phase**
You should see:
- ✅ Invoice Agent message with checkmarks
- ✅ Log: `🔍 DEBUG: require_hitl=True for plan {plan_id}`
- ✅ Log: `🔍 DEBUG: Routing to HITL agent for plan {plan_id}`

**Step 2.5: Expected Output - HITL Phase**
You should see:
- ✅ Log: `🔔 SENDING CLARIFICATION REQUEST for plan {plan_id}`
- ✅ ClarificationUI component appears with:
  - Agent Result section (showing Invoice Agent output)
  - Text input field
  - "Approve" and "Retry" buttons

**Step 2.6: Test Approval Path**
1. In the ClarificationUI, type: `OK`
2. Click "Approve" button
3. Expected: Task completes with success message

**Step 2.7: Test Revision Path (Optional)**
1. Submit another invoice task
2. Approve the plan
3. In ClarificationUI, type: `Please double-check the vendor information`
4. Click "Retry" button
5. Expected: Task loops back to Planner with revision

### Phase 3: Monitor Logs

**Backend Logs to Watch For:**

```
✅ CORRECT FLOW:
🔍 DEBUG: Storing execution state with require_hitl=True for plan {id}
🔍 DEBUG: require_hitl=True for plan {id}
🔍 DEBUG: Routing to HITL agent for plan {id}
🔔 SENDING CLARIFICATION REQUEST for plan {id}

❌ WRONG FLOW (if you see this):
🔍 DEBUG: HITL is disabled, completing task for plan {id}
Plan {id} completed (HITL skipped)
```

**Frontend Logs to Watch For:**

```
✅ CORRECT FLOW:
📋 Clarification Message received
✅ Parsed clarification message
ClarificationUI should render

❌ WRONG FLOW (if you see this):
Final Result Message received
Task completed without clarification
```

### Phase 4: Troubleshooting

**If you see "HITL skipped" in logs:**

1. Check that `require_hitl=True` is being stored
2. Verify the execution state is being retrieved correctly
3. Add this check in `resume_after_approval`:
   ```python
   logger.info(f"🔍 DEBUG: Full execution_state: {json.dumps(execution_state, default=str)}")
   ```

**If ClarificationUI doesn't appear:**

1. Check browser console for errors
2. Verify `clarificationMessage` state in PlanPage
3. Check that WebSocket message type is `user_clarification_request`
4. Verify ClarificationUI component is imported correctly

**If approval doesn't complete:**

1. Check that `handle_user_clarification` is being called
2. Verify the answer is being parsed correctly
3. Check that "OK" is recognized as approval

### Phase 5: Expected Complete Flow

```
User Input: "Check invoice for accuracy"
    ↓
Planner Agent: "This is an invoice task"
    ↓
User Approves Plan
    ↓
Invoice Agent: "✓ Verified invoice accuracy..."
    ↓
HITL Agent: "Please review this result"
    ↓
ClarificationUI Appears
    ↓
User Types "OK"
    ↓
Task Completes: "Task approved and completed successfully"
```

## Quick Verification Checklist

- [ ] Backend restarted with fresh Python
- [ ] Python cache cleared
- [ ] Frontend restarted
- [ ] Invoice task submitted
- [ ] Plan approved
- [ ] ClarificationUI appears
- [ ] Approval completes task
- [ ] Logs show HITL routing

## If Everything Works

Great! The HITL feature is working. Next steps:
1. Test revision loop (provide feedback instead of "OK")
2. Test multiple revisions
3. Run property-based tests
4. Test with other agents (Closing, Audit)

## If Something Doesn't Work

1. Share the backend logs showing the issue
2. Share the browser console logs
3. Check if `require_hitl` is being set to False somewhere
4. Verify the WebSocket connection is active
