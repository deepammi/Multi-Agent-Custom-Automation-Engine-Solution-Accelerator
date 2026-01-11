"""Agent node implementations."""
import logging
import os
from typing import Dict, Any
from datetime import datetime, timezone

from app.agents.state import AgentState
from app.services.llm_service import LLMService
from app.agents.prompts import build_invoice_prompt

logger = logging.getLogger(__name__)


def detect_invoice_text(text: str) -> bool:

    """ function to check if a body of text looks like an Invoice document. Returns T/F"""

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

# is this planner_node() being used at all ??
async def planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Simplified planner agent node - works with linear execution.
    
    Note: This is a legacy planner. The AI Planner Service now handles
    intelligent sequence generation. This planner provides basic fallback
    functionality for simple workflows.

    This checks first if it is a po investigation or a simple one. If former, it creates a cookie cutter
    plan in form of a prompt text i.e. Gmail->Invoice->Salesforce.
    If not PO investigation, it goes with the AI generated sequence
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
    logger.info(f"Planner processing task for plan {plan_id}")
    
    # Simple task analysis for fallback scenarios
    task_lower = task.lower()
    
    # Detect PO investigation pattern
    import re
    po_patterns = [
        r'po.*(?:missing|stuck|delayed|not processed)',
        r'purchase order.*(?:missing|stuck|delayed|not processed)', 
        r'why.*po.*(?:missing|stuck|delayed)',
        r'invoice.*(?:inv-\d+).*(?:missing|stuck|delayed|not processed)',
        r'(?:missing|stuck|delayed).*po.*invoice',
    ]
    
    is_po_investigation = any(re.search(pattern, task_lower) for pattern in po_patterns)
    invoice_numbers = re.findall(r'inv-?\d+', task_lower, re.IGNORECASE)
    
    if is_po_investigation and invoice_numbers:
        # Complex PO investigation workflow
        invoice_num = invoice_numbers[0].upper()
        
        response = f"""🔍 **PO Investigation Plan for {invoice_num}**

        I've analyzed your request and created an investigation plan:

        **Planned Steps:**
        1. Gmail Agent - Search email communications
        2. Invoice Agent - Retrieve Bill.com data  
        3. Salesforce Agent - Analyze vendor relationships

        This will provide a complete analysis of your PO status.

        Proceeding with execution..."""

        # Store invoice number for subsequent agents
        collected_data = state.get("collected_data", {})
        collected_data["invoice_number"] = invoice_num
        
        # Save planner response to database
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="Planner",
            content=response,
            agent_type="planner",
            metadata={"po_investigation": True, "invoice_number": invoice_num}
        )
        
        return {
            "messages": [response],
            "current_agent": "Planner",
            "planner_result": response,
            "collected_data": collected_data,
            "execution_results": state.get("execution_results", [])
        }
    
    else:
        # Simple workflow analysis
        response = f"""📋 **Task Analysis Complete**

        I've analyzed your request: "{task}"

        The system will now execute the appropriate agents based on the AI-generated sequence.

        Proceeding with workflow execution..."""
        
        # Save planner response to database
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="Planner",
            content=response,
            agent_type="planner",
            metadata={"simple_workflow": True}
        )
                
        return {
            "messages": [response],
            "current_agent": "Planner",
            "planner_result": response,
            "collected_data": state.get("collected_data", {}),
            "execution_results": state.get("execution_results", [])
        }


