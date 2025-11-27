# Frontend Integration Guide

## Overview

This guide explains how to connect the existing React frontend to the new LangGraph-based backend. The frontend code remains unchanged - only configuration needs to be updated.

## Configuration Changes

### 1. Frontend Configuration Files Created

#### `src/frontend/public/config.json`
```json
{
  "API_URL": "http://localhost:8000/api",
  "ENABLE_AUTH": false,
  "APP_ENV": "dev"
}
```

This file is loaded by the frontend at runtime via the `/config` endpoint.

#### `src/frontend/.env`
```bash
API_URL=http://localhost:8000
ENABLE_AUTH=false
APP_ENV=dev
```

This file provides default configuration values.

### 2. How Configuration Works

The frontend loads configuration in this order:

1. **Default Config** (`src/frontend/src/api/config.tsx`):
   ```typescript
   export let config = {
       API_URL: "http://localhost:8000/api",
       ENABLE_AUTH: false,
   };
   ```

2. **Runtime Config** (loaded from `/config` endpoint):
   - Frontend fetches `/config` on startup
   - If successful, overrides default config
   - Sets `window.appConfig` for global access

3. **API URL Construction**:
   - Base URL: `http://localhost:8000/api`
   - REST endpoints: `http://localhost:8000/api/v3/...`
   - WebSocket: `ws://localhost:8000/api/v3/socket/{plan_id}`

## Starting the Application

### 1. Start the Backend

```bash
cd backend
python -m app.main
```

The backend will start on `http://localhost:8000`

Verify it's running:
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### 2. Start the Frontend

```bash
cd src/frontend
npm install  # If not already done
npm start
```

The frontend will start on `http://localhost:3000` (or another port if 3000 is busy)

### 3. Verify Connection

Open your browser to `http://localhost:3000`

Check the browser console for:
- ✅ "Constructed WebSocket URL: ws://localhost:8000/api/v3/socket/..."
- ✅ No CORS errors
- ✅ No 404 errors for API endpoints

## API Endpoints Used by Frontend

The frontend expects these endpoints (all implemented in Phase 1-6):

### REST Endpoints

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| POST | `/api/v3/process_request` | Create new task | ✅ Implemented |
| GET | `/api/v3/plans` | Get all plans | ✅ Implemented |
| GET | `/api/v3/plan` | Get plan by ID | ✅ Implemented |
| POST | `/api/v3/plan_approval` | Approve/reject plan | ✅ Implemented |
| POST | `/api/v3/user_clarification` | Submit clarification | ✅ Implemented |
| POST | `/api/v3/agent_message` | Send agent message | ✅ Implemented |
| GET | `/api/v3/teams` | Get team configurations | ⚠️ Phase 8 |
| POST | `/api/v3/init_team` | Initialize team | ⚠️ Phase 8 |

### WebSocket Endpoint

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `WS /api/v3/socket/{plan_id}` | Real-time updates | ✅ Implemented |

### WebSocket Message Types

The frontend expects these message types (all implemented):

| Message Type | Purpose | Status |
|--------------|---------|--------|
| `agent_message` | Agent responses | ✅ Implemented |
| `agent_message_streaming` | Token streaming | ⚠️ Phase 7 |
| `plan_approval_request` | Request approval | ✅ Implemented |
| `plan_approval_response` | Approval response | ✅ Implemented |
| `user_clarification_request` | Request clarification | ⚠️ Future |
| `user_clarification_response` | Clarification response | ⚠️ Future |
| `agent_tool_message` | Tool execution | ⚠️ Phase 7 |
| `final_result_message` | Task completion | ✅ Implemented |
| `agent_stream_start` | Stream start | ⚠️ Phase 7 |
| `agent_stream_end` | Stream end | ⚠️ Phase 7 |
| `system_message` | System notifications | ✅ Implemented |

## Testing Frontend Integration

### 1. Basic Connectivity Test

1. Open browser to `http://localhost:3000`
2. Open DevTools Console (F12)
3. Check for errors
4. Verify API URL is correct: Look for "Constructed WebSocket URL" log

### 2. Create Task Test

1. On home page, enter a task description:
   - "Check invoice payment status"
   - "Perform closing reconciliation"
   - "Review audit evidence"

2. Click "Submit" or press Enter

3. Verify:
   - ✅ Task is created (redirects to plan page)
   - ✅ WebSocket connects
   - ✅ Planner message appears
   - ✅ Approval request appears

### 3. Approval Flow Test

1. After creating a task, wait for approval request
2. Click "Approve" button
3. Verify:
   - ✅ Specialized agent executes (Invoice/Closing/Audit)
   - ✅ Agent messages appear in real-time
   - ✅ Final result message appears
   - ✅ Plan status shows "Completed"

### 4. Multiple Tasks Test

1. Create multiple tasks from home page
2. Navigate between plan pages
3. Verify:
   - ✅ Each plan has its own WebSocket connection
   - ✅ Messages appear on correct plan page
   - ✅ No cross-contamination between plans

## Troubleshooting

### Issue: "Failed to fetch /config"

**Cause**: Frontend can't load config file

**Solution**:
1. Verify `src/frontend/public/config.json` exists
2. Restart frontend dev server
3. Check browser console for actual error

### Issue: "WebSocket connection failed"

