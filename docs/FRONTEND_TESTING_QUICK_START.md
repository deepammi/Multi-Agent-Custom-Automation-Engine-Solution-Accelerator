# Frontend Testing Quick Start

Get started testing workflows in the frontend in 5 minutes.

## 1. Start Services (2 minutes)

### Terminal 1: Backend
```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

Wait for: `Application startup complete.`

### Terminal 2: Frontend
```bash
cd src/frontend
npm run dev
```

Wait for: `Local: http://localhost:5173/`

## 2. Open Browser (30 seconds)

1. Open browser
2. Go to: `http://localhost:5173`
3. Press `F12` to open DevTools (optional but recommended)

## 3. Test Workflows (2 minutes)

### Test 1: Invoice Verification (30 seconds)

**Type:**
```
Verify invoice INV-000001
```

**Press:** Enter or click Submit

**Expected:**
- ✅ See "Starting task..." message
- ✅ See "Executing Invoice Verification workflow..." message
- ✅ See 4 progress steps
- ✅ See final verification report with invoice details

### Test 2: Payment Tracking (30 seconds)

**Type:**
```
Track payment for INV-000002
```

**Press:** Enter or click Submit

**Expected:**
- ✅ See workflow execution messages
- ✅ See payment status report
- ✅ See payment confirmation details

### Test 3: Customer 360 (30 seconds)

**Type:**
```
Customer 360 view for University of Chicago
```

**Press:** Enter or click Submit

**Expected:**
- ✅ See workflow execution messages
- ✅ See comprehensive customer profile
- ✅ See data from CRM, ERP, and Accounting

## 4. Verify Success (30 seconds)

### Check Frontend
- [ ] All messages appeared in real-time
- [ ] Final results are formatted nicely
- [ ] No error messages shown

### Check DevTools (if open)
- [ ] Console: No red errors
- [ ] Network: All requests show 200 OK
- [ ] WebSocket: Shows "101 Switching Protocols"

## Done! ✅

You've successfully tested all three workflows!

## Quick Troubleshooting

### Problem: Nothing happens when I submit

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### Problem: Error messages appear

**Solution:**
1. Check backend terminal for errors
2. Restart backend: `Ctrl+C` then run command again
3. Refresh browser page

### Problem: Messages appear all at once

**Solution:**
- This is normal for fast workflows
- Check DevTools → Network → WS to see real-time messages

## Next Steps

### Learn More
- [Complete Frontend Testing Guide](WORKFLOW_FRONTEND_TESTING_GUIDE.md)
- [Visual Testing Guide](WORKFLOW_FRONTEND_TESTING_VISUAL_GUIDE.md)
- [Workflow Architecture](WORKFLOW_ARCHITECTURE_GUIDE.md)

### Test More
- Try different invoice IDs: `INV-123456`
- Try different customer names: `Acme Corp`, `Microsoft`
- Try invalid inputs to see error handling

### Advanced Testing
- Open DevTools → Network tab
- Watch WebSocket messages
- Use Console to run test scripts

## Test Commands Reference

### Quick Tests
```javascript
// In browser console (F12 → Console)

// Test 1: List workflows
fetch('http://localhost:8000/api/v3/workflows')
  .then(r => r.json())
  .then(data => console.table(data))

// Test 2: Execute workflow
fetch('http://localhost:8000/api/v3/process_request_v2', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    description: 'Verify invoice INV-000001',
    session_id: 'test-' + Date.now(),
    require_hitl: false
  })
}).then(r => r.json()).then(console.log)
```

## Summary

**Time to test:** 5 minutes
**Workflows tested:** 3
**Commands needed:** 2 (start backend, start frontend)
**Browser needed:** Any modern browser

**Success criteria:**
- ✅ All 3 workflows execute
- ✅ Real-time messages appear
- ✅ Final results are formatted
- ✅ No errors in console

---

**Start testing now:** Open `http://localhost:5173` and type `"Verify invoice INV-000001"`
