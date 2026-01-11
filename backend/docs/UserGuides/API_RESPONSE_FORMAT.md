# API Response Format Documentation

## GET /api/v3/plan Response Format

This document defines the expected response format for the GET /api/v3/plan endpoint to ensure consistency between WebSocket and non-WebSocket execution modes.

### Response Structure

```json
{
  "plan": {
    "id": "string (UUID)",
    "session_id": "string (UUID)", 
    "description": "string",
    "status": "pending|in_progress|completed|failed|approved|rejected",
    "steps": [
      {
        "id": "string",
        "description": "string", 
        "agent": "string",
        "status": "string"
      }
    ]
  },
  "messages": [
    {
      "plan_id": "string (UUID)",
      "agent_name": "string",
      "agent_type": "string", 
      "content": "string",
      "timestamp": "string (ISO 8601)",
      "metadata": {}
    }
  ],
  "m_plan": null,
  "team": null,
  "streaming_message": null
}
```

### Field Descriptions

#### Plan Object
- `id`: Unique plan identifier (UUID format)
- `session_id`: Session identifier (UUID format)
- `description`: Human-readable task description
- `status`: Current plan status (enum values)
- `steps`: Array of execution steps

#### Step Object
- `id`: Unique step identifier
- `description`: Step description
- `agent`: Agent responsible for the step
- `status`: Step execution status

#### Message Object
- `plan_id`: Plan identifier this message belongs to
- `agent_name`: Name of the agent that generated the message
- `agent_type`: Type/category of the agent
- `content`: Message content (text)
- `timestamp`: ISO 8601 formatted timestamp
- `metadata`: Additional metadata (object)

#### Optional Fields
- `m_plan`: Reserved for future use (currently null)
- `team`: Team configuration (currently null)
- `streaming_message`: Current streaming message (currently null)

### Format Consistency Requirements

1. **Message Persistence Independence**: Messages must be retrievable regardless of WebSocket connection status
2. **Timestamp Format**: All timestamps must be ISO 8601 format with UTC timezone
3. **Field Types**: All fields must maintain consistent types across retrieval methods
4. **Required Fields**: All required fields must be present in every response
5. **Null Handling**: Optional fields should be explicitly null rather than missing

### Validation Rules

#### Message Validation
- `plan_id`: Must be non-empty string
- `agent_name`: Must be non-empty string  
- `agent_type`: Must be valid agent type
- `content`: Must be non-empty string
- `timestamp`: Must be valid ISO 8601 datetime
- `metadata`: Must be valid JSON object

#### Plan Validation
- `id`: Must be valid UUID format
- `session_id`: Must be valid UUID format
- `description`: Must be non-empty string
- `status`: Must be one of the valid status values
- `steps`: Must be array of valid step objects

### Error Responses

#### 404 Not Found
```json
{
  "detail": "Plan not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

### Implementation Notes

1. **Database Retrieval**: Messages are retrieved using MessagePersistenceService
2. **Chronological Ordering**: Messages are returned in chronological order by timestamp
3. **Format Consistency**: Same format whether messages were saved via WebSocket or direct database persistence
4. **Error Handling**: Graceful handling of missing plans or database errors

### Testing

The format consistency is validated by:
- Unit tests for message structure validation
- Integration tests for API endpoint responses
- Format consistency tests between WebSocket and database retrieval

### Version History

- v1.0: Initial format definition for Task 4.3 (Fix Message Persistence Without WebSocket)