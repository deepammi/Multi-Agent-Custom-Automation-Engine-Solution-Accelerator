"""Agent node implementations."""
import logging
from typing import Dict, Any

from app.agents.state import AgentState
from app.services.llm_service import LLMService
from app.agents.prompts import build_invoice_prompt

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


async def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Invoice agent node - handles invoice management tasks.
    Now supports real LLM API calls with streaming or mock mode.
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    websocket_manager = state.get("websocket_manager")
    
    logger.info(f"Invoice Agent processing task for plan {plan_id}")
    
    # Check if mock mode is enabled
    if LLMService.is_mock_mode():
        logger.info("🎭 Using mock mode for Invoice Agent")
        response = LLMService.get_mock_response("Invoice", task)
        return {
            "messages": [response],
            "current_agent": "Invoice",
            "final_result": response
        }
    
    # Build prompt for LLM
    prompt = build_invoice_prompt(task)
    
    # Call LLM with streaming if websocket_manager is available
    if websocket_manager:
        try:
            response = await LLMService.call_llm_streaming(
                prompt=prompt,
                plan_id=plan_id,
                websocket_manager=websocket_manager,
                agent_name="Invoice"
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            response = (
                f"I apologize, but I encountered an error while processing your request: {str(e)}\n\n"
                f"Please try again or enable mock mode (USE_MOCK_LLM=true) for testing."
            )
    else:
        # Fallback to mock if no websocket manager
        logger.warning("No websocket_manager available, falling back to mock mode")
        response = LLMService.get_mock_response("Invoice", task)
    
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


def hitl_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Human-in-the-Loop (HITL) agent node - requests human approval or revision.
    Phase 7: Takes specialized agent result and formats clarification request.
    
    **Feature: multi-agent-hitl-loop, Property 1: HITL Routing**
    **Validates: Requirements 1.1, 1.2**
    """
    plan_id = state["plan_id"]
    final_result = state.get("final_result", "")
    current_agent = state.get("current_agent", "Unknown")
    
    logger.info(f"HITL Agent processing result from {current_agent} for plan {plan_id}")
    
    # Format clarification request message
    clarification_message = (
        f"I've reviewed the {current_agent} Agent's work:\n\n"
        f"{final_result}\n\n"
        f"Please review this result and let me know if you'd like to approve it or provide revisions."
    )
    
    return {
        "messages": [clarification_message],
        "current_agent": "HITL",
        "clarification_required": True,
        "clarification_message": clarification_message
    }
