# HITL Error Fix Summary

## Problem
The frontend was throwing an error: `Cannot read properties of null (reading 'question')`

This happened because:
1. Backend sends: `{ type: "user_clarification_request", data: { question: "...", request_id: "...", agent_result: "..." } }`
2. WebSocket service was trying to parse it as a string format
3. Parser returned `null`
4. Frontend tried to access `clarificationMessage.data.question` on a null object

## Root Cause
The `parseUserClarificationRequest` function was designed for an old string format, but the backend is now sending proper JSON objects.

## Solution Applied

### 1. Updated WebSocket Service (`src/frontend/src/services/WebSocketService.tsx`)
- Added check for new JSON format (direct properties)
- Falls back to old string parsing if needed
- Now properly emits the message data

### 2. Updated PlanPage (`src/frontend/src/pages/PlanPage.tsx`)
- Added null-safe property access
- Handles both old and new message formats
- Properly extracts `question`, `request_id`, and `agent_result`
- Stores clarification message with all required fields

### 3. Updated Type Definition (`src/frontend/src/models/messages.tsx`)
- Added optional `agent_result` field to `ParsedUserClarification` interface
- Now matches the backend message structure

## Files Changed
1. `src/frontend/src/services/WebSocketService.tsx` - Line 225-233
2. `src/frontend/src/pages/PlanPage.tsx` - Line 296-340
3. `src/frontend/src/models/messages.tsx` - Line 150-154

## Testing the Fix

1. **Restart frontend** (clear cache):
   ```bash
   pkill -f "npm run dev"
   cd src/frontend
   npm run dev
   ```

2. **Submit invoice task**: "Check invoice for accuracy"

3. **Approve the plan**

4. **Expected result**:
   - ✅ No error in console
   - ✅ ClarificationUI appears
   - ✅ Shows agent result
   - ✅ Shows input field for approval/revision

## Verification

Check browser console for:
```
✅ Clarification Message received
✅ Parsed clarification message
```

No errors should appear.

## Next Steps

1. Test approval flow (type "OK")
2. Test revision flow (type feedback)
3. Test multiple revisions
4. Run property-based tests
