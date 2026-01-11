# Troubleshooting Workflow Integration

## Issue: Frontend Not Using Workflow Routing

### Problem
When entering "Verify invoice INV-000001" in the frontend, it routes to the old Invoice Agent instead of the new workflow system.

### Root Cause
The frontend was using the old `/api/v3/process_request` endpoint instead of the new `/api/v3/process_request_v2` endpoint that includes workflow support.

### Solution Applied

**File Changed**: `src/frontend/src/api/apiService.tsx`

```typescript
// OLD (before fix)
const API_ENDPOINTS = {
    PROCESS_REQUEST: '/v3/process_request',  // Old endpoint
    ...
};

// NEW (after fix)
const API_ENDPOINTS = {
    PROCESS_REQUEST: '/v3/process_request_v2',  // Workflow-enabled endpoint
    ...
};
```

## Verification Steps

### Step 1: Restart Frontend

```bash
# Stop the frontend (Ctrl+C)
cd src/frontend

# Clear cache and restart
rm -rf node_modules/.vite
npm run dev
```

The frontend should now be running on **http://localhost:3001** (not 5173).

### Step 2: Verify Backend is Running

```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

If backend is not running:

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

### Step 3: Test Workflow Endpoint

```bash
# Test the workflow endpoint directly
curl -X POST http://localhost:8000/api/v3/process_request_v2 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Verify invoice INV-000001",
    "session_id": "test-session",
    "require_hitl": false
  }'

# Should return: {"plan_id": "...", "status": "pending", "session_id": "..."}
```

### Step 4: Check Backend Logs

Look for these log messages when you submit a task:

```
🚀 Executing task for plan <plan_id>: Verify invoice INV-000001...
📋 Detected workflow: invoice_verification
📊 Workflow parameters: {'invoice_id': 'INV-000001', 'erp_system': 'zoho', 'crm_system': 'salesforce'}
🔄 Executing Invoice Verification workflow...
```

If you see these logs, the workflow system is working!

### Step 5: Test in Frontend

1. Open **http://localhost:3001** (not 5173)
2. Enter: "Verify invoice INV-000001"
3. Click Submit

**Expected Behavior:**
- You should see workflow-specific messages
- Progress updates from the workflow
- Formatted invoice verification report

**If Still Using Old Agent:**
- Check browser console for errors
- Verify frontend restarted after code change
- Clear browser cache (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)

## Common Issues

### Issue 1: Port 5173 vs 3001

**Problem**: Documentation mentions port 5173, but frontend runs on 3001.

**Solution**: Always use **http://localhost:3001** for your frontend.

**Why**: Your Vite configuration is set to use port 3001.

### Issue 2: Frontend Shows Old Behavior

**Problem**: Frontend still routes to old agent after code change.

**Solutions**:
1. **Hard refresh browser**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. **Clear Vite cache**:
   ```bash
   cd src/frontend
   rm -rf node_modules/.vite
   npm run dev
   ```
3. **Check browser console** for API errors
4. **Verify API endpoint** in Network tab (should be `/v3/process_request_v2`)

### Issue 3: Backend Not Detecting Workflow

**Problem**: Backend logs show regular agent routing instead of workflow.

**Check**:
1. Verify `agent_service_refactored.py` exists
2. Check detection patterns in `detect_workflow()`
3. Test detection directly:
   ```bash
   cd backend
   python3 test_phase4_integration.py
   ```

### Issue 4: 404 Error on /v3/process_request_v2

**Problem**: API returns 404 for the new endpoint.

**Solution**: Verify the endpoint is registered in `routes.py`:

```bash
cd backend
grep -n "process_request_v2" app/api/v3/routes.py
```

Should show the endpoint definition around line 450.

### Issue 5: CORS Errors

**Problem**: Browser shows CORS errors.

**Solution**: Check backend CORS configuration in `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Should include 3001
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Testing Workflow Detection

### Test 1: Direct Backend Test

```bash
cd backend
python3 test_phase4_integration.py
```

**Expected Output:**
```
✅ PASS: Workflow Detection
✅ PASS: Parameter Extraction
✅ PASS: Workflow Listing
✅ PASS: Direct Workflow Execution
✅ PASS: Integration Scenarios
```

### Test 2: API Test

```bash
cd backend
python3 test_phase4_api.py
```

**Expected Output:**
```
✅ PASS: Workflow Listing API
✅ PASS: Workflow Execution API
✅ PASS: Smart Routing API
```

### Test 3: Manual API Test

```bash
# Test workflow detection
curl -X POST http://localhost:8000/api/v3/process_request_v2 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Verify invoice INV-000001",
    "session_id": "test",
    "require_hitl": false
  }'

# Check the plan
curl "http://localhost:8000/api/v3/plan?plan_id=<plan_id_from_above>"
```

## Debugging Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3001
- [ ] Frontend using `/v3/process_request_v2` endpoint
- [ ] Browser cache cleared
- [ ] Backend logs show workflow detection
- [ ] Integration tests passing
- [ ] API tests passing

## Quick Fix Commands

```bash
# 1. Stop everything
# Press Ctrl+C in both terminal windows

# 2. Restart backend
cd backend
python3 -m uvicorn app.main:app --reload --port 8000

# 3. Restart frontend (in new terminal)
cd src/frontend
rm -rf node_modules/.vite
npm run dev

# 4. Test
# Open http://localhost:3001
# Enter: "Verify invoice INV-000001"
# Submit and check logs
```

## Verification Checklist

After applying the fix, verify:

✅ Frontend uses `/v3/process_request_v2` endpoint
✅ Backend logs show "Detected workflow: invoice_verification"
✅ Frontend displays workflow-specific messages
✅ Invoice verification report is formatted correctly
✅ Other workflows also work (payment tracking, customer 360)

## Success Indicators

You'll know it's working when you see:

1. **In Backend Logs:**
   ```
   📋 Detected workflow: invoice_verification
   🔄 Executing Invoice Verification workflow...
   ```

2. **In Frontend:**
   - Workflow Engine message
   - Progress updates
   - Formatted verification report

3. **In Browser Network Tab:**
   - Request to `/api/v3/process_request_v2`
   - Response includes workflow execution

## Still Having Issues?

1. **Check backend logs** for errors
2. **Check browser console** for errors
3. **Run integration tests** to verify backend
4. **Test API directly** with curl
5. **Verify file changes** were saved

## Contact Points

- Backend code: `backend/app/services/agent_service_refactored.py`
- Frontend code: `src/frontend/src/api/apiService.tsx`
- API routes: `backend/app/api/v3/routes.py`
- Tests: `backend/test_phase4_integration.py`

---

**Fix Applied**: Frontend now uses `/v3/process_request_v2` endpoint with workflow support.

**Next Step**: Restart frontend and test with "Verify invoice INV-000001"
