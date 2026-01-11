# Planner Agent Routing Analysis

## Current Implementation

### How the Planner Works

The **Planner Agent** currently uses **keyword-based routing** - it does **NOT** use an AI model to interpret requests. Here's exactly how it works:

### Routing Logic (from `backend/app/agents/nodes.py`)

```python
def planner_node(state: AgentState) -> Dict[str, Any]:
    """Planner agent node - analyzes task and creates execution plan."""
    task = state["task_description"]
    task_lower = task.lower()
    
    # Simple keyword matching
    if any(word in task_lower for word in ["zoho", "zoho invoice", "zoho customer"]):
        next_agent = "zoho"
    elif any(word in task_lower for word in ["salesforce", "account", "opportunity", "contact", "lead", "soql", "crm"]):
        next_agent = "salesforce"
    elif any(word in task_lower for word in ["invoice", "payment", "bill", "vendor"]):
        next_agent = "invoice"
    elif any(word in task_lower for word in ["closing", "reconciliation", "journal", "variance", "gl"]):
        next_agent = "closing"
    elif any(word in task_lower for word in ["audit", "compliance", "evidence", "exception", "monitoring"]):
        next_agent = "audit"
    else:
        next_agent = "invoice"  # Default
```

## Key Characteristics

### ✅ What It Does
- **Keyword Matching**: Checks for specific words in the task description
- **Case Insensitive**: Converts to lowercase before matching
- **Priority Order**: Checks keywords in a specific order (Zoho → Salesforce → Invoice → Closing → Audit)
- **Default Fallback**: Routes to Invoice Agent if no keywords match

### ❌ What It Doesn't Do
- **No AI/LLM**: Does not use any language model for understanding
- **No Context Understanding**: Cannot understand intent beyond keywords
- **No Semantic Analysis**: Cannot handle synonyms or related concepts
- **No Learning**: Cannot improve based on past routing decisions

## Comparison: Planner vs Phase 4 Refactored Service

### Original Planner (Keyword-Based)
```python
# In backend/app/agents/nodes.py
if "invoice" in task_lower:
    next_agent = "invoice"
elif "closing" in task_lower:
    next_agent = "closing"
```

**Limitations:**
- ❌ Only routes to **agents** (invoice, closing, audit, zoho, salesforce)
- ❌ Cannot route to **workflows** (invoice_verification, payment_tracking, customer_360)
- ❌ Simple keyword matching only
- ❌ No parameter extraction

### Phase 4 Refactored Service (Enhanced Keyword-Based)
```python
# In backend/app/services/agent_service_refactored.py
if any(phrase in task_lower for phrase in [
    "verify invoice", "check invoice", "validate invoice"
]):
    return "invoice_verification"  # Routes to workflow
```

**Improvements:**
- ✅ Routes to both **agents** AND **workflows**
- ✅ More sophisticated phrase matching
- ✅ Automatic parameter extraction
- ✅ Better pattern recognition
- ✅ Still keyword-based (no AI needed)

## Why Keyword-Based Routing Works

### Advantages
1. **Fast**: No API calls, instant routing
2. **Predictable**: Same input always routes the same way
3. **Debuggable**: Easy to see why something routed where
4. **Cost-Effective**: No LLM API costs
5. **Reliable**: No model hallucinations or errors

### When It Works Well
- ✅ Users use consistent terminology
- ✅ Clear domain-specific keywords exist
- ✅ Tasks are well-structured
- ✅ Limited number of routing options

### When It Struggles
- ❌ Users use varied language ("check invoice" vs "verify bill")
- ❌ Ambiguous requests ("show me the data")
- ❌ Complex multi-step tasks
- ❌ Requests requiring context understanding

## Could We Use AI for Routing?

### Option 1: LLM-Based Routing

**Implementation:**
```python
async def planner_node_with_llm(state: AgentState) -> Dict[str, Any]:
    task = state["task_description"]
    
    prompt = f"""
    Analyze this task and determine which agent should handle it:
    
    Task: {task}
    
    Available agents:
    - invoice: Invoice processing and extraction
    - closing: Month-end closing and reconciliation
    - audit: Compliance and audit tasks
    - zoho: Zoho Books queries
    - salesforce: Salesforce CRM queries
    
    Respond with just the agent name.
    """
    
    response = await LLMService.call_llm(prompt)
    next_agent = response.strip().lower()
    
    return {
        "messages": [f"Routing to {next_agent} agent"],
        "next_agent": next_agent
    }
```

