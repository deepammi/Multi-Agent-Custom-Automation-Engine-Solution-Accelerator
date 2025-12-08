# Fix Zoho Routing Issues

## Problems Identified:

1. **"No specialized agent selected"** - Graph not routing to Zoho agent
2. **HITL box appearing** - Extraction approval logic triggering incorrectly  
3. **Spinner timeout** - Agent not completing properly

## Root Causes:

### 1. Graph Not Reloaded
The backend server needs to be restarted to load the new Zoho agent node.

### 2. Planner Routing Keywords
The planner needs "zoho" keyword but task might not contain it.

### 3. HITL Triggering
The invoice agent's extraction logic is triggering HITL even for Zoho tasks.

## Fixes:

### Fix 1: Restart Backend Server

```bash
# Stop the current backend server (Ctrl+C)
# Then restart:
cd backend
python3 -m app.main
```

### Fix 2: Update Planner Keywords

The planner should route ANY invoice-related task to Zoho if it mentions "zoho", otherwise to the invoice agent.

Current logic is correct, but we need to ensure the task contains "zoho".

### Fix 3: Test with Explicit "Zoho" Keyword

Try these tasks:
- ✅ "Show me invoices from Zoho"
- ✅ "List Zoho customers"
- ✅ "Get Zoho invoice details"
- ❌ "Show me invoices" (will route to Invoice agent, not Zoho)

### Fix 4: Disable HITL for Zoho Agent

The Zoho agent shouldn't trigger extraction approval. This is already handled correctly in the zoho_agent_node.py (it doesn't set `requires_extraction_approval`).

## Quick Test:

1. **Restart backend:**
   ```bash
   # In backend directory
   python3 -m app.main
   ```

2. **Test in frontend:**
   ```
   Show me recent invoices from Zoho
   ```

3. **Expected behavior:**
   - Planner routes to "Zoho Agent"
   - Zoho agent returns mock invoice data
   - No HITL box appears
   - No spinner timeout

## If Still Not Working:

Check backend logs for:
```
Planner processing task for plan <plan_id>
Supervisor routing to: zoho
Zoho Agent processing task for plan <plan_id>
```

If you see "Supervisor routing to: invoice" instead of "zoho", the keyword matching isn't working.

## Alternative: Make Zoho the Default for Invoice Tasks

If you want Zoho to handle all invoice tasks (not just those mentioning "Zoho"), update the planner:

```python
elif any(word in task_lower for word in ["invoice", "payment", "bill", "vendor"]):
    next_agent = "zoho"  # Changed from "invoice"
    response = "I've analyzed your task: This appears to be an invoice task. Routing to Zoho Agent."
```
