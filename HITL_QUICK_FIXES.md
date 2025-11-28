# HITL Quick Fixes - Most Likely Issues

## Issue 1: Backend Not Reloaded Properly ⭐ MOST LIKELY

**Symptoms:**
- HITL routing not happening
- Task completes after Invoice Agent
- No clarification request sent

**Fix:**
```bash
# Kill the backend process completely
pkill -9 -f "uvicorn"
pkill -9 -f "python"

# Clear Python cache
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Start fresh
cd backend
python -m uvicorn app.main:app --reload
```

## Issue 2: require_hitl Flag Not Being Passed

**Symptoms:**
- Logs show `require_hitl=False`
- HITL is being skipped

**Check:**
In `backend/app/services/agent_service.py`, verify:

```python
# In execute_task method
async def execute_task(plan_id: str, session_id: str, task_description: str, require_hitl: bool = True):
    # ✅ Should have require_hitl parameter with default True
    
    # In the execution state storage
    AgentService._pending_executions[plan_id] = {
        ...
        "require_hitl": require_hitl  # ✅ Should be stored
    }
```

## Issue 3: Old Code Still Running

**Symptoms:**
- Changes don't take effect
- Logs don't show debug messages

**Fix:**
```bash
# Check if old process is still running
ps aux | grep uvicorn
ps aux | grep python

# Kill all Python processes
pkill -9 python

# Restart
cd backend
python -m uvicorn app.main:app --reload
```

## Issue 4: Frontend Not Receiving Clarification Message

**Symptoms:**
- Backend sends clarification request
- Frontend doesn't show ClarificationUI
- No "Clarification Message" in browser console

**Check:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for: `📋 Clarification Message received`
4. If not there, check Network tab for WebSocket messages

**Fix:**
```bash
# Restart frontend
pkill -f "npm run dev"
cd src/frontend
npm run dev
```

## Issue 5: WebSocket Connection Issue

**Symptoms:**
- Messages not being received
- WebSocket shows as disconnected

**Check:**
1. Open browser DevTools
2. Go to Network tab
3. Filter for "WS" (WebSocket)
4. Should see connection to `/api/v3/socket/{plan_id}`

**Fix:**
```bash
# Restart both backend and frontend
pkill -f "uvicorn"
pkill -f "npm run dev"

# Start backend first
cd backend
python -m uvicorn app.main:app --reload

# Wait 2 seconds, then start frontend
sleep 2
cd src/frontend
npm run dev
```

## Quick Diagnostic Script

Run this to check if the code is correct:

```bash
# Check if hitl_agent_node is defined
grep -n "def hitl_agent_node" backend/app/agents/nodes.py

# Check if ExecutionContext is defined
grep -n "class ExecutionContext" backend/app/services/agent_service.py

# Check if handle_user_clarification is defined
grep -n "def handle_user_clarification" backend/app/services/agent_service.py

# Check if ClarificationUI is imported
grep -n "import ClarificationUI" src/frontend/src/components/content/PlanChat.tsx
```

All should return results. If any don't, the code wasn't saved properly.

## Nuclear Option: Full Reset

If nothing works:

```bash
# Kill everything
pkill -9 python
pkill -9 node
pkill -9 npm

# Clear all caches
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete

# Reinstall dependencies
cd backend
pip install -r requirements.txt

cd ../src/frontend
npm install

# Start fresh
cd ../../backend
python -m uvicorn app.main:app --reload
```

## Verification Commands

After restart, verify the code is loaded:

```bash
# Check backend has the new code
python -c "from app.services.agent_service import ExecutionContext; print('✅ ExecutionContext loaded')"

# Check frontend has the new component
grep -q "ClarificationUI" src/frontend/src/components/content/PlanChat.tsx && echo "✅ ClarificationUI imported"
```

## Expected Behavior After Fix

1. Submit invoice task
2. Approve plan
3. See Invoice Agent message
4. See ClarificationUI component
5. Type "OK" and click Approve
6. See completion message

If you see all 5 steps, HITL is working! 🎉
