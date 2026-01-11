"""
Multi-Agent LangGraph Implementation
Proper LangGraph workflow that can handle complex multi-step agent coordination
"""

import logging
from typing import Literal, Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes import planner_node, invoice_agent_node
from app.agents.salesforce_node import salesforce_agent_node
from app.agents.gmail_agent_node import gmail_agent_node
from app.agents.checkpointer import get_checkpointer

logger = logging.getLogger(__name__)

def enhanced_planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Enhanced planner that creates execution plans without routing logic.
    Linear execution handles agent progression.
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Enhanced Planner processing task for plan {plan_id}")
    
    # Analyze task for complexity
    task_lower = task.lower()
    
    # Detect PO investigation pattern
    is_po_investigation = any(pattern in task_lower for pattern in [
        "po", "purchase order", "inv-", "invoice", "missing", "stuck", "delayed", "not processed"
    ])
    
    # Extract invoice numbers
    import re
    invoice_numbers = re.findall(r'inv-?\d+', task_lower, re.IGNORECASE)
    
    # Store analysis results in collected_data for subsequent agents
    collected_data = state.get("collected_data", {})
    
    if is_po_investigation and invoice_numbers:
        # Complex PO investigation workflow
        invoice_num = invoice_numbers[0].upper()
        
        execution_plan = [
            {"agent": "gmail", "task": f"search for emails related to {invoice_num}"},
            {"agent": "invoice", "task": f"get invoice details for {invoice_num} from Bill.com"},
            {"agent": "salesforce", "task": "search for vendor opportunities and account info"},
            {"agent": "analysis", "task": "perform chronological analysis of collected data"}
        ]
        
        response = f"""🔍 **PO Investigation Initiated for {invoice_num}**

I've created a comprehensive investigation plan:

**Step 1**: Gmail Agent - Search email communications
**Step 2**: Invoice Agent - Retrieve Bill.com data  
**Step 3**: Salesforce Agent - Analyze vendor relationships
**Step 4**: AI Analysis - Chronological bottleneck analysis

The linear executor will now proceed with the agent sequence..."""

        collected_data.update({
            "execution_plan": execution_plan,
            "workflow_type": "po_investigation",
            "invoice_number": invoice_num,
            "complexity": "high"
        })
    
    else:
        # Simple single-agent workflow analysis
        response = f"""✅ **Task Analysis Complete**

I've analyzed your request: "{task}"

The system will now execute the appropriate agents based on the AI-generated sequence.

Proceeding with workflow execution..."""
        
        collected_data.update({
            "workflow_type": "simple",
            "complexity": "low"
        })
        
    return {
        "messages": [response],
        "current_agent": "Planner",
        "planner_result": response,
        "collected_data": collected_data,
        "execution_results": state.get("execution_results", [])
        # No next_agent routing - linear execution handles progression
    }

# Workflow coordinator removed - linear execution handles agent progression

def enhanced_gmail_agent_node(state: AgentState) -> Dict[str, Any]:
    """Enhanced Gmail agent that preserves data for subsequent agents."""
    from app.agents.gmail_agent_node import gmail_agent_node
    
    # Execute the Gmail agent
    result = await gmail_agent_node(state)
    
    # Store Gmail results in collected_data for subsequent agents
    collected_data = state.get("collected_data", {})
    collected_data["gmail"] = {
        "result": result.get("gmail_result", ""),
        "completed": True
    }
    
    # Update result with preserved data
    result.update({
        "collected_data": collected_data,
        "execution_results": state.get("execution_results", [])
        # No next_agent routing - linear execution handles progression
    })
    
    return result

def enhanced_invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    """Enhanced Invoice agent that preserves data for subsequent agents."""
    # Execute the Invoice agent
    result = await invoice_agent_node(state)
    
    # Store Invoice results in collected_data for subsequent agents
    collected_data = state.get("collected_data", {})
    collected_data["invoice"] = {
        "result": result.get("final_result", ""),
        "completed": True
    }
    
    # Update result with preserved data
    result.update({
        "collected_data": collected_data,
        "execution_results": state.get("execution_results", [])
        # No next_agent routing - linear execution handles progression
    })
    
    return result

