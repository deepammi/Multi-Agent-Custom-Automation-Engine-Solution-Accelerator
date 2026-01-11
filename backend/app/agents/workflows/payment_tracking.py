"""Payment Tracking Workflow - Track payment status across ERP and Email systems."""
import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.checkpointer import get_checkpointer

logger = logging.getLogger(__name__)


async def check_invoice_status_node(state: AgentState) -> Dict[str, Any]:
    """Check invoice status in ERP system."""
    logger.info("Checking invoice status in ERP...")
    
    invoice_id = state.get("workflow_params", {}).get("invoice_id")
    erp_system = state.get("workflow_params", {}).get("erp_system", "zoho")
    
    try:
        from app.services.zoho_mcp_service import get_zoho_service
        
        zoho_service = get_zoho_service()
        await zoho_service.initialize()
        
        result = await zoho_service.get_invoice(invoice_id)
        
        if result.get("success"):
            invoice_data = result.get("invoice", {})
            status = invoice_data.get("status", "unknown")
            balance = invoice_data.get("balance", 0)
            
            return {
                "erp_data": invoice_data,
                "messages": [f"✅ Invoice {invoice_id} status: {status}, Balance: ${balance:,.2f}"]
            }
        else:
            return {
                "erp_data": {},
                "messages": [f"❌ Failed to retrieve invoice: {result.get('error')}"]
            }
    except Exception as e:
        logger.error(f"Error checking invoice status: {e}")
        return {
            "erp_data": {},
            "messages": [f"❌ Error: {str(e)}"]
        }


async def search_payment_emails_node(state: AgentState) -> Dict[str, Any]:
    """Search for payment confirmation emails."""
    logger.info("Searching for payment emails...")
    
    erp_data = state.get("erp_data", {})
    invoice_number = erp_data.get("invoice_number", "")
    customer_name = erp_data.get("customer_name", "")
    
    # Mock email search (in production, would search email system)
    # Simulate finding or not finding payment email
    import random
    payment_found = random.choice([True, False])
    
    if payment_found:
        email_data = {
            "found": True,
            "subject": f"Payment Confirmation - {invoice_number}",
            "from": f"{customer_name} <payments@{customer_name.lower().replace(' ', '')}.com>",
            "date": "2025-12-05",
            "amount": erp_data.get("total", 0),
            "confirmation_number": "PAY-2025-001234"
        }
        
        return {
            "email_data": email_data,
            "messages": [f"✅ Found payment confirmation email for {invoice_number}"]
        }
    else:
        email_data = {
            "found": False
        }
        
        return {
            "email_data": email_data,
            "messages": [f"⚠️  No payment confirmation email found for {invoice_number}"]
        }


def payment_status_router(state: AgentState) -> Literal["match_payment", "send_reminder"]:
    """Route based on whether payment email was found."""
    email_data = state.get("email_data", {})
    
    if email_data.get("found"):
        return "match_payment"
    else:
        return "send_reminder"


async def match_payment_node(state: AgentState) -> Dict[str, Any]:
    """Match payment email to invoice and update status."""
    logger.info("Matching payment to invoice...")
    
    erp_data = state.get("erp_data", {})
    email_data = state.get("email_data", {})
    
    invoice_amount = erp_data.get("total", 0)
    payment_amount = email_data.get("amount", 0)
    
    if abs(invoice_amount - payment_amount) < 0.01:  # Match within 1 cent
        match_status = "exact_match"
        message = f"✅ Payment amount matches invoice: ${payment_amount:,.2f}"
    else:
        match_status = "amount_mismatch"
        message = f"⚠️  Payment amount mismatch: Invoice ${invoice_amount:,.2f}, Payment ${payment_amount:,.2f}"
    
    analysis_results = {
        "payment_matched": True,
        "match_status": match_status,
        "payment_date": email_data.get("date"),
        "confirmation_number": email_data.get("confirmation_number"),
        "action": "update_erp" if match_status == "exact_match" else "review_required"
    }
    
    return {
        "analysis_results": analysis_results,
        "messages": [message]
    }


