# Workflow Configuration - Complete Summary

## Quick Answer

**How are workflows configured?**

Workflows are configured through a **three-layer architecture**:

1. **Workflow Layer** - Individual workflow files define business logic
2. **Service Layer** - Pattern detection and parameter extraction
3. **API Layer** - REST endpoints expose workflows to clients

**How to add a new workflow?**

1. Create workflow file (30 lines minimum)
2. Register in WorkflowFactory (5 lines)
3. Add detection pattern (3 lines)
4. Add parameter extraction (5 lines)
5. Test (1 command)

**Total time**: ~30 minutes

## Architecture Overview

```
User Input → API → Service Layer → Workflow Layer → Result
                    ↓
              Pattern Detection
              Parameter Extraction
              Smart Routing
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Workflows** | `backend/app/agents/workflows/*.py` | Business logic |
| **Factory** | `backend/app/agents/workflows/factory.py` | Registry |
| **Service** | `backend/app/services/agent_service_refactored.py` | Routing |
| **API** | `backend/app/api/v3/routes.py` | Endpoints |

## Current Workflows

### 1. Invoice Verification
- **Pattern**: "verify invoice", "check invoice"
- **Parameters**: invoice_id, erp_system, crm_system
- **Systems**: Zoho (ERP), Salesforce (CRM)
- **Output**: Verification report with discrepancies

### 2. Payment Tracking
- **Pattern**: "track payment", "payment status"
- **Parameters**: invoice_id, erp_system
- **Systems**: Zoho (ERP), Email
- **Output**: Payment status and recommendations

### 3. Customer 360
- **Pattern**: "customer 360", "customer view"
- **Parameters**: customer_name
- **Systems**: Salesforce (CRM), Zoho (ERP), QuickBooks (Accounting)
- **Output**: Comprehensive customer profile

## Adding New Workflows

### Minimal Example (50 lines)

```python
# 1. Create workflow file
class MyWorkflow:
    @staticmethod
    async def execute(plan_id, session_id, parameters):
        return {
            "status": "completed",
            "messages": ["Step 1", "Step 2"],
            "final_result": "Done!"
        }

# 2. Register in factory
_workflows["my_workflow"] = {
    "executor": MyWorkflow.execute,
    "title": "My Workflow"
}

# 3. Add detection
if "my keyword" in task_lower:
    return "my_workflow"

# 4. Add extraction
if workflow_name == "my_workflow":
    parameters["param"] = extract_value(task)
```

### Complete Example (300 lines)

See `docs/ADDING_WORKFLOW_EXAMPLE.md` for a full expense approval workflow with:
- Policy checking
- Receipt verification
- Approval routing
- Formatted reports

## Agent Interaction Patterns

### Pattern 1: Sequential
Agents execute one after another:
```
Agent1 → Agent2 → Agent3 → Result
```

### Pattern 2: Parallel
Agents execute simultaneously:
```
        ┌─ Agent1 ─┐
Start ──┼─ Agent2 ─┼── Combine → Result
        └─ Agent3 ─┘
```

### Pattern 3: Conditional
Agents execute based on conditions:
```
Check → Yes → Agent A → Result
     → No  → Agent B → Result
```

### Pattern 4: Iterative
Agents loop until condition met:
```
Agent → Check → Done? → Yes → Result
   ↑              ↓
   └──── No ──────┘
```

### Pattern 5: Human-in-the-Loop
Agents pause for human input:
```
Agent → Generate → Pause → Approval → Execute → Result
```

## Configuration Files

### Workflow Definition
```python
# backend/app/agents/workflows/my_workflow.py
class MyWorkflow:
    @staticmethod
    async def execute(plan_id, session_id, parameters):
        # Your logic here
        return result
```

### Registry Entry
```python
# backend/app/agents/workflows/factory.py
_workflows = {
    "my_workflow": {
        "executor": MyWorkflow.execute,
        "title": "My Workflow",
        "description": "What it does",
        "systems": ["System1", "System2"],
        "parameters": ["param1", "param2"]
    }
}
```

### Detection Pattern
```python
# backend/app/services/agent_service_refactored.py
def detect_workflow(task_description):
    if "keyword" in task_description.lower():
        return "my_workflow"
```

### Parameter Extraction
```python
# backend/app/services/agent_service_refactored.py
def extract_parameters(workflow_name, task_description):
    if workflow_name == "my_workflow":
        # Extract using regex
        match = re.search(r'PATTERN', task_description)
        return {"param": match.group(0)}
```

## API Endpoints

### List Workflows
```bash
GET /api/v3/workflows
```

Returns all available workflows with metadata.

### Execute Workflow
```bash
POST /api/v3/execute_workflow
{
  "workflow_name": "my_workflow",
  "plan_id": "plan-123",
  "session_id": "session-456",
  "parameters": {...}
}
```

Executes a specific workflow.

### Smart Routing
```bash
POST /api/v3/process_request_v2
{
  "description": "Natural language task",
  "session_id": "session-456",
  "require_hitl": false
}
```

Automatically detects and executes appropriate workflow.

## Testing

### Unit Test
```python
# Test workflow directly
result = await MyWorkflow.execute(
    plan_id="test",
    session_id="test",
    parameters={"param": "value"}
)
assert result["status"] == "completed"
```

### Integration Test
```python
# Test detection
workflow = AgentServiceRefactored.detect_workflow("my task")
assert workflow == "my_workflow"

# Test extraction
params = AgentServiceRefactored.extract_parameters(workflow, "my task")
assert "param" in params

# Test execution
result = await WorkflowFactory.execute_workflow(
    workflow_name=workflow,
    plan_id="test",
    session_id="test",
    parameters=params
)
assert result["status"] == "completed"
```

### API Test
```bash
# Test via curl
curl -X POST http://localhost:8000/api/v3/process_request_v2 \
  -H "Content-Type: application/json" \
  -d '{"description": "my task", "session_id": "test"}'
```

## Best Practices

### Workflow Design
✅ Single responsibility per workflow
✅ Clear progress messages
✅ Structured output format
✅ Error handling
✅ Parameter validation

### Pattern Detection
✅ Specific before generic
✅ Test with real user input
✅ Avoid overlapping patterns
✅ Document pattern choices

### Parameter Extraction
✅ Use regex for structured data
✅ Provide sensible defaults
✅ Validate extracted values
✅ Handle missing parameters

### Testing
✅ Test each layer independently
✅ Test integration end-to-end
✅ Test edge cases
✅ Test error scenarios

### Documentation
✅ Document workflow purpose
✅ Document parameters
✅ Document output format
✅ Provide examples

## Common Patterns

### Extract ID
```python
match = re.search(r'ID-\d{6}', task, re.IGNORECASE)
if match:
    parameters["id"] = match.group(0)
```

### Extract Name
```python
patterns = [r'for\s+([^,\.]+)', r'about\s+([^,\.]+)']
for pattern in patterns:
    match = re.search(pattern, task, re.IGNORECASE)
    if match:
        parameters["name"] = match.group(1).strip()
        break
```

### Extract Date
```python
match = re.search(r'\d{4}-\d{2}-\d{2}', task)
if match:
    parameters["date"] = match.group(0)
```

### Extract Amount
```python
match = re.search(r'\$[\d,]+\.?\d*', task)
if match:
    parameters["amount"] = match.group(0)
```

## Troubleshooting

### Workflow Not Detected
1. Check pattern in `detect_workflow()`
2. Verify keywords are lowercase
3. Test with debug logging
4. Check pattern order (first match wins)

### Parameters Not Extracted
1. Test regex at regex101.com
2. Check extraction logic
3. Verify parameter name matches workflow
4. Add debug logging

### Workflow Fails
1. Check workflow logic
2. Verify parameters are valid
3. Check external system connections
4. Review error logs

### API Returns Error
1. Check request format
2. Verify workflow is registered
3. Check server logs
4. Test with curl first

## Resources

### Documentation
- `docs/WORKFLOW_ARCHITECTURE_GUIDE.md` - Complete architecture guide
- `docs/WORKFLOW_ARCHITECTURE_DIAGRAM.md` - Visual diagrams
- `docs/ADDING_WORKFLOW_EXAMPLE.md` - Complete example
- `docs/PHASE_4_COMPLETE.md` - Phase 4 documentation
- `docs/PHASE_4_QUICK_REFERENCE.md` - Quick reference

### Code Examples
- `backend/app/agents/workflows/invoice_verification.py` - Invoice workflow
- `backend/app/agents/workflows/payment_tracking.py` - Payment workflow
- `backend/app/agents/workflows/customer_360.py` - Customer workflow

### Tests
- `backend/test_phase4_integration.py` - Integration tests
- `backend/test_phase4_api.py` - API tests
- `backend/test_workflows.py` - Workflow tests

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│ ADDING A NEW WORKFLOW                                   │
├─────────────────────────────────────────────────────────┤
│ 1. Create File                                          │
│    backend/app/agents/workflows/my_workflow.py         │
│                                                         │
│ 2. Define Class                                         │
│    class MyWorkflow:                                    │
│        @staticmethod                                    │
│        async def execute(...): ...                      │
│                                                         │
│ 3. Register                                             │
│    factory.py: _workflows["my_workflow"] = {...}       │
│                                                         │
│ 4. Add Pattern                                          │
│    if "keyword" in task: return "my_workflow"          │
│                                                         │
│ 5. Extract Params                                       │
│    if workflow == "my_workflow": extract params        │
│                                                         │
│ 6. Test                                                 │
│    python3 test_phase4_integration.py                  │
└─────────────────────────────────────────────────────────┘
```

---

**Summary**: Workflows are easy to add and configure. The architecture is designed for extensibility and maintainability. Adding a new workflow takes ~30 minutes and requires changes to only 4 files.
