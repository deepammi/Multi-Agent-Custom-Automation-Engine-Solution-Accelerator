# Design Document: Team JSON Upload Feature

## Overview

This feature enables users to upload team configurations via JSON files to customize the available teams in the application. The system validates the uploaded JSON structure, stores team configurations in MongoDB, and makes them immediately available for selection in the UI. The Current Team section in the left panel displays the selected team's information including name, description, and agent details.

## Architecture

### High-Level Flow

```
User selects JSON file
    ↓
Frontend validates file format
    ↓
Frontend sends JSON to backend API
    ↓
Backend validates team structure
    ↓
Backend stores teams in MongoDB
    ↓
Backend returns success response
    ↓
Frontend refreshes team list
    ↓
User sees uploaded teams in selector
```

### Component Interaction

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  TeamSelector   │────────▶│  TeamService     │────────▶│  API Client │
│  (UI Component) │         │  (Frontend)      │         │             │
└─────────────────┘         └──────────────────┘         └──────┬──────┘
                                                                  │
                                                                  │ HTTP POST
                                                                  │
                                                                  ▼
                                                          ┌──────────────┐
                                                          │  Backend API │
                                                          │  /teams/upload│
                                                          └──────┬───────┘
                                                                  │
                                                                  ▼
                                                          ┌──────────────┐
                                                          │   MongoDB    │
                                                          │   teams      │
                                                          │  collection  │
                                                          └──────────────┘
```

## Components and Interfaces

### Frontend Components

#### 1. TeamSelector Component
**Location**: `src/frontend/src/components/common/TeamSelector.tsx`

**Responsibilities**:
- Render file upload UI with drag-and-drop support
- Validate JSON file format before upload
- Display upload progress and status messages
- Handle upload success/error states
- Refresh team list after successful upload

**Key Methods**:
- `handleFileUpload(file: File)`: Process file upload
- `validateJSONStructure(json: any)`: Client-side validation
- `handleDrop(event: DragEvent)`: Handle drag-and-drop
- `showUploadFeedback(message: string, type: 'success' | 'error')`: Display feedback

#### 2. TeamService
**Location**: `src/frontend/src/services/TeamService.tsx`

**Responsibilities**:
- Communicate with backend API for team operations
- Validate team configuration structure
- Store selected team in localStorage
- Retrieve team list from backend

**Key Methods**:
```typescript
static async uploadCustomTeam(teamFile: File): Promise<{
    success: boolean;
    team?: TeamConfig;
    error?: string;
}>

static async getUserTeams(): Promise<TeamConfig[]>

static validateTeamConfig(config: any): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
}
```

#### 3. Current Team Display
**Location**: `src/frontend/src/components/content/PlanPanelLeft.tsx`

**Responsibilities**:
- Display currently selected team information
- Show team name, description, and agent list
- Persist team selection across page navigation
- Update when team selection changes

### Backend Components

#### 1. Upload Endpoint
**Location**: `backend/app/api/v3/routes.py`

**Current Implementation**:
```python
@router.post("/teams/upload")
async def upload_teams(teams_data: dict):
    """Upload team configurations from JSON file."""
```

**Responsibilities**:
- Receive team configuration JSON
- Validate team structure using Pydantic models
- Store teams in MongoDB
- Return success response with uploaded teams

**Request Format**:
```json
{
  "teams": [
    {
      "team_id": "string",
      "name": "string",
      "description": "string",
      "agents": [...]
    }
  ]
}
```

**Response Format**:
```json
{
  "status": "success",
  "message": "Uploaded N teams",
  "teams": [...]
}
```

#### 2. Team Models
**Location**: `backend/app/models/team.py`

**Models**:
```python
class Agent(BaseModel):
    name: str
    role: str
    instructions: str

class TeamConfiguration(BaseModel):
    team_id: str
    name: str
    description: str
    agents: List[Agent]
    created_at: datetime
```

#### 3. MongoDB Repository
**Location**: `backend/app/db/repositories.py`

**Operations**:
- `insert_teams(teams: List[TeamConfiguration])`: Bulk insert teams
- `get_all_teams()`: Retrieve all teams
- `delete_all_teams()`: Clear existing teams before upload

## Data Models

### Frontend Team Configuration

```typescript
interface TeamConfig {
    id: string;
    team_id: string;
    name: string;
    description: string;
    status: 'visible' | 'hidden';
    protected?: boolean;
    created: string;
    created_by: string;
    logo: string;
    plan: string;
    agents: Agent[];
    starting_tasks: StartingTask[];
}

