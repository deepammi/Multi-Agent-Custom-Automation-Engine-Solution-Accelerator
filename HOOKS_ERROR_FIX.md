# React Hooks Error Fix

## Problem
When requesting a retry, the application threw an error:
```
Error: Rendered more hooks than during the previous render.
```

## Root Cause
The error occurred because:
1. We were mapping over `approvalRequestHistory` array in PlanChat
2. Each iteration called `renderPlanResponse()` which uses React hooks (`useState`)
3. The number of hook calls changed based on the history length
4. This violates React's rules of hooks (hooks must be called the same number of times in every render)

## Solution
Created a new component `ApprovalRequestHistory` that:
1. Wraps the mapping logic in a proper React component
2. Ensures hooks are called consistently
3. Displays all approval requests in chronological order
4. Only shows approval buttons on the latest request

## Files Changed

### 1. Created: `src/frontend/src/components/content/ApprovalRequestHistory.tsx`
- New component to handle displaying approval request history
- Maps over approval requests and renders each one
- Properly manages hook calls

### 2. Updated: `src/frontend/src/components/content/PlanChat.tsx`
- Imported the new `ApprovalRequestHistory` component
- Replaced inline mapping with component usage
- Cleaner and more maintainable code

## How It Works

**Before (Broken):**
```jsx
{approvalRequestHistory.map((approvalRequest, index) => (
  <div key={`approval-${index}`}>
    {renderPlanResponse(...)}  // ❌ Variable number of hook calls
  </div>
))}
```

**After (Fixed):**
```jsx
{approvalRequestHistory.length > 0 && (
  <ApprovalRequestHistory
    approvalRequestHistory={approvalRequestHistory}
    {...props}
  />
)}
```

The `ApprovalRequestHistory` component handles the mapping internally, ensuring hooks are called consistently.

## Testing

1. **Restart frontend:**
   ```bash
   pkill -f "npm run dev"
   cd src/frontend
   npm run dev
   ```

2. **Test the flow:**
   - Submit invoice task
   - Approve plan
   - Request retry (provide feedback)
   - Should see all approval requests in order
   - No error should appear

3. **Expected behavior:**
   - First Planner message appears
   - Invoice Agent message appears
   - ClarificationUI appears
   - User provides revision
   - Second Planner message appears BELOW the first one
   - All messages in chronological order
   - No React errors

## Success Criteria

✅ All of these should be true:
- [ ] No "Rendered more hooks" error
- [ ] All approval requests display in order
- [ ] Approval buttons only on latest request
- [ ] Can retry multiple times
- [ ] Messages appear chronologically
