"""Refactored Agent Service integrating LangGraph workflows."""
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.workflows.factory import WorkflowFactory
from app.services.langgraph_service import LangGraphService
from app.db.repositories import PlanRepository
from app.services.websocket_service import get_websocket_manager

websocket_manager = get_websocket_manager()

logger = logging.getLogger(__name__)


class AgentServiceRefactored:
    """Refactored agent service with workflow integration."""
    
    @staticmethod
    def detect_workflow(task_description: str) -> Optional[str]:
        """
        Detect if task should use a workflow template.
        
        Args:
            task_description: User's task description
            
        Returns:
            Workflow name or None for regular agent
        """
        task_lower = task_description.lower()
        
        # Invoice verification patterns
        if any(phrase in task_lower for phrase in [
            "verify invoice", "check invoice", "validate invoice",
            "cross-check invoice", "invoice verification", "compare invoice"
        ]):
            return "invoice_verification"
        
        # Payment tracking patterns
        if any(phrase in task_lower for phrase in [
            "track payment", "payment status", "payment tracking",
            "check payment", "payment confirmation", "find payment"
        ]):
            return "payment_tracking"
        
        # Customer 360 patterns
        if any(phrase in task_lower for phrase in [
            "customer 360", "customer view", "customer profile",
            "complete view", "customer summary", "customer analysis",
            "customer overview"
        ]):
            return "customer_360"
        
        return None
    
    @staticmethod
    def extract_parameters(workflow_name: str, task_description: str) -> Dict[str, Any]:
        """
        Extract parameters from task description for workflow.
        
        Args:
            workflow_name: Name of workflow
            task_description: Task description
            
        Returns:
            Parameters dictionary
        """
        parameters = {}
        
        if workflow_name == "invoice_verification":
            # Extract invoice ID (format: INV-XXXXXX)
            invoice_match = re.search(r'INV-\d{6}', task_description, re.IGNORECASE)
            if invoice_match:
                parameters["invoice_id"] = invoice_match.group(0)
            else:
                # Default for demo
                parameters["invoice_id"] = "INV-000001"
            
            parameters["erp_system"] = "zoho"
            parameters["crm_system"] = "salesforce"
        
        elif workflow_name == "payment_tracking":
            # Extract invoice ID
            invoice_match = re.search(r'INV-\d{6}', task_description, re.IGNORECASE)
            if invoice_match:
                parameters["invoice_id"] = invoice_match.group(0)
            else:
                parameters["invoice_id"] = "INV-000002"
            
            parameters["erp_system"] = "zoho"
        
        elif workflow_name == "customer_360":
            # Extract customer name from various patterns
            customer_patterns = [
                r'for\s+([^,\.\?!]+)',
                r'about\s+([^,\.\?!]+)',
                r'of\s+([^,\.\?!]+)',
                r'customer\s+([^,\.\?!]+)',
            ]
            
            customer_name = None
            for pattern in customer_patterns:
                match = re.search(pattern, task_description, re.IGNORECASE)
                if match:
                    customer_name = match.group(1).strip()
                    # Clean up common words and phrases
                    customer_name = re.sub(r'\b(the|a|an|customer|360|view)\b', '', customer_name, flags=re.IGNORECASE).strip()
                    # Remove extra whitespace
                    customer_name = ' '.join(customer_name.split())
                    if customer_name and len(customer_name) > 2:
                        break
            
            if not customer_name:
                # Default for demo
                customer_name = "University of Chicago"
            
            parameters["customer_name"] = customer_name
        
        return parameters
    
    @staticmethod
    async def execute_task(
        plan_id: str,
        session_id: str,
        task_description: str,
        require_hitl: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a task using workflows or regular agents.
        
        Args:
            plan_id: Plan identifier
            session_id: Session identifier
            task_description: Task to execute
            require_hitl: Whether to require HITL approval
            
        Returns:
            Execution result
        """
        try:
            logger.info(f"🚀 Executing task for plan {plan_id}: {task_description[:100]}...")
            
            # Update plan status
            await PlanRepository.update_status(plan_id, "in_progress")
            
            # Send initial message
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message",
                "data": {
                    "agent_name": "System",
                    "content": f"🚀 Starting task: {task_description[:100]}...",
                    "status": "in_progress",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
            
            # Detect workflow
            workflow_name = AgentServiceRefactored.detect_workflow(task_description)
            
            if workflow_name:
                # Execute workflow
                logger.info(f"📋 Detected workflow: {workflow_name}")
                result = await AgentServiceRefactored._execute_workflow(
                    workflow_name=workflow_name,
                    plan_id=plan_id,
                    session_id=session_id,
                    task_description=task_description
                )
            else:
                # Execute regular agent using LangGraph service (with approval flow)
                logger.info(f"🤖 Using LangGraph service with approval flow")
                from app.services.langgraph_service import LangGraphService
                
                # Call LangGraph service which handles approval flow properly
                result = await LangGraphService.execute_task(
                    plan_id=plan_id,
                    session_id=session_id,
                    task_description=task_description
                )
                
                # The LangGraph service returns {"status": "pending_approval"} 
                # We should return this as-is since it's the correct flow
                return result
            
            # Update plan status based on result
            if result.get("status") == "completed":
                await PlanRepository.update_status(plan_id, "completed")
                
                # Send completion message
                await websocket_manager.send_message(plan_id, {
                    "type": "final_result_message",
                    "data": {
                        "content": result.get("final_result", "Task completed successfully"),
                        "status": "completed",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Task execution failed for plan {plan_id}: {e}", exc_info=True)
            
            # Update plan status
            await PlanRepository.update_status(plan_id, "failed")
            
            # Send error message
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message",
                "data": {
                    "agent_name": "System",
                    "content": f"❌ Task failed: {str(e)}",
                    "status": "error",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
            
            return {
                "status": "error",
                "plan_id": plan_id,
                "error": str(e)
            }
    
    @staticmethod
    async def _execute_workflow(
        workflow_name: str,
        plan_id: str,
        session_id: str,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Execute a workflow template.
        
        Args:
            workflow_name: Name of workflow
            plan_id: Plan identifier
            session_id: Session identifier
            task_description: Original task description
            
        Returns:
            Execution result
        """
        try:
            # Send workflow start message
            workflow_title = workflow_name.replace('_', ' ').title()
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message",
                "data": {
                    "agent_name": "Workflow Engine",
                    "content": f"🔄 Executing {workflow_title} workflow...",
                    "status": "in_progress",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
            
            # Extract parameters
            parameters = AgentServiceRefactored.extract_parameters(
                workflow_name, task_description
            )
            
            logger.info(f"📊 Workflow parameters: {parameters}")
            
            # Execute workflow
            result = await WorkflowFactory.execute_workflow(
                workflow_name=workflow_name,
                plan_id=plan_id,
                session_id=session_id,
                parameters=parameters
            )
            
            # Stream workflow messages
            if result.get("messages"):
                for message in result["messages"]:
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": "Workflow",
                            "content": message,
                            "status": "in_progress",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
            
            # Send final result
            if result.get("final_result"):
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": workflow_title,
                        "content": result["final_result"],
                        "status": "completed",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "workflow_name": workflow_name,
                "plan_id": plan_id,
                "error": str(e)
            }
    
    @staticmethod
    async def list_workflows() -> Dict[str, Any]:
        """
        List available workflow templates.
        
        Returns:
            Available workflows
        """
        try:
            workflows = WorkflowFactory.list_workflows()
            return {
                "status": "success",
                "workflows": workflows
            }
        except Exception as e:
            logger.error(f"❌ Failed to list workflows: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