async def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Invoice agent node - handles invoice management with structured extraction and Bill.com integration.
    Supports structured extraction, text analysis, and real Bill.com data access.
    Algo: first checks if Bill.com integration required. If so, tries to do an invoice search or invoices list
    based on Inv number or Vendor name. Second, if extraction is required, uses LangGraph extraction to pull 
    data based on LLM Prompt. 
    Suggest study code for: LangExtractService.extract_invoice_data() and LangExtractService.format_extraction_result()
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    # Get websocket manager from global instance
    from app.services.websocket_service import get_websocket_manager
    websocket_manager = get_websocket_manager()
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
    logger.info(f"Invoice Agent processing task for plan {plan_id}")
    
    # Check if structured extraction is enabled
    enable_extraction = os.getenv("ENABLE_STRUCTURED_EXTRACTION", "false").lower() == "true"
    
    # Check if Bill.com integration is requested
    # ?? should this also include keywords like Bill, PO, Purchase Order ?
    needs_bill_com = any(keyword in task.lower() for keyword in [
        "bill.com", "billcom", "real invoice", "actual invoice", "live data",
        "invoice data", "vendor invoice", "ap invoice"
    ])
    
    # Detect if task contains invoice text for extraction
    needs_extraction = enable_extraction and detect_invoice_text(task)
    
    # Handle Bill.com integration first if requested
    if needs_bill_com:
        logger.info(f"📊 Bill.com integration requested for plan {plan_id}")
        
        try:
            from app.services.mcp_client_service import get_bill_com_service
            from datetime import datetime
            import asyncio
            
            # Send initial processing message
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "Invoice",
                        "content": "🔗 Connecting to Bill.com...",
                        "status": "in_progress",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
                await asyncio.sleep(0.1)
            
            # Save initial processing message to database
            await message_persistence.save_agent_message(
                plan_id=plan_id,
                agent_name="Invoice",
                content="🔗 Connecting to Bill.com...",
                agent_type="agent",
                metadata={"status": "in_progress"}
            )
            
            bill_com_service = await get_bill_com_service()
            
            # Check Bill.com health first
            health_result = await bill_com_service.check_bill_com_health()
            
            if not health_result.get("success"):
                logger.warning(f"Bill.com health check failed: {health_result.get('error')}")
                response = (
                    "📋 **Invoice Agent** - Bill.com Integration\n\n"
                    "⚠️ **Bill.com Service Unavailable**\n\n"
                    "I attempted to connect to Bill.com but the service is currently unavailable.\n\n"
                    "**Possible Issues:**\n"
                    "• MCP server not running (start with: `cd src/mcp_server && python mcp_server.py`)\n"
                    "• Bill.com credentials not configured\n"
                    "• Network connectivity issues\n\n"
                    "**Fallback:** I can still help with invoice text extraction and analysis if you provide invoice content."
                )
                
                # Update state with simplified structure for early return
                from app.agents.state import AgentStateManager
                
                agent_result = {
                    "status": "error",
                    "data": {"error_response": response},
                    "message": response
                }
                
                AgentStateManager.add_agent_result(state, "Invoice", agent_result)
                
                # Save error message to database
                await message_persistence.save_error_message(
                    plan_id=plan_id,
                    error_message="Bill.com service unavailable",
                    agent_name="Invoice",
                    metadata={"bill_com_health_check": False}
                )
                
                # Save full error response to database
                await message_persistence.save_agent_message(
                    plan_id=plan_id,
                    agent_name="Invoice",
                    content=response,
                    agent_type="error",
                    metadata={"bill_com_integration": True, "status": "error"}
                )
                
                return {
                    "messages": [response],
                    "current_agent": "Invoice",
                    "final_result": response,
                    "collected_data": state["collected_data"],
                    "execution_results": state["execution_results"]
                }
            
            # Analyze task to determine what Bill.com operation to perform
            task_lower = task.lower()
            response = "📋 **Invoice Agent** - Bill.com Integration\n\n"
            
            if "search" in task_lower or "find" in task_lower:
                # Search for specific invoices
                search_terms = []
                
                # Extract potential invoice numbers or vendor names
                import re
                invoice_numbers = re.findall(r'INV-?\d+|BILL-?\d+|\d{4,}', task, re.IGNORECASE)
                
                if invoice_numbers:
                    # Search by invoice number
                    search_result = await bill_com_service.search_invoices(
                        search_term=invoice_numbers[0],
                        search_type="invoice_number"
                    )
                    
                    if search_result.get("success"):
                        invoices = search_result.get("invoices", [])
                        response += f"🔍 **Search Results for '{invoice_numbers[0]}'**\n\n"
                        
                        if invoices:
                            for i, invoice in enumerate(invoices, 1):
                                response += f"{i}. **{invoice.get('invoiceNumber', 'N/A')}**\n"
                                response += f"   - Vendor: {invoice.get('vendorName', 'N/A')}\n"
                                response += f"   - Amount: ${invoice.get('amount', 0):,.2f}\n"
                                response += f"   - Status: {invoice.get('approvalStatus', 'N/A')}\n"
                                response += f"   - Due Date: {invoice.get('dueDate', 'N/A')}\n\n"
                        else:
                            response += "No invoices found matching your search criteria.\n"
                    else:
                        response += f"❌ Search failed: {search_result.get('error', 'Unknown error')}\n"
                else:
                    response += "Please specify an invoice number or vendor name to search for.\n"
            
            elif "list" in task_lower or "show" in task_lower or "get" in task_lower:
                # List recent invoices
                status_filter = None
                if "unpaid" in task_lower or "outstanding" in task_lower:
                    status_filter = "NeedsApproval"
                elif "paid" in task_lower:
                    status_filter = "Paid"
                elif "overdue" in task_lower:
                    status_filter = "Overdue"
                
                invoices_result = await bill_com_service.get_invoices(
                    status=status_filter,
                    limit=10
                )
                
                if invoices_result.get("success"):
                    invoices = invoices_result.get("invoices", [])
                    
                    status_text = f" ({status_filter})" if status_filter else ""
                    response += f"📄 **Recent Invoices{status_text}** ({len(invoices)} found)\n\n"
                    
                    total_amount = 0
                    for i, invoice in enumerate(invoices, 1):
                        status = invoice.get('approvalStatus', 'N/A')
                        status_emoji = {
                            'Paid': '✅',
                            'NeedsApproval': '⏳',
                            'Approved': '👍',
                            'Overdue': '⚠️',
                            'Rejected': '❌'
                        }.get(status, '📄')
                        
                        response += f"{i}. {status_emoji} **{invoice.get('invoiceNumber', 'N/A')}**\n"
                        response += f"   - Vendor: {invoice.get('vendorName', 'N/A')}\n"
                        response += f"   - Amount: ${invoice.get('amount', 0):,.2f}\n"
                        response += f"   - Status: {status}\n"
                        response += f"   - Due Date: {invoice.get('dueDate', 'N/A')}\n\n"
                        
                        total_amount += invoice.get('amount', 0)
                    
                    if invoices:
                        response += f"**Total Amount:** ${total_amount:,.2f}\n"
                    else:
                        response += "No invoices found.\n"
                else:
                    response += f"❌ Failed to retrieve invoices: {invoices_result.get('error', 'Unknown error')}\n"
            
            elif "vendor" in task_lower:
                # Get vendor information
                vendors_result = await bill_com_service.get_vendors(limit=15)
                
                if vendors_result.get("success"):
                    vendors = vendors_result.get("vendors", [])
                    response += f"🏢 **Vendors** ({len(vendors)} found)\n\n"
                    
                    for i, vendor in enumerate(vendors, 1):
                        response += f"{i}. **{vendor.get('name', 'N/A')}**\n"
                        response += f"   - Email: {vendor.get('email', 'N/A')}\n"
                        response += f"   - Phone: {vendor.get('phone', 'N/A')}\n"
                        
                        balance = vendor.get('balance', 0)
                        if balance != 0:
                            response += f"   - Balance: ${balance:,.2f}\n"
                        
                        response += f"   - Vendor ID: {vendor.get('id', 'N/A')}\n\n"
                    
                    if not vendors:
                        response += "No vendors found.\n"
                else:
                    response += f"❌ Failed to retrieve vendors: {vendors_result.get('error', 'Unknown error')}\n"
            
            else:
                # General Bill.com help
                response += "**Available Bill.com Operations:**\n\n"
                response += "🔍 **Search:** 'Find invoice INV-12345' or 'Search for vendor ABC Corp'\n"
                response += "📄 **List Invoices:** 'Show recent invoices' or 'List unpaid invoices'\n"
                response += "🏢 **Vendors:** 'Get vendor list' or 'Show vendors'\n"
                response += "📊 **Details:** 'Get details for invoice INV-12345'\n\n"
                response += "I can also help with invoice text extraction if you provide invoice content."
            
            # Send completion message
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "Invoice",
                        "content": "✅ Bill.com query complete",
                        "status": "completed",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
            
            # Save completion message to database
            await message_persistence.save_agent_message(
                plan_id=plan_id,
                agent_name="Invoice",
                content="✅ Bill.com query complete",
                agent_type="agent",
                metadata={"status": "completed"}
            )
            
            # Save main response to database
            await message_persistence.save_agent_message(
                plan_id=plan_id,
                agent_name="Invoice",
                content=response,
                agent_type="agent",
                metadata={"bill_com_integration": True, "status": "completed"}
            )
            
            # Update state with simplified structure
            from app.agents.state import AgentStateManager
            
            agent_result = {
                "status": "completed",
                "data": {"bill_com_response": response},
                "message": response
            }
            
            AgentStateManager.add_agent_result(state, "Invoice", agent_result)
            
            return {
                "messages": [response],
                "current_agent": "Invoice",
                "invoice_result": response,
                "collected_data": state.get("collected_data", {}),
                "execution_results": state.get("execution_results", [])
            }
            
        except Exception as e:
            logger.error(f"Bill.com integration error: {e}", exc_info=True)
            error_response = (
                "📋 **Invoice Agent** - Bill.com Integration Error\n\n"
                f"❌ Error connecting to Bill.com: {str(e)}\n\n"
                "**Troubleshooting:**\n"
                "• Ensure MCP server is running\n"
                "• Check Bill.com credentials configuration\n"
                "• Verify network connectivity\n\n"
                "**Fallback:** I can still help with invoice text extraction if you provide invoice content."
            )
            
            # Update state with simplified structure for error case
            from app.agents.state import AgentStateManager
            
            agent_result = {
                "status": "error",
                "data": {"error_response": error_response},
                "message": error_response
            }
            
            AgentStateManager.add_agent_result(state, "Invoice", agent_result)
            
            # Save error message to database
            await message_persistence.save_error_message(
                plan_id=plan_id,
                error_message=f"Bill.com integration error: {str(e)}",
                agent_name="Invoice",
                metadata={"bill_com_integration": True, "exception": str(e)}
            )
            
            # Save full error response to database
            await message_persistence.save_agent_message(
                plan_id=plan_id,
                agent_name="Invoice",
                content=error_response,
                agent_type="error",
                metadata={"bill_com_integration": True, "status": "error"}
            )
            
            return {
                "messages": [error_response],
                "current_agent": "Invoice",
                "invoice_result": error_response,
                "collected_data": state.get("collected_data", {}),
                "execution_results": state.get("execution_results", [])
            }
    
    elif needs_extraction:
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
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
                # Small delay to ensure message is sent before extraction starts
                await asyncio.sleep(0.1)
            
            # Save initial processing message to database
            await message_persistence.save_agent_message(
                plan_id=plan_id,
                agent_name="Invoice",
                content="📊 Processing invoice extraction...",
                agent_type="agent",
                metadata={"status": "in_progress", "extraction": True}
            )
            
            # Extract structured data
            # check langextract prompt for few shot examples and structured output ??
            logger.info(f"📊 [Invoice Agent] Starting extraction for plan {plan_id}")
            extraction_start = datetime.now(timezone.utc)
            
            extraction_result = await LangExtractService.extract_invoice_data(
                invoice_text=task,
                plan_id=plan_id
            )
            
            extraction_elapsed = (datetime.now(timezone.utc) - extraction_start).total_seconds()
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
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
                # Small delay to ensure message is sent before returning
                await asyncio.sleep(0.1)
            
            # Save completion message to database
            await message_persistence.save_agent_message(
                plan_id=plan_id,
                agent_name="Invoice",
                content="✅ Invoice extraction complete. Awaiting approval...",
                agent_type="agent",
                metadata={"status": "in_progress", "extraction": True}
            )
            
            # Save extraction result to database
            await message_persistence.save_agent_message(
                plan_id=plan_id,
                agent_name="Invoice",
                content=structured_response,
                agent_type="agent",
                metadata={"extraction": True, "status": "completed", "requires_approval": True}
            )
            
            # Update state with simplified structure for extraction case
            from app.agents.state import AgentStateManager
            
            agent_result = {
                "status": "completed",
                "data": {"extraction_response": structured_response, "extraction_result": extraction_result},
                "message": structured_response
            }
            
            AgentStateManager.add_agent_result(state, "Invoice", agent_result)
            
            # Store extraction result in state for HITL approval
            # DO NOT store to database yet - wait for human approval
            return {
                "messages": [structured_response],
                "current_agent": "Invoice",
                "invoice_result": structured_response,
                "extraction_result": extraction_result,
                "requires_extraction_approval": True,
                "collected_data": state.get("collected_data", {}),
                "execution_results": state.get("execution_results", [])
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
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                        }
                    })
                except Exception as ws_error:
                    logger.error(f"Failed to send error message via WebSocket: {ws_error}")
            
            # Save error message to database
            await message_persistence.save_error_message(
                plan_id=plan_id,
                error_message=f"Extraction failed: {str(e)}",
                agent_name="Invoice",
                metadata={"extraction": True, "fallback": "text_analysis"}
            )
            # Fall through to regular text analysis
    
    # Regular text analysis (existing behavior)
    logger.info(f"Using text analysis mode for Invoice Agent")
    
    # Check if mock mode is enabled
    if LLMService.is_mock_mode():
        logger.info("🎭 Using mock mode for Invoice Agent")
        response = LLMService.get_mock_response("Invoice", task)
        
        # Update state with simplified structure for mock case
        from app.agents.state import AgentStateManager
        
        agent_result = {
            "status": "completed",
            "data": {"mock_response": response},
            "message": response
        }
        
        AgentStateManager.add_agent_result(state, "Invoice", agent_result)
        
        # Save mock response to database
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="Invoice",
            content=response,
            agent_type="agent",
            metadata={"status": "completed", "mock_mode": True}
        )
        
        return {
            "messages": [response],
            "current_agent": "Invoice",
            "invoice_result": response,
            "collected_data": state.get("collected_data", {}),
            "execution_results": state.get("execution_results", [])
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
    
    # Update state with simplified structure
    from app.agents.state import AgentStateManager
    
    # Add agent result to state
    agent_result = {
        "status": "completed",
        "data": {"invoice_response": response},
        "message": response
    }
    
    AgentStateManager.add_agent_result(state, "Invoice", agent_result)
    
    # Save final response to database
    await message_persistence.save_agent_message(
        plan_id=plan_id,
        agent_name="Invoice",
        content=response,
        agent_type="agent",
        metadata={"status": "completed", "text_analysis": True}
    )
    
    # Send progress update if websocket available
    if websocket_manager:
        from datetime import datetime
        import asyncio
        progress = AgentStateManager.get_progress_info(state)
        asyncio.create_task(websocket_manager.send_message(state["plan_id"], {
            "type": "step_progress",
            "data": {
                "step": progress["current_step"],
                "total": progress["total_steps"],
                "agent": "Invoice",
                "progress_percentage": progress["progress_percentage"],
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            }
        }))
    
    return {
        "messages": [response],
        "current_agent": "Invoice",
        "invoice_result": response,
        "collected_data": state.get("collected_data", {}),
        "execution_results": state.get("execution_results", [])
    }


async def approval_checkpoint_node(state: AgentState) -> Dict[str, Any]:
    """
    Approval checkpoint node - requests human approval before proceeding.
    Works with simplified linear execution state.
    """
    plan_id = state["plan_id"]
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
    logger.info(f"Approval checkpoint reached for plan {plan_id}")
    
    approval_message = "Approval checkpoint reached - awaiting human approval"
    
    # Save approval checkpoint message to database
    await message_persistence.save_agent_message(
        plan_id=plan_id,
        agent_name="Approval",
        content=approval_message,
        agent_type="system",
        metadata={"approval_required": True}
    )
    
    return {
        "messages": [approval_message],
        "current_agent": "Approval",
        "approval_required": True,
        "approved": None,
        "collected_data": state.get("collected_data", {}),
        "execution_results": state.get("execution_results", [])
    }


async def hitl_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Human-in-the-Loop (HITL) agent node - requests human approval or revision.
    Works with simplified linear execution state.
    
    **Feature: multi-agent-hitl-loop, Property 1: HITL Routing**
    **Validates: Requirements 1.1, 1.2**
    """
    plan_id = state["plan_id"]
    execution_results = state.get("execution_results", [])
    current_agent = state.get("current_agent", "Unknown")
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
    logger.info(f"HITL Agent processing results for plan {plan_id}")
    
    # Gather results from all executed agents
    if execution_results:
        latest_result = execution_results[-1]
        agent_name = latest_result.get("agent", "Unknown")
        result_message = latest_result.get("result", {}).get("message", "No result available")
        
        clarification_message = (
            f"I've reviewed the {agent_name} Agent's work:\n\n"
            f"{result_message}\n\n"
            f"Please review this result and let me know if you'd like to approve it or provide revisions."
        )
    else:
        clarification_message = (
            "I'm ready to review the workflow results. "
            "Please provide your feedback on the execution."
        )
    
    # Save HITL message to database
    await message_persistence.save_agent_message(
        plan_id=plan_id,
        agent_name="HITL",
        content=clarification_message,
        agent_type="agent",
        metadata={"clarification_required": True, "current_agent": current_agent}
    )
    
    return {
        "messages": [clarification_message],
        "current_agent": "HITL",
        "clarification_required": True,
        "clarification_message": clarification_message,
        "collected_data": state.get("collected_data", {}),
        "execution_results": state.get("execution_results", [])
    }
