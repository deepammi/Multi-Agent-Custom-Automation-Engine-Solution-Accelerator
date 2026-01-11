# Invoice Agent Debug Tests

This document explains the comprehensive set of debug tests created to troubleshoot the Bill.com Invoice Agent integration.

## Test Files Overview

### 1. `test_invoice_agent_simple.py`
**Purpose**: Basic single-prompt testing with minimal setup
**Best for**: Quick testing of specific prompts
**Usage**: 
```bash
python3 test_invoice_agent_simple.py
```
**Features**:
- Edit the `PROMPT` variable at the top to test different queries
- Minimal output, focused on results
- Basic debugging information
- Restart required for each new prompt

### 2. `test_invoice_agent_interactive.py`
**Purpose**: Interactive testing without restarting
**Best for**: Testing multiple prompts quickly
**Usage**:
```bash
python3 test_invoice_agent_interactive.py
```
**Features**:
- Type prompts directly when running
- No restart needed between tests
- Built-in help with example prompts
- Quick result analysis

### 3. `test_invoice_agent_debug.py`
**Purpose**: Comprehensive debugging with structured output
**Best for**: Understanding the complete flow
**Usage**:
```bash
python3 test_invoice_agent_debug.py
```
**Features**:
- Structured debug sections
- JSON-formatted data display
- Multiple test modes (comprehensive or interactive)
- Detailed error analysis

### 4. `test_invoice_agent_ultimate_debug.py` ⭐ **RECOMMENDED**
**Purpose**: Maximum debugging with complete MCP communication logging
**Best for**: Finding the root cause of Bill.com integration issues
**Usage**:
```bash
python3 test_invoice_agent_ultimate_debug.py
```
**Features**:
- **Complete MCP request/response logging**
- **Three-tier testing**: Direct MCP → Client Service → Invoice Agent
- **Root cause analysis** - tells you exactly where the failure occurs
- **Debug log file** saved for later analysis
- **Maximum verbosity** - shows every data transformation

### 5. `test_invoice_agent_standalone.py`
**Purpose**: Original comprehensive test (enhanced)
**Best for**: Full feature testing with health checks
**Usage**:
```bash
python3 test_invoice_agent_standalone.py
```
**Features**:
- Health checks and diagnostics
- Direct Bill.com tool testing
- Interactive prompt testing
- Multiple search strategies

## Key Improvements Made

### 1. Verbose MCP Communication Logging
All tests now show:
- **Request data** sent to MCP server
- **Response data** received from MCP server
- **Data transformations** at each step
- **Error details** with full stack traces

### 2. Fixed DateTime Usage
Replaced all `datetime.utcnow()` with `datetime.now(timezone.utc)` for Python 3.12+ compatibility.

### 3. Enhanced Error Reporting
- Full exception stack traces
- Detailed error context
- Step-by-step failure analysis

### 4. Root Cause Analysis
The ultimate debug test specifically identifies:
1. **MCP Server Issues** - Is the server running and responding?
2. **Tool Availability** - Are Bill.com tools registered?
3. **Client Service Issues** - Is the service wrapper working?
4. **Agent Issues** - Is the Invoice Agent processing correctly?

## Debugging Strategy

### Step 1: Start with Ultimate Debug Test
```bash
cd backend
python3 test_invoice_agent_ultimate_debug.py
```

This will tell you exactly where the problem is:

- **If Direct FastMCP fails**: MCP server is not running or not responding
- **If Client Service fails**: Service wrapper has issues
- **If Invoice Agent fails**: Agent logic has problems
- **If all pass but no data**: Bill.com service is unavailable (but system works)

### Step 2: Use Interactive Test for Prompt Testing
Once you know the system is working, use the interactive test to try different prompts:
```bash
python3 test_invoice_agent_interactive.py
```

### Step 3: Use Simple Test for Focused Testing
For testing specific prompts repeatedly:
```bash
python3 test_invoice_agent_simple.py
```

## Debug Output Explanation

### MCP Request Logging
```
🔍 DEBUG MCP REQUEST #1
==================================================
Method: search_invoices
Timestamp: 2024-12-26T10:30:45.123456+00:00
Kwargs:
  search_term: "INV-1001"
  search_type: "invoice_number"
==================================================
```

### MCP Response Logging
```
🔍 DEBUG MCP RESPONSE #1
==================================================
Method: search_invoices
Timestamp: 2024-12-26T10:30:45.234567+00:00
Success: True
Result Type: <class 'dict'>
Result:
{
  "success": true,
  "invoices": [...],
  "count": 0
}
==================================================
```

### Root Cause Analysis
```
🔍 ROOT CAUSE: Direct FastMCP connection failed
   This means the MCP server is not responding properly
   Error: Connection refused
```

## Common Issues and Solutions

### 1. SSL Certificate Verification Error ⭐ **MOST COMMON**
**Symptoms**: "SSLCertVerificationError", "certificate verify failed", "Cannot connect to host gateway.stage.bill.com:443"
**Root Cause**: SSL certificate verification failing for Bill.com's staging environment
**Solutions**:

#### Option A: Quick SSL Bypass Test (Recommended)
```bash
python3 test_invoice_agent_ssl_bypass.py
```
This test will:
- Temporarily disable SSL verification
- Test if SSL was the root cause
- Show if the system works without SSL issues

#### Option B: Apply Permanent SSL Fix
```bash
python3 fix_bill_com_ssl.py
```
This will:
- Patch the Bill.com service to support SSL bypass
- Add `BILL_COM_SSL_VERIFY=false` to your .env file
- Make the fix permanent

#### Option C: Manual Environment Variable
Add to your `.env` file:
```
BILL_COM_SSL_VERIFY=false
```

⚠️ **Important**: SSL bypass should only be used for development/testing!

### 2. MCP Server Not Starting
**Symptoms**: "MCP server script not found" or "Connection refused"
**Solution**: 
- Check that `src/mcp_server/mcp_server.py` exists
- Verify environment variables are set
- Check server logs in debug output

### 2. No Bill.com Tools Found
**Symptoms**: "No Bill.com tools available"
**Solution**:
- Verify `BILL_COM_MCP_ENABLED=true` is set
- Check Bill.com credentials are configured
- Review MCP server startup logs

### 3. Tools Found But No Data
**Symptoms**: Tools work but return empty results
**Solution**:
- Check Bill.com service availability
- Verify authentication credentials
- Test with different search terms

### 4. Agent Gets No Response
**Symptoms**: Agent completes but says "Service Unavailable"
**Solution**:
- Check if MCP client service is properly connecting
- Verify tool calls are reaching the MCP server
- Review agent logic for proper tool usage

## Files Modified

1. **test_invoice_agent_interactive.py** - Added verbose debugging and fixed datetime
2. **test_invoice_agent_simple.py** - Added debugging and fixed datetime  
3. **test_multi_agent_invoice_workflow.py** - Added verbose logging and fixed datetime
4. **test_invoice_agent_standalone.py** - Fixed datetime usage

## New Files Created

1. **test_invoice_agent_debug.py** - Structured debugging test
2. **test_invoice_agent_ultimate_debug.py** - Maximum verbosity test
3. **debug_mcp_wrapper.py** - MCP communication wrapper
4. **INVOICE_AGENT_DEBUG_TESTS.md** - This documentation

## Next Steps

1. Run the ultimate debug test to identify the root cause
2. Based on the results, focus on the specific failing component
3. Use the interactive test to verify fixes
4. Check the generated debug log files for detailed analysis

The ultimate debug test should give you a clear path forward by showing exactly where in the chain the Bill.com integration is failing.