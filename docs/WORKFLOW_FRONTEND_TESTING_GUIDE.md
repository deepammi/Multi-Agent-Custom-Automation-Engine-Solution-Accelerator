# Testing Workflows Using the Frontend

Complete guide to testing LangGraph workflows through the React frontend.

## Overview

The frontend provides a user-friendly interface to test workflows without writing code. You can submit natural language requests and see real-time workflow execution.

## Prerequisites

### 1. Start the Backend

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

Verify backend is running:
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### 2. Start the Frontend

```bash
cd src/frontend
npm run dev
```

Frontend should be available at: `http://localhost:5173`

### 3. Verify Workflow Endpoints

```bash
# List available workflows
curl http://localhost:8000/api/v3/workflows

# Should return:
# [
#   {"name": "invoice_verification", "title": "Invoice Verification", ...},
#   {"name": "payment_tracking", "title": "Payment Tracking", ...},
#   {"name": "customer_360", "title": "Customer 360 View", ...}
# ]
```

## Testing Workflows via Frontend

### Method 1: Natural Language Input (Recommended)

The frontend automatically detects workflows from natural language.

#### Test Invoice Verification

1. **Open the frontend** at `http://localhost:5173`

2. **Navigate to the main chat/task interface**

3. **Enter one of these prompts:**
   ```
   Verify invoice INV-000001
   Check invoice INV-000001 across systems
   Validate invoice INV-000001 from Zoho and Salesforce
   Cross-check invoice data for INV-000001
   ```

4. **Click Submit or Press Enter**

5. **Watch the workflow execute:**
   - ✅ System detects "invoice_verification" workflow
   - ✅ Extracts invoice_id: "INV-000001"
   - ✅ Executes workflow steps
   - ✅ Shows real-time progress messages
   - ✅ Displays final verification report

**Expected Output:**
```
🚀 Starting task: Verify invoice INV-000001
🔄 Executing Invoice Verification workflow...
📊 Workflow parameters: {invoice_id: "INV-000001", ...}

Step 1: Fetching invoice from Zoho...
Step 2: Fetching customer from Salesforce...
Step 3: Cross-referencing data...
Step 4: Generating verification report...

# Invoice Verification Report
## Invoice Details
- Invoice Number: INV-000001
- Customer: Test1Customer Co.
- Amount: $12,200.00
...
```

#### Test Payment Tracking

1. **Enter one of these prompts:**
   ```
   Track payment for INV-000002
   Payment status for invoice INV-000002
   Check payment confirmation for INV-000002
   Find payment for INV-000002
   ```

2. **Watch the workflow execute:**
   - ✅ Detects "payment_tracking" workflow
   - ✅ Extracts invoice_id: "INV-000002"
   - ✅ Checks ERP system
   - ✅ Searches email for payment confirmation
   - ✅ Shows payment status

**Expected Output:**
```
🔄 Executing Payment Tracking workflow...

Step 1: Checking invoice status in ERP...
Step 2: Searching for payment emails...
Step 3: Matching payment to invoice...

# Payment Tracking Report
## Invoice Details
- Invoice Number: INV-000002
- Customer: University of Chicago
- Total Amount: $12,400.00
- Status: sent

## Payment Status
✅ Payment Received
- Payment Date: 2025-12-05
- Confirmation: PAY-2025-001234
...
```

#### Test Customer 360

1. **Enter one of these prompts:**
   ```
   Customer 360 view for University of Chicago
   Show me complete customer profile for Acme Corp
   Customer analysis for Microsoft
   Complete view of customer Tesla Inc
   ```

2. **Watch the workflow execute:**
   - ✅ Detects "customer_360" workflow
   - ✅ Extracts customer_name
   - ✅ Aggregates data from CRM, ERP, Accounting
   - ✅ Shows comprehensive customer profile

**Expected Output:**
```
🔄 Executing Customer 360 View workflow...

Step 1: Fetching customer from CRM...
Step 2: Fetching invoices from ERP...
Step 3: Fetching transactions from Accounting...
Step 4: Aggregating customer data...

# Customer 360 View: University of Chicago

## Customer Health
🔴 Needs Attention
- Payment Ratio: 0.0%
- Risk Level: High

## CRM Profile
- Account Name: University of Chicago
- Industry: Education
...
```

### Method 2: Using Browser Developer Tools

For more detailed testing and debugging:

#### 1. Open Developer Tools

- **Chrome/Edge**: Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
- **Firefox**: Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)

#### 2. Go to Network Tab

- Click on "Network" tab
- Check "Preserve log" to keep requests after navigation

