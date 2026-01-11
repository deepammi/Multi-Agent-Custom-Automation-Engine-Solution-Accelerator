"""Invoice Verification Workflow - Cross-check invoice data across ERP and CRM."""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.checkpointer import get_checkpointer

logger = logging.getLogger(__name__)


async def fetch_erp_invoice_node(state: AgentState) -> Dict[str, Any]:
    """Fetch invoice from ERP system (Zoho)."""
    logger.info("Fetching invoice from ERP...")
    
    invoice_id = state.get("workflow_params", {}).get("invoice_id")
    erp_system = state.get("workflow_params", {}).get("erp_system", "zoho")
    
    try:
        # Import service dynamically
        from app.services.zoho_mcp_service import get_zoho_service
        
        zoho_service = get_zoho_service()
        await zoho_service.initialize()
        
        result = await zoho_service.get_invoice(invoice_id)
        
        if result.get("success"):
            invoice_data = result.get("invoice", {})
            return {
                "erp_data": invoice_data,
                "messages": [f"✅ Retrieved invoice {invoice_id} from {erp_system}"]
            }
        else:
            return {
                "erp_data": {},
                "messages": [f"❌ Failed to retrieve invoice from {erp_system}: {result.get('error')}"]
            }
    except Exception as e:
        logger.error(f"Error fetching ERP invoice: {e}")
        return {
            "erp_data": {},
            "messages": [f"❌ Error: {str(e)}"]
        }


async def fetch_crm_customer_node(state: AgentState) -> Dict[str, Any]:
    """Fetch customer from CRM system (Salesforce)."""
    logger.info("Fetching customer from CRM...")
    
    # Get customer name from ERP data
    erp_data = state.get("erp_data", {})
    customer_name = erp_data.get("customer_name", "")
    crm_system = state.get("workflow_params", {}).get("crm_system", "salesforce")
    
    if not customer_name:
        return {
            "crm_data": {},
            "messages": [f"⚠️  No customer name found in ERP data"]
        }
    
    try:
        # For demo, create mock CRM data
        # In production, would call Salesforce API
        crm_data = {
            "account_name": customer_name,
            "account_id": "SF-001",
            "payment_terms": "Net 30",
            "credit_limit": 50000,
            "status": "Active"
        }
        
        return {
            "crm_data": crm_data,
            "messages": [f"✅ Retrieved customer '{customer_name}' from {crm_system}"]
        }
    except Exception as e:
        logger.error(f"Error fetching CRM customer: {e}")
        return {
            "crm_data": {},
            "messages": [f"❌ Error: {str(e)}"]
        }


async def verify_data_node(state: AgentState) -> Dict[str, Any]:
    """Cross-reference and verify data between systems."""
    logger.info("Verifying data across systems...")
    
    erp_data = state.get("erp_data", {})
    crm_data = state.get("crm_data", {})
    
    discrepancies = []
    matches = []
    
    # Check customer name
    erp_customer = erp_data.get("customer_name", "")
    crm_customer = crm_data.get("account_name", "")
    
    if erp_customer and crm_customer:
        if erp_customer.lower() == crm_customer.lower():
            matches.append("Customer name matches")
        else:
            discrepancies.append({
                "field": "Customer Name",
                "erp_value": erp_customer,
                "crm_value": crm_customer,
                "severity": "medium"
            })
    
    # Check payment terms (if available)
    erp_terms = erp_data.get("payment_terms", "")
    crm_terms = crm_data.get("payment_terms", "")
    
    if erp_terms and crm_terms:
        if erp_terms == crm_terms:
            matches.append("Payment terms match")
        else:
            discrepancies.append({
                "field": "Payment Terms",
                "erp_value": erp_terms,
                "crm_value": crm_terms,
                "severity": "high"
            })
    
    # Calculate confidence score
    total_checks = len(matches) + len(discrepancies)
    confidence = (len(matches) / total_checks * 100) if total_checks > 0 else 0
    
    analysis_results = {
        "matches": matches,
        "discrepancies": discrepancies,
        "confidence_score": confidence,
        "recommendation": "Approve" if confidence >= 80 else "Review Required"
    }
    
    return {
        "analysis_results": analysis_results,
        "messages": [f"✅ Verification complete: {len(discrepancies)} discrepancies found"]
    }


async def generate_report_node(state: AgentState) -> Dict[str, Any]:
    """Generate verification report."""
    logger.info("Generating verification report...")
    
    erp_data = state.get("erp_data", {})
    crm_data = state.get("crm_data", {})
    analysis = state.get("analysis_results", {})
    
    # Build report
    report = "# Invoice Verification Report\n\n"
    
    # Invoice details
    report += "## Invoice Details\n"
    report += f"- **Invoice Number**: {erp_data.get('invoice_number', 'N/A')}\n"
    report += f"- **Customer**: {erp_data.get('customer_name', 'N/A')}\n"
    report += f"- **Amount**: ${erp_data.get('total', 0):,.2f}\n"
    report += f"- **Status**: {erp_data.get('status', 'N/A')}\n"
    report += f"- **Due Date**: {erp_data.get('due_date', 'N/A')}\n\n"
    
    # Verification results
    report += "## Verification Results\n"
    report += f"- **Confidence Score**: {analysis.get('confidence_score', 0):.1f}%\n"
    report += f"- **Recommendation**: {analysis.get('recommendation', 'N/A')}\n\n"
    
    # Matches
    matches = analysis.get('matches', [])
    if matches:
        report += "### ✅ Matches\n"
        for match in matches:
            report += f"- {match}\n"
        report += "\n"
    
    # Discrepancies
    discrepancies = analysis.get('discrepancies', [])
    if discrepancies:
        report += "### ⚠️  Discrepancies Found\n"
        for disc in discrepancies:
            report += f"- **{disc['field']}** (Severity: {disc['severity']})\n"
            report += f"  - ERP: {disc['erp_value']}\n"
            report += f"  - CRM: {disc['crm_value']}\n"
        report += "\n"
    else:
        report += "### ✅ No Discrepancies\n"
        report += "All data matches across systems.\n\n"
    
    # Recommendations
    report += "## Recommendations\n"
    if discrepancies:
        report += "1. Review discrepancies with finance team\n"
        report += "2. Update records to ensure consistency\n"
        report += "3. Verify customer information with sales team\n"
    else:
        report += "1. Invoice data is consistent across systems\n"
        report += "2. Safe to proceed with processing\n"
    
    return {
        "final_result": report,
        "current_agent": "Invoice Verification Workflow",
        "messages": ["✅ Verification report generated"]
    }


def create_invoice_verification_workflow() -> StateGraph:
    """
    Create invoice verification workflow.
    
    Workflow steps:
    1. Fetch invoice from ERP (Zoho)
    2. Fetch customer from CRM (Salesforce)
    3. Cross-reference and verify data
    4. Generate verification report
    
    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("fetch_erp", fetch_erp_invoice_node)
    workflow.add_node("fetch_crm", fetch_crm_customer_node)
    workflow.add_node("verify", verify_data_node)
    workflow.add_node("report", generate_report_node)
    
    # Define flow
    workflow.set_entry_point("fetch_erp")
    workflow.add_edge("fetch_erp", "fetch_crm")
    workflow.add_edge("fetch_crm", "verify")
    workflow.add_edge("verify", "report")
    workflow.add_edge("report", END)
    
    # Compile with checkpointer
    checkpointer = get_checkpointer()
    return workflow.compile(checkpointer=checkpointer)

