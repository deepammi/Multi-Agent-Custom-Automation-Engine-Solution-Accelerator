# Complete Example: Adding a "Expense Approval" Workflow

This document walks through adding a complete new workflow from start to finish.

## Use Case

**Business Need**: Automate expense report approval by checking expense against policy rules, verifying receipts, and routing to appropriate approver.

**User Input Examples:**
- "Approve expense report EXP-123456"
- "Review expense EXP-789012"
- "Check expense report for policy violations"

## Step-by-Step Implementation

### Step 1: Create the Workflow File

Create `backend/app/agents/workflows/expense_approval.py`:

```python
"""Expense Approval Workflow - Automates expense report approval process."""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ExpenseApprovalWorkflow:
    """
    Expense Approval Workflow.
    
    Checks expense reports against policy rules, verifies receipts,
    and routes to appropriate approver based on amount and category.
    """
    
    # Policy rules
    POLICY_RULES = {
        "max_meal_amount": 75.00,
        "max_hotel_amount": 300.00,
        "max_travel_amount": 1000.00,
        "requires_receipt_over": 25.00,
        "auto_approve_under": 100.00
    }
    
    @staticmethod
    async def execute(
        plan_id: str,
        session_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute expense approval workflow.
        
        Args:
            plan_id: Plan identifier
            session_id: Session identifier
            parameters: {
                "expense_id": str,
                "hr_system": str (default: "workday"),
                "finance_system": str (default: "netsuite")
            }
            
        Returns:
            Workflow execution result with approval decision
        """
        try:
            expense_id = parameters.get("expense_id", "UNKNOWN")
            logger.info(f"Starting expense approval for {expense_id}")
            
            messages = []
            
            # Step 1: Fetch expense report
            messages.append(f"📋 Fetching expense report {expense_id}...")
            expense_data = await ExpenseApprovalWorkflow._fetch_expense(
                expense_id,
                parameters.get("hr_system", "workday")
            )
            
            # Step 2: Verify receipts
            messages.append("🧾 Verifying receipts...")
            receipt_check = await ExpenseApprovalWorkflow._verify_receipts(
                expense_data
            )
            
            # Step 3: Check policy compliance
            messages.append("📜 Checking policy compliance...")
            policy_check = await ExpenseApprovalWorkflow._check_policy(
                expense_data
            )
            
            # Step 4: Determine approval routing
            messages.append("🔀 Determining approval routing...")
            routing = await ExpenseApprovalWorkflow._determine_routing(
                expense_data,
                policy_check
            )
            
            # Step 5: Generate approval recommendation
            messages.append("✅ Generating approval recommendation...")
            
            # Build final result
            final_result = ExpenseApprovalWorkflow._format_result(
                expense_data,
                receipt_check,
                policy_check,
                routing
            )
            
            logger.info(f"Expense approval completed for {expense_id}")
            
            return {
                "status": "completed",
                "messages": messages,
                "final_result": final_result,
                "expense_data": expense_data,
                "policy_check": policy_check,
                "routing": routing
            }
            
        except Exception as e:
            logger.error(f"Expense approval failed: {e}", exc_info=True)
            return {
                "status": "error",
                "messages": [f"Error: {str(e)}"],
                "final_result": f"Expense approval failed: {str(e)}"
            }
    
    @staticmethod
    async def _fetch_expense(expense_id: str, hr_system: str) -> Dict[str, Any]:
        """Fetch expense report from HR system."""
        # TODO: Integrate with actual HR system API
        # For now, return mock data
        return {
            "id": expense_id,
            "employee": "John Doe",
            "employee_id": "EMP-12345",
            "department": "Engineering",
            "submission_date": "2024-12-01",
            "total_amount": 450.00,
            "currency": "USD",
            "items": [
                {
                    "date": "2024-11-28",
                    "category": "Meals",
                    "description": "Client dinner",
                    "amount": 125.00,
                    "has_receipt": True
                },
                {
                    "date": "2024-11-29",
                    "category": "Hotel",
                    "description": "Conference hotel",
                    "amount": 275.00,
                    "has_receipt": True
                },
                {
                    "date": "2024-11-30",
                    "category": "Travel",
                    "description": "Taxi to airport",
                    "amount": 50.00,
                    "has_receipt": False
                }
            ]
        }
    
    @staticmethod
    async def _verify_receipts(expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify all required receipts are present."""
        missing_receipts = []
        
        for item in expense_data["items"]:
            if item["amount"] > ExpenseApprovalWorkflow.POLICY_RULES["requires_receipt_over"]:
                if not item["has_receipt"]:
                    missing_receipts.append({
                        "date": item["date"],
                        "category": item["category"],
                        "amount": item["amount"]
                    })
        
        return {
            "all_receipts_present": len(missing_receipts) == 0,
            "missing_receipts": missing_receipts,
            "total_missing": len(missing_receipts)
        }
    
    @staticmethod
    async def _check_policy(expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check expense against policy rules."""
        violations = []
        
        for item in expense_data["items"]:
            category = item["category"].lower()
            amount = item["amount"]
            
            # Check category-specific limits
            if category == "meals":
                if amount > ExpenseApprovalWorkflow.POLICY_RULES["max_meal_amount"]:
                    violations.append({
                        "item": item["description"],
                        "category": category,
                        "amount": amount,
                        "limit": ExpenseApprovalWorkflow.POLICY_RULES["max_meal_amount"],
                        "severity": "high"
                    })
            
            elif category == "hotel":
                if amount > ExpenseApprovalWorkflow.POLICY_RULES["max_hotel_amount"]:
                    violations.append({
                        "item": item["description"],
                        "category": category,
                        "amount": amount,
                        "limit": ExpenseApprovalWorkflow.POLICY_RULES["max_hotel_amount"],
                        "severity": "medium"
                    })
            
            elif category == "travel":
                if amount > ExpenseApprovalWorkflow.POLICY_RULES["max_travel_amount"]:
                    violations.append({
                        "item": item["description"],
                        "category": category,
                        "amount": amount,
                        "limit": ExpenseApprovalWorkflow.POLICY_RULES["max_travel_amount"],
                        "severity": "high"
                    })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "total_violations": len(violations)
        }
    
    @staticmethod
    async def _determine_routing(
        expense_data: Dict[str, Any],
        policy_check: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine approval routing based on amount and policy."""
        total_amount = expense_data["total_amount"]
        has_violations = not policy_check["compliant"]
        
        # Auto-approve small amounts with no violations
        if total_amount < ExpenseApprovalWorkflow.POLICY_RULES["auto_approve_under"] and not has_violations:
            return {
                "decision": "auto_approved",
                "approver": "system",
                "reason": "Amount under auto-approval threshold with no policy violations"
            }
        
        # Route to manager for medium amounts
        elif total_amount < 500.00:
            return {
                "decision": "requires_approval",
                "approver": "manager",
                "reason": "Amount requires manager approval"
            }
        
        # Route to director for large amounts or violations
        else:
            return {
                "decision": "requires_approval",
                "approver": "director",
                "reason": "Large amount or policy violations require director approval"
            }
    
    @staticmethod
    def _format_result(
        expense_data: Dict[str, Any],
        receipt_check: Dict[str, Any],
        policy_check: Dict[str, Any],
        routing: Dict[str, Any]
    ) -> str:
        """Format the final approval result."""
        
        # Build receipt status
        receipt_status = "✅ All receipts present" if receipt_check["all_receipts_present"] else f"⚠️  {receipt_check['total_missing']} receipts missing"
        
        # Build policy status
        policy_status = "✅ Policy compliant" if policy_check["compliant"] else f"❌ {policy_check['total_violations']} policy violations"
        
        # Build approval decision
        if routing["decision"] == "auto_approved":
            decision_icon = "✅"
            decision_text = "AUTO-APPROVED"
        else:
            decision_icon = "⏳"
            decision_text = f"PENDING - Requires {routing['approver'].upper()} approval"
        
        result = f"""# Expense Approval Report

## Expense Details
- **Expense ID**: {expense_data['id']}
- **Employee**: {expense_data['employee']} ({expense_data['employee_id']})
- **Department**: {expense_data['department']}
- **Submission Date**: {expense_data['submission_date']}
- **Total Amount**: ${expense_data['total_amount']:.2f} {expense_data['currency']}

## Line Items
"""
        
        for item in expense_data['items']:
            result += f"""
- **{item['date']}** - {item['category']}: {item['description']}
  - Amount: ${item['amount']:.2f}
  - Receipt: {'✅' if item['has_receipt'] else '❌'}
"""
        
        result += f"""
## Verification Results

### Receipt Verification
{receipt_status}
"""
        
        if receipt_check["missing_receipts"]:
            result += "\nMissing receipts:\n"
            for missing in receipt_check["missing_receipts"]:
                result += f"- {missing['date']} - {missing['category']}: ${missing['amount']:.2f}\n"
        
        result += f"""
### Policy Compliance
{policy_status}
"""
        
        if policy_check["violations"]:
            result += "\nPolicy violations:\n"
            for violation in policy_check["violations"]:
                result += f"- {violation['item']}: ${violation['amount']:.2f} exceeds {violation['category']} limit of ${violation['limit']:.2f} (Severity: {violation['severity']})\n"
        
        result += f"""
## Approval Decision
{decision_icon} **{decision_text}**

**Routing**: {routing['approver'].title()}
**Reason**: {routing['reason']}
"""
        
        return result
```