interface Agent {
    input_key: string;
    type: string;
    name: string;
    role?: string;
    system_message?: string;
    description?: string;
    deployment_name?: string;
    use_rag?: boolean;
    use_mcp?: boolean;
    coding_tools?: boolean;
}
```

### Backend Team Configuration

```python
class Agent(BaseModel):
    name: str
    role: str
    instructions: str

class TeamConfiguration(BaseModel):
    team_id: str
    name: str
    description: str
    agents: List[Agent]
    created_at: datetime
```

### Data Model Mapping

The frontend and backend use different field names for agent configuration:
- Frontend: `system_message` → Backend: `instructions`
- Frontend: `role` (optional) → Backend: `role` (required)

The upload process must handle this mapping to ensure compatibility.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated:

**Redundancies Identified**:
1. Properties 2.1, 2.2, and 2.3 (displaying team name, description, and agents) can be combined into a single comprehensive property about complete team information display
2. Properties 5.1, 5.2, and 5.3 (loading, validation, and upload status messages) can be combined into a single property about status feedback throughout the upload process
3. Properties 1.3 and 5.4 (success messages) are redundant - both test that success messages appear with appropriate information
4. Properties 1.4 and 5.5 (error messages) are redundant - both test that error messages provide clear feedback

**Consolidated Properties**:
- Combine 2.1, 2.2, 2.3 → Property about complete team information display
- Combine 5.1, 5.2, 5.3 → Property about continuous status feedback
- Combine 1.3, 5.4 → Single property about success feedback
- Combine 1.4, 5.5 → Single property about error feedback

### Correctness Properties

Property 1: JSON validation correctness
*For any* uploaded file, the validation function should accept files that conform to the team configuration schema and reject files that do not, returning specific validation errors for non-conforming files
**Validates: Requirements 1.1, 1.4**

Property 2: Database storage consistency
*For any* valid team configuration, after successful upload, querying the database should return the exact team data that was uploaded
**Validates: Requirements 1.2, 3.5**

Property 3: Team availability after upload
*For any* successfully uploaded team, the team should immediately appear in the team selector without requiring a page refresh
**Validates: Requirements 1.5**

Property 4: Complete team information display
*For any* selected team, the Current Team section should display the team name, description, and all agents with their roles
**Validates: Requirements 2.1, 2.2, 2.3**

Property 5: Team selection persistence
*For any* selected team, navigating to different pages and returning should preserve the team selection and display the same team information
**Validates: Requirements 2.5**

Property 6: Data model mapping consistency
*For any* team configuration, the transformation between frontend and backend data models should preserve all essential information (name, description, agents, roles, instructions)
**Validates: Requirements 3.2**

Property 7: API contract compliance
*For any* upload request, the backend response structure should match the frontend's expected interface with status, message, and teams fields
**Validates: Requirements 3.3**

Property 8: HTTP status code correctness
*For any* API request, successful operations should return 2xx status codes and errors should return appropriate 4xx or 5xx codes that the frontend can interpret
**Validates: Requirements 3.4**

Property 9: Multiple teams processing
*For any* JSON file containing N teams, the system should process all N teams and store all N teams to the database
**Validates: Requirements 4.1**

Property 10: Independent validation
*For any* set of team configurations where some are valid and some invalid, the validation should identify all invalid teams with specific error messages for each
**Validates: Requirements 4.2, 4.3**

Property 11: Atomic team replacement
*For any* upload operation, either all teams should be stored successfully or no teams should be stored (all-or-nothing atomicity)
**Validates: Requirements 4.4, 4.5**

Property 12: Continuous status feedback
*For any* upload operation, the UI should display appropriate status messages during each phase: loading, validation, uploading, and completion
**Validates: Requirements 5.1, 5.2, 5.3**

Property 13: Success feedback completeness
*For any* successful upload, the success message should include the count of uploaded teams and their names
**Validates: Requirements 1.3, 5.4**

Property 14: Error feedback clarity
*For any* failed upload, the error message should clearly explain what went wrong and provide actionable guidance for fixing the issue
**Validates: Requirements 1.4, 5.5**

## Error Handling

### Frontend Error Handling

**File Validation Errors**:
- Invalid JSON syntax → "Invalid JSON file. Please check the file format."
- Missing required fields → "Missing required field: {field_name}"
- Invalid field types → "Invalid type for field {field_name}: expected {expected_type}"
- Empty teams array → "No teams found in the uploaded file"

**Upload Errors**:
- Network errors → "Network error. Please check your connection and try again."
- Server errors (5xx) → "Server error. Please try again later."
- Validation errors (400) → Display specific validation error from backend
- Timeout errors → "Upload timed out. Please try again."

**Error Display**:
- Show errors in toast notifications with error intent
- Display inline errors in the upload dialog
- Provide "Try Again" action for recoverable errors
- Log errors to console for debugging

### Backend Error Handling

**Validation Errors** (400 Bad Request):
```python
{
    "detail": "Validation error: {specific_error_message}"
}
```

**Database Errors** (500 Internal Server Error):
```python
{
    "detail": "Failed to store teams: {error_message}"
}
```

**Empty Upload** (400 Bad Request):
```python
{
    "detail": "No teams found in upload data"
}
```

**Error Logging**:
- Log all errors with context (user_id, timestamp, error details)
- Include stack traces for server errors
- Track error rates for monitoring

## Testing Strategy

### Unit Testing

**Frontend Unit Tests**:
1. Test `TeamService.validateTeamConfig()` with various valid and invalid configurations
2. Test file upload handler with different file types and sizes
3. Test team selection and storage in localStorage
4. Test error message formatting and display
5. Test data model transformation between frontend and backend formats

**Backend Unit Tests**:
1. Test Pydantic model validation with valid and invalid data
2. Test team upload endpoint with various payloads
3. Test database operations (insert, delete, query)
4. Test error response formatting
5. Test data model serialization/deserialization

### Property-Based Testing

**Testing Framework**: Use `fast-check` for frontend (TypeScript) and `hypothesis` for backend (Python)

**Test Configuration**: Each property-based test should run a minimum of 100 iterations

**Property Test Tagging**: Each test must reference the design document property using this format:
`**Feature: team-json-upload, Property {number}: {property_text}**`

**Frontend Property Tests**:

1. **Property 1 Test**: Generate random JSON structures (valid and invalid) and verify validation correctly accepts/rejects them
   - Generator: Create JSON with varying field presence, types, and values
   - Assertion: Validation result matches expected outcome based on schema

2. **Property 3 Test**: Generate random team configurations, upload them, and verify they appear in the team selector
   - Generator: Create valid team configurations with random names, descriptions, and agents
   - Assertion: Uploaded team appears in selector list

3. **Property 4 Test**: Generate random teams, select them, and verify all information displays correctly
   - Generator: Create teams with varying numbers of agents and field values
   - Assertion: UI displays all team fields correctly

4. **Property 6 Test**: Generate random team data and verify frontend-to-backend transformation preserves information
   - Generator: Create team configurations with all possible field combinations
   - Assertion: Transformed data contains all original information

**Backend Property Tests**:

1. **Property 2 Test**: Generate random valid team configurations, store them, and verify database retrieval returns identical data
   - Generator: Create valid TeamConfiguration objects with random field values
   - Assertion: Retrieved data equals stored data

2. **Property 7 Test**: Generate random upload requests and verify response structure matches expected interface
   - Generator: Create various upload payloads
   - Assertion: Response contains status, message, and teams fields

3. **Property 9 Test**: Generate arrays of N teams and verify all N are processed and stored
   - Generator: Create arrays of varying sizes (1-20 teams)
   - Assertion: Database contains exactly N teams after upload

4. **Property 11 Test**: Generate upload operations and verify atomicity (all-or-nothing)
   - Generator: Create scenarios with database failures mid-operation
   - Assertion: Either all teams stored or none stored

### Integration Testing

**End-to-End Upload Flow**:
1. User selects valid JSON file
2. Frontend validates file
3. Frontend sends to backend
4. Backend stores teams
5. Frontend refreshes team list
6. User sees uploaded teams

**Test Scenarios**:
- Upload single team
- Upload multiple teams (5, 10, 20 teams)
- Upload with invalid JSON
- Upload with missing required fields
- Upload with network interruption
- Upload with database unavailable
- Concurrent uploads from multiple users

**Test Data**:
- Use `SAMPLE_TEAM_CONFIGURATION.json` as baseline
- Generate variations with different team counts
- Create invalid configurations for error testing

### Manual Testing Checklist

- [ ] Upload valid JSON file via file picker
- [ ] Upload valid JSON file via drag-and-drop
- [ ] Upload invalid JSON file and verify error message
- [ ] Upload file with missing required fields
- [ ] Upload multiple teams and verify all appear
- [ ] Select uploaded team and verify Current Team section updates
- [ ] Navigate between pages and verify team selection persists
- [ ] Upload new teams and verify old teams are replaced
- [ ] Test with large JSON files (100+ teams)
- [ ] Test with special characters in team names
- [ ] Test upload cancellation
- [ ] Test concurrent uploads

## Implementation Notes

### API Endpoint Mismatch Fix

**Current Issue**: Frontend calls `/v3/upload_team_config` but backend expects `/teams/upload`

**Solution Options**:
1. **Option A**: Update frontend to call `/v3/teams/upload` (recommended)
   - Change `TeamService.uploadCustomTeam()` to use correct endpoint
   - Minimal backend changes required

2. **Option B**: Add alias route in backend
   - Add `@router.post("/upload_team_config")` that calls `upload_teams()`
   - Maintains backward compatibility

**Recommendation**: Use Option A for cleaner API design

### Data Model Transformation

The frontend and backend use different field structures. The transformation layer should:

1. **Frontend → Backend**:
   ```typescript
   {
     system_message: string  // Frontend
   } → {
     instructions: string    // Backend
   }
   ```

2. **Backend → Frontend**:
   ```python
   {
     instructions: str       // Backend
   } → {
     system_message: string  // Frontend
   }
   ```

Implement transformation in `TeamService` to handle this mapping transparently.

### MongoDB Operations

**Atomic Replacement Strategy**:
```python
async def upload_teams(teams_data: dict):
    # Start transaction
    async with await client.start_session() as session:
        async with session.start_transaction():
            # Delete existing teams
            await teams_collection.delete_many({}, session=session)
            # Insert new teams
            await teams_collection.insert_many(teams_list, session=session)
            # Transaction commits automatically if no errors