async def send_reminder_node(state: AgentState) -> Dict[str, Any]:
    """Send payment reminder."""
    logger.info("Sending payment reminder...")
    
    erp_data = state.get("erp_data", {})
    customer_name = erp_data.get("customer_name", "")
    invoice_number = erp_data.get("invoice_number", "")
    amount = erp_data.get("balance", 0)
    due_date = erp_data.get("due_date", "")
    
    # Mock sending reminder
    reminder_data = {
        "sent": True,
        "to": f"{customer_name}",
        "subject": f"Payment Reminder - Invoice {invoice_number}",
        "amount": amount,
        "due_date": due_date
    }
    
    analysis_results = {
        "payment_matched": False,
        "reminder_sent": True,
        "action": "follow_up_required"
    }
    
    return {
        "analysis_results": analysis_results,
        "messages": [f"📧 Payment reminder sent to {customer_name} for ${amount:,.2f}"]
    }


async def generate_tracking_report_node(state: AgentState) -> Dict[str, Any]:
    """Generate payment tracking report."""
    logger.info("Generating payment tracking report...")
    
    erp_data = state.get("erp_data", {})
    email_data = state.get("email_data", {})
    analysis = state.get("analysis_results", {})
    
    # Build report
    report = "# Payment Tracking Report\n\n"
    
    # Invoice details
    report += "## Invoice Details\n"
    report += f"- **Invoice Number**: {erp_data.get('invoice_number', 'N/A')}\n"
    report += f"- **Customer**: {erp_data.get('customer_name', 'N/A')}\n"
    report += f"- **Total Amount**: ${erp_data.get('total', 0):,.2f}\n"
    report += f"- **Balance Due**: ${erp_data.get('balance', 0):,.2f}\n"
    report += f"- **Status**: {erp_data.get('status', 'N/A')}\n"
    report += f"- **Due Date**: {erp_data.get('due_date', 'N/A')}\n\n"
    
    # Payment status
    report += "## Payment Status\n"
    
    if analysis.get("payment_matched"):
        report += "### ✅ Payment Received\n"
        report += f"- **Payment Date**: {analysis.get('payment_date', 'N/A')}\n"
        report += f"- **Confirmation**: {analysis.get('confirmation_number', 'N/A')}\n"
        report += f"- **Match Status**: {analysis.get('match_status', 'N/A')}\n\n"
        
        if analysis.get("match_status") == "exact_match":
            report += "**Action**: Update ERP system to mark invoice as paid\n"
        else:
            report += "**Action**: Review payment amount discrepancy\n"
    else:
        report += "### ⚠️  Payment Not Found\n"
        report += "- No payment confirmation email found\n"
        if analysis.get("reminder_sent"):
            report += "- Payment reminder has been sent to customer\n"
        report += "\n**Action**: Follow up with customer on payment status\n"
    
    # Next steps
    report += "\n## Next Steps\n"
    if analysis.get("payment_matched"):
        report += "1. Verify payment in bank account\n"
        report += "2. Update invoice status in ERP\n"
        report += "3. Send payment confirmation to customer\n"
    else:
        report += "1. Wait for customer response to reminder\n"
        report += "2. Check payment status in 3 business days\n"
        report += "3. Escalate to collections if no response\n"
    
    return {
        "final_result": report,
        "current_agent": "Payment Tracking Workflow",
        "messages": ["✅ Payment tracking report generated"]
    }


def create_payment_tracking_workflow() -> StateGraph:
    """
    Create payment tracking workflow.
    
    Workflow steps:
    1. Check invoice status in ERP
    2. Search for payment confirmation emails
    3. If found: Match payment to invoice
    4. If not found: Send payment reminder
    5. Generate tracking report
    
    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("check_status", check_invoice_status_node)
    workflow.add_node("search_emails", search_payment_emails_node)
    workflow.add_node("match_payment", match_payment_node)
    workflow.add_node("send_reminder", send_reminder_node)
    workflow.add_node("report", generate_tracking_report_node)
    
    # Define flow
    workflow.set_entry_point("check_status")
    workflow.add_edge("check_status", "search_emails")
    
    # Conditional routing based on email search results
    workflow.add_conditional_edges(
        "search_emails",
        payment_status_router,
        {
            "match_payment": "match_payment",
            "send_reminder": "send_reminder"
        }
    )
    
    # Both paths lead to report
    workflow.add_edge("match_payment", "report")
    workflow.add_edge("send_reminder", "report")
    workflow.add_edge("report", END)
    
    # Compile with checkpointer
    checkpointer = get_checkpointer()
    return workflow.compile(checkpointer=checkpointer)

