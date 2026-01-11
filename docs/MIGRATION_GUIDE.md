# Migration Guide: LangGraph Orchestrator Simplification

## Overview

This guide helps you migrate from the old Azure-based routing system to the new LangGraph Orchestrator Simplification. The new system eliminates infinite loops, provides AI-driven planning, and uses linear execution patterns.

## What Changed

### 🔄 Major Architecture Changes

#### 1. Routing System Elimination
**Before**: Complex supervisor routing with conditional logic
```python
# OLD - Complex routing logic
def supervisor_router(state: AgentState) -> str:
    next_agent = state.get("next_agent")
    if next_agent in ["invoice", "closing", "audit"]:
        return next_agent
    return "invoice"  # Default
```

**After**: Linear execution with AI-generated sequences
```python
# NEW - Linear execution
agent_sequence = ["planner", "invoice", "closing"]
graph = LinearGraphFactory.create_graph_from_sequence(agent_sequence)
```

#### 2. AI-Driven Planning
**Before**: Manual agent specification or hardcoded routing
```python
# OLD - Manual routing
if "invoice" in task.lower():
    next_agent = "invoice"
elif "closing" in task.lower():
    next_agent = "closing"
```

**After**: Intelligent AI planning
```python
# NEW - AI-driven planning
planning_summary = await ai_planner.plan_workflow(task_description)
agent_sequence = planning_summary.agent_sequence.agents
```

#### 3. State Management Simplification
**Before**: Complex state with routing fields
```python
# OLD - Complex state
state = {
    "next_agent": "invoice",
    "workflow_type": "complex",
    "routing_history": [...],
    # ... many routing fields
}
```

**After**: Simplified linear state
```python
# NEW - Simplified state
state = {
    "agent_sequence": ["planner", "invoice"],
    "current_step": 0,
    "total_steps": 2,
    "collected_data": {},
    # ... clean, focused fields
}
```

## Migration Steps

### Step 1: Update API Calls

#### Frontend Changes
**Minimal changes required** - mostly configuration updates:

```typescript
// OLD - API configuration
const API_BASE_URL = "https://your-azure-backend.com/api/v3";

// NEW - Update to new backend
const API_BASE_URL = "http://localhost:8000/api/v3";
```

#### Request Format (No Changes)
```typescript
// Same request format works
const response = await fetch(`${API_BASE_URL}/process_request`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    description: "Verify invoice INV-123456",
    session_id: sessionId
  })
});
```

### Step 2: Update Backend Integration

#### Old Service Usage
```python
# OLD - Manual agent service
from app.services.agent_service import AgentService

result = await AgentService.execute_task(
    plan_id=plan_id,
    task_description=description,
    next_agent="invoice"  # Manual specification
)
```

#### New Service Usage
```python
# NEW - AI-driven service
from app.services.langgraph_service import LangGraphService

result = await LangGraphService.execute_task_with_ai_planner(
    plan_id=plan_id,
    session_id=session_id,
    task_description=description,
    websocket_manager=websocket_manager
)
```

### Step 3: Update Graph Creation

#### Old Graph Creation
```python
# OLD - Complex conditional routing
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("invoice", invoice_agent_node)

workflow.add_conditional_edges(
    "planner",
    supervisor_router,  # Complex routing function
    {
        "invoice": "invoice",
        "closing": "closing",
        "audit": "audit"
    }
)
```

#### New Graph Creation
```python
# NEW - Simple linear connections
from app.agents.graph_factory import LinearGraphFactory

agent_sequence = ["planner", "invoice", "closing"]
graph = LinearGraphFactory.create_graph_from_sequence(
    agent_sequence=agent_sequence,
    graph_type="ai_driven",
    enable_hitl=True
)
```

### Step 4: Update Agent Implementations

#### Remove Routing Logic from Agents
```python
# OLD - Agent with routing logic
async def invoice_agent_node(state: AgentState) -> AgentState:
    # Process invoice
    result = process_invoice(state["task_description"])
    
    # OLD - Routing logic (REMOVE THIS)
    if "closing" in result:
        state["next_agent"] = "closing"
    else:
        state["next_agent"] = "audit"
    
    return state
```

