---
inclusion: always
---

# LangGraph Migration Development Guide

## Project Overview

This steering document provides development guidelines for migrating the Multi-Agent Custom Automation Engine (MACAE) from an Azure-based backend to an open-source LangGraph-based backend while preserving the existing React frontend.

**Migration Goal**: Build a working prototype that replaces Azure AI Foundry, Semantic Kernel, and Azure services with LangGraph, FastAPI, and open-source alternatives while maintaining 100% frontend compatibility. The prototype focuses on core functionality with simplified implementations that can be extended for production later.

---

## Architecture Principles

### Backend Architecture
- **Framework**: FastAPI for REST API and WebSocket endpoints
- **Agent Orchestration**: LangGraph multi-agent collaboration pattern
- **Database**: MongoDB for document storage (plans, messages, teams, sessions)
- **Real-time Communication**: WebSocket for streaming agent responses
- **LLM Provider**: Configurable (Ollama for local, OpenAI API, Anthropic)
- **Tool Integration**: Existing FastMCP server (unchanged)

### Frontend Architecture (Preserved)
- **Framework**: React 18 with TypeScript
- **UI Library**: Fluent UI React Components
- **Build Tool**: Vite
- **State Management**: React hooks with service layer pattern
- **API Communication**: Axios with custom API client
- **Real-time Updates**: WebSocket service

---

## Development Standards

### Python Backend Standards

#### Code Style
- **Formatter**: Black (line length: 88)
- **Linter**: Ruff for fast linting
- **Type Checking**: mypy with strict mode
- **Import Sorting**: isort with Black-compatible profile

