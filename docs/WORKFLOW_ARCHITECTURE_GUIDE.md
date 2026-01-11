# Workflow Architecture Guide

## Overview

This guide explains how workflows are configured in the current architecture and provides step-by-step instructions for adding new workflows and agent interaction patterns.

## Current Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 1: API Layer                        │
│  (backend/app/api/v3/routes.py)                             │
│  - Receives user requests                                    │
│  - Routes to AgentServiceRefactored                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Layer 2: Service Layer                          │
│  (backend/app/services/agent_service_refactored.py)         │
│  - Detects workflow patterns                                 │
│  - Extracts parameters                                       │
│  - Routes to workflow or regular agent                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Layer 3: Workflow Layer                         │
│  (backend/app/agents/workflows/)                            │
│  - WorkflowFactory: Manages workflow registry                │
│  - Individual workflows: Execute business logic              │
└─────────────────────────────────────────────────────────────┘
```

## How Workflows Are Configured

### 1. Workflow Definition

Each workflow is a Python class in `backend/app/agents/workflows/`:

```python
# backend/app/agents/workflows/your_workflow.py

class YourWorkflow:
    """Your workflow description."""
    
    @staticmethod
    async def execute(plan_id: str, session_id: str, parameters: dict) -> dict:
        """
        Execute the workflow.
        
        Args:
            plan_id: Unique plan identifier
            session_id: Session identifier
            parameters: Workflow-specific parameters
            
        Returns:
            dict with status, messages, final_result
        """
        messages = []
        
        # Step 1: Do something
        messages.append("Step 1 completed")
        
        # Step 2: Do something else
        messages.append("Step 2 completed")
        
        # Generate final result
        final_result = "Workflow completed successfully"
        
        return {
            "status": "completed",
            "messages": messages,
            "final_result": final_result
        }
```

### 2. Workflow Registration

Workflows are registered in `WorkflowFactory`:

```python
# backend/app/agents/workflows/factory.py

class WorkflowFactory:
    """Factory for managing and executing workflows."""
    
    # Registry of available workflows
    _workflows = {
        "your_workflow": {
            "executor": YourWorkflow.execute,
            "title": "Your Workflow Title",
            "description": "What this workflow does",
            "systems": ["System1", "System2"],
            "parameters": ["param1", "param2"]
        }
    }
```

### 3. Pattern Detection

Detection patterns are defined in `AgentServiceRefactored`:

```python
# backend/app/services/agent_service_refactored.py

@staticmethod
def detect_workflow(task_description: str) -> Optional[str]:
    task_lower = task_description.lower()
    
    # Your workflow patterns
    if any(phrase in task_lower for phrase in [
        "your keyword", "another keyword", "trigger phrase"
    ]):
        return "your_workflow"
    
    return None
```

### 4. Parameter Extraction

Parameter extraction logic is also in `AgentServiceRefactored`:

```python
@staticmethod
def extract_parameters(workflow_name: str, task_description: str) -> Dict[str, Any]:
    parameters = {}
    
    if workflow_name == "your_workflow":
        # Extract parameters using regex
        param_match = re.search(r'YOUR-PATTERN', task_description, re.IGNORECASE)
        if param_match:
            parameters["param_name"] = param_match.group(0)
        else:
            parameters["param_name"] = "default_value"
    
    return parameters
```

## Adding a New Workflow: Step-by-Step

### Example: Adding a "Contract Review" Workflow

Let's add a workflow that reviews contracts across legal and finance systems.

#### Step 1: Create the Workflow File

```python
# backend/app/agents/workflows/contract_review.py

