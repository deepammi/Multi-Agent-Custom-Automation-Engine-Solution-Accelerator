# Next Steps to Test HITL Fix

## Immediate Actions

### 1. Restart Frontend (Required)
```bash
# Kill the frontend process
pkill -f "npm run dev"

# Clear npm cache
cd src/frontend
npm cache clean --force

# Restart
npm run dev
```

### 2. Test the Flow

**Step 1: Submit Invoice Task**
- Go to http://localhost:5173
- Type: `Check invoice for accuracy and verify payment terms`
- Click Send

**Step 2: Approve Plan**
- Click "Approve Task Plan" button
- Watch for Invoice Agent message

**Step 3: Check for ClarificationUI**
- Should see:
  - Agent Result section (showing Invoice Agent output)
  - Text input field
  - "Approve" and "Retry" buttons
- Should NOT see error in console

**Step 4: Test Approval**
- Type: `OK`
- Click "Approve" button
- Should see: "Task approved and completed successfully"

**Step 5: Test Revision (Optional)**
- Submit another invoice task
- Approve the plan
- In ClarificationUI, type: `Please double-check the vendor information`
- Click "Retry" button
- Should loop back to Planner

## Expected Console Logs

### ✅ Correct Flow
```
📋 Clarification Message received
✅ Parsed clarification message
WebSocket USER_CLARIFICATION_REQUEST message received (new format)
```

### ❌ Wrong Flow (if you see this)
```
Cannot read properties of null (reading 'question')
```

## Troubleshooting

**If you still see the error:**
1. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Check that frontend restarted properly
3. Check browser console for any other errors

**If ClarificationUI doesn't appear:**
1. Check backend logs for: `🔔 SENDING CLARIFICATION REQUEST`
2. Check browser Network tab for WebSocket messages
3. Verify WebSocket connection is active

**If approval doesn't work:**
1. Check that `handleOnchatSubmit` is being called
2. Verify the answer is being sent to backend
3. Check backend logs for: `Processing clarification for plan`

## Success Criteria

✅ All of these should be true:
- [ ] No error in browser console
- [ ] ClarificationUI appears after Invoice Agent
- [ ] Can type "OK" and approve
- [ ] Task completes successfully
- [ ] Can type revision and loop back

## If Everything Works

Congratulations! HITL is now working. Next:
1. Test with other agents (Closing, Audit)
2. Test multiple revision loops
3. Run property-based tests
4. Mark tasks as complete in tasks.md
