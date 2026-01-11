# API Documentation v3 - LangGraph Orchestrator Simplification

## Overview

This document describes the updated API v3 endpoints following the LangGraph Orchestrator Simplification. The system now uses AI-driven planning and linear execution patterns instead of complex routing logic.

## Key Changes

### 1. AI-Driven Task Processing
- **NEW**: AI Planner automatically generates optimal agent sequences
- **NEW**: Dynamic workflow creation based on task complexity
- **IMPROVED**: Intelligent agent selection and routing

### 2. Linear Execution Model
- **REMOVED**: Complex supervisor routing logic
- **NEW**: Linear graph execution with automatic progression
- **IMPROVED**: Predictable workflow execution without infinite loops

### 3. Enhanced HITL (Human-in-the-Loop)
- **NEW**: LangGraph state-based approval system
- **IMPROVED**: Plan approval and revision workflows
- **NEW**: Real-time WebSocket communication for approvals

## Core Endpoints

### POST /api/v3/process_request
**Description**: Process a new task request using AI Planner for dynamic agent sequence generation.

**Request Body**:
```json
{
  "description": "string (required) - Task description",
  "session_id": "string (optional) - Session identifier",
  "team_id": "string (optional) - Team configuration ID"
}
```

**Response**:
```json
{
  "plan_id": "string - Unique plan identifier",
  "status": "string - Plan status (created/pending)",
  "session_id": "string - Session identifier"
}
```

**AI Planning Process**:
1. Task analysis using LLM for complexity assessment
2. Agent sequence generation based on task requirements
3. Graph creation using LinearGraphFactory
4. Background execution with real-time updates

### POST /api/v3/process_request_ai
**Description**: Enhanced AI-driven request processing with comprehensive task analysis.

**Features**:
- Full AI workflow analysis
- Complexity-based agent selection
- Detailed reasoning for agent choices
- Estimated execution duration

**Request/Response**: Same as `/process_request` but with enhanced AI analysis.

### GET /api/v3/plans
**Description**: Retrieve all plans, optionally filtered by session.

**Query Parameters**:
- `session_id` (optional): Filter plans by session

**Response**:
```json
[
  {
    "id": "string",
    "session_id": "string",
    "description": "string",
    "status": "string",
    "steps": [
      {
        "id": "string",
        "description": "string",
        "agent": "string",
        "status": "string"
      }
    ]
  }
]
```

### GET /api/v3/plan
**Description**: Get detailed plan information with messages.

**Query Parameters**:
- `plan_id` (required): Plan identifier

**Response**:
```json
{
  "plan": {
    "id": "string",
    "description": "string",
    "status": "string",
    "steps": []
  },
  "messages": [
    {
      "plan_id": "string",
      "agent_name": "string",
      "content": "string",
      "timestamp": "string"
    }
  ],
  "m_plan": null,
  "team": null,
  "streaming_message": null
}
```

## HITL Approval Endpoints

### POST /api/v3/plan_approval
**Description**: Handle plan approval/rejection using new HITL system.

**Request Body**:
```json
{
  "m_plan_id": "string (required) - Plan identifier",
  "approved": "boolean (required) - Approval decision",
  "feedback": "string (optional) - User feedback"
}
```

**Response**:
```json
{
  "status": "string - processing/rejected/error",
  "message": "string - Status description"
}
```

**Workflow**:
1. **Approved**: Updates LangGraph state and resumes execution
2. **Rejected**: Terminates workflow and sends rejection message via WebSocket

### POST /api/v3/user_clarification
**Description**: Handle user clarification responses with revision support.

**Request Body**:
```json
{
  "plan_id": "string (required) - Plan identifier",
  "request_id": "string (optional) - Request identifier",
  "answer": "string (required) - User response"
}
```

**Response**:
```json
{
  "status": "string - approved/revision/processing",
  "session_id": "string - Session identifier"
}
```

**Logic**:
- **Approval keywords** ("OK", "YES", "APPROVE"): Completes task
- **Other responses**: Treated as revision feedback, continues execution

## AI Planning Endpoints

### GET /api/v3/ai_planning/analyze
**Description**: Preview AI task analysis without execution.

**Query Parameters**:
- `task` (required): Task description to analyze

**Response**:
```json
{
  "success": true,
  "analysis": {
    "complexity": "string - low/medium/high",
    "required_systems": ["string"],
    "business_context": "string",
    "data_sources_needed": ["string"],
    "estimated_agents": "number",
    "confidence_score": "number",
    "reasoning": "string"
  }
}
```

### GET /api/v3/ai_planning/sequence
**Description**: Preview AI agent sequence generation.

**Query Parameters**:
- `task` (required): Task description

