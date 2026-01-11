# PO Investigation Test Scripts - Usage Guide

## Overview

Three test scripts are available for testing PO investigation workflows with real-world data integration (Gmail, Bill.com, Salesforce).

## Changes Made

### 1. Removed Zoho Agent References
- **Changed**: All references to "zoho" agent have been replaced with "accounts_receivable"
- **Reason**: Avoid confusion with Zoho ERP system
- **Files Updated**:
  - `backend/app/services/ai_planner_service.py`
  - `backend/app/agents/graph_factory.py`
  - `backend/app/agents/state.py`
  - All test scripts

### 2. Added Verbose Debug Mode
- **Feature**: `--verbose` flag to show actual agent data
- **Purpose**: Detect AI hallucination by displaying real MCP responses
- **Implementation**: Calls real agents and displays full JSON responses

### 3. Fixed Datetime Deprecation
- **Changed**: `datetime.utcnow()` → `datetime.now(timezone.utc)`
- **Reason**: Python 3.12+ deprecation warning
- **Files Updated**: All files using datetime

## Test Scripts

### 1. Frontend Workflow Simulation (RECOMMENDED)
**File**: `backend/test_frontend_workflow_simulation.py`

**Purpose**: Exact simulation of frontend workflow

**Usage**:
```bash
# Normal mode (simulated data)
python3 backend/test_frontend_workflow_simulation.py

# Verbose debug mode (real agent calls)
python3 backend/test_frontend_workflow_simulation.py --verbose
```

**Verbose Mode Features**:
- Calls real Gmail, Salesforce, and Invoice agents
- Displays actual MCP response data
- Shows full JSON responses for debugging
- Helps identify AI hallucination

**What It Tests**:
1. User query input (like frontend form)
2. AI Planner analysis and sequence generation
3. Human approval simulation
4. Multi-agent execution with WebSocket updates
5. Final results compilation

**Sample Queries**:
1. Payment Dispute Investigation
2. Invoice Discrepancy Analysis
3. Vendor Communication Review
4. Overdue Payment Investigation
5. Duplicate PO Analysis

### 2. Real-World Integration Test
**File**: `backend/test_real_world_integration.py`

**Purpose**: Direct system integration testing

**Usage**:
```bash
python3 backend/test_real_world_integration.py
```

**What It Tests**:
- Direct Gmail MCP service calls
- Direct Salesforce agent calls
- Direct Invoice/Bill.com agent calls
- System connectivity validation

### 3. PO Investigation Interactive
**File**: `backend/test_po_investigation_interactive.py`

**Purpose**: Full AI-driven workflow with realistic scenarios

**Usage**:
```bash
python3 backend/test_po_investigation_interactive.py
```

**What It Tests**:
- Complete AI planning workflow
- 8 realistic PO investigation scenarios
- Human approval simulation
- Comprehensive investigation reports

## Verbose Debug Mode Details

### How to Enable
Add `--verbose`, `--debug`, or `-v` flag:
```bash
python3 backend/test_frontend_workflow_simulation.py --verbose
```

### What You'll See

#### Without Verbose Mode:
```
🤖 Executing Agent 1/4: Gmail
   ✅ Email analysis completed - found relevant communications
```

#### With Verbose Mode:
```
🤖 Executing Agent 1/4: Gmail
   🔍 DEBUG: Starting gmail agent execution...
   🔍 DEBUG: Processing time: 3s
   🔍 DEBUG: Task: Investigate PO-2024-001...
   🔍 DEBUG: Attempting to call real gmail agent...
   🔍 DEBUG: Real agent result received
   🔍 DEBUG: Status: success
   🔍 DEBUG: Data keys: ['real_agent_result', 'gmail_result', 'last_agent']
   🔍 DEBUG: Full result: {
     "agent": "gmail",
     "status": "success",
     "execution_time": 3,
     "message": "Real Gmail agent executed",
     "data": {
       "real_agent_result": {...},
       "gmail_result": "Actual response from Gmail MCP",
       "last_agent": "gmail"
     }
   }
   ✅ Real Gmail agent executed
```

