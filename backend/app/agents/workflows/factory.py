"""Workflow Factory - Create and manage workflow templates."""
import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph

from app.agents.workflows.invoice_verification import create_invoice_verification_workflow
from app.agents.workflows.payment_tracking import create_payment_tracking_workflow
from app.agents.workflows.customer_360 import create_customer_360_workflow

logger = logging.getLogger(__name__)


class WorkflowFactory:
    """Factory for creating and managing workflow templates."""
    
    _workflows: Dict[str, StateGraph] = {}
    
    @classmethod
    def get_workflow(cls, workflow_name: str) -> Optional[StateGraph]:
        """
        Get or create a workflow by name.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            Compiled StateGraph or None
        """
        if workflow_name in cls._workflows:
            return cls._workflows[workflow_name]
        
        # Create workflow
        if workflow_name == "invoice_verification":
            workflow = create_invoice_verification_workflow()
        elif workflow_name == "payment_tracking":
            workflow = create_payment_tracking_workflow()
        elif workflow_name == "customer_360":
            workflow = create_customer_360_workflow()
        else:
            logger.error(f"Unknown workflow: {workflow_name}")
            return None
        
        # Cache it
        cls._workflows[workflow_name] = workflow
        logger.info(f"Created workflow: {workflow_name}")
        
        return workflow
    
    @classmethod
    def list_workflows(cls) -> list[Dict[str, Any]]:
        """
        List all available workflows.
        
        Returns:
            List of workflow metadata
        """
        return [
            {
                "name": "invoice_verification",
                "title": "Invoice Verification",
                "description": "Cross-check invoice data across ERP and CRM systems",
                "systems": ["ERP", "CRM"],
                "parameters": ["invoice_id", "erp_system", "crm_system"]
            },
            {
                "name": "payment_tracking",
                "title": "Payment Tracking",
                "description": "Track payment status across ERP and Email systems",
                "systems": ["ERP", "Email"],
                "parameters": ["invoice_id", "erp_system"]
            },
            {
                "name": "customer_360",
                "title": "Customer 360 View",
                "description": "Aggregate customer data from CRM, ERP, and Accounting",
                "systems": ["CRM", "ERP", "Accounting"],
                "parameters": ["customer_name"]
            }
        ]
    
    @classmethod
    async def execute_workflow(
        cls,
        workflow_name: str,
        plan_id: str,
        session_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a workflow with parameters.
        
        Args:
            workflow_name: Name of workflow to execute
            plan_id: Plan identifier
            session_id: Session identifier
            parameters: Workflow-specific parameters
            
        Returns:
            Execution results
        """
        try:
            # Get workflow
            workflow = cls.get_workflow(workflow_name)
            if not workflow:
                return {
                    "status": "error",
                    "error": f"Workflow '{workflow_name}' not found"
                }
            
            # Create initial state
            initial_state = {
                "plan_id": plan_id,
                "session_id": session_id,
                "workflow_name": workflow_name,
                "workflow_params": parameters,
                "messages": [],
                "current_agent": "",
            }
            
            # Execute workflow
            config = {"configurable": {"thread_id": f"workflow_{plan_id}"}}
            logger.info(f"Executing workflow '{workflow_name}' for plan {plan_id}")
            
            result = await workflow.ainvoke(initial_state, config)
            
            logger.info(f"Workflow '{workflow_name}' completed for plan {plan_id}")
            
            return {
                "status": "completed",
                "workflow_name": workflow_name,
                "plan_id": plan_id,
                "final_result": result.get("final_result"),
                "messages": result.get("messages", [])
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "workflow_name": workflow_name,
                "plan_id": plan_id,
                "error": str(e)
            }

