# Workflow Architecture - Visual Guide

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                 │
│  "Verify invoice INV-000001" or "Review contract CTR-123456"        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    API LAYER (routes.py)                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  POST /api/v3/process_request_v2                            │   │
│  │  - Receives user request                                     │   │
│  │  - Creates plan in database                                  │   │
│  │  - Calls AgentServiceRefactored.execute_task()              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              SERVICE LAYER (agent_service_refactored.py)             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. detect_workflow(task_description)                       │   │
│  │     - Checks for workflow patterns                           │   │
│  │     - Returns workflow name or None                          │   │
│  │                                                               │   │
│  │  2. extract_parameters(workflow_name, task_description)     │   │
│  │     - Extracts IDs, names, dates using regex                │   │
│  │     - Returns parameters dict                                │   │
│  │                                                               │   │
│  │  3. Route to appropriate handler                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────┬───────────────────────────────────┬────────────────────┘
             │                                   │
             │ Workflow Detected                 │ No Workflow
             ▼                                   ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│   WORKFLOW LAYER             │    │   REGULAR AGENT LAYER        │
│   (workflows/factory.py)     │    │   (langgraph_service.py)     │
│                              │    │                              │
│  WorkflowFactory             │    │  LangGraphService            │
│  - Looks up workflow         │    │  - Uses LangGraph            │
│  - Executes workflow         │    │  - Multi-agent routing       │
│  - Returns result            │    │  - HITL support              │
└──────────────────────────────┘    └──────────────────────────────┘
             │                                   │
             └───────────────┬───────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         RESULT                                       │
│  - Status (completed/error)                                          │
│  - Messages (progress updates)                                       │
│  - Final result (formatted output)                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Workflow Detection Flow

```
User Input: "Verify invoice INV-000001"
     │
     ▼
┌─────────────────────────────────────┐
│  detect_workflow()                  │
│  - Convert to lowercase             │
│  - Check patterns in order:         │
│    • "verify invoice" ✓ MATCH       │
│    • "track payment"                │
│    • "customer 360"                 │
└─────────────────────────────────────┘
     │
     ▼ Returns "invoice_verification"
     │
┌─────────────────────────────────────┐
│  extract_parameters()               │
│  - Regex: r'INV-\d{6}'             │
│  - Match: "INV-000001" ✓            │
│  - Add defaults:                    │
│    • erp_system: "zoho"            │
│    • crm_system: "salesforce"      │
└─────────────────────────────────────┘
     │
     ▼ Returns {"invoice_id": "INV-000001", ...}
     │
┌─────────────────────────────────────┐
│  WorkflowFactory.execute_workflow() │
│  - Lookup: "invoice_verification"  │
│  - Execute: InvoiceVerification     │
│  - Return: Result dict              │
└─────────────────────────────────────┘
```

## Workflow Registry Structure

```
WorkflowFactory._workflows = {
    
    "invoice_verification": {
        "executor": InvoiceVerificationWorkflow.execute,
        "title": "Invoice Verification",
        "description": "Cross-check invoice data",
        "systems": ["ERP", "CRM"],
        "parameters": ["invoice_id", "erp_system", "crm_system"]
    },
    
    "payment_tracking": {
        "executor": PaymentTrackingWorkflow.execute,
        "title": "Payment Tracking",
        "description": "Track payment status",
        "systems": ["ERP", "Email"],
        "parameters": ["invoice_id", "erp_system"]
    },
    
    "customer_360": {
        "executor": Customer360Workflow.execute,
        "title": "Customer 360 View",
        "description": "Aggregate customer data",
        "systems": ["CRM", "ERP", "Accounting"],
        "parameters": ["customer_name"]
    }
}
```

## Adding a New Workflow - Visual Steps

```
Step 1: Create Workflow File
┌────────────────────────────────────────────┐
│ backend/app/agents/workflows/              │
│   ├── invoice_verification.py             │
│   ├── payment_tracking.py                 │
│   ├── customer_360.py                     │
│   └── your_new_workflow.py  ← CREATE THIS │
└────────────────────────────────────────────┘

Step 2: Register in Factory
┌────────────────────────────────────────────┐
│ backend/app/agents/workflows/factory.py   │
│                                            │
│ _workflows = {                             │
│     "your_workflow": {                     │
│         "executor": YourWorkflow.execute,  │
│         "title": "Your Workflow",          │
│         ...                                │
│     }                                      │
│ }                                          │
└────────────────────────────────────────────┘

Step 3: Add Detection Pattern
┌────────────────────────────────────────────┐
│ backend/app/services/                      │
│   agent_service_refactored.py             │
│                                            │
│ def detect_workflow():                     │
│     if "your keyword" in task_lower:       │
│         return "your_workflow"             │
└────────────────────────────────────────────┘

Step 4: Add Parameter Extraction
┌────────────────────────────────────────────┐
│ backend/app/services/                      │
│   agent_service_refactored.py             │
│                                            │
│ def extract_parameters():                  │
│     if workflow_name == "your_workflow":   │
│         # Extract params                   │
│         return parameters                  │
└────────────────────────────────────────────┘

Step 5: Test
┌────────────────────────────────────────────┐
│ python3 test_phase4_integration.py        │
│ ✅ All tests passing                       │
└────────────────────────────────────────────┘
```

