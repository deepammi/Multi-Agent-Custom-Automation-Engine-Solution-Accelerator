"""Agent node implementations."""
import logging
import os
from typing import Dict, Any

from app.agents.state import AgentState
from app.services.llm_service import LLMService
from app.agents.prompts import build_invoice_prompt

logger = logging.getLogger(__name__)


def detect_invoice_text(text: str) -> bool:
    """
    Detect if text contains invoice data suitable for structured extraction.
    
    Args:
        text: Text to analyze
        
    Returns:
        bool: True if text appears to be an invoice document
    """
    text_lower = text.lower()
    
    # Check for invoice indicators
    invoice_keywords = [
        "invoice",
        "bill to",
        "invoice number",
        "invoice #",
        "due date",
        "payment terms",
        "subtotal",
        "total amount",
        "line item"
    ]
    
    # Check for structured data indicators
    structure_indicators = [
        "qty",
        "quantity",
        "unit price",
        "description",
        "amount due"
    ]
    
    # Count matches
    keyword_matches = sum(1 for keyword in invoice_keywords if keyword in text_lower)
    structure_matches = sum(1 for indicator in structure_indicators if indicator in text_lower)
    
    # Check for currency symbols
    has_currency = any(symbol in text for symbol in ['$', '€', '£', '¥', 'USD', 'EUR', 'GBP'])
    
    # Check for date patterns (YYYY-MM-DD, MM/DD/YYYY, Month DD, YYYY, etc.)
    import re
    date_patterns = [
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # 2025-03-20 or 2025/03/20
        r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',  # 03/20/2025 or 03-20-2025
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',  # March 20, 2025
        r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',  # 20 Mar 2025
    ]
    has_dates = any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns)
    
    # Decision logic - RELAXED for better detection
    is_invoice = (
        keyword_matches >= 2 and  # At least 2 invoice keywords
        (structure_matches >= 1 or has_currency)  # Some structure or currency
        # Removed has_dates requirement - dates are nice to have but not required
    )
    
    logger.info(
        f"Invoice detection: {is_invoice} "
        f"(keywords={keyword_matches}, structure={structure_matches}, "
        f"currency={has_currency}, dates={has_dates})"
    )
    
    return is_invoice

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
    
    # Create brief task summary (first 100 chars or first line)
    task_summary = task.split('\n')[0][:100]
    if len(task) > 100:
        task_summary += "..."
    
    if any(word in task_lower for word in ["invoice", "payment", "bill", "vendor"]):
        next_agent = "invoice"
        response = "I've analyzed your task: This appears to be an invoice processing task. Routing to Invoice Agent."
    elif any(word in task_lower for word in ["closing", "reconciliation", "journal", "variance", "gl"]):
        next_agent = "closing"
        response = "I've analyzed your task: This appears to be a closing process task. Routing to Closing Agent."
    elif any(word in task_lower for word in ["audit", "compliance", "evidence", "exception", "monitoring"]):
        next_agent = "audit"
        response = "I've analyzed your task: This appears to be an audit-related task. Routing to Audit Agent."
    else:
        # Default to invoice agent
        next_agent = "invoice"
        response = "I've analyzed your task. Routing to Invoice Agent for processing."
    
    return {
        "messages": [response],
        "current_agent": "Planner",
        "next_agent": next_agent
    }


async def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Invoice agent node - handles invoice management with structured extraction.
    Supports both structured extraction and text analysis.
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    websocket_manager = state.get("websocket_manager")
    
    logger.info(f"Invoice Agent processing task for plan {plan_id}")
    
    # Check if structured extraction is enabled
    enable_extraction = os.getenv("ENABLE_STRUCTURED_EXTRACTION", "false").lower() == "true"
    
    # Detect if task contains invoice text for extraction
    needs_extraction = enable_extraction and detect_invoice_text(task)
    
    if needs_extraction:
        logger.info(f"📊 Invoice text detected - attempting structured extraction")
        
        try:
            # Import here to avoid errors if not installed
            from app.services.langextract_service import LangExtractService
            from datetime import datetime
            import asyncio
            
            # Send initial processing message via WebSocket
            if websocket_manager:
                logger.info(f"📊 [Invoice Agent] Sending processing message for plan {plan_id}")
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "Invoice",
                        "content": "📊 Processing invoice extraction...",
                        "status": "in_progress",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
                # Small delay to ensure message is sent before extraction starts
                await asyncio.sleep(0.1)
            
            # Extract structured data
            logger.info(f"📊 [Invoice Agent] Starting extraction for plan {plan_id}")
            extraction_start = datetime.utcnow()
            
            extraction_result = await LangExtractService.extract_invoice_data(
                invoice_text=task,
                plan_id=plan_id
            )
            
            extraction_elapsed = (datetime.utcnow() - extraction_start).total_seconds()
            logger.info(f"📊 [Invoice Agent] Extraction completed in {extraction_elapsed:.2f}s for plan {plan_id}")
            
            # Format extraction result for display
            structured_response = LangExtractService.format_extraction_result(extraction_result)
            
            # Send completion message via WebSocket
            if websocket_manager:
                logger.info(f"📊 [Invoice Agent] Sending completion message for plan {plan_id}")
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "Invoice",
                        "content": "✅ Invoice extraction complete. Awaiting approval...",
                        "status": "in_progress",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
                # Small delay to ensure message is sent before returning
                await asyncio.sleep(0.1)
            
            # Store extraction result in state for HITL approval
            # DO NOT store to database yet - wait for human approval
            return {
                "messages": [structured_response],
                "current_agent": "Invoice",
                "final_result": structured_response,
                "extraction_result": extraction_result,
                "requires_extraction_approval": True
            }
            
        except Exception as e:
            logger.error(f"Extraction failed, falling back to text analysis: {e}")
            # Send error message via WebSocket if available
            if websocket_manager:
                try:
                    from datetime import datetime
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": "Invoice",
                            "content": f"⚠️ Extraction failed: {str(e)}. Falling back to text analysis...",
                            "status": "warning",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
                except Exception as ws_error:
                    logger.error(f"Failed to send error message via WebSocket: {ws_error}")
            # Fall through to regular text analysis
    
    # Regular text analysis (existing behavior)
    logger.info(f"Using text analysis mode for Invoice Agent")
    
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
