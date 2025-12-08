# Phase 3: Frontend Testing Guide

## Goal
Test Zoho agent through the UI with mock data to verify end-to-end integration.

---

## Prerequisites

✅ Phase 1 Complete: Mock service working
✅ Phase 2 Complete: Agent integration working

---

## Step 1: Start Backend Server

```bash
cd backend
python3 -m app.main
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 2: Start Frontend (if not running)

```bash
cd src/frontend
npm run dev
```

**Expected Output:**
```
VITE v7.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

## Step 3: Test Queries

Open your browser to `http://localhost:5173` and try these queries:

### Test 1: List All Invoices
**Query:** `Show me recent invoices from Zoho`

**Expected Result:**
- Planner routes to Zoho agent
- Displays list of mock invoices
- Shows invoice numbers, customers, amounts, status
- Includes summary totals

### Test 2: List Customers
**Query:** `Show me Zoho customers`

**Expected Result:**
- Displays list of mock customers
- Shows customer names, emails, phone numbers
- Includes outstanding balances

### Test 3: Filter by Status
**Query:** `Show me unpaid invoices from Zoho`

**Expected Result:**
- Displays only unpaid invoices
- Filters correctly by status
- Shows balance due amounts

### Test 4: Get Invoice Details
**Query:** `Show me details for invoice INV-001`

**Expected Result:**
- Displays detailed invoice information
- Shows line items
- Includes customer and payment info

### Test 5: Overdue Invoices
**Query:** `List overdue invoices from Zoho`

**Expected Result:**
- Displays only overdue invoices
- Shows warning indicators
- Includes due dates

---

## Step 4: Verify UI Elements

Check that the following work correctly:

- [ ] Task submission works
- [ ] Planner message appears
- [ ] Zoho agent messages stream in real-time
- [ ] Mock data displays with proper formatting
- [ ] Status emojis show correctly (✅ 📤 ⚠️)
- [ ] Amounts format with currency symbols
- [ ] No errors in browser console
- [ ] WebSocket connection stable

---

## Step 5: Test Error Handling

### Test Invalid Query
**Query:** `Show me invoice XYZ-999 from Zoho`

**Expected Result:**
- Agent responds gracefully
- Shows "Invoice not found" message
- No crashes or errors

---

## Success Criteria

✅ All test queries return expected results
✅ UI displays mock data correctly
✅ Real-time streaming works
✅ No console errors
✅ Agent routing works correctly
✅ Formatting and emojis display properly

---

## Troubleshooting

### Issue: "Connection refused"
**Solution:** Make sure backend is running on port 8000

### Issue: "Agent not responding"
**Solution:** Check backend logs for errors

### Issue: "Planner routes to wrong agent"
**Solution:** Make sure query includes "Zoho" keyword

### Issue: "No data displays"
**Solution:** Check browser console for errors

---

## Phase 3 Complete!

Once all tests pass, you're ready for:
- **Phase 4:** Create Zoho MCP Server
- **Phase 5:** MCP Client Integration
- **Phase 6:** OAuth Integration (when ready)

---

## Next Steps

After verifying frontend works:
1. Take screenshots of working UI (optional)
2. Note any UI improvements needed
3. Proceed to Phase 4: MCP Server creation

**Ready to move to Phase 4?** Let me know when frontend testing is complete!