#### 3. Submit a Workflow Request

Enter: `Verify invoice INV-000001`

#### 4. Inspect the Request

Look for `POST /api/v3/process_request_v2` or `POST /api/v3/process_request`

**Request Payload:**
```json
{
  "description": "Verify invoice INV-000001",
  "session_id": "session-abc-123",
  "require_hitl": false
}
```

**Response:**
```json
{
  "plan_id": "plan-xyz-789",
  "status": "pending",
  "session_id": "session-abc-123"
}
```

#### 5. Watch WebSocket Messages

- Go to "WS" or "WebSocket" tab in Network
- Click on the WebSocket connection
- Watch real-time messages:

```json
// Message 1: Workflow start
{
  "type": "agent_message",
  "data": {
    "agent_name": "System",
    "content": "🚀 Starting task: Verify invoice INV-000001",
    "status": "in_progress"
  }
}

// Message 2: Workflow detection
{
  "type": "agent_message",
  "data": {
    "agent_name": "Workflow Engine",
    "content": "🔄 Executing Invoice Verification workflow...",
    "status": "in_progress"
  }
}

// Message 3-N: Progress updates
{
  "type": "agent_message",
  "data": {
    "agent_name": "Workflow",
    "content": "Step 1: Fetching invoice from Zoho...",
    "status": "in_progress"
  }
}

// Final message: Result
{
  "type": "agent_message",
  "data": {
    "agent_name": "Invoice Verification",
    "content": "# Invoice Verification Report\n...",
    "status": "completed"
  }
}
```

### Method 3: Using Browser Console

For programmatic testing:

#### 1. Open Console

Press `F12` and go to "Console" tab

#### 2. Test Workflow Detection

```javascript
// Test what workflow would be detected
const testInputs = [
  "Verify invoice INV-000001",
  "Track payment for INV-000002",
  "Customer 360 for Acme Corp"
];

testInputs.forEach(input => {
  console.log(`Input: "${input}"`);
  // The backend will detect the workflow
});
```

#### 3. Submit Request Programmatically

```javascript
// Submit a workflow request
const submitWorkflow = async (description) => {
  const response = await fetch('http://localhost:8000/api/v3/process_request_v2', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      description: description,
      session_id: 'test-session-' + Date.now(),
      require_hitl: false
    })
  });
  
  const result = await response.json();
  console.log('Plan ID:', result.plan_id);
  console.log('Status:', result.status);
  return result;
};

// Test it
await submitWorkflow("Verify invoice INV-000001");
```

#### 4. List Available Workflows

```javascript
// Get all available workflows
const listWorkflows = async () => {
  const response = await fetch('http://localhost:8000/api/v3/workflows');
  const workflows = await response.json();
  
  console.log('Available Workflows:');
  workflows.forEach(wf => {
    console.log(`- ${wf.title}: ${wf.description}`);
    console.log(`  Parameters: ${wf.parameters.join(', ')}`);
  });
  
  return workflows;
};

// Test it
await listWorkflows();
```

#### 5. Execute Specific Workflow

```javascript
// Execute a specific workflow directly
const executeWorkflow = async (workflowName, parameters) => {
  const response = await fetch('http://localhost:8000/api/v3/execute_workflow', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      workflow_name: workflowName,
      plan_id: 'test-plan-' + Date.now(),
      session_id: 'test-session-' + Date.now(),
      parameters: parameters
    })
  });
  
  const result = await response.json();
  console.log('Status:', result.status);
  console.log('Result:', result.final_result);
  return result;
};

// Test invoice verification
await executeWorkflow('invoice_verification', {
  invoice_id: 'INV-000001',
  erp_system: 'zoho',
  crm_system: 'salesforce'
});

// Test payment tracking
await executeWorkflow('payment_tracking', {
  invoice_id: 'INV-000002',
  erp_system: 'zoho'
});

// Test customer 360
await executeWorkflow('customer_360', {
  customer_name: 'University of Chicago'
});
```

## Testing Scenarios

### Scenario 1: Happy Path Testing

Test that workflows execute successfully with valid inputs.

**Test Cases:**

| Workflow | Input | Expected Result |
|----------|-------|-----------------|
| Invoice Verification | "Verify invoice INV-000001" | ✅ Verification report with matches/discrepancies |
| Payment Tracking | "Track payment INV-000002" | ✅ Payment status and recommendations |
| Customer 360 | "Customer 360 for Acme Corp" | ✅ Comprehensive customer profile |