"""Contract Review Workflow - Reviews contracts across legal and finance systems."""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ContractReviewWorkflow:
    """
    Contract Review Workflow.
    
    Reviews contract terms, financial implications, and legal compliance
    across multiple systems.
    """
    
    @staticmethod
    async def execute(
        plan_id: str,
        session_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute contract review workflow.
        
        Args:
            plan_id: Plan identifier
            session_id: Session identifier
            parameters: {
                "contract_id": str,
                "legal_system": str,
                "finance_system": str
            }
            
        Returns:
            Workflow execution result
        """
        try:
            logger.info(f"Starting contract review for {parameters.get('contract_id')}")
            
            messages = []
            contract_id = parameters.get("contract_id", "UNKNOWN")
            
            # Step 1: Fetch contract from legal system
            messages.append(f"📄 Fetching contract {contract_id} from legal system...")
            # TODO: Integrate with legal system API
            contract_data = {
                "id": contract_id,
                "title": "Software License Agreement",
                "parties": ["Company A", "Company B"],
                "term": "3 years",
                "value": "$500,000"
            }
            
            # Step 2: Analyze financial terms
            messages.append("💰 Analyzing financial terms...")
            # TODO: Integrate with finance system
            financial_analysis = {
                "total_value": "$500,000",
                "payment_schedule": "Quarterly",
                "risk_level": "Medium"
            }
            
            # Step 3: Check legal compliance
            messages.append("⚖️  Checking legal compliance...")
            compliance_check = {
                "compliant": True,
                "issues": [],
                "recommendations": ["Add termination clause", "Update liability limits"]
            }
            
            # Step 4: Generate review report
            messages.append("📊 Generating review report...")
            
            final_result = f"""# Contract Review Report

## Contract Details
- **Contract ID**: {contract_id}
- **Title**: {contract_data['title']}
- **Parties**: {', '.join(contract_data['parties'])}
- **Term**: {contract_data['term']}
- **Total Value**: {contract_data['value']}

## Financial Analysis
- **Total Value**: {financial_analysis['total_value']}
- **Payment Schedule**: {financial_analysis['payment_schedule']}
- **Risk Level**: {financial_analysis['risk_level']}

## Legal Compliance
- **Status**: {'✅ Compliant' if compliance_check['compliant'] else '❌ Non-Compliant'}
- **Issues**: {len(compliance_check['issues'])} found
- **Recommendations**:
{chr(10).join(f"  - {rec}" for rec in compliance_check['recommendations'])}

## Overall Assessment
Contract is ready for approval with minor recommendations.
"""
            
            logger.info(f"Contract review completed for {contract_id}")
            
            return {
                "status": "completed",
                "messages": messages,
                "final_result": final_result,
                "contract_data": contract_data,
                "financial_analysis": financial_analysis,
                "compliance_check": compliance_check
            }
            
        except Exception as e:
            logger.error(f"Contract review failed: {e}", exc_info=True)
            return {
                "status": "error",
                "messages": [f"Error: {str(e)}"],
                "final_result": f"Contract review failed: {str(e)}"
            }
```

#### Step 2: Register in WorkflowFactory

```python
# backend/app/agents/workflows/factory.py

from app.agents.workflows.contract_review import ContractReviewWorkflow

class WorkflowFactory:
    """Factory for managing and executing workflows."""
    
    _workflows = {
        # ... existing workflows ...
        
        "contract_review": {
            "executor": ContractReviewWorkflow.execute,
            "title": "Contract Review",
            "description": "Review contracts across legal and finance systems",
            "systems": ["Legal", "Finance"],
            "parameters": ["contract_id", "legal_system", "finance_system"]
        }
    }
```

#### Step 3: Add Detection Pattern

```python
# backend/app/services/agent_service_refactored.py

@staticmethod
def detect_workflow(task_description: str) -> Optional[str]:
    task_lower = task_description.lower()
    
    # ... existing patterns ...
    
    # Contract review patterns
    if any(phrase in task_lower for phrase in [
        "review contract", "contract review", "analyze contract",
        "check contract", "contract analysis", "evaluate contract"
    ]):
        return "contract_review"
    
    return None
```

#### Step 4: Add Parameter Extraction

```python
# backend/app/services/agent_service_refactored.py

@staticmethod
def extract_parameters(workflow_name: str, task_description: str) -> Dict[str, Any]:
    parameters = {}
    
    # ... existing extractions ...
    
    if workflow_name == "contract_review":
        # Extract contract ID (format: CTR-XXXXXX)
        contract_match = re.search(r'CTR-\d{6}', task_description, re.IGNORECASE)
        if contract_match:
            parameters["contract_id"] = contract_match.group(0)
        else:
            # Default for demo
            parameters["contract_id"] = "CTR-000001"
        
        parameters["legal_system"] = "docusign"
        parameters["finance_system"] = "netsuite"
    
    return parameters
```

#### Step 5: Test the Workflow

```python
# backend/test_contract_review.py

import asyncio
from app.agents.workflows.factory import WorkflowFactory
from app.services.agent_service_refactored import AgentServiceRefactored

async def test_contract_review():
    # Test detection
    task = "Review contract CTR-123456"
    workflow = AgentServiceRefactored.detect_workflow(task)
    print(f"Detected: {workflow}")  # Should be "contract_review"
    
    # Test parameter extraction
    params = AgentServiceRefactored.extract_parameters(workflow, task)
    print(f"Parameters: {params}")
    
    # Test execution
    result = await WorkflowFactory.execute_workflow(
        workflow_name="contract_review",
        plan_id="test-001",
        session_id="test-session",
        parameters=params
    )
    
    print(f"Status: {result['status']}")
    print(f"Result:\n{result['final_result']}")

if __name__ == "__main__":
    asyncio.run(test_contract_review())
```

#### Step 6: Run Tests

```bash
cd backend
python3 test_contract_review.py
python3 test_phase4_integration.py  # Verify no regressions
```

## Adding New Agent Interaction Patterns

### Pattern 1: Sequential Multi-Agent Workflow

For workflows that need multiple agents in sequence:

```python
class SequentialWorkflow:
    @staticmethod
    async def execute(plan_id: str, session_id: str, parameters: dict) -> dict:
        messages = []
        
        # Agent 1: Data Collection
        messages.append("Agent 1: Collecting data...")
        data = await collect_data(parameters)
        
        # Agent 2: Analysis
        messages.append("Agent 2: Analyzing data...")
        analysis = await analyze_data(data)
        
        # Agent 3: Report Generation
        messages.append("Agent 3: Generating report...")
        report = await generate_report(analysis)
        
        return {
            "status": "completed",
            "messages": messages,
            "final_result": report
        }
```

### Pattern 2: Parallel Multi-Agent Workflow

For workflows where agents can work in parallel:

```python
import asyncio

class ParallelWorkflow:
    @staticmethod
    async def execute(plan_id: str, session_id: str, parameters: dict) -> dict:
        messages = []
        
        # Execute agents in parallel
        messages.append("Starting parallel execution...")
        
        results = await asyncio.gather(
            agent1_task(parameters),
            agent2_task(parameters),
            agent3_task(parameters)
        )
        
        # Combine results
        messages.append("Combining results...")
        final_result = combine_results(results)
        
        return {
            "status": "completed",
            "messages": messages,
            "final_result": final_result
        }
```

### Pattern 3: Conditional Branching Workflow

For workflows with conditional logic:

```python
class ConditionalWorkflow:
    @staticmethod
    async def execute(plan_id: str, session_id: str, parameters: dict) -> dict:
        messages = []
        
        # Initial check
        messages.append("Performing initial check...")
        check_result = await initial_check(parameters)
        
        if check_result["needs_approval"]:
            # Branch A: Requires approval
            messages.append("Approval required - routing to approval agent...")
            result = await approval_workflow(check_result)
        else:
            # Branch B: Auto-process
            messages.append("Auto-processing...")
            result = await auto_process(check_result)
        
        return {
            "status": "completed",
            "messages": messages,
            "final_result": result
        }
```

### Pattern 4: Iterative Refinement Workflow

For workflows that iterate until a condition is met:

```python
class IterativeWorkflow:
    @staticmethod
    async def execute(plan_id: str, session_id: str, parameters: dict) -> dict:
        messages = []
        max_iterations = 5
        iteration = 0
        
        result = None
        while iteration < max_iterations:
            iteration += 1
            messages.append(f"Iteration {iteration}...")
            
            # Process
            result = await process_step(parameters, result)
            
            # Check if done
            if result["quality_score"] > 0.9:
                messages.append("Quality threshold met!")
                break
        
        return {
            "status": "completed",
            "messages": messages,
            "final_result": result["output"],
            "iterations": iteration
        }
```

### Pattern 5: Human-in-the-Loop Workflow

For workflows requiring human approval:

```python
class HITLWorkflow:
    @staticmethod
    async def execute(plan_id: str, session_id: str, parameters: dict) -> dict:
        messages = []
        
        # Step 1: Generate proposal
        messages.append("Generating proposal...")
        proposal = await generate_proposal(parameters)
        
        # Step 2: Request approval (this would pause execution)
        messages.append("Awaiting human approval...")
        # In real implementation, this would:
        # 1. Send approval request via WebSocket
        # 2. Store state
        # 3. Wait for approval callback
        
        # Step 3: Execute based on approval
        messages.append("Executing approved action...")
        result = await execute_action(proposal)
        
        return {
            "status": "completed",
            "messages": messages,
            "final_result": result,
            "requires_approval": True  # Flag for service layer
        }
```

## Advanced Configuration

### Adding Workflow Metadata

```python
# In WorkflowFactory
_workflows = {
    "your_workflow": {
        "executor": YourWorkflow.execute,
        "title": "Your Workflow",
        "description": "What it does",
        "systems": ["System1", "System2"],
        "parameters": ["param1", "param2"],
        
        # Advanced metadata
        "category": "finance",  # For grouping
        "tags": ["invoice", "payment"],  # For search
        "estimated_duration": 30,  # seconds
        "requires_auth": True,  # Needs authentication
        "version": "1.0.0",  # Workflow version
        "author": "team@company.com"
    }
}
```

### Adding Workflow Validation

```python
class YourWorkflow:
    @staticmethod
    def validate_parameters(parameters: dict) -> tuple[bool, str]:
        """Validate workflow parameters."""
        if "required_param" not in parameters:
            return False, "Missing required_param"
        
        if not parameters["required_param"]:
            return False, "required_param cannot be empty"
        
        return True, ""
    
    @staticmethod
    async def execute(plan_id: str, session_id: str, parameters: dict) -> dict:
        # Validate first
        valid, error = YourWorkflow.validate_parameters(parameters)
        if not valid:
            return {
                "status": "error",
                "messages": [f"Validation failed: {error}"],
                "final_result": f"Error: {error}"
            }
        
        # Continue with execution...
```

### Adding Workflow Hooks

```python
class YourWorkflow:
    @staticmethod
    async def before_execute(parameters: dict):
        """Hook called before execution."""
        logger.info(f"Starting workflow with params: {parameters}")
        # Setup, logging, metrics, etc.
    
    @staticmethod
    async def after_execute(result: dict):
        """Hook called after execution."""
        logger.info(f"Workflow completed with status: {result['status']}")
        # Cleanup, metrics, notifications, etc.
    
    @staticmethod
    async def execute(plan_id: str, session_id: str, parameters: dict) -> dict:
        await YourWorkflow.before_execute(parameters)
        
        try:
            # Main execution logic
            result = {"status": "completed", ...}
        finally:
            await YourWorkflow.after_execute(result)
        
        return result
```

## Best Practices

### 1. Workflow Design
- ✅ Keep workflows focused on a single business process
- ✅ Make workflows reusable with parameters
- ✅ Include clear progress messages
- ✅ Handle errors gracefully
- ✅ Return structured results

### 2. Pattern Detection
- ✅ Use specific keywords before generic ones
- ✅ Test patterns with real user input
- ✅ Avoid overlapping patterns
- ✅ Document pattern choices

### 3. Parameter Extraction
- ✅ Provide sensible defaults
- ✅ Validate extracted parameters
- ✅ Use regex for structured data (IDs, dates)
- ✅ Use NLP for unstructured data (names, descriptions)

### 4. Testing
- ✅ Test workflow execution independently
- ✅ Test pattern detection with edge cases
- ✅ Test parameter extraction with variations
- ✅ Test integration with service layer

### 5. Documentation
- ✅ Document workflow purpose and steps
- ✅ Document required parameters
- ✅ Document expected output format
- ✅ Provide usage examples

## Troubleshooting

### Workflow Not Detected
```python
# Debug detection
task = "your task description"
workflow = AgentServiceRefactored.detect_workflow(task)
print(f"Detected: {workflow}")  # Should not be None

# Check patterns
task_lower = task.lower()
print(f"Contains 'keyword': {'keyword' in task_lower}")
```

### Parameters Not Extracted
```python
# Debug extraction
params = AgentServiceRefactored.extract_parameters("workflow_name", task)
print(f"Extracted: {params}")

# Test regex
import re
match = re.search(r'YOUR-PATTERN', task)
print(f"Match: {match.group(0) if match else 'No match'}")
```

### Workflow Execution Fails
```python
# Add detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test directly
result = await WorkflowFactory.execute_workflow(
    workflow_name="your_workflow",
    plan_id="test",
    session_id="test",
    parameters={"param": "value"}
)
print(f"Result: {result}")
```

## Summary

**To add a new workflow:**
1. Create workflow file in `backend/app/agents/workflows/`
2. Register in `WorkflowFactory`
3. Add detection pattern in `AgentServiceRefactored.detect_workflow()`
4. Add parameter extraction in `AgentServiceRefactored.extract_parameters()`
5. Test thoroughly

**The architecture is designed to be:**
- ✅ Easy to extend (add workflows in minutes)
- ✅ Maintainable (clear separation of concerns)
- ✅ Testable (each layer can be tested independently)
- ✅ Flexible (supports various interaction patterns)

---

**Need help?** Check the existing workflows in `backend/app/agents/workflows/` for examples!