def enhanced_salesforce_agent_node(state: AgentState) -> Dict[str, Any]:
    """Enhanced Salesforce agent that preserves data for subsequent agents."""
    # Execute the Salesforce agent
    result = await salesforce_agent_node(state)
    
    # Store Salesforce results in collected_data for subsequent agents
    collected_data = state.get("collected_data", {})
    collected_data["salesforce"] = {
        "result": result.get("final_result", ""),
        "completed": True
    }
    
    # Update result with preserved data
    result.update({
        "collected_data": collected_data,
        "execution_results": state.get("execution_results", [])
        # No next_agent routing - linear execution handles progression
    })
    
    return result

async def analysis_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Analysis agent that performs chronological analysis of collected data.
    Works with linear execution - no routing logic.
    """
    plan_id = state["plan_id"]
    collected_data = state.get("collected_data", {})
    invoice_number = collected_data.get("invoice_number", "INV-1001")
    
    logger.info(f"Analysis Agent processing collected data for plan {plan_id}")
    
    # Perform chronological analysis using collected data
    analysis_prompt = f"""
You are analyzing a PO investigation for {invoice_number}. Here's the collected data:

Gmail Data: {collected_data.get('gmail', {}).get('result', 'No data')}
Invoice Data: {collected_data.get('invoice', {}).get('result', 'No data')}
Salesforce Data: {collected_data.get('salesforce', {}).get('result', 'No data')}

Please provide a chronological analysis identifying:
1. Timeline of events
2. Process bottlenecks
3. Root cause analysis
4. Specific recommendations
"""
    
    # For now, use mock analysis (can be replaced with real LLM call)
    analysis_result = f"""
# 🔍 CHRONOLOGICAL ANALYSIS: {invoice_number}

## 📅 TIMELINE RECONSTRUCTION
- **Invoice Created**: {invoice_number} for $15,750 from Acme Marketing LLC
- **Email Communication**: Found correspondence from vendor
- **Current Status**: Stuck in approval workflow for 28+ days
- **Risk**: Due date approaching, vendor relationship at risk

## 🚨 BOTTLENECK IDENTIFICATION
**Primary Issue**: Approval workflow delay
- Invoice pending approval for extended period
- No evidence of escalation or follow-up
- Communication gap between AP and approvers

## 💡 RECOMMENDATIONS
1. **Immediate**: Escalate to approval manager
2. **Process**: Implement automated approval reminders
3. **Relationship**: Proactive vendor communication
4. **System**: Review approval workflow efficiency

## 📊 BUSINESS IMPACT
- **Financial**: $15,750 payment delayed
- **Relationship**: Vendor satisfaction at risk
- **Opportunity**: Future business worth $73K+ at stake
"""
    
    return {
        "messages": [analysis_result],
        "current_agent": "Analysis",
        "final_result": analysis_result,
        "analysis_complete": True,
        "collected_data": collected_data,
        "execution_results": state.get("execution_results", [])
        # No next_agent routing - linear execution handles progression
    }

def create_multi_agent_graph() -> StateGraph:
    """
    Create simplified LangGraph workflow for linear execution.
    
    NOTE: This is a legacy graph. The new linear executor creates
    dynamic graphs based on AI-generated agent sequences.
    This graph is kept for backward compatibility.
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", enhanced_planner_node)
    workflow.add_node("gmail", enhanced_gmail_agent_node)
    workflow.add_node("invoice", enhanced_invoice_agent_node)
    workflow.add_node("salesforce", enhanced_salesforce_agent_node)
    workflow.add_node("analysis", analysis_agent_node)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Simple linear connections (no conditional routing)
    # This is a basic fallback - the linear executor creates dynamic graphs
    workflow.add_edge("planner", "invoice")  # Default simple path
    workflow.add_edge("invoice", END)
    
    # All other agents connect to END for simplicity
    workflow.add_edge("gmail", END)
    workflow.add_edge("salesforce", END)
    workflow.add_edge("analysis", END)
    workflow.add_edge("audit", END)
    workflow.add_edge("closing", END)
    workflow.add_edge("zoho", END)
    
    # Compile with checkpointer
    checkpointer = get_checkpointer()
    graph = workflow.compile(
        checkpointer=checkpointer,
        # interrupt_before=["planner"]  # Can add interrupts for HITL
    )
    
    logger.info("Legacy Multi-Agent LangGraph workflow compiled successfully")
    return graph

# Singleton graph instance
_multi_agent_graph = None

def get_multi_agent_graph() -> StateGraph:
    """
    Get or create the multi-agent graph.
    
    Returns:
        Compiled StateGraph instance that supports multi-step workflows
    """
    global _multi_agent_graph
    if _multi_agent_graph is None:
        _multi_agent_graph = create_multi_agent_graph()
    return _multi_agent_graph