### Detecting Hallucination

**Signs of Hallucination**:
1. Agent returns generic/template responses
2. Data doesn't match your actual Gmail/Salesforce/Bill.com data
3. Specific PO numbers or vendor names that don't exist
4. Consistent patterns across different queries

**How Verbose Mode Helps**:
- Shows actual MCP response vs simulated data
- Displays real API call results
- Reveals if agent is making up data
- Shows exact JSON structure returned

## Agent Sequence Changes

### Old Sequence (with Zoho):
```
gmail → invoice → salesforce → zoho → analysis
```

### New Sequence (with Accounts Receivable):
```
gmail → invoice → salesforce → accounts_receivable → analysis
```

### Available Agents:
- `gmail`: Email search and analysis
- `invoice`: Bill.com invoice processing
- `salesforce`: CRM and vendor relationships
- `accounts_receivable`: AR financial data
- `audit`: Compliance and audit checks
- `analysis`: Data analysis and insights

## Troubleshooting

### Issue: Still seeing "zoho" in agent sequence
**Solution**: 
1. Check if you're using mock mode (LLM might still generate "zoho")
2. Restart the test script
3. Check `backend/app/services/ai_planner_service.py` for any remaining "zoho" references

### Issue: Verbose mode not showing debug messages
**Solution**:
1. Verify you're using the `--verbose` flag
2. Check that the script starts with "🔍 VERBOSE DEBUG MODE ENABLED"
3. Run: `python3 backend/test_verbose_debug.py` to test verbose functionality

### Issue: Real agent calls failing
**Solution**:
1. Check MCP server is running
2. Verify OAuth credentials for Gmail
3. Check Salesforce and Bill.com API credentials
4. Review error messages in verbose output

### Issue: Datetime deprecation warnings
**Solution**: All datetime calls have been updated. If you still see warnings:
1. Check Python version (should be 3.9+)
2. Verify all files are using `datetime.now(timezone.utc)`

## Example Workflow

### Step 1: Run with Verbose Mode
```bash
python3 backend/test_frontend_workflow_simulation.py --verbose
```

### Step 2: Select a Query
```
Select scenario (1-5): 1
```

### Step 3: Review AI Plan
```
📋 Execution Plan for Approval:
  Task: Investigate PO-2024-001...
  Agents: gmail → invoice → salesforce → analysis
  Estimated Time: 300s (5m 0s)
```

### Step 4: Approve Plan
```
❓ Approve this plan? (y/n/details): y
```

### Step 5: Watch Execution with Debug Info
```
🤖 Executing Agent 1/4: Gmail
   🔍 DEBUG: Starting gmail agent execution...
   🔍 DEBUG: Attempting to call real gmail agent...
   🔍 DEBUG: Real agent result received
   🔍 DEBUG: Full result: {...actual MCP response...}
   ✅ Real Gmail agent executed
```

### Step 6: Review Results
```
📊 INVESTIGATION COMPLETE
Status: completed

PO INVESTIGATION REPORT
=======================
[Detailed report with actual data from agents]
```

## Best Practices

1. **Always use verbose mode for debugging**: `--verbose` flag
2. **Check actual data**: Review the JSON responses to verify real data
3. **Compare with your systems**: Verify PO numbers, vendors, amounts match reality
4. **Test incrementally**: Start with one agent, then add more
5. **Monitor MCP logs**: Check MCP server logs for actual API calls

## Next Steps

1. Run `test_verbose_debug.py` to verify verbose mode works
2. Run `test_frontend_workflow_simulation.py --verbose` with a real query
3. Review the actual agent responses in debug output
4. Verify data matches your Gmail/Salesforce/Bill.com systems
5. Report any hallucination or data mismatches

## Support

If you encounter issues:
1. Check this guide first
2. Run `test_verbose_debug.py` to isolate the problem
3. Review MCP server logs
4. Check agent implementation files in `backend/app/agents/`
