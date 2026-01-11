"""Customer 360 Workflow - Aggregate customer data from multiple systems."""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.checkpointer import get_checkpointer

logger = logging.getLogger(__name__)


async def fetch_crm_data_node(state: AgentState) -> Dict[str, Any]:
    """Fetch customer data from CRM."""
    logger.info("Fetching customer from CRM...")
    
    customer_name = state.get("workflow_params", {}).get("customer_name")
    
    # Mock CRM data
    crm_data = {
        "account_name": customer_name,
        "account_id": "SF-12345",
        "industry": "Technology",
        "annual_revenue": 5000000,
        "employees": 150,
        "status": "Active",
        "owner": "John Smith",
        "created_date": "2023-01-15"
    }
    
    return {
        "crm_data": crm_data,
        "messages": [f"✅ Retrieved CRM data for {customer_name}"]
    }


async def fetch_erp_data_node(state: AgentState) -> Dict[str, Any]:
    """Fetch invoices and transactions from ERP."""
    logger.info("Fetching ERP data...")
    
    customer_name = state.get("workflow_params", {}).get("customer_name")
    
    try:
        from app.services.zoho_mcp_service import get_zoho_service
        
        zoho_service = get_zoho_service()
        await zoho_service.initialize()
        
        # Get invoices
        result = await zoho_service.list_invoices(limit=10)
        
        if result.get("success"):
            invoices = result.get("invoices", [])
            
            # Filter by customer (simple name match)
            customer_invoices = [
                inv for inv in invoices 
                if customer_name.lower() in inv.get("customer_name", "").lower()
            ]
            
            total_invoiced = sum(inv.get("total", 0) for inv in customer_invoices)
            total_outstanding = sum(inv.get("balance", 0) for inv in customer_invoices)
            
            erp_data = {
                "total_invoices": len(customer_invoices),
                "total_invoiced": total_invoiced,
                "total_outstanding": total_outstanding,
                "invoices": customer_invoices[:5]  # Top 5
            }
            
            return {
                "erp_data": erp_data,
                "messages": [f"✅ Retrieved {len(customer_invoices)} invoices from ERP"]
            }
        else:
            return {
                "erp_data": {},
                "messages": [f"⚠️  No ERP data found"]
            }
    except Exception as e:
        logger.error(f"Error fetching ERP data: {e}")
        return {
            "erp_data": {},
            "messages": [f"❌ Error: {str(e)}"]
        }


async def aggregate_data_node(state: AgentState) -> Dict[str, Any]:
    """Aggregate and analyze data from all systems."""
    logger.info("Aggregating customer data...")
    
    crm_data = state.get("crm_data", {})
    erp_data = state.get("erp_data", {})
    
    # Calculate customer health score
    outstanding = erp_data.get("total_outstanding", 0)
    invoiced = erp_data.get("total_invoiced", 1)  # Avoid division by zero
    
    payment_ratio = ((invoiced - outstanding) / invoiced * 100) if invoiced > 0 else 0
    
    if payment_ratio >= 90:
        health_score = "Excellent"
        health_color = "🟢"
    elif payment_ratio >= 70:
        health_score = "Good"
        health_color = "🟡"
    else:
        health_score = "Needs Attention"
        health_color = "🔴"
    
    analysis_results = {
        "health_score": health_score,
        "health_color": health_color,
        "payment_ratio": payment_ratio,
        "total_value": erp_data.get("total_invoiced", 0),
        "risk_level": "Low" if payment_ratio >= 80 else "Medium" if payment_ratio >= 60 else "High"
    }
    
    return {
        "analysis_results": analysis_results,
        "messages": ["✅ Customer data aggregated and analyzed"]
    }