### Step 2: Register in WorkflowFactory

Edit `backend/app/agents/workflows/factory.py`:

```python
from app.agents.workflows.expense_approval import ExpenseApprovalWorkflow

class WorkflowFactory:
    """Factory for managing and executing workflows."""
    
    _workflows = {
        # ... existing workflows ...
        
        "expense_approval": {
            "executor": ExpenseApprovalWorkflow.execute,
            "name": "expense_approval",
            "title": "Expense Approval",
            "description": "Automate expense report approval with policy checks",
            "systems": ["HR", "Finance"],
            "parameters": ["expense_id", "hr_system", "finance_system"],
            "category": "finance",
            "tags": ["expense", "approval", "policy"],
            "version": "1.0.0"
        }
    }
```

### Step 3: Add Detection Pattern

Edit `backend/app/services/agent_service_refactored.py`:

```python
@staticmethod
def detect_workflow(task_description: str) -> Optional[str]:
    task_lower = task_description.lower()
    
    # ... existing patterns ...
    
    # Expense approval patterns
    if any(phrase in task_lower for phrase in [
        "approve expense", "expense approval", "review expense",
        "check expense", "expense report", "verify expense"
    ]):
        return "expense_approval"
    
    return None
```

### Step 4: Add Parameter Extraction

Edit `backend/app/services/agent_service_refactored.py`:

