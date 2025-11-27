# Debugging: Approval Flow Hanging Issue

## Problem Summary

When a user approves a plan, the frontend shows a spinning wheel but doesn't display the specialized agent's response. The backend is working correctly (verified with debug script), but the frontend isn't displaying the messages.

## Root Cause Analysis

### Backend Status: ✅ WORKING
- Planner executes and sends approval request
- User approves via REST API
- Specialized agent (Invoice) executes
- Messages are sent via WebSocket
- Plan status updates to "completed"

**Verified with**: `debug_approval_flow.py` - All messages received correctly

### Frontend Status: ⚠️ ISSUE IDENTIFIED

The issue is in `src/frontend/src/pages/PlanPage.tsx`:

1. **After approval is sent** (line 516-530):
   - `setShowProcessingPlanSpinner(true)` is set
   - `setShowApprovalButtons(false)` is set
   - But the component doesn't properly wait for or display incoming messages

2. **WebSocket listeners are set up** (line 369-382):
   - AGENT_MESSAGE listener exists
   - Should receive messages after approval
   - But messages might not be displaying due to UI state issues

3. **Potential Issues**:
   - The spinner might be covering the messages
   - The `planData` state might not be updating
   - The `agentMessages` state might not be triggering re-renders
   - The WebSocket connection might be closing after approval

## Solution: Step-by-Step Fix

### Step 1: Verify WebSocket Connection Stays Open

**File**: `src/frontend/src/pages/PlanPage.tsx`

**Issue**: After approval, the WebSocket connection might be closing or not properly listening.

**Fix**: Add logging to verify connection status after approval.

**Location**: In `handleApprovePlan` function (around line 510)

```typescript
const handleApprovePlan = useCallback(async () => {
    if (!planApprovalRequest) return;

    setProcessingApproval(true);
    let id = showToast("Submitting Approval", "progress");
    try {
        console.log('🔍 [DEBUG] Approval being sent for plan:', planApprovalRequest.id);
        console.log('🔍 [DEBUG] WebSocket connected:', wsConnected);
        
        await apiService.approvePlan({
            m_plan_id: planApprovalRequest.id,
            plan_id: planData?.plan?.id,
            approved: true,
            feedback: 'Plan approved by user'
        });

        dismissToast(id);
        setShowProcessingPlanSpinner(true);
        setShowApprovalButtons(false);
        
        console.log('🔍 [DEBUG] Approval sent, waiting for agent messages...');
        console.log('🔍 [DEBUG] Current agent messages:', agentMessages.length);

    } catch (error) {
        dismissToast(id);
        showToast("Failed to submit approval", "error");
        console.error('❌ Failed to approve plan:', error);
    } finally {
        setProcessingApproval(false);
    }
}, [planApprovalRequest, planData, setProcessingApproval, wsConnected, agentMessages]);
```

### Step 2: Ensure Agent Messages Display

**File**: `src/frontend/src/pages/PlanPage.tsx`

**Issue**: Agent messages might be received but not displayed.

**Fix**: Update the AGENT_MESSAGE listener to ensure messages are displayed.

**Location**: AGENT_MESSAGE listener (around line 369)

```typescript
useEffect(() => {
    const unsubscribe = webSocketService.on(WebsocketMessageType.AGENT_MESSAGE, (agentMessage: any) => {
        console.log('📋 Agent Message received:', agentMessage);
        console.log('📋 Current plan data:', planData);
        
        const agentMessageData = agentMessage.data as AgentMessageData;
        if (agentMessageData) {
            console.log('✅ Adding agent message to state:', agentMessageData.agent_name);
            
            agentMessageData.content = PlanDataService.simplifyHumanClarification(agentMessageData?.content);
            setAgentMessages(prev => {
                const updated = [...prev, agentMessageData];
                console.log('📊 Agent messages count:', updated.length);
                return updated;
            });
            
            // Keep spinner visible while processing
            setShowProcessingPlanSpinner(true);
            scrollToBottom();
            processAgentMessage(agentMessageData, planData);
        } else {
            console.warn('⚠️ No agent message data found');
        }
    });

    return () => unsubscribe();
}, [scrollToBottom, planData, processAgentMessage]);
```

### Step 3: Handle Final Result Message

**File**: `src/frontend/src/pages/PlanPage.tsx`

**Issue**: Final result message might not be properly handled.

**Fix**: Update the FINAL_RESULT_MESSAGE listener.

**Location**: FINAL_RESULT_MESSAGE listener (around line 321)