async def generate_360_report_node(state: AgentState) -> Dict[str, Any]:
    """Generate comprehensive customer 360 report."""
    logger.info("Generating Customer 360 report...")
    
    customer_name = state.get("workflow_params", {}).get("customer_name")
    crm_data = state.get("crm_data", {})
    erp_data = state.get("erp_data", {})
    analysis = state.get("analysis_results", {})
    
    # Build report
    report = f"# Customer 360 View: {customer_name}\n\n"
    
    # Health score
    report += "## Customer Health\n"
    report += f"{analysis.get('health_color', '⚪')} **{analysis.get('health_score', 'Unknown')}**\n"
    report += f"- Payment Ratio: {analysis.get('payment_ratio', 0):.1f}%\n"
    report += f"- Risk Level: {analysis.get('risk_level', 'Unknown')}\n\n"
    
    # CRM data
    report += "## CRM Profile\n"
    report += f"- **Account ID**: {crm_data.get('account_id', 'N/A')}\n"
    report += f"- **Industry**: {crm_data.get('industry', 'N/A')}\n"
    report += f"- **Annual Revenue**: ${crm_data.get('annual_revenue', 0):,.0f}\n"
    report += f"- **Employees**: {crm_data.get('employees', 'N/A')}\n"
    report += f"- **Status**: {crm_data.get('status', 'N/A')}\n"
    report += f"- **Account Owner**: {crm_data.get('owner', 'N/A')}\n\n"
    
    # Financial data
    report += "## Financial Summary\n"
    report += f"- **Total Invoices**: {erp_data.get('total_invoices', 0)}\n"
    report += f"- **Total Invoiced**: ${erp_data.get('total_invoiced', 0):,.2f}\n"
    report += f"- **Outstanding Balance**: ${erp_data.get('total_outstanding', 0):,.2f}\n"
    report += f"- **Paid Amount**: ${erp_data.get('total_invoiced', 0) - erp_data.get('total_outstanding', 0):,.2f}\n\n"
    
    # Recent invoices
    invoices = erp_data.get("invoices", [])
    if invoices:
        report += "## Recent Invoices\n"
        for inv in invoices[:3]:
            status_emoji = "✅" if inv.get("status") == "paid" else "📤"
            report += f"{status_emoji} **{inv.get('invoice_number')}** - "
            report += f"${inv.get('total', 0):,.2f} ({inv.get('status', 'unknown')})\n"
        report += "\n"
    
    # Recommendations
    report += "## Recommendations\n"
    if analysis.get("health_score") == "Excellent":
        report += "- Customer is in excellent standing\n"
        report += "- Consider upsell opportunities\n"
        report += "- Maintain regular communication\n"
    elif analysis.get("health_score") == "Good":
        report += "- Customer is performing well\n"
        report += "- Monitor payment patterns\n"
        report += "- Explore expansion opportunities\n"
    else:
        report += "- Review outstanding invoices\n"
        report += "- Schedule payment discussion\n"
        report += "- Consider credit limit review\n"
    
    return {
        "final_result": report,
        "current_agent": "Customer 360 Workflow",
        "messages": ["✅ Customer 360 report generated"]
    }


def create_customer_360_workflow() -> StateGraph:
    """
    Create Customer 360 workflow.
    
    Workflow steps:
    1. Fetch customer data from CRM
    2. Fetch invoices from ERP
    3. Aggregate and analyze data
    4. Generate comprehensive report
    
    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("fetch_crm", fetch_crm_data_node)
    workflow.add_node("fetch_erp", fetch_erp_data_node)
    workflow.add_node("aggregate", aggregate_data_node)
    workflow.add_node("report", generate_360_report_node)
    
    # Define flow
    workflow.set_entry_point("fetch_crm")
    workflow.add_edge("fetch_crm", "fetch_erp")
    workflow.add_edge("fetch_erp", "aggregate")
    workflow.add_edge("aggregate", "report")
    workflow.add_edge("report", END)
    
    # Compile with checkpointer
    checkpointer = get_checkpointer()
    return workflow.compile(checkpointer=checkpointer)

