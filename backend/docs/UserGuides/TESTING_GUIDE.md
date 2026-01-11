# MACAE Backend Testing Guide

This guide provides a comprehensive approach to testing the MACAE backend system using command-line tools before testing with the frontend.

## Quick Start

### 1. Start the Full System

```bash
cd backend
./start_full_system.sh
```

This script will:
- ✅ Start MongoDB (Docker container)
- ✅ Start all 3 MCP servers (Gmail, Salesforce, Zoho)
- ✅ Start the FastAPI backend
- ✅ Show system status and health

### 2. Test with CLI Simulator

#### Interactive Mode (Recommended for debugging)
```bash
python3 test_cli_frontend_simulation.py
```

#### Automated Mode (Quick validation)
```bash
python3 test_cli_frontend_simulation.py --auto
```

### 3. Stop the System

```bash
./stop_full_system.sh
```

## System Components

| Component | Port | URL | Purpose |
|-----------|------|-----|---------|
| MongoDB | 27017 | mongodb://localhost:27017 | Database |
| Gmail MCP | 9000 | http://localhost:9000 | Email integration |
| Salesforce MCP | 9001 | http://localhost:9001 | CRM integration |
| Main MCP (Bill.com) | 9002 | http://localhost:9002 | AP/ERP integration |
| Backend API | 8000 | http://localhost:8000 | Main API |

## CLI Tester Features

### Interactive Commands

1. **Submit Task** - Send a task description to the backend
2. **Connect WebSocket** - Establish real-time connection
3. **Listen for Messages** - Monitor agent communications
4. **Get Plan Status** - Check current execution status
5. **Approve/Reject Plan** - Simulate HITL interactions
6. **Full Test Workflow** - Complete end-to-end test

### Message Types Monitored

- 🤖 **agent_message** - Agent responses and updates
- 📋 **plan_approval_request** - Human approval requests
- 🎯 **final_result_message** - Task completion results
- 📊 **step_progress** - Workflow progress updates
- 🔌 **connection_established** - WebSocket status

## Test Scenarios

### Scenario 1: Invoice Analysis
```
Task: "Analyze invoice INV-12345 for Acme Corp and check payment status"
Expected: Planner → Invoice Agent → Results
```

### Scenario 2: PO Investigation
```
Task: "Why is PO INV-67890 stuck and not processed?"
Expected: Planner → Gmail → Invoice → Salesforce → Analysis
```

### Scenario 3: Customer 360 View
```
Task: "Get complete view of customer Acme Marketing"
Expected: Planner → CRM Agent → Comprehensive Report
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   ./stop_full_system.sh
   sleep 5
   ./start_full_system.sh
   ```

2. **MongoDB Connection Failed**
   ```bash
   docker stop macae-mongodb
   docker rm macae-mongodb
   ./start_full_system.sh
   ```

3. **MCP Server Not Starting**
   - Check logs in `logs/` directory
   - Verify Python dependencies: `pip install -r requirements.txt`
   - Check MCP server configuration

4. **Backend API Errors**
   - Check `logs/backend.log`
   - Verify environment variables
   - Test health endpoint: `curl http://localhost:8000/health`

### Log Files

- **Backend**: `logs/backend.log`
- **Gmail MCP**: `logs/gmail_mcp.log`
- **Salesforce MCP**: `logs/salesforce_mcp.log`
- **Main MCP**: `logs/main_mcp.log`

## API Endpoints for Manual Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Submit Task
```bash
curl -X POST http://localhost:8000/api/v3/process_request \
  -H "Content-Type: application/json" \
  -d '{"description": "Test task", "session_id": null}'
```

### Get Plan Status
```bash
curl "http://localhost:8000/api/v3/plan?plan_id=YOUR_PLAN_ID"
```

### WebSocket Connection
```bash
# Using wscat (install with: npm install -g wscat)
wscat -c "ws://localhost:8000/api/v3/socket/YOUR_PLAN_ID?user_id=test-user"
```

## Environment Variables

Key environment variables for testing:

```bash
# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=macae_db

# MCP Servers
MCP_GMAIL_URL=http://localhost:9000
MCP_SALESFORCE_URL=http://localhost:9001
MCP_MAIN_URL=http://localhost:9002

# LLM Configuration (optional for testing)
USE_MOCK_LLM=true
OPENAI_API_KEY=your_key_here
```

## Next Steps

After successful CLI testing:

1. **Frontend Testing**: Start the React frontend and test the same workflows
2. **Integration Testing**: Run comprehensive integration tests
3. **Performance Testing**: Test with multiple concurrent users
4. **Production Deployment**: Deploy to staging/production environment

## Success Criteria

✅ All services start without errors
✅ Health check returns 200 OK
✅ Task submission returns plan_id
✅ WebSocket connection established
✅ Agent messages received via WebSocket
✅ Plan approval workflow functions
✅ Final results delivered

## Support

If you encounter issues:

1. Check the logs in the `logs/` directory
2. Verify all dependencies are installed
3. Ensure Docker is running (for MongoDB)
4. Check that no other services are using the required ports
5. Review the error messages in the CLI tester output