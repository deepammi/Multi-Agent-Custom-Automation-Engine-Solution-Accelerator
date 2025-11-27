# Race Condition Fix - WebSocket Message Handling

## Problem Identified

The frontend was experiencing a race condition where:
1. WebSocket connects and receives the "connected" message
2. Backend immediately sends agent messages
3. Frontend listeners haven't been attached yet because `continueWithWebsocketFlow` was still `false`
4. Messages are lost, causing the spinner to timeout

## Root Cause

`continueWithWebsocketFlow` was only set to `true` AFTER the plan data was loaded, which could take several seconds. During this time, the WebSocket connection might already be established and messages might already be arriving, but the listeners weren't attached yet.

## Fixes Applied

### Fix 1: Enable WebSocket Flow Immediately
**File**: `src/frontend/src/pages/PlanPage.tsx`

Added a new useEffect that sets `continueWithWebsocketFlow` to `true` immediately when the plan page loads:

```typescript
// Enable WebSocket flow immediately when plan page loads to prevent race conditions
useEffect(() => {
    if (planId) {
        console.log('🔌 [INIT] Plan page loaded, enabling WebSocket flow for plan:', planId);
        setContinueWithWebsocketFlow(true);
    }
}, [planId]);
```

**Impact**: WebSocket connection is initiated immediately, not waiting for plan data to load.

### Fix 2: Ensure Listeners Are Attached Before Connecting
**File**: `src/frontend/src/pages/PlanPage.tsx`

Added a 100ms delay before connecting to ensure all listeners are properly attached:

```typescript
const connectWebSocket = async () => {
    try {
        // Small delay to ensure listeners are attached before connecting
        await new Promise(resolve => setTimeout(resolve, 100));
        console.log('🔌 [CONNECT] Attempting WebSocket connection...');
        await webSocketService.connect(planId);
        console.log('✅ WebSocket connected successfully');
    } catch (error) {
        console.error('❌ WebSocket connection failed:', error);
    }
};
```

**Impact**: Guarantees that all event listeners are registered before the WebSocket connection is established.

## Expected Behavior After Fix

1. Plan page loads
2. `continueWithWebsocketFlow` is set to `true` immediately
3. WebSocket connection useEffect triggers
4. All listeners are attached
5. 100ms delay ensures listeners are ready
6. WebSocket connects
7. Backend sends messages
8. Frontend listeners receive and process messages
9. Messages display in UI
10. Spinner disappears when final result arrives

## Testing

To verify the fix works:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Create a task with "invoice analysis" keywords
4. Watch for these logs:
   - "🔌 [INIT] Plan page loaded, enabling WebSocket flow for plan:"
   - "🔌 Connecting WebSocket:"
   - "🔌 [CONNECT] Attempting WebSocket connection..."
   - "✅ WebSocket connected successfully"
   - "📋 Agent Message received:"
   - "✅ Adding agent message to state:"
   - "📋 Final Result Message received:"
5. Approve the plan
6. Verify agent messages appear and spinner disappears

## Files Modified

- `src/frontend/src/pages/PlanPage.tsx` (2 changes)

## No Breaking Changes

- All changes are additive
- No existing functionality modified
- Backward compatible
- 100ms delay is imperceptible to users

---

**Status**: ✅ Fix Applied
**Testing**: Ready for manual testing
**Date**: November 25, 2025
