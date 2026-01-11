# Workflow Testing Guide

## Quick Start

### Option 1: Automated Tests (Fastest)
```bash
cd backend
python3 test_workflows.py
```

This runs all 3 workflows with default parameters and shows the results.

### Option 2: Interactive Testing (Recommended)
```bash
cd backend
python3 test_workflows_interactive.py
```

This gives you a menu to:
- Choose which workflow to test
- Enter custom parameters
- See full reports
- Test multiple times

### Option 3: Manual Python Testing
```python
cd backend
python3

# Then in Python:
import asyncio
from app.agents.workflows.factory import WorkflowFactory

# Test Invoice Verification
result = asyncio.run(WorkflowFactory.execute_workflow(
    workflow_name="invoice_verification",
    plan_id="manual-test-001",
    session_id="test",
    parameters={
        "invoice_id": "INV-000001",
        "erp_system": "zoho",
        "crm_system": "salesforce"
    }
))

print(result['final_result'])
```

## Available Test Data

### Invoices (from your Zoho account)
- **INV-000001**: Test1Customer Co. - $12,200.00 (sent)
- **INV-000002**: University of Chicago - $12,400.00 (sent)

### Customers
- Test1Customer Co.
- University of Chicago
- Test2 Customer Co

## Testing Each Workflow

### 1. Invoice Verification

**What it does**: Cross-checks invoice data between ERP and CRM

**Test command**:
```bash
python3 test_workflows_interactive.py
# Select option 1
# Enter: INV-000001
```

**Expected output**:
- Invoice details from Zoho
- Customer data from CRM
- Verification results
- Discrepancy report
- Recommendations

**What to look for**:
- ✅ Invoice fetched from Zoho
- ✅ Customer data generated
- ✅ Cross-reference completed
- ✅ Confidence score calculated
- ✅ Recommendations provided

### 2. Payment Tracking

**What it does**: Tracks payment status across ERP and Email

**Test command**:
```bash
python3 test_workflows_interactive.py
# Select option 2
# Enter: INV-000002
```

**Expected output**:
- Invoice status from ERP
- Email search results (random: found or not found)
- If found: Payment matching
- If not found: Reminder sent
- Next steps

**What to look for**:
- ✅ Invoice status checked
- ✅ Email search executed
- ✅ Conditional routing working
- ✅ Appropriate action taken
- ✅ Report generated

**Note**: Email search is randomized for demo purposes

### 3. Customer 360 View

**What it does**: Aggregates customer data from multiple systems

**Test command**:
```bash
python3 test_workflows_interactive.py
# Select option 3
# Enter: University of Chicago
```

**Expected output**:
- Customer health score
- CRM profile data
- Financial summary from ERP
- Recent invoices
- Risk assessment
- Recommendations

**What to look for**:
- ✅ CRM data retrieved
- ✅ ERP invoices fetched
- ✅ Health score calculated
- ✅ Risk level assessed
- ✅ Recommendations provided

## Troubleshooting

### Issue: "Module not found"
**Solution**: Make sure you're in the backend directory
```bash
cd backend
python3 test_workflows_interactive.py
```

### Issue: "No invoices found"
**Solution**: Check that Zoho OAuth is working
```bash
python3 test_zoho_real_api.py
```

### Issue: Workflow fails
**Solution**: Check the error message and ensure:
- Zoho credentials are in backend/.env
- ZOHO_USE_MOCK=false
- ZOHO_MCP_ENABLED=true

## Demo Script for Customers

### Setup (Before Demo)
1. Run automated tests to verify everything works
2. Choose which workflow to demo
3. Have invoice IDs ready

### During Demo

**Opening**: "Let me show you how our system connects multiple enterprise systems to automate complex workflows."

**Demo 1: Invoice Verification**
1. "Let's verify this invoice across our ERP and CRM systems"
2. Run workflow with INV-000001
3. Show the report
4. Highlight: "Notice how it automatically found a discrepancy in the customer name"

**Demo 2: Payment Tracking**
1. "Now let's track a payment across systems"
2. Run workflow with INV-000002
3. Show the conditional logic
4. Highlight: "The system automatically sent a reminder when no payment was found"

**Demo 3: Customer 360**
1. "Finally, let's get a complete view of this customer"
2. Run workflow with "University of Chicago"
3. Show the health score
4. Highlight: "This aggregates data from CRM, ERP, and calculates risk automatically"

**Closing**: "These workflows run automatically, saving hours of manual work and reducing errors."

## Next Steps After Testing

Once you've verified the workflows work:

1. **Integrate with Frontend** (Phase 4)
   - Add workflow selection UI
   - Display reports in frontend
   - Add parameter input forms

2. **Add More Workflows**
   - Use existing templates as examples
   - Create new workflows for specific use cases
   - Test with real customer scenarios

3. **Production Deployment**
   - Add error handling
   - Implement retry logic
   - Add monitoring and logging

## Quick Reference

### Run All Tests
```bash
python3 test_workflows.py
```

### Interactive Testing
```bash
python3 test_workflows_interactive.py
```

### List Workflows
```python
from app.agents.workflows.factory import WorkflowFactory
workflows = WorkflowFactory.list_workflows()
```

### Execute Specific Workflow
```python
result = await WorkflowFactory.execute_workflow(
    workflow_name="invoice_verification",
    plan_id="test-001",
    session_id="session-001",
    parameters={"invoice_id": "INV-000001"}
)
```

---

**Happy Testing!** 🎉

If you encounter any issues, check the error messages and refer to the troubleshooting section above.