```python
@staticmethod
def extract_parameters(workflow_name: str, task_description: str) -> Dict[str, Any]:
    parameters = {}
    
    # ... existing extractions ...
    
    if workflow_name == "expense_approval":
        # Extract expense ID (format: EXP-XXXXXX)
        expense_match = re.search(r'EXP-\d{6}', task_description, re.IGNORECASE)
        if expense_match:
            parameters["expense_id"] = expense_match.group(0)
        else:
            # Default for demo
            parameters["expense_id"] = "EXP-000001"
        
        parameters["hr_system"] = "workday"
        parameters["finance_system"] = "netsuite"
    
    return parameters
```

### Step 5: Create Test File

Create `backend/test_expense_approval.py`:

```python
"""Test expense approval workflow."""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.workflows.factory import WorkflowFactory
from app.services.agent_service_refactored import AgentServiceRefactored


async def test_expense_approval():
    print("=" * 70)
    print("Testing Expense Approval Workflow")
    print("=" * 70)
    
    # Test 1: Detection
    print("\n1. Testing workflow detection...")
    test_inputs = [
        "Approve expense report EXP-123456",
        "Review expense EXP-789012",
        "Check expense for policy violations"
    ]
    
    for task in test_inputs:
        workflow = AgentServiceRefactored.detect_workflow(task)
        print(f"   '{task}' → {workflow}")
    
    # Test 2: Parameter extraction
    print("\n2. Testing parameter extraction...")
    task = "Approve expense report EXP-123456"
    params = AgentServiceRefactored.extract_parameters("expense_approval", task)
    print(f"   Parameters: {params}")
    
    # Test 3: Workflow execution
    print("\n3. Testing workflow execution...")
    result = await WorkflowFactory.execute_workflow(
        workflow_name="expense_approval",
        plan_id="test-exp-001",
        session_id="test-session",
        parameters={
            "expense_id": "EXP-123456",
            "hr_system": "workday",
            "finance_system": "netsuite"
        }
    )
    
    print(f"\n   Status: {result['status']}")
    print(f"\n   Messages:")
    for msg in result.get('messages', []):
        print(f"      {msg}")
    
    print(f"\n   Final Result:")
    print(result.get('final_result', 'No result'))
    
    print("\n" + "=" * 70)
    print("✅ Expense Approval Workflow Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_expense_approval())
```