## Workflow Execution Sequence

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌─────────────────────────┐
│ 1. Validate Parameters  │
│    - Check required     │
│    - Set defaults       │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ 2. Initialize State     │
│    - messages = []      │
│    - data = {}          │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ 3. Execute Steps        │
│    ┌─────────────────┐  │
│    │ Step 1: Fetch   │  │
│    │ Step 2: Process │  │
│    │ Step 3: Analyze │  │
│    │ Step 4: Report  │  │
│    └─────────────────┘  │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ 4. Generate Result      │
│    - Format output      │
│    - Add metadata       │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ 5. Return Response      │
│    {                    │
│      status: "completed"│
│      messages: [...]    │
│      final_result: "..."│
│    }                    │
└────┬────────────────────┘
     │
     ▼
┌─────────┐
│   END   │
└─────────┘
```

## Pattern Detection Priority

```
Priority Order (First Match Wins):
┌─────────────────────────────────────┐
│ 1. Specific Patterns                │
│    "verify invoice INV-123456"      │
│    → invoice_verification           │
├─────────────────────────────────────┤
│ 2. Action + Entity Patterns         │
│    "track payment"                  │
│    → payment_tracking               │
├─────────────────────────────────────┤
│ 3. Compound Patterns                │
│    "customer 360 view"              │
│    → customer_360                   │
├─────────────────────────────────────┤
│ 4. Generic Patterns                 │
│    "list invoices"                  │
│    → regular_agent (no workflow)    │
└─────────────────────────────────────┘
```

## Parameter Extraction Patterns

```
┌──────────────────────────────────────────────────────────┐
│ Pattern Type          │ Regex                │ Example   │
├──────────────────────────────────────────────────────────┤
│ Invoice ID            │ INV-\d{6}           │ INV-000001│
│ Contract ID           │ CTR-\d{6}           │ CTR-123456│
│ Customer Name         │ for\s+([^,\.]+)     │ for Acme  │
│ Date                  │ \d{4}-\d{2}-\d{2}   │ 2024-12-09│
│ Amount                │ \$[\d,]+\.?\d*      │ $1,234.56 │
│ Email                 │ [a-z0-9@\.]+        │ user@co.com│
└──────────────────────────────────────────────────────────┘
```

## Workflow Communication Flow

```
┌──────────────┐
│   Workflow   │
└──────┬───────┘
       │
       │ Sends progress messages
       ▼
┌──────────────────────┐
│  WebSocket Manager   │
└──────┬───────────────┘
       │
       │ Broadcasts to client
       ▼
┌──────────────────────┐
│  Frontend UI         │
│  - Shows progress    │
│  - Updates in real   │
│    time              │
└──────────────────────┘
```

## Error Handling Flow

```
┌─────────────────┐
│ Workflow Start  │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │  Try   │
    └───┬────┘
        │
        ▼
   ┌─────────────┐
   │  Execute    │
   │  Steps      │
   └─┬─────────┬─┘
     │         │
     │ Success │ Error
     │         │
     ▼         ▼
┌─────────┐ ┌──────────────┐
│ Return  │ │ Catch Error  │
│ Success │ │ - Log error  │
│ Result  │ │ - Format msg │
└─────────┘ │ - Return err │
            └──────────────┘
```

## Multi-Agent Workflow Pattern

```
Sequential Pattern:
┌────────┐    ┌────────┐    ┌────────┐
│ Agent1 │───▶│ Agent2 │───▶│ Agent3 │
│ Fetch  │    │Analyze │    │ Report │
└────────┘    └────────┘    └────────┘

Parallel Pattern:
            ┌────────┐
         ┌─▶│ Agent1 │─┐
         │  └────────┘ │
┌──────┐ │  ┌────────┐ │  ┌────────┐
│Start │─┼─▶│ Agent2 │─┼─▶│Combine │
└──────┘ │  └────────┘ │  └────────┘
         │  ┌────────┐ │
         └─▶│ Agent3 │─┘
            └────────┘

Conditional Pattern:
┌────────┐
│ Check  │
└───┬────┘
    │
    ├─Yes─▶┌────────┐
    │      │ Path A │
    │      └────────┘
    │
    └─No──▶┌────────┐
           │ Path B │
           └────────┘
```

## File Structure Map

```
backend/
├── app/
│   ├── api/
│   │   └── v3/
│   │       └── routes.py ..................... API endpoints
│   │
│   ├── services/
│   │   ├── agent_service.py ................ Original service
│   │   └── agent_service_refactored.py ..... NEW: Smart routing
│   │
│   └── agents/
│       └── workflows/
│           ├── __init__.py
│           ├── factory.py .................. Workflow registry
│           ├── invoice_verification.py ..... Workflow 1
│           ├── payment_tracking.py ......... Workflow 2
│           ├── customer_360.py ............. Workflow 3
│           └── your_workflow.py ............ Add new here
│
└── tests/
    ├── test_phase4_integration.py .......... Integration tests
    └── test_phase4_api.py .................. API tests
```

## Quick Reference: Adding Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Create File                                              │
│    backend/app/agents/workflows/my_workflow.py             │
│                                                             │
│ 2. Define Class                                             │
│    class MyWorkflow:                                        │
│        @staticmethod                                        │
│        async def execute(...): ...                          │
│                                                             │
│ 3. Register                                                 │
│    factory.py: _workflows["my_workflow"] = {...}           │
│                                                             │
│ 4. Add Pattern                                              │
│    agent_service_refactored.py:                            │
│    if "my keyword" in task: return "my_workflow"           │
│                                                             │
│ 5. Extract Params                                           │
│    agent_service_refactored.py:                            │
│    if workflow == "my_workflow": extract params            │
│                                                             │
│ 6. Test                                                     │
│    python3 test_phase4_integration.py                      │
└─────────────────────────────────────────────────────────────┘
```

---

**Visual guides make it easier to understand the architecture!**
