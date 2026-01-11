# Frontend Error Fix - "Unable to create plan"

## Error
Frontend shows: **"Unable to create plan. Please try again"**

## Root Cause
The `ProcessRequestInput` model was missing the `require_hitl` field that the endpoint was trying to access.

## Fixes Applied

### Fix 1: Updated Frontend Endpoint
**File**: `src/frontend/src/api/apiService.tsx`

```typescript
// Changed from old endpoint to workflow-enabled endpoint
PROCESS_REQUEST: '/v3/process_request_v2'
```

### Fix 2: Added Missing Field to Model
**File**: `backend/app/models/plan.py`

```python
class ProcessRequestInput(BaseModel):
    """Input for process_request endpoint."""
    description: str
    session_id: Optional[str] = None
    team_id: Optional[str] = None
    require_hitl: bool = True  # NEW: Added this field
```

## Restart Instructions

### 1. Stop Both Services
Press `Ctrl+C` in both terminal windows

### 2. Restart Backend
```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

**Wait for**: `Application startup complete`

### 3. Restart Frontend (New Terminal)
```bash
cd src/frontend

# Clear cache
rm -rf node_modules/.vite

# Restart
npm run dev
```

**Wait for**: `Local: http://localhost:3001/`

### 4. Clear Browser Cache
- **Mac**: `Cmd+Shift+R`
- **Windows**: `Ctrl+Shift+R`

### 5. Test
1. Open **http://localhost:3001**
2. Enter: **"Verify invoice INV-000001"**
3. Click **Submit**

## Expected Behavior

### Backend Logs Should Show:
```
INFO:     Processing request v2: Verify invoice INV-000001...
INFO:     🚀 Executing task for plan <id>: Verify invoice INV-000001...
INFO:     📋 Detected workflow: invoice_verification
INFO:     📊 Workflow parameters: {'invoice_id': 'INV-000001', 'erp_system': 'zoho', 'crm_system': 'salesforce'}
INFO:     🔄 Executing Invoice Verification workflow...
```

### Frontend Should Show:
1. **System message**: "🚀 Starting task: Verify invoice INV-000001..."
2. **Workflow Engine message**: "🔄 Executing Invoice Verification workflow..."
3. **Progress messages**:
   - "📋 Fetching invoice INV-000001 from Zoho..."
   - "🔍 Querying customer from Salesforce..."
   - "⚖️  Comparing data across systems..."
   - "📊 Generating verification report..."
4. **Final formatted report** with invoice details and verification results

## Verification Tests

### Test 1: Backend Model
```bash
cd backend
python3 test_endpoint_fix.py
```

**Expected**: `✅ Model test passed!`

### Test 2: Integration Tests
```bash
cd backend
python3 test_phase4_integration.py
```

**Expected**: `✅ ALL INTEGRATION TESTS PASSED!`

### Test 3: Direct API Call
```bash
curl -X POST http://localhost:8000/api/v3/process_request_v2 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Verify invoice INV-000001",
    "session_id": "test-session",
    "require_hitl": false
  }'
```

**Expected**: JSON response with `plan_id`, `status`, and `session_id`

### Test 4: Frontend
1. Open http://localhost:3001
2. Enter: "Verify invoice INV-000001"
3. Submit

**Expected**: No error, workflow executes successfully

## Troubleshooting

### Still Getting "Unable to create plan"?

**Check 1: Backend Running?**
```bash
curl http://localhost:8000/health
```
Should return: `{"status": "healthy"}`

**Check 2: Correct Endpoint?**
Open browser DevTools → Network tab
- Should see request to `/api/v3/process_request_v2`
- If you see `/api/v3/process_request` (without _v2), frontend didn't reload

**Check 3: Backend Errors?**
Check backend terminal for error messages

**Check 4: CORS Issues?**
Check browser console for CORS errors

### Backend Shows Error?

**Error: "Field required: require_hitl"**
- Model fix not applied
- Restart backend after applying fix

**Error: "AgentServiceRefactored not found"**
- File `agent_service_refactored.py` missing
- Verify file exists in `backend/app/services/`

**Error: "WorkflowFactory not found"**
- Workflow files missing
- Verify files exist in `backend/app/agents/workflows/`

### Frontend Shows Different Error?

**"Network Error"**
- Backend not running
- Wrong API URL in frontend .env

**"404 Not Found"**
- Endpoint not registered
- Check `routes.py` has `process_request_v2`

**"500 Internal Server Error"**
- Backend error
- Check backend logs for details

## Quick Diagnostic Commands

```bash
# 1. Check backend health
curl http://localhost:8000/health

# 2. Test endpoint directly
curl -X POST http://localhost:8000/api/v3/process_request_v2 \
  -H "Content-Type: application/json" \
  -d '{"description": "test", "require_hitl": false}'

# 3. Check if model is correct
cd backend
python3 -c "from app.models.plan import ProcessRequestInput; print(ProcessRequestInput.model_fields.keys())"

# Should show: dict_keys(['description', 'session_id', 'team_id', 'require_hitl'])

# 4. Run integration tests
python3 test_phase4_integration.py
```

## Files Changed

1. ✅ `src/frontend/src/api/apiService.tsx` - Updated endpoint
2. ✅ `backend/app/models/plan.py` - Added `require_hitl` field

## Success Checklist

- [ ] Backend restarts without errors
- [ ] Frontend restarts without errors
- [ ] Browser cache cleared
- [ ] Test endpoint returns valid response
- [ ] Integration tests pass
- [ ] Frontend submits task successfully
- [ ] Backend logs show workflow detection
- [ ] Frontend displays workflow messages

## Summary

**Two fixes were needed:**
1. Frontend using wrong endpoint (fixed)
2. Backend model missing field (fixed)

**After restart, everything should work!**

---

**Next**: Test with "Verify invoice INV-000001" and you should see the workflow system in action! 🎉