#### Project Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   └── v3/
│   │       ├── routes.py    # REST endpoints
│   │       └── websocket.py # WebSocket handlers
│   ├── agents/
│   │   ├── graph.py         # LangGraph workflow definition
│   │   ├── nodes.py         # Agent node implementations
│   │   ├── supervisor.py    # Supervisor/router logic
│   │   └── tools.py         # Tool definitions
│   ├── models/
│   │   ├── plan.py          # Plan data models
│   │   ├── message.py       # Message data models
│   │   └── team.py          # Team configuration models
│   ├── services/
│   │   ├── plan_service.py  # Plan management logic
│   │   ├── agent_service.py # Agent orchestration
│   │   └── websocket_service.py # WebSocket management
│   └── db/
│       ├── mongodb.py       # Database connection
│       └── repositories.py  # Data access layer
├── tests/
├── requirements.txt
├── pyproject.toml
└── docker-compose.yml
```

#### Dependencies Management
- Use `requirements.txt` for production dependencies
- Use `requirements-dev.txt` for development dependencies
- Pin major versions, allow minor/patch updates (e.g., `fastapi>=0.104.0,<0.105.0`)
- Document why each dependency is needed

#### Error Handling
- Use custom exception classes for domain errors
- Return appropriate HTTP status codes (400, 404, 500, etc.)
- Log all errors with context (request ID, user ID, plan ID)
- Never expose internal errors to clients

#### Async/Await
- Use async/await for all I/O operations (database, HTTP, LLM calls)
- Use `asyncio.gather()` for concurrent operations
- Implement proper timeout handling
- Use connection pooling for database connections

### TypeScript Frontend Standards (Existing)

#### Code Style
- **Linter**: ESLint with React plugin
- **Formatter**: Prettier
- **Type Checking**: TypeScript strict mode enabled

#### API Contract Compliance
- All API responses must match existing TypeScript interfaces
- WebSocket message types must match `WebsocketMessageType` enum
- Maintain backward compatibility with existing frontend code

---

## API Contract Requirements

### REST Endpoints (Must Implement)

#### 1. Process Request
```
POST /api/v3/process_request
Request: { description: string, session_id?: string, team_id?: string }
Response: { plan_id: string, status: string, session_id: string }
```

#### 2. Get Plans
```
GET /api/v3/plans?session_id={session_id}
Response: Plan[]
```

#### 3. Get Plan by ID
```
GET /api/v3/plan?plan_id={plan_id}
Response: {
  plan: Plan,
  messages: AgentMessage[],
  m_plan: MPlan | null,
  team: TeamConfiguration | null,
  streaming_message: string | null
}
```

#### 4. Plan Approval
```
POST /api/v3/plan_approval
Request: { m_plan_id: string, approved: boolean, feedback?: string }
Response: { status: string }
```

#### 5. User Clarification
```
POST /api/v3/user_clarification
Request: { request_id: string, answer: string, plan_id: string, m_plan_id: string }
Response: { status: string, session_id: string }
```

#### 6. Agent Message
```
POST /api/v3/agent_message
Request: { agent: string, agent_type: string, content: string, ... }
Response: AgentMessage
```

#### 7. Get Teams
```
GET /api/v3/teams
Response: TeamConfiguration[]
```

#### 8. Initialize Team
```
POST /api/v3/init_team?team_switched={boolean}
Response: { status: string, team_id: string }
```

### WebSocket Endpoint (Must Implement)

```
WS /api/v3/socket/{plan_id}?user_id={user_id}
```

#### Required Message Types
- `agent_message`: Agent response with content
- `agent_message_streaming`: Token-by-token streaming
- `plan_approval_request`: Request human approval for plan
- `plan_approval_response`: Response to approval request
- `user_clarification_request`: Request clarification from user
- `user_clarification_response`: Response to clarification
- `agent_tool_message`: Tool execution updates
- `final_result_message`: Final task completion message
- `agent_stream_start`: Start of streaming response
- `agent_stream_end`: End of streaming response
- `system_message`: System-level notifications

---

## LangGraph Integration Guidelines

### Agent Definition Pattern

Based on the LangGraph multi-agent collaboration tutorial:

1. **Define Agent State**: Create TypedDict with all required fields
2. **Create Agent Nodes**: One function per agent (HR, Tech Support, Marketing, Product)
3. **Implement Supervisor**: Router that decides which agent to call next
4. **Build Graph**: Connect nodes with conditional edges
5. **Add Checkpointing**: Enable state persistence for human-in-the-loop

### Agent Domains

Map MACAE agents to LangGraph nodes:
- **Planner Agent**: Initial task analysis and plan creation
- **Invoice Agent**: Manage invoices (accuracy, due date, payment status, complaints)
- **Closing Agent**: Close process automation (reconcilliations, draft journal entries, GL anomalies, Variance analysis)
- **Audit Agent**: Audit automation (continuous monitoring, audit evidence, exception detection,audit responses)
- **Contract Agent**: Contract Accounting (Contract summaries, accounting memos, revenue schedules, ERP validation)
- **Procurement Agent**: Prcurement Management  (classify spend, duplicate or suspicious invoices, risk analysis, contract summaries)
- **Supervisor Agent**: Routes tasks to appropriate agents

### Tool Integration

- Keep existing FastMCP server unchanged
- Create LangChain tool wrappers that call MCP endpoints
- Register tools with appropriate agents based on domain
- Implement tool result parsing and error handling

### Human-in-the-Loop

Implement two patterns:
1. **Plan Approval**: Pause execution, send plan via WebSocket, wait for approval
2. **Clarification**: Pause execution, request information, resume with response

Use LangGraph's interrupt mechanism for pausing execution.

---

## Database Schema

### Collections

#### plans
```json
{
  "_id": "ObjectId",
  "plan_id": "string (UUID)",
  "session_id": "string (UUID)",
  "user_id": "string",
  "description": "string",
  "status": "pending | in_progress | completed | failed",
  "steps": [
    {
      "id": "string",
      "description": "string",
      "agent": "string",
      "status": "string",
      "result": "string | null"
    }
  ],
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

#### messages
```json
{
  "_id": "ObjectId",
  "plan_id": "string",
  "agent_name": "string",
  "agent_type": "string",
  "content": "string",
  "timestamp": "ISODate",
  "metadata": {}
}
```

#### teams
```json
{
  "_id": "ObjectId",
  "team_id": "string (UUID)",
  "name": "string",
  "description": "string",
  "agents": [
    {
      "name": "string",
      "role": "string",
      "instructions": "string"
    }
  ],
  "created_at": "ISODate"
}
```

#### sessions
```json
{
  "_id": "ObjectId",
  "session_id": "string (UUID)",
  "user_id": "string",
  "team_id": "string",
  "created_at": "ISODate",
  "last_activity": "ISODate"
}
```

---

## Testing Requirements

### Backend Testing

#### Unit Tests
- Test each agent node independently
- Test supervisor routing logic
- Test tool calling and response parsing
- Test database repositories
- Target: 80% code coverage

#### Integration Tests
- Test complete LangGraph workflow execution
- Test API endpoints with database
- Test WebSocket message flow
- Test human-in-the-loop interrupts

#### End-to-End Tests
- Test full task submission to completion
- Test multi-agent collaboration
- Test plan approval flow
- Test clarification flow
- Test error scenarios

### Frontend Testing (Existing)
- Maintain existing Vitest tests
- Add tests for new API interactions if needed

---

## Environment Configuration

### Backend Environment Variables

```bash
# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=macae_db

# LLM Provider (choose one)
LLM_PROVIDER=ollama  # or openai, anthropic
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# MCP Server
MCP_SERVER_URL=http://localhost:9000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
```

### Frontend Environment Variables

```bash
REACT_APP_API_URL=http://localhost:8000
```

---

## Development Workflow

### Local Development Setup

1. **Start MongoDB**: `docker-compose up -d mongodb`
2. **Start MCP Server**: `cd src/mcp_server && python mcp_server.py`
3. **Start Backend**: `cd backend && uvicorn app.main:app --reload`
4. **Start Frontend**: `cd src/frontend && npm run dev`

### Git Workflow

- **Main Branch**: Production-ready code
- **Develop Branch**: Integration branch for features
- **Feature Branches**: `feature/description`
- **Bugfix Branches**: `bugfix/description`

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example: `feat(agents): implement Invoice agent with contract summarization tools`

---

## Deployment Guidelines

### Docker Deployment

Provide `docker-compose.yml` with:
- Backend service
- Frontend service (nginx)
- MongoDB service
- MCP server service
- Ollama service (optional)

### Environment-Specific Configurations

- **Development**: Hot reload, verbose logging, local LLM
- **Staging**: Production-like, test data, monitoring
- **Production**: Optimized, secure, scaled, monitored

---

## Security Considerations

### API Security
- Implement rate limiting on all endpoints
- Add request validation with Pydantic
- Sanitize user inputs
- Implement CORS properly
- Add authentication/authorization (future enhancement)

### Database Security
- Use connection strings with authentication
- Implement least-privilege access
- Enable encryption at rest
- Regular backups

### WebSocket Security
- Validate user_id and plan_id
- Implement connection limits per user
- Add timeout for idle connections
- Validate all incoming messages

---

## Performance Guidelines

### Backend Performance
- Use connection pooling for MongoDB
- Implement caching for team configurations
- Stream large responses via WebSocket
- Use async operations for all I/O
- Implement request timeouts

### Frontend Performance (Existing)
- Maintain existing caching strategy
- Keep WebSocket connection management
- Preserve lazy loading patterns

---

## Monitoring and Logging

### Logging Standards
- Use structured logging (JSON format)
- Include correlation IDs (request_id, plan_id, user_id)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Never log sensitive data (API keys, user data)

### Metrics to Track
- Request latency per endpoint
- WebSocket connection count
- Agent execution time
- Database query performance
- Error rates by type

---

## Documentation Requirements

### Code Documentation
- Docstrings for all public functions and classes
- Type hints for all function parameters and returns
- Inline comments for complex logic
- README.md in each major directory

### API Documentation
- OpenAPI/Swagger documentation (auto-generated by FastAPI)
- WebSocket message type documentation
- Example requests and responses
- Error code documentation

### Deployment Documentation
- Setup instructions for local development
- Docker deployment guide
- Environment variable reference
- Troubleshooting guide

---

## Prototype Development Phases

Each phase is designed to be independently testable with clear validation criteria before moving to the next phase.

---

### Phase 1: Foundation Setup & Validation
**Goal**: Set up minimal working environment with database connectivity

**Tasks**:
- [ ] Create backend project structure following the defined layout
- [ ] Set up MongoDB (Docker or local)
- [ ] Install core dependencies (FastAPI, LangGraph, Motor, Pydantic)
- [ ] Create basic FastAPI app with health check endpoint
- [ ] Implement MongoDB connection with basic CRUD operations

**Validation Tests**:
- [ ] Health check endpoint returns 200 OK
- [ ] MongoDB connection successful
- [ ] Can create and retrieve a test document from MongoDB
- [ ] FastAPI server starts without errors

**Success Criteria**: Backend server runs and connects to database successfully

---

### Phase 2: Data Models & Basic API
**Goal**: Implement core data models and minimal REST endpoints

**Tasks**:
- [ ] Create Pydantic models for Plan, Step, AgentMessage
- [ ] Create simplified Team and Session models
- [ ] Implement database repositories for plans and messages
- [ ] Create POST /api/v3/process_request endpoint (returns mock plan_id)
- [ ] Create GET /api/v3/plans endpoint (returns empty list or mock data)
- [ ] Create GET /api/v3/plan endpoint (returns mock plan structure)

**Validation Tests**:
- [ ] POST /api/v3/process_request returns valid plan_id and session_id
- [ ] GET /api/v3/plans returns properly formatted Plan array
- [ ] GET /api/v3/plan returns complete plan structure matching frontend interface
- [ ] All endpoints return correct HTTP status codes
- [ ] Data models serialize/deserialize correctly

**Success Criteria**: Frontend can call all basic endpoints and receive valid responses

---

### Phase 3: Simple LangGraph Agent
**Goal**: Implement single-agent LangGraph workflow without tools

**Tasks**:
- [ ] Adapt LangGraph multi-agent example to project structure
- [ ] Create AgentState TypedDict with minimal fields
- [ ] Implement single agent node (Planner) with hardcoded responses
- [ ] Build simple graph with entry point and end
- [ ] Integrate graph execution with process_request endpoint
- [ ] Store execution results in MongoDB

**Validation Tests**:
- [ ] LangGraph workflow executes without errors
- [ ] Agent node receives input and produces output
- [ ] Execution results are stored in database
- [ ] Can retrieve execution results via GET /api/v3/plan
- [ ] Graph state transitions correctly

**Success Criteria**: Single agent can process a task and store results

---

### Phase 4: WebSocket Streaming (Simplified)
**Goal**: Implement basic WebSocket connection and message streaming

**Tasks**:
- [ ] Create WebSocket manager for connection tracking
- [ ] Implement WS /api/v3/socket/{plan_id} endpoint
- [ ] Send simple agent_message on connection
- [ ] Send final_result_message after agent completes
- [ ] Handle WebSocket disconnection gracefully

**Validation Tests**:
- [ ] WebSocket connection establishes successfully
- [ ] Frontend receives agent_message via WebSocket
- [ ] Frontend receives final_result_message via WebSocket
- [ ] Connection closes cleanly
- [ ] Multiple concurrent connections work

**Success Criteria**: Frontend displays real-time agent messages via WebSocket

---

### Phase 5: Multi-Agent Collaboration
**Goal**: Add supervisor and multiple specialized agents

**Tasks**:
- [ ] Implement supervisor node with routing logic
- [ ] Create 2-3 specialized agent nodes (Invoice, Closing, Audit)
- [ ] Add conditional edges based on supervisor decisions
- [ ] Update graph to route between agents
- [ ] Stream messages from each agent via WebSocket

**Validation Tests**:
- [ ] Supervisor correctly routes to appropriate agent
- [ ] Multiple agents execute in sequence
- [ ] Each agent's messages appear in frontend
- [ ] Graph completes with all agents contributing
- [ ] Agent routing logic is deterministic and testable

**Success Criteria**: Task is processed by multiple agents with visible collaboration

---

### Phase 6: Human-in-the-Loop (Basic)
**Goal**: Implement plan approval flow without clarification

**Tasks**:
- [ ] Add interrupt to graph after plan creation
- [ ] Implement POST /api/v3/plan_approval endpoint
- [ ] Send plan_approval_request via WebSocket
- [ ] Handle approval response and resume execution
- [ ] Update plan status based on approval

**Validation Tests**:
- [ ] Graph pauses and waits for approval
- [ ] Frontend receives plan_approval_request
- [ ] Approval response resumes execution
- [ ] Rejection stops execution appropriately
- [ ] Plan status updates correctly in database

**Success Criteria**: User can approve/reject plans and execution responds accordingly

---

### Phase 7: Tool Integration (Simplified)
**Goal**: Connect one MCP tool to one agent

**Tasks**:
- [ ] Keep existing MCP server running
- [ ] Create LangChain tool wrapper for one MCP endpoint
- [ ] Register tool with one agent (e.g., Invoice agent)
- [ ] Test tool calling from agent
- [ ] Stream tool execution messages via WebSocket

**Validation Tests**:
- [ ] Agent successfully calls MCP tool
- [ ] Tool response is received and processed
- [ ] Tool execution appears in message stream
- [ ] Tool errors are handled gracefully
- [ ] Frontend displays tool execution updates

**Success Criteria**: Agent can call external tool and use results

---

### Phase 8: Team Configuration (Basic)
**Goal**: Implement basic team selection

**Tasks**:
- [ ] Create GET /api/v3/teams endpoint returning hardcoded teams
- [ ] Create POST /api/v3/init_team endpoint
- [ ] Store team selection in session
- [ ] Load team configuration when processing requests
- [ ] Map team agents to graph nodes

**Validation Tests**:
- [ ] GET /api/v3/teams returns valid team list
- [ ] Team selection persists across requests
- [ ] Different teams use different agent configurations
- [ ] Frontend team selector works with backend

**Success Criteria**: User can select team and agents adjust accordingly

---

### Phase 9: Frontend Integration & Polish
**Goal**: Ensure complete frontend compatibility

**Tasks**:
- [ ] Update frontend API URL configuration
- [ ] Test all frontend pages and components
- [ ] Verify all WebSocket message types display correctly
- [ ] Add missing API endpoints if needed
- [ ] Fix any data format mismatches

**Validation Tests**:
- [ ] Home page loads and displays correctly
- [ ] Task submission works end-to-end
- [ ] Plan page shows agent messages in real-time
- [ ] Plan approval UI functions correctly
- [ ] Team selector works properly
- [ ] No console errors in frontend

**Success Criteria**: Frontend works identically to Azure backend version

---

### Phase 10: Docker & Documentation
**Goal**: Package prototype for easy deployment

**Tasks**:
- [ ] Create Dockerfile for backend
- [ ] Create docker-compose.yml for full stack
- [ ] Write README with setup instructions
- [ ] Document environment variables
- [ ] Create basic troubleshooting guide

**Validation Tests**:
- [ ] Docker containers build successfully
- [ ] docker-compose up starts all services
- [ ] Application works in containerized environment
- [ ] Documentation is clear and complete

**Success Criteria**: Another developer can run the prototype using Docker

---

## Prototype Simplifications

To accelerate prototype development, the following simplifications are acceptable:

### Database
- Single MongoDB instance (no replication)
- Basic indexes only
- No backup strategy initially
- Simple connection pooling

### Security
- No authentication/authorization (add later)
- Basic CORS configuration
- No rate limiting initially
- Simple input validation

### Error Handling
- Basic try/catch blocks
- Simple error messages
- Console logging (no structured logging initially)
- No retry logic

### Performance
- No caching layer
- No load balancing
- Single server instance
- Basic async operations

### Testing
- Manual testing per phase
- No automated test suite initially
- Focus on integration testing
- Add unit tests in production version

### Monitoring
- Console logs only
- No metrics collection
- No alerting
- Basic health checks

### Agent Complexity
- Start with 2-3 agents (not all 6)
- Simple routing logic
- Hardcoded prompts initially
- Basic tool integration (1-2 tools)

### Human-in-the-Loop
- Plan approval only (no clarification initially)
- Simple approve/reject (no modifications)
- No timeout handling initially

---

## Phase Testing Strategy

### Per-Phase Testing Approach

Each phase must pass its validation tests before proceeding to the next phase. Use this testing workflow:

1. **Complete Phase Tasks**: Implement all items in the phase checklist
2. **Run Validation Tests**: Execute all tests listed for that phase
3. **Document Issues**: Record any failures or unexpected behavior
4. **Fix and Retest**: Address issues and rerun tests until all pass
5. **Commit Code**: Commit working code with clear commit message
6. **Move to Next Phase**: Only proceed when all tests pass

### Testing Tools

- **API Testing**: Use Postman, curl, or httpie for endpoint testing
- **WebSocket Testing**: Use browser DevTools or wscat for WebSocket testing
- **Database Testing**: Use MongoDB Compass or mongosh for data verification
- **Frontend Testing**: Manual testing in browser with DevTools open
- **Integration Testing**: Test complete flows from frontend to database

### Test Data

Create simple test data for each phase:
- **Phase 2**: Mock plans with 2-3 steps
- **Phase 3**: Simple task descriptions
- **Phase 5**: Tasks requiring multiple agents
- **Phase 6**: Plans requiring approval
- **Phase 7**: Tasks requiring tool usage

---

## Production Extension Path

After prototype validation, extend to production with:

1. **Security**: Add authentication, authorization, rate limiting
2. **Testing**: Add comprehensive unit and integration test suites
3. **Monitoring**: Add structured logging, metrics, alerting
4. **Performance**: Add caching, connection pooling, optimization
5. **Reliability**: Add error recovery, retries, circuit breakers
6. **Scalability**: Add load balancing, horizontal scaling
7. **All Agents**: Implement remaining agents (Contract, Procurement)
8. **Full HITL**: Add clarification flow and timeout handling
9. **All Tools**: Connect all MCP tools to appropriate agents
10. **Documentation**: Complete API docs, deployment guides, runbooks

---

## Prototype Success Criteria

### Minimum Viable Prototype
- ✅ Frontend works without code changes (except API URL)
- ✅ Core API endpoints return correct data structures
- ✅ WebSocket streaming works for agent messages and final results
- ✅ Plan approval flow functions correctly
- ✅ Multi-agent collaboration executes with 2-3 agents
- ✅ Database persists plans and messages
- ✅ Single user can complete full task workflow
- ✅ Basic documentation exists for setup and usage

### Optional Enhancements (Post-Prototype)
- ⚪ Clarification requests work end-to-end
- ⚪ All 6 agents implemented
- ⚪ All MCP tools connected
- ⚪ System handles concurrent users
- ⚪ Automated tests achieve 80% coverage
- ⚪ Production-ready error handling
- ⚪ Performance optimization
- ⚪ Security hardening
- ⚪ Comprehensive documentation

---

## References

- [LangGraph Multi-Agent Collaboration Tutorial](https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/multi_agent/multi-agent-collaboration.ipynb)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Motor Documentation](https://motor.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [MACAE Frontend API Contract](../../../src/frontend/src/api/apiService.tsx)
