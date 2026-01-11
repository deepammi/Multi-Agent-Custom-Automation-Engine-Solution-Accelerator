"""
Complex Planner Node for Multi-Agent Workflows
Handles complex business scenarios requiring multiple agents working together
"""

import logging
import re
from typing import Dict, Any, List
from datetime import datetime

from app.agents.state import AgentState

logger = logging.getLogger(__name__)

class ComplexPlannerNode:
    """Enhanced planner that can create multi-step plans requiring multiple agents."""
    
    def __init__(self):
        self.name = "complex_planner"
        
    def analyze_task_complexity(self, task: str) -> Dict[str, Any]:
        """
        Analyze if a task requires complex multi-agent workflow.
        
        Args:
            task: User's task description
            
        Returns:
            Analysis result with complexity level and required agents
        """
        task_lower = task.lower()
        
        # Detect PO investigation patterns
        po_patterns = [
            r'po.*(?:missing|stuck|delayed|not processed)',
            r'purchase order.*(?:missing|stuck|delayed|not processed)',
            r'why.*po.*(?:missing|stuck|delayed)',
            r'invoice.*(?:inv-\d+).*(?:missing|stuck|delayed|not processed)',
            r'(?:missing|stuck|delayed).*po.*invoice',
        ]
        
        is_po_investigation = any(re.search(pattern, task_lower) for pattern in po_patterns)
        
        # Extract invoice numbers
        invoice_numbers = re.findall(r'inv-?\d+', task_lower, re.IGNORECASE)
        
        # Detect multi-system requirements
        needs_gmail = any(word in task_lower for word in ["email", "communication", "correspondence"])
        needs_billcom = any(word in task_lower for word in ["invoice", "vendor", "payment", "bill"])
        needs_salesforce = any(word in task_lower for word in ["opportunity", "account", "vendor relationship", "crm"])
        
        if is_po_investigation and invoice_numbers:
            return {
                "complexity": "high",
                "workflow_type": "po_investigation",
                "invoice_numbers": invoice_numbers,
                "required_agents": self._determine_required_agents(task_lower),
                "estimated_steps": 5,
                "needs_analysis": True
            }
        elif len([needs_gmail, needs_billcom, needs_salesforce]) >= 2:
            return {
                "complexity": "medium", 
                "workflow_type": "multi_system",
                "required_agents": self._determine_required_agents(task_lower),
                "estimated_steps": 3,
                "needs_analysis": False
            }
        else:
            return {
                "complexity": "simple",
                "workflow_type": "single_agent",
                "required_agents": [self._determine_single_agent(task_lower)],
                "estimated_steps": 1,
                "needs_analysis": False
            }
    
    def _determine_required_agents(self, task_lower: str) -> List[str]:
        """Determine which agents are needed for the task."""
        agents = []
        
        # Check for Gmail requirements
        if any(word in task_lower for word in ["email", "gmail", "communication", "correspondence"]):
            agents.append("gmail")
            
        # Check for Bill.com requirements  
        if any(word in task_lower for word in ["invoice", "vendor", "payment", "bill", "po", "purchase order"]):
            agents.append("invoice")  # Invoice agent handles Bill.com integration
            
        # Check for Salesforce requirements
        if any(word in task_lower for word in ["opportunity", "account", "salesforce", "crm", "vendor relationship"]):
            agents.append("salesforce")
            
        # Check for Audit requirements
        if any(word in task_lower for word in ["audit", "compliance", "trail", "history"]):
            agents.append("audit")
            
        return agents if agents else ["invoice"]  # Default to invoice agent
    
    def _determine_single_agent(self, task_lower: str) -> str:
        """Determine single agent for simple tasks."""
        if any(word in task_lower for word in ["gmail", "email"]):
            return "gmail"
        elif any(word in task_lower for word in ["salesforce", "opportunity", "account"]):
            return "salesforce"
        elif any(word in task_lower for word in ["audit", "compliance"]):
            return "audit"
        else:
            return "invoice"
    
    def create_complex_plan(self, task: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a detailed execution plan for complex workflows.
        
        Args:
            task: User's task description
            analysis: Task complexity analysis
            
        Returns:
            Detailed execution plan
        """
        if analysis["workflow_type"] == "po_investigation":
            return self._create_po_investigation_plan(task, analysis)
        elif analysis["workflow_type"] == "multi_system":
            return self._create_multi_system_plan(task, analysis)
        else:
            return self._create_simple_plan(task, analysis)
    
    def _create_po_investigation_plan(self, task: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create plan for PO investigation workflow."""
        invoice_number = analysis["invoice_numbers"][0] if analysis["invoice_numbers"] else "INV-1001"
        
        plan = {
            "workflow_type": "po_investigation",
            "title": f"PO Investigation for {invoice_number.upper()}",
            "description": f"Comprehensive investigation of purchase order issues related to {invoice_number.upper()}",
            "steps": [
                {
                    "step": 1,
                    "agent": "planner",
                    "title": "Analysis & Planning",
                    "description": f"Analyzing PO issue for {invoice_number.upper()} and creating investigation plan",
                    "status": "in_progress",
                    "estimated_duration": "30 seconds"
                },
                {
                    "step": 2,
                    "agent": "gmail",
                    "title": "Email Investigation",
                    "description": f"Searching Gmail for communications related to {invoice_number.upper()}",
                    "status": "pending",
                    "estimated_duration": "45 seconds"
                },
                {
                    "step": 3,
                    "agent": "invoice",
                    "title": "Invoice & Vendor Data",
                    "description": f"Retrieving invoice details and vendor information from Bill.com",
                    "status": "pending",
                    "estimated_duration": "60 seconds"
                },
                {
                    "step": 4,
                    "agent": "salesforce",
                    "title": "Vendor Relationship Analysis",
                    "description": "Analyzing vendor opportunities and account status in Salesforce",
                    "status": "pending",
                    "estimated_duration": "45 seconds"
                },
                {
                    "step": 5,
                    "agent": "analysis",
                    "title": "Chronological Analysis",
                    "description": "Performing AI-powered chronological analysis to identify bottlenecks",
                    "status": "pending",
                    "estimated_duration": "90 seconds"
                }
            ],
            "total_estimated_duration": "4-5 minutes",
            "expected_outcomes": [
                "Timeline of events related to the PO",
                "Identification of process bottlenecks",
                "Vendor relationship impact assessment",
                "Specific recommendations for resolution"
            ]
        }
        
        return plan
    
    def _create_multi_system_plan(self, task: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create plan for multi-system workflows."""
        agents = analysis["required_agents"]
        
        steps = [
            {
                "step": 1,
                "agent": "planner",
                "title": "Task Analysis",
                "description": "Analyzing requirements and coordinating multi-system approach",
                "status": "in_progress",
                "estimated_duration": "30 seconds"
            }
        ]
        
        step_num = 2
        for agent in agents:
            agent_titles = {
                "gmail": "Email Processing",
                "invoice": "Invoice/Financial Data",
                "salesforce": "CRM Data Analysis",
                "audit": "Compliance Review"
            }
            
            steps.append({
                "step": step_num,
                "agent": agent,
                "title": agent_titles.get(agent, f"{agent.title()} Processing"),
                "description": f"Processing task using {agent.title()} Agent",
                "status": "pending",
                "estimated_duration": "60 seconds"
            })
            step_num += 1
        
        plan = {
            "workflow_type": "multi_system",
            "title": "Multi-System Data Integration",
            "description": "Coordinated data collection and analysis across multiple systems",
            "steps": steps,
            "total_estimated_duration": f"{len(steps) * 45} seconds",
            "expected_outcomes": [
                "Integrated data from multiple systems",
                "Comprehensive analysis results",
                "Actionable recommendations"
            ]
        }
        
        return plan
    
    def _create_simple_plan(self, task: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create plan for simple single-agent workflows."""
        agent = analysis["required_agents"][0]
        
        agent_titles = {
            "gmail": "Email Processing",
            "invoice": "Invoice Processing", 
            "salesforce": "Salesforce Query",
            "audit": "Audit Analysis"
        }
        
        plan = {
            "workflow_type": "single_agent",
            "title": agent_titles.get(agent, f"{agent.title()} Task"),
            "description": f"Processing task using {agent.title()} Agent",
            "steps": [
                {
                    "step": 1,
                    "agent": "planner",
                    "title": "Task Analysis",
                    "description": "Analyzing task and routing to appropriate agent",
                    "status": "in_progress",
                    "estimated_duration": "15 seconds"
                },
                {
                    "step": 2,
                    "agent": agent,
                    "title": agent_titles.get(agent, f"{agent.title()} Processing"),
                    "description": f"Executing task using {agent.title()} Agent",
                    "status": "pending",
                    "estimated_duration": "60 seconds"
                }
            ],
            "total_estimated_duration": "1-2 minutes",
            "expected_outcomes": [
                f"Results from {agent.title()} Agent",
                "Task completion confirmation"
            ]
        }
        
        return plan

# Create the enhanced planner node function
async def complex_planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Enhanced planner node that can handle complex multi-agent workflows.
    
    This planner:
    1. Analyzes task complexity
    2. Creates detailed execution plans
    3. Coordinates multiple agents
    4. Provides step-by-step progress tracking
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    websocket_manager = state.get("websocket_manager")
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
    logger.info(f"Complex Planner processing task for plan {plan_id}")
    
    # Initialize planner
    planner = ComplexPlannerNode()
    
    # Analyze task complexity
    analysis = planner.analyze_task_complexity(task)
    logger.info(f"Task analysis: {analysis['complexity']} complexity, {analysis['workflow_type']} workflow")
    
    # Create execution plan
    execution_plan = planner.create_complex_plan(task, analysis)
    
    # Send initial plan via WebSocket
    if websocket_manager:
        await websocket_manager.send_message(plan_id, {
            "type": "plan_created",
            "data": {
                "plan": execution_plan,
                "analysis": analysis,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    # Generate response based on complexity (no routing logic)
    if analysis["complexity"] == "high" and analysis["workflow_type"] == "po_investigation":
        response = f"""🔍 **Complex Workflow Initiated: PO Investigation**

I've analyzed your request and identified this as a complex purchase order investigation requiring multiple agents.

**Investigation Plan for {analysis['invoice_numbers'][0].upper() if analysis['invoice_numbers'] else 'INV-1001'}:**

📧 **Step 1**: Gmail Agent - Search for related email communications
💰 **Step 2**: Invoice Agent - Retrieve invoice and vendor data from Bill.com  
🏢 **Step 3**: Salesforce Agent - Analyze vendor relationships and opportunities
🧠 **Step 4**: AI Analysis - Perform chronological analysis to identify bottlenecks

**Estimated Duration**: 4-5 minutes
**Expected Outcome**: Comprehensive analysis with specific recommendations

The linear executor will now proceed with the predefined agent sequence..."""

        # Save PO investigation response to database
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="Planner",
            content=response,
            agent_type="planner",
            metadata={
                "complexity": "high",
                "workflow_type": "po_investigation",
                "invoice_numbers": analysis.get("invoice_numbers", [])
            }
        )

    elif analysis["complexity"] == "medium":
        response = f"""🔄 **Multi-System Workflow Initiated**

I've identified this task requires coordination across {len(analysis['required_agents'])} systems.

**Agents Involved**: {', '.join([agent.title() for agent in analysis['required_agents']])}
**Estimated Duration**: {execution_plan['total_estimated_duration']}

The linear executor will now proceed with the agent sequence..."""

        # Save multi-system response to database
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="Planner",
            content=response,
            agent_type="planner",
            metadata={
                "complexity": "medium",
                "workflow_type": "multi_system",
                "required_agents": analysis.get("required_agents", [])
            }
        )

    else:
        response = f"""✅ **Task Analysis Complete**

The system will now execute the appropriate agent based on the AI-generated sequence.

**Estimated Duration**: {execution_plan['total_estimated_duration']}"""
    
    # Save complex planner response to database
    await message_persistence.save_agent_message(
        plan_id=plan_id,
        agent_name="Planner",
        content=response,
        agent_type="planner",
        metadata={
            "complexity": analysis["complexity"],
            "workflow_type": analysis["workflow_type"],
            "estimated_duration": execution_plan.get("total_estimated_duration", "unknown")
        }
    )
    
    # Store analysis results in collected_data for subsequent agents
    collected_data = state.get("collected_data", {})
    collected_data.update({
        "task_analysis": analysis,
        "execution_plan": execution_plan,
        "complexity": analysis["complexity"],
        "workflow_type": analysis["workflow_type"]
    })
    
    # Store invoice numbers if found for subsequent agents
    if analysis.get("invoice_numbers"):
        collected_data["invoice_numbers"] = analysis["invoice_numbers"]
    
    return {
        "messages": [response],
        "current_agent": "Planner",
        "planner_result": response,
        "collected_data": collected_data,
        "execution_results": state.get("execution_results", [])
        # No next_agent routing - linear execution handles progression
    }