"""Agent node implementations."""
import logging
from typing import Dict, Any

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Planner agent node - analyzes task and creates execution plan.
    Phase 5: Routes to appropriate specialized agent.
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Planner processing task for plan {plan_id}")
    
    # Analyze task and determine which agent to route to
    task_lower = task.lower()
    
    if any(word in task_lower for word in ["invoice", "payment", "bill", "vendor"]):
        next_agent = "invoice"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be an invoice-related task. Routing to Invoice Agent for specialized handling."
    elif any(word in task_lower for word in ["closing", "reconciliation", "journal", "variance", "gl"]):
        next_agent = "closing"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be a closing process task. Routing to Closing Agent for specialized handling."
    elif any(word in task_lower for word in ["audit", "compliance", "evidence", "exception", "monitoring"]):
        next_agent = "audit"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be an audit-related task. Routing to Audit Agent for specialized handling."
    else:
        # Default to invoice agent
        next_agent = "invoice"
        response = f"I've analyzed your task: '{task}'.\n\nRouting to Invoice Agent for processing."
    
    return {
        "messages": [response],
        "current_agent": "Planner",
        "next_agent": next_agent
    }


def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Invoice agent node - handles invoice management tasks.
    Phase 5: Hardcoded responses for invoice operations.
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Invoice Agent processing task for plan {plan_id}")
    
    response = f"Invoice Agent here. I've processed your request:\n\n"
    response += "✓ Verified invoice accuracy and completeness\n"
    response += "✓ Checked payment due dates and status\n"
    response += "✓ Reviewed vendor information\n"
    response += "✓ Validated payment terms\n\n"
    response += "Invoice analysis complete. All checks passed successfully."
    
    return {
        "messages": [response],
        "current_agent": "Invoice",
        "final_result": response
    }


def closing_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Closing agent node - handles closing process automation.
    Phase 5: Hardcoded responses for closing operations.
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Closing Agent processing task for plan {plan_id}")
    
    response = f"Closing Agent here. I've completed the closing process:\n\n"
    response += "✓ Performed account reconciliations\n"
    response += "✓ Drafted journal entries\n"
    response += "✓ Identified GL anomalies\n"
    response += "✓ Completed variance analysis\n\n"
    response += "Closing process complete. All reconciliations balanced."
    
    return {
        "messages": [response],
        "current_agent": "Closing",
        "final_result": response
    }


def audit_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Audit agent node - handles audit automation tasks.
    Phase 5: Hardcoded responses for audit operations.
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Audit Agent processing task for plan {plan_id}")
    
    response = f"Audit Agent here. I've completed the audit review:\n\n"
    response += "✓ Performed continuous monitoring\n"
    response += "✓ Gathered audit evidence\n"
    response += "✓ Detected exceptions and anomalies\n"
    response += "✓ Prepared audit responses\n\n"
    response += "Audit review complete. No critical issues identified."
    
    return {
        "messages": [response],
        "current_agent": "Audit",
        "final_result": response
    }


def approval_checkpoint_node(state: AgentState) -> Dict[str, Any]:
    """
    Approval checkpoint node - requests human approval before proceeding.
    Phase 6: Sets approval_required flag and waits for human input.
    """
    plan_id = state["plan_id"]
    
    logger.info(f"Approval checkpoint reached for plan {plan_id}")
    
    return {
        "approval_required": True,
        "approved": None
    }