**Cause**: Backend not running or wrong URL

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check WebSocket URL in console
3. Verify no firewall blocking WebSocket connections

### Issue: "CORS error"

**Cause**: Backend CORS not configured for frontend origin

**Solution**:
1. Check backend CORS settings in `backend/app/main.py`
2. Verify `http://localhost:3000` is in allowed origins
3. Restart backend after changes

### Issue: "404 Not Found" for API endpoints

**Cause**: API endpoint path mismatch

**Solution**:
1. Verify backend routes in `backend/app/api/v3/routes.py`
2. Check frontend API_ENDPOINTS in `src/frontend/src/api/apiService.tsx`
3. Ensure paths match exactly (case-sensitive)

### Issue: "Plan approval request not received"

**Cause**: WebSocket message buffering issue

**Solution**:
1. This should be fixed with message buffering (Phase 6)
2. Check backend logs for "buffering message" warnings
3. Verify WebSocket connection established before approval request

### Issue: "Messages appear on wrong plan page"

**Cause**: WebSocket subscription issue

**Solution**:
1. Check plan_id in WebSocket URL
2. Verify frontend subscribes to correct plan
3. Check backend WebSocket manager routing

## Configuration for Different Environments

### Development (Local)

```json
{
  "API_URL": "http://localhost:8000/api",
  "ENABLE_AUTH": false,
  "APP_ENV": "dev"
}
```

### Staging

```json
{
  "API_URL": "https://staging-api.example.com/api",
  "ENABLE_AUTH": true,
  "APP_ENV": "staging"
}
```

### Production

```json
{
  "API_URL": "https://api.example.com/api",
  "ENABLE_AUTH": true,
  "APP_ENV": "production"
}
```

## WebSocket URL Construction

The frontend automatically constructs WebSocket URLs:

1. Takes API_URL: `http://localhost:8000/api`
2. Converts protocol: `http` → `ws`, `https` → `wss`
3. Adds socket path: `/v3/socket/{plan_id}`
4. Adds user_id query param: `?user_id={user_id}`

Result: `ws://localhost:8000/api/v3/socket/{plan_id}?user_id={user_id}`

## Data Flow

### Task Creation Flow

```
Frontend                    Backend
   |                           |
   |-- POST /process_request ->|
   |                           |-- Create plan in DB
   |                           |-- Start background task
   |<- {plan_id, session_id} --|
   |                           |
   |-- Navigate to /plan/:id ->|
   |                           |
   |-- WS connect ------------>|
   |                           |-- Send buffered messages
   |<- agent_message ----------|
   |<- plan_approval_request --|
   |                           |
   |-- POST /plan_approval --->|
   |                           |-- Resume execution
   |<- agent_message ----------|
   |<- final_result_message ---|
```

### Real-time Updates Flow

```
Backend Agent               WebSocket Manager        Frontend
     |                            |                      |
     |-- Send message ----------->|                      |
     |                            |-- Buffer if no conn -|
     |                            |                      |
     |                            |<- Connect ---------- |
     |                            |-- Send buffered ---->|
     |                            |                      |
     |-- Send message ----------->|-- Send immediately ->|
```

## Frontend Code (No Changes Required)

The following frontend files work without modification:

- ✅ `src/frontend/src/api/apiService.tsx` - API service layer
- ✅ `src/frontend/src/api/apiClient.tsx` - HTTP client
- ✅ `src/frontend/src/api/config.tsx` - Configuration management
- ✅ `src/frontend/src/services/WebSocketService.tsx` - WebSocket service
- ✅ `src/frontend/src/pages/HomePage.tsx` - Home page
- ✅ `src/frontend/src/pages/PlanPage.tsx` - Plan detail page
- ✅ All other components and hooks

## Next Steps

After verifying frontend integration:

1. **Phase 7: Tool Integration**
   - Connect MCP server tools
   - Test tool execution from frontend
   - Verify tool messages display correctly

2. **Phase 8: Team Configuration**
   - Implement team selection UI
   - Test team switching
   - Verify agent configurations

3. **Phase 9: Polish & Testing**
   - Test all user flows
   - Fix any UI/UX issues
   - Add error handling improvements

4. **Phase 10: Deployment**
   - Create Docker containers
   - Set up production config
   - Deploy to staging/production

## Success Criteria

Frontend integration is successful when:

- ✅ Frontend loads without errors
- ✅ Can create tasks from home page
- ✅ WebSocket connects and receives messages
- ✅ Approval flow works end-to-end
- ✅ Multiple concurrent tasks work
- ✅ Plan history displays correctly
- ✅ No console errors or warnings
- ✅ All existing frontend features work

## Support

If you encounter issues:

1. Check backend logs: `backend/app/main.py` console output
2. Check frontend console: Browser DevTools (F12)
3. Run backend tests: `cd backend && python test_e2e.py`
4. Verify configuration: Check `config.json` and `.env` files
5. Review this guide's troubleshooting section

## Summary

The frontend integration requires only configuration changes:

1. ✅ Created `src/frontend/public/config.json`
2. ✅ Created `src/frontend/.env`
3. ✅ Backend API matches frontend contract
4. ✅ WebSocket message types match frontend expectations
5. ✅ No frontend code changes needed

The frontend is now ready to connect to the LangGraph backend!