**Pros:**
- ✅ Better understanding of natural language
- ✅ Can handle synonyms and variations
- ✅ More flexible routing logic
- ✅ Can consider context

**Cons:**
- ❌ Slower (API call latency)
- ❌ Costs money (per request)
- ❌ Less predictable (model variations)
- ❌ Requires error handling for bad responses
- ❌ Needs prompt engineering and testing

### Option 2: Hybrid Approach

**Implementation:**
```python
async def planner_node_hybrid(state: AgentState) -> Dict[str, Any]:
    task = state["task_description"]
    task_lower = task.lower()
    
    # Try keyword matching first (fast path)
    if any(word in task_lower for word in ["zoho", "salesforce", "invoice"]):
        # Use keyword routing
        next_agent = keyword_route(task_lower)
    else:
        # Fall back to LLM for ambiguous cases
        next_agent = await llm_route(task)
    
    return {"next_agent": next_agent}
```

**Pros:**
- ✅ Fast for common cases
- ✅ Smart for edge cases
- ✅ Cost-effective (LLM only when needed)

**Cons:**
- ❌ More complex to maintain
- ❌ Still has LLM costs for some requests

## Recommendation

### For Your Current System: Keep Keyword-Based ✅

**Reasons:**
1. **It Works**: Your domain has clear keywords (invoice, closing, audit, zoho, salesforce)
2. **Phase 4 Enhanced It**: The refactored service adds workflow routing with better patterns
3. **Fast & Reliable**: No latency, no costs, predictable behavior
4. **Easy to Extend**: Adding new keywords is simple

### When to Consider LLM Routing

**Consider switching if:**
- Users frequently use varied language that keywords miss
- You need to understand complex, multi-step requests
- You want to route based on intent, not just keywords
- You have budget for LLM API calls

**Example scenarios where LLM would help:**
```
"Can you help me figure out why our numbers don't match?" 
→ LLM could understand this is a reconciliation/closing task

"I need to see what we owe that vendor from last month"
→ LLM could understand this needs invoice + payment tracking

"Show me everything about customer XYZ"
→ LLM could understand this is a customer 360 request
```

## Current Architecture Summary

```
User Request
    ↓
Phase 4 Refactored Service (keyword-based)
    ↓
Workflow Detected? → Yes → Execute Workflow (invoice_verification, etc.)
    ↓
    No
    ↓
Original Planner Agent (keyword-based)
    ↓
Route to Specialized Agent (invoice, closing, audit, zoho, salesforce)
    ↓
Agent Uses LLM for Task Execution (not routing)
```

**Key Point**: The **routing** is keyword-based, but the **agents themselves** use LLMs to execute tasks.

## Example Flow

### Request: "Verify invoice INV-000001 across systems"

**Phase 4 Routing:**
```python
# Detects "verify invoice" keyword
workflow = "invoice_verification"  # ✅ Routes to workflow

# Extracts parameters
parameters = {
    "invoice_id": "INV-000001",
    "erp_system": "zoho",
    "crm_system": "salesforce"
}

# Executes workflow (no planner needed)
```

### Request: "Show me Zoho invoices"

**Original Planner Routing:**
```python
# Phase 4 doesn't detect workflow
# Falls back to planner

# Planner detects "zoho" keyword
next_agent = "zoho"  # ✅ Routes to Zoho agent

# Zoho agent uses LLM to execute query
```

## Conclusion

**Current State:**
- ✅ Planner uses **keyword-based routing** (no AI)
- ✅ Phase 4 adds **enhanced keyword routing** for workflows
- ✅ Agents use **LLMs for task execution** (not routing)

**This is a good architecture because:**
1. Routing is fast and predictable
2. LLMs are used where they add value (task execution)
3. Costs are controlled (no LLM for every routing decision)
4. Easy to debug and maintain

**Consider LLM routing only if:**
- Keyword matching frequently fails
- Users demand more natural language flexibility
- Budget allows for per-request LLM costs

---

**Bottom Line**: Your current keyword-based routing is appropriate for your use case. Phase 4 enhanced it with workflow detection. No need to add LLM routing unless you see specific failures in production.
