# Quick Fix Guide - Workflow Integration

## The Fix

✅ **Fixed**: Frontend now uses the workflow-enabled endpoint

**File Changed**: `src/frontend/src/api/apiService.tsx`
- Changed from `/v3/process_request` → `/v3/process_request_v2`

## Restart Instructions

### 1. Stop Everything
Press `Ctrl+C` in both terminal windows (backend and frontend)

### 2. Restart Backend
```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

**Wait for**: `Application startup complete`

### 3. Restart Frontend (New Terminal)
```bash
cd src/frontend

# Clear Vite cache
rm -rf node_modules/.vite

# Start frontend
npm run dev
```

**Wait for**: `Local: http://localhost:3001/`

### 4. Test It!

1. Open **http://localhost:3001** in your browser
2. Clear browser cache: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
3. Enter: **"Verify invoice INV-000001"**
4. Click **Submit**

## What You Should See

### In Backend Terminal:
```
🚀 Executing task for plan <id>: Verify invoice INV-000001...
📋 Detected workflow: invoice_verification
📊 Workflow parameters: {'invoice_id': 'INV-000001', ...}
🔄 Executing Invoice Verification workflow...
```

### In Frontend:
- Message from "Workflow Engine"
- Progress updates
- Formatted invoice verification report with:
  - Invoice Details
  - Verification Results
  - Matches and Discrepancies

## Quick Test Commands

### Test Backend Directly:
```bash
curl -X POST http://localhost:8000/api/v3/process_request_v2 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Verify invoice INV-000001",
    "session_id": "test",
    "require_hitl": false
  }'
```

### Run Integration Tests:
```bash
cd backend
python3 test_phase4_integration.py
```

Should show: `✅ ALL INTEGRATION TESTS PASSED!`

## Other Workflows to Test

Once the first one works, try these:

1. **Payment Tracking**: "Track payment for INV-000002"
2. **Customer 360**: "Customer 360 view for Acme Corp"
3. **Regular Agent**: "List Zoho invoices" (should use old agent)

## Troubleshooting

### Still seeing old agent?
1. Hard refresh browser: `Cmd+Shift+R` or `Ctrl+Shift+R`
2. Check browser console for errors
3. Verify Network tab shows `/v3/process_request_v2`

### Backend not detecting workflow?
1. Check backend logs for "Detected workflow" message
2. Run: `python3 test_phase4_integration.py`
3. Verify `agent_service_refactored.py` exists

### 404 Error?
1. Verify backend is running on port 8000
2. Check `routes.py` has `process_request_v2` endpoint
3. Restart backend

## Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3001
- [ ] Browser cache cleared
- [ ] Backend logs show "Detected workflow"
- [ ] Frontend shows workflow messages
- [ ] Verification report is formatted

---

**That's it!** The fix is applied. Just restart both services and test.
