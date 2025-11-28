# HITL Routing Debugging Plan

## Problem
The system runs the Invoice Agent successfully but doesn't route to HITL. It completes the task instead.

## Root Cause Analysis
The issue is likely in the `resume_after_approval` method. The `require_hitl` flag is being checked, but it's defaulting to `True`. However, the code path might be hitting the "HITL skipped" branch instead of the HITL routing branch.

## Simple Test Plan

### Step 1: Add Debug Logging
Add logging to identify which code path is being executed:

**File: `backend/app/services/agent_service.py`**

In the `resume_after_approval` method, add this debug log right after getting `require_hitl`:

```python
require_hitl = execution_state.get("require_hitl", True)
logger.info(f"🔍 DEBUG: require_hitl={require_hitl} for plan {plan_id}")
```

### Step 2: Check the Execution State
Add logging to see what's stored in execution_state:

```python
logger.info(f"🔍 DEBUG: execution_state keys: {execution_state.keys()}")
logger.info(f"🔍 DEBUG: execution_state content: {execution_state}")
```

### Step 3: Verify HITL Agent Node is Being Called
Add logging in the HITL routing section:

```python
# Route to HITL agent
logger.info(f"🔍 DEBUG: Routing to HITL agent for plan {plan_id}")
hitl_state = {**state, **result}
logger.info(f"🔍 DEBUG: hitl_state keys: {hitl_state.keys()}")
hitl_result = hitl_agent_node(hitl_state)
logger.info(f"🔍 DEBUG: hitl_result: {hitl_result}")
```

### Step 4: Test with Invoice Task
1. Start backend with logging enabled
2. Submit task: "Check invoice for accuracy"
3. Approve the plan
4. Watch the logs for the debug messages

### Step 5: Expected Log Output
You should see:
```
🔍 DEBUG: require_hitl=True for plan {plan_id}
🔍 DEBUG: Routing to HITL agent for plan {plan_id}
🔍 DEBUG: hitl_result: {...}
🔔 SENDING CLARIFICATION REQUEST for plan {plan_id}
```

If you see "HITL skipped" instead, then `require_hitl` is False.

## Quick Fix if require_hitl is False

If the issue is that `require_hitl` is not being set properly:

1. Check that `execute_task` is being called with `require_hitl=True` (default)
2. Verify that `execution_state["require_hitl"]` is being set in `execute_task`
3. Make sure the state is being preserved across the approval flow

## Frontend Verification

Once backend is routing to HITL:
1. Check browser console for "Clarification Message" log
2. Verify `clarificationMessage` state is being set in PlanPage
3. Check that ClarificationUI component is rendering

## Expected Flow

```
User Task
    ↓
Planner Agent (shows plan)
    ↓
User Approves Plan
    ↓
Invoice Agent (processes)
    ↓
HITL Agent (requests approval/revision) ← THIS SHOULD HAPPEN
    ↓
ClarificationUI appears on frontend
    ↓
User approves or provides revision
```

## Commands to Run

### Terminal 1: Backend with Debug Logging
```bash
cd backend
python -m uvicorn app.main:app --reload --log-level debug
```

### Terminal 2: Frontend
```bash
cd src/frontend
npm run dev
```

### Terminal 3: Monitor Logs
```bash
# Watch for HITL-related logs
tail -f backend.log | grep -i "hitl\|clarification\|routing"
```

## Next Steps After Debugging

1. Once you identify the issue, share the debug logs
2. We'll fix the root cause
3. Re-test the complete flow
4. Implement property-based tests for HITL routing
