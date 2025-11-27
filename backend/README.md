# MACAE LangGraph Backend

Multi-Agent Custom Automation Engine with LangGraph orchestration.

## Phase 1: Foundation Setup

### Prerequisites
- Python 3.9+
- Docker (for MongoDB)

### Setup Instructions

1. **Start MongoDB**:
```bash
cd backend
docker-compose up -d mongodb
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
pip install httpx  # For testing
pip install -U langgraph  # LangGraph framework
pip install websockets  # For WebSocket testing
npm install -g wscat  # Optional: WebSocket CLI tool
```

4. **Create .env file**:
```bash
cp .env.example .env
```

5. **Run Phase 1 validation tests**:
```bash
python test_phase1.py
```

6. **Start the backend server**:
```bash
python -m app.main
# Or use uvicorn directly:
uvicorn app.main:app --reload
```

7. **Test health endpoint**:
```bash
curl http://localhost:8000/health
```

### Expected Output

Health check should return:
```json
{
  "status": "healthy",
  "service": "macae-langgraph-backend",
  "version": "0.1.0"
}
```

## Current Status

✅ Phase 1: Foundation Setup & Validation - COMPLETE
- Backend project structure created
- MongoDB connectivity working
- Basic FastAPI app with health check
- CRUD operations validated

✅ Phase 2: Data Models & Basic API - COMPLETE
- Pydantic models for Plan, Step, AgentMessage, Team
- Database repositories for plans and messages
- POST /api/v3/process_request endpoint
- GET /api/v3/plans endpoint
- GET /api/v3/plan endpoint

✅ Phase 3: Simple LangGraph Agent - COMPLETE
- AgentState TypedDict for workflow state
- Planner agent node with hardcoded responses
- LangGraph workflow with entry point and end
- AgentService for orchestration
- Background task execution
- Message storage in MongoDB
- Plan status updates (pending → in_progress → completed)

✅ Phase 4: WebSocket Streaming (Simplified) - COMPLETE
- WebSocketManager for connection tracking
- WebSocket endpoint at /api/v3/socket/{plan_id}
- Real-time agent_message streaming
- Final_result_message on completion
- Multiple concurrent connections support
- Graceful connection cleanup
- Integration with AgentService

✅ Phase 5: Multi-Agent Collaboration - COMPLETE
- Supervisor router for agent selection
- Invoice Agent (invoice management tasks)
- Closing Agent (closing process automation)
- Audit Agent (audit automation tasks)
- Conditional routing based on task keywords
- Multi-agent message streaming via WebSocket
- Sequential agent execution (Planner → Supervisor → Specialized Agent)

✅ Phase 6: Human-in-the-Loop (Basic) - COMPLETE
- Approval checkpoint node with LangGraph interrupt
- POST /api/v3/plan_approval endpoint
- plan_approval_request WebSocket message
- Execution pause and resume with checkpointing
- Approval/rejection handling
- Plan status updates (pending_approval → completed/rejected)
- Thread config storage for resuming execution

### Phase 6 Testing

1. **Start the backend** (in one terminal):
```bash
python -m app.main
```

2. **Run Phase 6 tests** (in another terminal):
```bash
python test_phase6.py
```

## Prototype Complete!

All 6 phases of the prototype are now complete. The backend provides:
- Multi-agent collaboration with LangGraph
- Real-time WebSocket streaming
- Human-in-the-loop approval flow
- Full API compatibility with the MACAE frontend