```

This ensures atomicity - either all teams are replaced or none are.

### Performance Considerations

**Large File Uploads**:
- Set reasonable file size limit (e.g., 10MB)
- Implement streaming for very large files
- Show progress indicator for uploads > 1MB

**Database Performance**:
- Index `team_id` field for fast lookups
- Use bulk insert for multiple teams
- Implement connection pooling

**Frontend Performance**:
- Debounce file validation
- Use virtual scrolling for large team lists
- Cache team data in memory

## Security Considerations

### Input Validation

**Frontend Validation**:
- Validate file type (must be .json)
- Validate file size (max 10MB)
- Validate JSON structure before upload
- Sanitize team names and descriptions

**Backend Validation**:
- Use Pydantic models for strict type checking
- Validate all required fields
- Sanitize string inputs to prevent injection
- Limit array sizes to prevent DoS

### Access Control

**Future Enhancement** (not in current scope):
- Authenticate users before allowing uploads
- Authorize users to upload teams
- Track who uploaded which teams
- Implement team ownership and permissions

### Data Sanitization

**String Fields**:
- Remove HTML tags from names and descriptions
- Limit string lengths (name: 100 chars, description: 500 chars)
- Escape special characters
- Validate against XSS patterns

**Array Fields**:
- Limit agents array to 20 items
- Limit teams array to 50 items
- Validate array item structure

## Deployment Considerations

### Environment Variables

```bash
# Maximum file upload size (bytes)
MAX_UPLOAD_SIZE=10485760  # 10MB

