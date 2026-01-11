# Phase 4 Quick Reference Guide

## For Developers

### Adding a New Workflow

**Step 1: Create the workflow** (see Phase 3 docs)

**Step 2: Add detection pattern**
```python
# In backend/app/services/agent_service_refactored.py

@staticmethod
def detect_workflow(task_description: str) -> Optional[str]:
    task_lower = task_description.lower()
    
    # Add your pattern
    if any(phrase in task_lower for phrase in [
        "your keyword", "another keyword"
    ]):
        return "your_workflow_name"
```

**Step 3: Add parameter extraction**
```python
@staticmethod
def extract_parameters(workflow_name: str, task_description: str) -> Dict[str, Any]:
    parameters = {}
    
    if workflow_name == "your_workflow_name":
        # Extract parameters using regex
        match = re.search(r'YOUR-PATTERN', task_description)
        if match:
            parameters["param_name"] = match.group(0)
    
    return parameters
```

**Done!** The workflow is now automatically available.

### Using the API

**Smart Routing (Recommended):**
```bash
curl -X POST http://localhost:8000/api/v3/process_request_v2 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Verify invoice INV-000001",
    "session_id": "session-123",
    "require_hitl": false
  }'
```

**List Workflows:**
```bash
curl http://localhost:8000/api/v3/workflows
```

**Execute Specific Workflow:**
```bash
curl -X POST http://localhost:8000/api/v3/execute_workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "invoice_verification",
    "plan_id": "plan-123",
    "session_id": "session-456",
    "parameters": {
      "invoice_id": "INV-000001",
      "erp_system": "zoho",
      "crm_system": "salesforce"
    }
  }'
```

### Testing Your Changes

**Run integration tests:**
```bash
cd backend
python3 test_phase4_integration.py
```

**Run API tests:**
```bash
cd backend
python3 test_phase4_api.py
```

### Common Patterns

**Invoice ID Extraction:**
```python
invoice_match = re.search(r'INV-\d{6}', task_description, re.IGNORECASE)
if invoice_match:
    parameters["invoice_id"] = invoice_match.group(0)
```

**Customer Name Extraction:**
```python
customer_patterns = [
    r'for\s+([^,\.\?!]+)',
    r'about\s+([^,\.\?!]+)',
]

for pattern in customer_patterns:
    match = re.search(pattern, task_description, re.IGNORECASE)
    if match:
        customer_name = match.group(1).strip()
        break
```

**Date Extraction:**
```python
date_match = re.search(r'\d{4}-\d{2}-\d{2}', task_description)
if date_match:
    parameters["date"] = date_match.group(0)
```

### Debugging

**Enable debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check workflow detection:**
```python
from app.services.agent_service_refactored import AgentServiceRefactored

workflow = AgentServiceRefactored.detect_workflow("your task description")
print(f"Detected: {workflow}")
```

**Check parameter extraction:**
```python
params = AgentServiceRefactored.extract_parameters("workflow_name", "task description")
print(f"Parameters: {params}")
```

### Frontend Integration

**React/TypeScript Example:**
```typescript
// Submit task with smart routing
const submitTask = async (description: string) => {
  const response = await fetch('/api/v3/process_request_v2', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      description,
      session_id: sessionId,
      require_hitl: false
    })
  });
  
  const result = await response.json();
  return result.plan_id;
};

// Get available workflows
const getWorkflows = async () => {
  const response = await fetch('/api/v3/workflows');
  return await response.json();
};
```

### Error Handling

**Service Level:**
```python
try:
    result = await AgentServiceRefactored.execute_task(...)
except Exception as e:
    logger.error(f"Task execution failed: {e}")
    # Error is automatically sent via WebSocket
```

**API Level:**
```python
try:
    result = await AgentServiceRefactored.list_workflows()
    if result["status"] == "success":
        return result["workflows"]
    else:
        raise HTTPException(status_code=500, detail=result["error"])
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

## Quick Troubleshooting

**Workflow not detected?**
- Check detection patterns in `detect_workflow()`
- Verify keywords are lowercase
- Test with `test_phase4_integration.py`

**Parameters not extracted?**
- Check regex patterns in `extract_parameters()`
- Test regex at https://regex101.com
- Add debug logging to see what's being matched

**API endpoint not working?**
- Check FastAPI logs for errors
- Verify request format matches examples
- Test with curl or Postman first

**Tests failing?**
- Run `python3 test_phase4_integration.py` for details
- Check if workflows are registered in WorkflowFactory
- Verify all dependencies are installed

## Performance Tips

**Workflow Detection:**
- Patterns are checked in order
- Put most common patterns first
- Use simple string matching before regex

**Parameter Extraction:**
- Cache compiled regex patterns
- Use specific patterns before generic ones
- Provide sensible defaults

**API Calls:**
- Use `/process_request_v2` for automatic routing
- Use `/execute_workflow` when workflow is known
- Batch workflow listings if needed

## Best Practices

1. **Always test new workflows** with integration tests
2. **Use descriptive pattern keywords** for detection
3. **Provide default parameters** when extraction fails
4. **Log workflow routing decisions** for debugging
5. **Keep detection patterns simple** and maintainable
6. **Document new workflows** in Phase 3 docs
7. **Test with real user input** patterns

---

**Need Help?**
- Check `docs/PHASE_4_COMPLETE.md` for detailed documentation
- Run tests to verify your changes
- Review existing workflows for examples