**Steps:**
1. Enter each input in the frontend
2. Verify workflow is detected
3. Check all progress messages appear
4. Confirm final result is formatted correctly
5. Verify no errors in console

### Scenario 2: Parameter Extraction Testing

Test that parameters are correctly extracted from various input formats.

**Test Cases:**

```javascript
// Invoice ID extraction
"Verify invoice INV-000001"           → invoice_id: "INV-000001"
"Check INV-123456"                    → invoice_id: "INV-123456"
"Validate invoice number INV-999999"  → invoice_id: "INV-999999"

// Customer name extraction
"Customer 360 for Acme Corp"          → customer_name: "Acme Corp"
"Show me profile for Microsoft"       → customer_name: "Microsoft"
"Complete view of Tesla Inc"          → customer_name: "Tesla Inc"
```

**Steps:**
1. Enter each variation
2. Check Network tab for extracted parameters
3. Verify correct values are sent to backend

### Scenario 3: Fallback to Regular Agent

Test that non-workflow requests use regular agents.

**Test Cases:**

```javascript
// These should NOT trigger workflows
"List all Zoho invoices"              → Regular agent
"Show Salesforce accounts"            → Regular agent
"What's the weather today?"           → Regular agent
```

**Steps:**
1. Enter non-workflow input
2. Verify no workflow is detected
3. Check that regular agent routing is used
4. Confirm appropriate response

### Scenario 4: Error Handling

Test how the system handles errors.

**Test Cases:**

```javascript
// Invalid invoice ID format
"Verify invoice ABC-123"              → Should use default or show error

// Empty input
""                                    → Should show validation error

// Very long input
"Verify invoice " + "X".repeat(1000)  → Should handle gracefully
```

**Steps:**
1. Enter invalid input
2. Check for error messages
3. Verify system doesn't crash
4. Confirm user-friendly error display

### Scenario 5: Real-Time Updates

Test that progress messages appear in real-time.

**Steps:**
1. Enter: "Verify invoice INV-000001"
2. Watch for messages to appear sequentially:
   - ✅ "Starting task..."
   - ✅ "Executing workflow..."
   - ✅ "Step 1: Fetching..."
   - ✅ "Step 2: Processing..."
   - ✅ Final result
3. Verify no messages are missing
4. Check timing is reasonable (not too fast/slow)

## Frontend Testing Checklist

### Before Testing

- [ ] Backend is running (`http://localhost:8000`)
- [ ] Frontend is running (`http://localhost:5173`)
- [ ] Workflows endpoint is accessible (`/api/v3/workflows`)
- [ ] WebSocket connection is working
- [ ] Browser console is open for debugging

### During Testing

- [ ] Enter workflow trigger phrase
- [ ] Verify workflow is detected (check Network tab)
- [ ] Watch for real-time progress messages
- [ ] Check WebSocket messages in DevTools
- [ ] Verify final result is displayed
- [ ] Check for any console errors
- [ ] Test with different parameter values
- [ ] Try edge cases and invalid inputs

### After Testing

- [ ] All workflows executed successfully
- [ ] No errors in browser console
- [ ] No errors in backend logs
- [ ] WebSocket connection remained stable
- [ ] UI remained responsive
- [ ] Results were formatted correctly

## Common Issues and Solutions

### Issue 1: Workflow Not Detected

**Symptoms:**
- Regular agent is used instead of workflow
- No workflow-specific messages appear

**Solutions:**
1. Check your input matches detection patterns
2. Verify backend logs show workflow detection
3. Test with exact example phrases first
4. Check Network tab for request payload

**Debug:**
```javascript
// In browser console
const input = "Verify invoice INV-000001";
console.log('Testing input:', input);
console.log('Contains "verify invoice":', input.toLowerCase().includes('verify invoice'));
```

### Issue 2: Parameters Not Extracted

**Symptoms:**
- Workflow uses default parameters
- Wrong values in execution

**Solutions:**
1. Check parameter format (e.g., INV-XXXXXX)
2. Verify regex patterns in backend
3. Test with known working examples
4. Check Network tab for extracted params

**Debug:**
```javascript
// Test parameter extraction
const testPattern = /INV-\d{6}/i;
const input = "Verify invoice INV-000001";
const match = input.match(testPattern);
console.log('Extracted:', match ? match[0] : 'No match');
```

### Issue 3: No Real-Time Updates

**Symptoms:**
- Messages appear all at once at the end
- No progress indicators

**Solutions:**
1. Check WebSocket connection in Network tab
2. Verify WebSocket URL is correct
3. Check for CORS issues
4. Restart backend and frontend