```python
# NEW - Agent without routing logic
async def invoice_agent_node(state: AgentState) -> AgentState:
    # Process invoice
    result = process_invoice(state["task_description"])
    
    # NEW - Just preserve data, no routing
    state["collected_data"]["invoice_result"] = result
    
    return state
```

### Step 5: Update HITL Workflows

#### Old HITL System
```python
# OLD - Callback-based approval
def handle_approval(plan_id: str, approved: bool):
    if approved:
        # Complex routing logic
        next_agent = determine_next_agent(plan_id)
        execute_agent(next_agent, plan_id)
    else:
        terminate_workflow(plan_id)
```

#### New HITL System
```python
# NEW - State-based approval
async def plan_approval(request: PlanApprovalRequest):
    if request.approved:
        # Resume with state update
        updates = {
            "plan_approved": True,
            "hitl_feedback": request.feedback
        }
        await LangGraphService.resume_execution(
            request.m_plan_id, 
            updates
        )
    else:
        # Update plan status
        await PlanRepository.update_status(
            request.m_plan_id, 
            "rejected"
        )
```

## Configuration Updates

### Environment Variables

#### Old Configuration
```bash
# OLD - Azure-specific
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
SEMANTIC_KERNEL_VERSION=1.0.0
```

#### New Configuration
```bash
# NEW - LangGraph-specific
LLM_PROVIDER=openai  # or ollama, anthropic
OPENAI_API_KEY=your-key
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=macae_db
MCP_SERVER_URL=http://localhost:9000
```

### Database Migration

#### Schema Changes
The new system uses MongoDB instead of Azure Cosmos DB:

```javascript
// NEW - MongoDB collections
{
  // plans collection
  "_id": "ObjectId",
  "plan_id": "string (UUID)",
  "session_id": "string (UUID)",
  "description": "string",
  "status": "pending | in_progress | completed | failed",
  "steps": [
    {
      "id": "string",
      "description": "string", 
      "agent": "string",
      "status": "string"
    }
  ]
}
```

#### Data Migration Script
```python
# Migration script example
async def migrate_azure_to_mongodb():
    # 1. Export data from Azure Cosmos DB
    azure_plans = await export_from_cosmos_db()
    
    # 2. Transform data structure
    for plan in azure_plans:
        # Remove routing fields
        plan.pop('next_agent', None)
        plan.pop('workflow_type', None)
        
        # Add new fields
        plan['agent_sequence'] = determine_sequence(plan)
        plan['current_step'] = 0
    
    # 3. Import to MongoDB
    await import_to_mongodb(azure_plans)
```

## Testing Migration

### 1. Parallel Testing
Run both systems in parallel during migration:

```python
# Test both systems
async def test_migration(task_description: str):
    # Old system
    old_result = await old_agent_service.execute(task_description)
    
    # New system  
    new_result = await LangGraphService.execute_task_with_ai_planner(
        plan_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        task_description=task_description
    )
    
    # Compare results
    assert old_result["status"] == new_result["status"]
    assert len(old_result["messages"]) <= len(new_result["messages"])
```

### 2. Validation Tests
```python
# Validate no infinite loops
async def test_no_infinite_loops():
    for i in range(100):  # Test multiple scenarios
        result = await execute_random_task()
        assert result["status"] in ["completed", "failed"]
        assert len(result["messages"]) < 50  # Reasonable limit
```

### 3. Performance Comparison
```python
# Performance benchmarks
async def benchmark_performance():
    tasks = generate_test_tasks(100)
    
    # Old system timing
    old_start = time.time()
    old_results = await execute_old_system(tasks)
    old_duration = time.time() - old_start
    
    # New system timing
    new_start = time.time()
    new_results = await execute_new_system(tasks)
    new_duration = time.time() - new_start
    
    print(f"Performance improvement: {old_duration/new_duration:.2f}x")
```

## Common Issues and Solutions

### Issue 1: Missing Agent Routing
**Problem**: Agents no longer specify next agent
**Solution**: Use AI Planner for sequence generation

```python
# WRONG - Don't try to add routing back
state["next_agent"] = "closing"  # This is ignored

# RIGHT - Let AI Planner handle sequences
# The sequence is determined at workflow start
```