**Response**:
```json
{
  "success": true,
  "planning_summary": {
    "task_analysis": {
      "complexity": "string",
      "required_systems": ["string"],
      "confidence_score": "number"
    },
    "agent_sequence": {
      "agents": ["string"],
      "reasoning": "string",
      "estimated_duration": "number",
      "complexity_score": "number"
    },
    "total_duration": "number"
  }
}
```

## Team Management

### GET /api/v3/teams
**Description**: Get available team configurations.

**Response**:
```json
[
  {
    "team_id": "string",
    "name": "string",
    "description": "string",
    "agents": [
      {
        "name": "string",
        "role": "string",
        "instructions": "string"
      }
    ]
  }
]
```

### POST /api/v3/init_team
**Description**: Initialize team with AI planning support.

**Query Parameters**:
- `team_switched` (optional): Boolean indicating team switch

**Response**:
```json
{
  "status": "initialized",
  "team_id": "string",
  "ai_planning_enabled": "boolean",
  "available_agents": ["string"],
  "capabilities": {
    "agent_name": ["capability"]
  }
}
```

## WebSocket Communication

### WS /api/v3/socket/{plan_id}
**Description**: Real-time communication for workflow updates.

**Query Parameters**:
- `user_id` (required): User identifier

**Message Types**:

#### agent_message
```json
{
  "type": "agent_message",
  "data": {
    "agent_name": "string",
    "content": "string",
    "timestamp": "string"
  }
}
```

#### agent_message_streaming
```json
{
  "type": "agent_message_streaming",
  "data": {
    "agent_name": "string",
    "content": "string",
    "is_complete": "boolean"
  }
}
```

#### plan_approval_request
```json
{
  "type": "plan_approval_request",
  "data": {
    "plan_id": "string",
    "plan_steps": ["string"],
    "reasoning": "string",
    "requires_approval": "boolean"
  }
}
```

#### user_clarification_request
```json
{
  "type": "user_clarification_request",
  "data": {
    "request_id": "string",
    "question": "string",
    "context": "string"
  }
}
```

#### final_result_message
```json
{
  "type": "final_result_message",
  "data": {
    "content": "string",
    "status": "string",
    "timestamp": "string"
  }
}
```

## Error Handling

### Standard Error Response
```json
{
  "detail": "string - Error description",
  "status_code": "number - HTTP status code"
}
```

### Common Status Codes
- **400**: Bad Request - Invalid parameters
- **404**: Not Found - Resource not found
- **500**: Internal Server Error - System error

## Migration Notes

### From Old System
1. **Routing Logic**: No longer need to specify `next_agent` in requests
2. **AI Planning**: System automatically determines optimal agent sequences
3. **HITL Workflows**: New state-based approval system replaces old callback methods
4. **WebSocket Messages**: Enhanced message types for better real-time communication

### Backward Compatibility
- All existing endpoints remain functional
- Old routing parameters are ignored (no errors)
- Frontend requires no changes except API URL configuration

## Performance Improvements

### Graph Caching
- Compiled graphs are cached for performance
- Cache hit rates typically >80% for common workflows
- Automatic cache cleanup and optimization

### AI Planning Optimization
- Task analysis cached for similar requests
- Agent sequence generation optimized for common patterns
- Fallback sequences for AI planning failures

### Linear Execution Benefits
- Predictable execution times
- No infinite loop possibilities
- Simplified debugging and monitoring

## Security Considerations

### Input Validation
- All user inputs validated using Pydantic models
- SQL injection prevention through parameterized queries
- XSS protection for WebSocket messages

### Rate Limiting
- API endpoints have built-in rate limiting
- WebSocket connections limited per user
- Concurrent workflow limits enforced

## Monitoring and Logging

### Performance Metrics
- Workflow execution times tracked
- Agent performance statistics
- Cache hit rates monitored
- Memory usage optimization

### Error Tracking
- Comprehensive error logging
- Workflow failure analysis
- Real-time error notifications via WebSocket

## Examples

### Basic Task Submission
```bash
curl -X POST "http://localhost:8000/api/v3/process_request" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Verify invoice INV-123456 against Zoho and Salesforce data"
  }'
```

### AI Planning Preview
```bash
curl "http://localhost:8000/api/v3/ai_planning/analyze?task=Analyze customer payment patterns"
```

### Plan Approval
```bash
curl -X POST "http://localhost:8000/api/v3/plan_approval" \
  -H "Content-Type: application/json" \
  -d '{
    "m_plan_id": "plan-uuid",
    "approved": true,
    "feedback": "Looks good, proceed"
  }'
```

## Support

For technical support or questions about the API, please refer to:
- System logs for debugging information
- Performance monitoring dashboard
- WebSocket message inspection tools