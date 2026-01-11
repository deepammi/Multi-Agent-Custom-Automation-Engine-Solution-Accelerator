# MCP Server Management Guide

## Overview

The comprehensive agent integration tests require **3 MCP servers** to be running:

- **Bill.com MCP Server** (port 9000)
- **Salesforce MCP Server** (port 9001) 
- **Email MCP Server** (port 9002)

## Test Scripts and Their Server Management

### 🔴 Tests That **DO NOT** Start Servers (Require Manual Startup)

1. **`test_agent_integration_comprehensive.py`** ⭐ **MAIN TEST**
   - **Does NOT start servers automatically**
   - **Requires all 3 servers to be running**
   - **Aborts if any server is missing**
   - Usage: `python3 test_agent_integration_comprehensive.py`

### 🟢 Tests That **DO** Start Servers Automatically

1. **`test_planner_ap_integration.py`**
   - Starts **Bill.com MCP server only** (port 9000)
   - Usage: `python3 test_planner_ap_integration.py`

2. **`test_salesforce_integration_comprehensive.py`**
   - Starts **Salesforce MCP server only** (port 9001)
   - Usage: `python3 test_salesforce_integration_comprehensive.py`

3. **`test_vendor_agnostic_invoice_analysis.py`**
   - Starts **all 3 MCP servers** (ports 9000, 9001, 9002)
   - Usage: `python3 test_vendor_agnostic_invoice_analysis.py`

## How to Start MCP Servers

### Option 1: Use the All-in-One Script ⭐ **RECOMMENDED**

```bash
cd backend
python3 start_all_mcp_servers.py
```

This will:
- Start all 3 MCP servers
- Show startup status
- Keep servers running until Ctrl+C
- Clean shutdown when interrupted

### Option 2: Manual Startup (3 separate terminals)

**Terminal 1 - Bill.com MCP Server:**
```bash
cd backend
python3 ../src/mcp_server/mcp_server.py --transport http --port 9000
```

**Terminal 2 - Salesforce MCP Server:**
```bash
cd backend  
python3 ../src/mcp_server/mcp_server.py --transport http --port 9001
```

**Terminal 3 - Email MCP Server:**
```bash
cd backend
python3 ../src/mcp_server/mcp_server.py --transport http --port 9002
```

### Option 3: Use Individual Test Scripts

If you want to test specific functionality:

**For Bill.com only:**
```bash
python3 test_planner_ap_integration.py  # Starts Bill.com server automatically
```

**For Salesforce only:**
```bash
python3 test_salesforce_integration_comprehensive.py  # Starts Salesforce server automatically
```

**For all 3 servers:**
```bash
python3 test_vendor_agnostic_invoice_analysis.py  # Starts all 3 servers automatically
```

## Running the Comprehensive Test

### Step 1: Start All MCP Servers
```bash
cd backend
python3 start_all_mcp_servers.py
```

Wait for this output:
```
✅ All MCP servers started successfully!

🔗 Server URLs:
   Bill.com MCP Server: http://localhost:9000
   Salesforce MCP Server: http://localhost:9001
   Email MCP Server: http://localhost:9002

🧪 Ready to run comprehensive tests:
   cd backend
   python3 test_agent_integration_comprehensive.py
```

### Step 2: Run Comprehensive Test (in another terminal)
```bash
cd backend
python3 test_agent_integration_comprehensive.py
```

## Verification

### Check if servers are running:
```bash
# Check Bill.com MCP Server
curl http://localhost:9000/

# Check Salesforce MCP Server  
curl http://localhost:9001/

# Check Email MCP Server
curl http://localhost:9002/
```

### Expected Response:
Each should return a FastMCP server response (not an error).

## Troubleshooting

### Problem: "Required MCP servers not available"
**Solution:** Start the servers first using one of the methods above.

### Problem: "Port already in use"
**Solution:** 
1. Kill existing processes: `lsof -ti:9000,9001,9002 | xargs kill`
2. Or use different ports in the startup commands

### Problem: Server fails to start
**Solution:**
1. Check if the MCP server script exists: `ls ../src/mcp_server/mcp_server.py`
2. Check Python path and dependencies
3. Look at error messages in the startup output

## Summary

- **For comprehensive testing**: Use `start_all_mcp_servers.py` + `test_agent_integration_comprehensive.py`
- **For quick Bill.com testing**: Use `test_planner_ap_integration.py` (auto-starts server)
- **For quick Salesforce testing**: Use `test_salesforce_integration_comprehensive.py` (auto-starts server)
- **For full workflow testing**: Use `test_vendor_agnostic_invoice_analysis.py` (auto-starts all servers)