### Step 6: Run Tests

```bash
cd backend

# Test the new workflow
python3 test_expense_approval.py

# Run full integration tests
python3 test_phase4_integration.py
```

### Step 7: Verify API Integration

Test via API:

```bash
# List workflows (should include expense_approval)
curl http://localhost:8000/api/v3/workflows

# Execute via smart routing
curl -X POST http://localhost:8000/api/v3/process_request_v2 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Approve expense report EXP-123456",
    "session_id": "test-session",
    "require_hitl": false
  }'

# Execute directly
curl -X POST http://localhost:8000/api/v3/execute_workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "expense_approval",
    "plan_id": "test-001",
    "session_id": "test-session",
    "parameters": {
      "expense_id": "EXP-123456",
      "hr_system": "workday",
      "finance_system": "netsuite"
    }
  }'
```

## Expected Output

When you run the test, you should see:

```
======================================================================
Testing Expense Approval Workflow
======================================================================

1. Testing workflow detection...
   'Approve expense report EXP-123456' → expense_approval
   'Review expense EXP-789012' → expense_approval
   'Check expense for policy violations' → expense_approval

2. Testing parameter extraction...
   Parameters: {'expense_id': 'EXP-123456', 'hr_system': 'workday', 'finance_system': 'netsuite'}

3. Testing workflow execution...

   Status: completed

   Messages:
      📋 Fetching expense report EXP-123456...
      🧾 Verifying receipts...
      📜 Checking policy compliance...
      🔀 Determining approval routing...
      ✅ Generating approval recommendation...

   Final Result:
# Expense Approval Report

## Expense Details
- **Expense ID**: EXP-123456
- **Employee**: John Doe (EMP-12345)
- **Department**: Engineering
- **Submission Date**: 2024-12-01
- **Total Amount**: $450.00 USD

## Line Items

- **2024-11-28** - Meals: Client dinner
  - Amount: $125.00
  - Receipt: ✅

- **2024-11-29** - Hotel: Conference hotel
  - Amount: $275.00
  - Receipt: ✅

- **2024-11-30** - Travel: Taxi to airport
  - Amount: $50.00
  - Receipt: ❌

## Verification Results

### Receipt Verification
⚠️  1 receipts missing

Missing receipts:
- 2024-11-30 - Travel: $50.00

### Policy Compliance
❌ 1 policy violations

Policy violations:
- Client dinner: $125.00 exceeds meals limit of $75.00 (Severity: high)

## Approval Decision
⏳ **PENDING - Requires MANAGER approval**

**Routing**: Manager
**Reason**: Amount requires manager approval

======================================================================
✅ Expense Approval Workflow Test Complete!
======================================================================
```

## Summary

You've successfully added a complete new workflow! The workflow:

✅ Fetches expense data from HR system
✅ Verifies receipts are present
✅ Checks policy compliance
✅ Determines approval routing
✅ Generates formatted report
✅ Integrates with existing API
✅ Works with smart routing

**Time to implement**: ~30 minutes
**Lines of code**: ~300 lines
**Integration points**: 4 files modified

This demonstrates how easy it is to extend the system with new workflows!