# Maximum teams per upload
MAX_TEAMS_PER_UPLOAD=50

# Maximum agents per team
MAX_AGENTS_PER_TEAM=20

# Enable team upload feature
ENABLE_TEAM_UPLOAD=true
```

### Database Migration

**Initial Setup**:
```javascript
// Create teams collection with indexes
db.teams.createIndex({ "team_id": 1 }, { unique: true })
db.teams.createIndex({ "name": 1 })
db.teams.createIndex({ "created_at": -1 })
```

**Backward Compatibility**:
- Existing teams in database should remain accessible
- New upload format should support old team structure
- Provide migration script for existing teams

### Monitoring

**Metrics to Track**:
- Upload success rate
- Upload failure rate by error type
- Average upload time
- File size distribution
- Number of teams per upload
- Database storage usage

**Alerts**:
- Upload failure rate > 10%
- Upload time > 30 seconds
- Database storage > 80% capacity
- Validation error rate > 20%

## Future Enhancements

### Phase 2 Features

1. **Team Versioning**:
   - Track team configuration history
   - Allow rollback to previous versions
   - Show diff between versions

2. **Team Templates**:
   - Provide pre-built team templates
   - Allow users to customize templates
   - Share templates between users

3. **Partial Updates**:
   - Update individual teams without replacing all
   - Add/remove agents from existing teams
   - Modify team properties

4. **Validation Enhancements**:
   - Validate agent deployment names against available deployments
   - Check RAG index availability
   - Validate MCP tool availability

5. **Import/Export**:
   - Export current teams to JSON
   - Import teams from other formats (YAML, CSV)
   - Bulk operations on teams

6. **Team Analytics**:
   - Track team usage statistics
   - Show most popular teams
   - Analyze agent performance by team

## References

- [LangGraph Multi-Agent Collaboration](https://github.com/langchain-ai/langgraph)
- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [MongoDB Transactions](https://www.mongodb.com/docs/manual/core/transactions/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)
- [React File Upload Best Practices](https://react.dev/reference/react-dom/components/input#reading-the-files-information-without-reading-their-contents)