**Debug:**
```javascript
// Check WebSocket status
// In Network tab → WS → Click connection
// Status should be "101 Switching Protocols"
```

### Issue 4: Frontend Errors

**Symptoms:**
- Console shows errors
- UI doesn't update
- Requests fail

**Solutions:**
1. Check browser console for specific errors
2. Verify API endpoints are correct
3. Check CORS configuration
4. Clear browser cache and reload

**Debug:**
```javascript
// Test API connectivity
fetch('http://localhost:8000/api/v3/workflows')
  .then(r => r.json())
  .then(data => console.log('Workflows:', data))
  .catch(err => console.error('Error:', err));
```

## Advanced Testing

### Testing with Different Sessions

```javascript
// Test multiple concurrent sessions
const sessions = ['session-1', 'session-2', 'session-3'];

sessions.forEach(async (sessionId) => {
  const result = await fetch('http://localhost:8000/api/v3/process_request_v2', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description: 'Verify invoice INV-000001',
      session_id: sessionId,
      require_hitl: false
    })
  });
  
  console.log(`Session ${sessionId}:`, await result.json());
});
```

### Testing Workflow Performance

```javascript
// Measure workflow execution time
const testPerformance = async (description) => {
  const start = Date.now();
  
  const response = await fetch('http://localhost:8000/api/v3/process_request_v2', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description: description,
      session_id: 'perf-test-' + Date.now(),
      require_hitl: false
    })
  });
  
  const result = await response.json();
  const duration = Date.now() - start;
  
  console.log(`Workflow: ${description}`);
  console.log(`Duration: ${duration}ms`);
  console.log(`Status: ${result.status}`);
  
  return { duration, result };
};

// Test all workflows
await testPerformance("Verify invoice INV-000001");
await testPerformance("Track payment INV-000002");
await testPerformance("Customer 360 for Acme Corp");
```

### Testing Error Recovery

```javascript
// Test how system handles errors
const testErrorHandling = async () => {
  // Test with invalid endpoint
  try {
    await fetch('http://localhost:8000/api/v3/invalid_endpoint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test: 'data' })
    });
  } catch (err) {
    console.log('Error handled:', err.message);
  }
  
  // Test with malformed request
  try {
    await fetch('http://localhost:8000/api/v3/process_request_v2', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: 'invalid json'
    });
  } catch (err) {
    console.log('Malformed request handled:', err.message);
  }
};

await testErrorHandling();
```

## Best Practices

### 1. Test Systematically
- ✅ Test one workflow at a time
- ✅ Use consistent test data
- ✅ Document expected vs actual results
- ✅ Test both happy path and edge cases

### 2. Monitor Everything
- ✅ Keep browser console open
- ✅ Watch Network tab for requests
- ✅ Monitor WebSocket messages
- ✅ Check backend logs

### 3. Use Realistic Data
- ✅ Use realistic invoice IDs
- ✅ Use real company names
- ✅ Test with actual use cases
- ✅ Vary input formats

### 4. Document Issues
- ✅ Screenshot errors
- ✅ Copy error messages
- ✅ Note reproduction steps
- ✅ Check browser/OS versions

## Quick Test Script

Save this as a bookmark for quick testing:

```javascript
javascript:(async function() {
  const tests = [
    { name: 'Invoice Verification', input: 'Verify invoice INV-000001' },
    { name: 'Payment Tracking', input: 'Track payment INV-000002' },
    { name: 'Customer 360', input: 'Customer 360 for Acme Corp' }
  ];
  
  console.log('🧪 Running Workflow Tests...\n');
  
  for (const test of tests) {
    console.log(`Testing: ${test.name}`);
    const response = await fetch('http://localhost:8000/api/v3/process_request_v2', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        description: test.input,
        session_id: 'test-' + Date.now(),
        require_hitl: false
      })
    });
    const result = await response.json();
    console.log(`✅ ${test.name}: ${result.status}\n`);
  }
  
  console.log('🎉 All tests completed!');
})();
```

## Summary

**Frontend testing provides:**
- ✅ Visual feedback on workflow execution
- ✅ Real-time progress monitoring
- ✅ Easy parameter testing
- ✅ User experience validation
- ✅ Integration testing

**Best tested via:**
1. Natural language input (easiest)
2. Browser DevTools (most detailed)
3. Console commands (most flexible)

**Start with:** Natural language input for quick validation
**Use DevTools for:** Debugging and detailed inspection
**Use Console for:** Automated testing and performance checks

---

**Ready to test?** Start the backend and frontend, then try: `"Verify invoice INV-000001"`