### Issue 2: Complex Conditional Logic
**Problem**: Need complex routing based on results
**Solution**: Use workflow templates or AI planning

```python
# OLD - Complex conditional routing
if result.contains_errors and result.severity > 5:
    next_agent = "audit"
elif result.needs_approval:
    next_agent = "hitl"
else:
    next_agent = "closing"

# NEW - Use workflow templates
workflow_name = "error_handling" if result.contains_errors else "standard"
await WorkflowFactory.execute_workflow(workflow_name, plan_id, parameters)
```

### Issue 3: State Compatibility
**Problem**: Old state fields not recognized
**Solution**: Update state structure

```python
# Migration helper
def migrate_state(old_state: dict) -> AgentState:
    return {
        "plan_id": old_state["plan_id"],
        "session_id": old_state["session_id"],
        "task_description": old_state["task_description"],
        "agent_sequence": extract_sequence(old_state),
        "current_step": 0,
        "total_steps": len(extract_sequence(old_state)),
        "collected_data": old_state.get("collected_data", {}),
        "messages": old_state.get("messages", []),
        # ... other new fields
    }
```

## Rollback Plan

### Emergency Rollback
If issues arise, you can quickly rollback:

1. **Switch API endpoint** back to Azure backend
2. **Restore database** from backup
3. **Revert environment variables**
4. **Restart services** with old configuration

### Gradual Rollback
For partial rollback:

```python
# Feature flag for gradual migration
USE_NEW_SYSTEM = os.getenv("USE_LANGGRAPH", "false").lower() == "true"

async def process_request(request):
    if USE_NEW_SYSTEM:
        return await new_langgraph_service.execute(request)
    else:
        return await old_azure_service.execute(request)
```

## Validation Checklist

### ✅ Pre-Migration
- [ ] Backup all data
- [ ] Set up new MongoDB instance
- [ ] Configure new environment variables
- [ ] Test new system in isolation
- [ ] Prepare rollback procedures

### ✅ During Migration
- [ ] Run parallel testing
- [ ] Monitor performance metrics
- [ ] Validate no infinite loops
- [ ] Check WebSocket functionality
- [ ] Verify HITL workflows

### ✅ Post-Migration
- [ ] All tests passing
- [ ] Performance meets expectations
- [ ] No infinite loop occurrences
- [ ] Frontend works without changes
- [ ] WebSocket messages correct
- [ ] HITL approval flows working
- [ ] AI planning generates valid sequences

## Performance Expectations

### Improvements Expected
- **50-80% reduction** in execution time for complex workflows
- **90%+ elimination** of infinite loop issues
- **60%+ improvement** in system reliability
- **40%+ reduction** in memory usage

### Metrics to Monitor
- Workflow completion rates
- Average execution time per agent
- Cache hit rates (should be >80%)
- Error rates (should be <5%)
- WebSocket connection stability

## Support and Troubleshooting

### Common Commands
```bash
# Check system status
python3 -m pytest backend/test_integration_validation.py

# Verify no routing logic
python3 -m pytest backend/test_routing_logic_elimination.py

# Performance validation
python3 -m pytest backend/test_task12_performance.py

# Clear graph cache if needed
curl -X POST "http://localhost:8000/api/v3/clear_cache"
```

### Log Analysis
```bash
# Check for routing issues
grep -r "next_agent" backend/logs/

# Monitor AI planning
grep -r "AI Planner" backend/logs/

# Check for infinite loops
grep -r "timeout" backend/logs/
```

### Getting Help
1. Check the comprehensive test suite results
2. Review performance monitoring dashboard
3. Analyze WebSocket message logs
4. Consult API documentation for new endpoints
5. Use the cleanup utility for deprecated code detection

## Success Criteria

Migration is successful when:
- ✅ All property tests pass (13/13)
- ✅ No infinite loops detected in 100+ test runs
- ✅ Frontend works without code changes
- ✅ AI planning generates valid sequences >95% of the time
- ✅ HITL workflows complete successfully
- ✅ Performance improvements achieved
- ✅ System stability maintained over 24+ hours