```typescript
useEffect(() => {
    const unsubscribe = webSocketService.on(WebsocketMessageType.FINAL_RESULT_MESSAGE, (finalMessage: any) => {
        console.log('📋 Final Result Message received:', finalMessage);
        
        if (!finalMessage) {
            console.warn('⚠️ No final message data');
            return;
        }
        
        const finalMessageData = finalMessage.data as FinalMessage;
        if (finalMessageData) {
            console.log('✅ Final result received, hiding spinner');
            
            // Add final message to agent messages
            const finalAgentMessage: AgentMessageData = {
                agent_name: 'System',
                agent_type: AgentType.HUMAN,
                content: finalMessageData.content,
                timestamp: new Date().toISOString(),
                status: finalMessageData.status
            };
            
            setAgentMessages(prev => [...prev, finalAgentMessage]);
            setShowProcessingPlanSpinner(false);  // Hide spinner when done
            scrollToBottom();
        }
    });

    return () => unsubscribe();
}, [scrollToBottom]);
```

### Step 4: Add Timeout Protection

**File**: `src/frontend/src/pages/PlanPage.tsx`

**Issue**: If messages don't arrive, spinner spins forever.

**Fix**: Add a timeout to hide spinner after 30 seconds.

**Location**: After `handleApprovePlan` function

```typescript
// Add timeout to prevent infinite spinner
useEffect(() => {
    if (showProcessingPlanSpinner) {
        const timeout = setTimeout(() => {
            console.warn('⚠️ Spinner timeout - hiding spinner after 30 seconds');
            setShowProcessingPlanSpinner(false);
        }, 30000);
        
        return () => clearTimeout(timeout);
    }
}, [showProcessingPlanSpinner]);
```

## Testing the Fix

### Manual Test Steps

1. **Open browser DevTools** (F12)
2. **Go to Console tab**
3. **Create a task**: "I want to automate invoice analysis for accuracy"
4. **Watch console logs**:
   - Should see: "🔍 [DEBUG] Approval being sent..."
   - Should see: "📋 Agent Message received..."
   - Should see: "📋 Final Result Message received..."
5. **Verify UI**:
   - Spinner should disappear
   - Agent message should appear
   - Final result should appear

### Expected Console Output

```
🔍 [DEBUG] Approval being sent for plan: d74d4143-73ae-4083-aa51-ba2305214c00
🔍 [DEBUG] WebSocket connected: true
🔍 [DEBUG] Approval sent, waiting for agent messages...
📋 Agent Message received: {type: "agent_message", data: {...}}
✅ Adding agent message to state: Invoice
📊 Agent messages count: 1
📋 Final Result Message received: {type: "final_result_message", data: {...}}
✅ Final result received, hiding spinner
```

## Verification Checklist

After applying fixes:

- [ ] Console shows "Approval being sent" message
- [ ] Console shows "Agent Message received" message
- [ ] Console shows "Final Result Message received" message
- [ ] Spinner disappears after agent response
- [ ] Agent message displays on screen
- [ ] Final result displays on screen
- [ ] No console errors
- [ ] WebSocket connection stays open

## If Still Not Working

### Debug Steps

1. **Check WebSocket Connection**:
   ```javascript
   // In browser console
   console.log(webSocketService.isConnected());
   ```

2. **Check Agent Messages State**:
   ```javascript
   // In browser console (if React DevTools installed)
   // Look at PlanPage component state
   // Check agentMessages array
   ```

3. **Check Backend Logs**:
   ```bash
   # Look for errors in backend output
   # Should see: "Resume execution failed" or similar
   ```

4. **Run Debug Script Again**:
   ```bash
   python debug_approval_flow.py
   # Verify backend is still working
   ```

## Alternative: Simpler Fix

If the above doesn't work, there might be a simpler issue:

**Check**: Is the spinner component actually visible?

**File**: Look for where `showProcessingPlanSpinner` is used in the render

**Possible Issue**: The spinner might be covering the messages

**Fix**: Ensure messages display above or alongside the spinner

## Summary

The backend is working perfectly. The issue is on the frontend where:
1. Messages are being received via WebSocket
2. But they're not being displayed to the user
3. The spinner keeps spinning because the UI isn't updating

Apply the fixes above to:
1. Add proper logging to debug
2. Ensure messages are added to state
3. Hide spinner when done
4. Add timeout protection

This should resolve the hanging spinner issue.

---

**Next Steps**:
1. Apply the fixes above
2. Test with the manual test steps
3. Check console logs
4. Verify messages display
5. If still issues, run debug script and check backend logs
