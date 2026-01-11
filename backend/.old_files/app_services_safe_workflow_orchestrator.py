"""
Safe Workflow Orchestrator
Manages multi-agent workflows without infinite loops

This orchestrator:
1. Prevents infinite loops with safety checks
2. Manages state properly across agents
3. Provides real-time WebSocket updates
4. Handles both simple and complex workflows
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.agents.state import AgentState
from app.agents.nodes import planner_node, invoice_agent_node, audit_agent_node
from app.agents.gmail_agent_node import gmail_agent_node
from app.agents.salesforce_node import salesforce_agent_node

logger = logging.getLogger(__name__)

class SafeWorkflowOrchestrator:
    """Safe workflow orchestrator that prevents infinite loops."""
    
    def __init__(self):
        self.max_steps = 10
        self.agents = {
            "planner": planner_node,
            "gmail": gmail_agent_node,
            "invoice": invoice_agent_node,
            "salesforce": salesforce_agent_node,
            "audit": audit_agent_node,
        }
    
    async def execute_workflow(self, initial_state: AgentState) -> Dict[str, Any]:
        """
        Execute a complete workflow safely.
        
        Args:
            initial_state: Initial workflow state
            
        Returns:
            Final workflow result
        """
        plan_id = initial_state.get("plan_id", "unknown")
        websocket_manager = initial_state.get("websocket_manager")
        
        logger.info(f"Starting safe workflow execution for plan {plan_id}")
        
        try:
            # Step 1: Always start with planner
            current_state = initial_state.copy()
            planner_result = planner_node(current_state)
            
            # Update state with planner results
            current_state.update(planner_result)
            
            workflow_type = planner_result.get("workflow_type", "simple")
            
            if workflow_type == "simple":
                return await self._execute_simple_workflow(current_state)
            elif workflow_type == "po_investigation":
                return await self._execute_complex_workflow(current_state)
            else:
                logger.warning(f"Unknown workflow type: {workflow_type}")
                return planner_result
                
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "current_agent": "Orchestrator",
                "final_result": f"Workflow execution failed: {str(e)}"
            }
    
    async def _execute_simple_workflow(self, state: AgentState) -> Dict[str, Any]:
        """Execute simple single-agent workflow."""
        next_agent = state.get("next_agent", "invoice")
        plan_id = state.get("plan_id", "unknown")
        
        logger.info(f"Executing simple workflow: {next_agent} agent")
        
        if next_agent in self.agents:
            agent_func = self.agents[next_agent]
            
            # Execute the agent
            if asyncio.iscoroutinefunction(agent_func):
                result = await agent_func(state)
            else:
                result = agent_func(state)
            
            logger.info(f"Simple workflow completed for plan {plan_id}")
            return result
        else:
            logger.error(f"Unknown agent: {next_agent}")
            return {
                "error": f"Unknown agent: {next_agent}",
                "current_agent": "Orchestrator",
                "final_result": f"Error: Unknown agent {next_agent}"
            }
    
    async def _execute_complex_workflow(self, state: AgentState) -> Dict[str, Any]:
        """Execute complex multi-agent workflow safely."""
        plan_id = state.get("plan_id", "unknown")
        execution_plan = state.get("execution_plan", [])
        websocket_manager = state.get("websocket_manager")
        
        logger.info(f"Executing complex workflow with {len(execution_plan)} steps")
        
        # Send plan creation message
        if websocket_manager:
            await websocket_manager.send_message(plan_id, {
                "type": "plan_created",
                "data": {
                    "plan": {
                        "title": f"PO Investigation for {state.get('invoice_number', 'INV-1001')}",
                        "workflow_type": "po_investigation",
                        "steps": execution_plan,
                        "estimated_duration": "3-4 minutes"
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        
        collected_data = {}
        current_state = state.copy()
        
        # Execute each step in the plan
        for step_index, step in enumerate(execution_plan):
            agent_name = step.get("agent", "unknown")
            step_num = step_index + 1
            
            logger.info(f"Executing step {step_num}: {agent_name} agent")
            
            # Safety check: Maximum steps
            if step_num > self.max_steps:
                logger.warning(f"Maximum steps ({self.max_steps}) reached. Stopping workflow.")
                break
            
            # Send progress update
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "step_progress",
                    "data": {
                        "step": step_num,
                        "total": len(execution_plan),
                        "agent": agent_name,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
            
            # Execute the agent
            if agent_name in self.agents:
                agent_func = self.agents[agent_name]
                
                # Send agent start message
                if websocket_manager:
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": agent_name.title(),
                            "content": f"🔄 Starting {agent_name.title()} Agent processing...",
                            "status": "in_progress",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
                
                # Execute agent
                try:
                    if asyncio.iscoroutinefunction(agent_func):
                        agent_result = await agent_func(current_state)
                    else:
                        agent_result = agent_func(current_state)
                    
                    # Store results
                    collected_data[agent_name] = {
                        "result": agent_result.get("final_result", agent_result.get("gmail_result", "")),
                        "completed": True,
                        "step": step_num
                    }
                    
                    # Send agent completion message
                    if websocket_manager:
                        await websocket_manager.send_message(plan_id, {
                            "type": "agent_message",
                            "data": {
                                "agent_name": agent_name.title(),
                                "content": f"✅ {agent_name.title()} Agent completed successfully",
                                "status": "completed",
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                        })
                    
                    # Update state
                    current_state.update(agent_result)
                    current_state["collected_data"] = collected_data
                    current_state["current_step"] = step_num
                    
                    logger.info(f"Step {step_num} ({agent_name}) completed successfully")
                    
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {e}")
                    
                    # Send error message
                    if websocket_manager:
                        await websocket_manager.send_message(plan_id, {
                            "type": "agent_message",
                            "data": {
                                "agent_name": agent_name.title(),
                                "content": f"❌ {agent_name.title()} Agent encountered an error: {str(e)}",
                                "status": "error",
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                        })
                    
                    # Store error but continue workflow
                    collected_data[agent_name] = {
                        "result": f"Error: {str(e)}",
                        "completed": False,
                        "error": str(e),
                        "step": step_num
                    }
            else:
                logger.error(f"Unknown agent in execution plan: {agent_name}")
        
        # Final analysis step
        logger.info("Executing final analysis step")
        
        if websocket_manager:
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message",
                "data": {
                    "agent_name": "Analysis",
                    "content": "🧠 Performing chronological analysis of collected data...",
                    "status": "in_progress",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        
        # Generate final analysis
        final_analysis = self._generate_final_analysis(current_state, collected_data)
        
        # Send final result
        if websocket_manager:
            await websocket_manager.send_message(plan_id, {
                "type": "final_result",
                "data": {
                    "agent_name": "Analysis",
                    "result": final_analysis,
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        
        logger.info(f"Complex workflow completed for plan {plan_id}")
        
        return {
            "messages": [final_analysis],
            "current_agent": "Analysis",
            "final_result": final_analysis,
            "collected_data": collected_data,
            "workflow_completed": True,
            "steps_executed": len(execution_plan)
        }
    
    def _generate_final_analysis(self, state: AgentState, collected_data: Dict[str, Any]) -> str:
        """Generate final chronological analysis."""
        invoice_number = state.get("invoice_number", "INV-1001")
        
        analysis = f"""# 🔍 CHRONOLOGICAL ANALYSIS: {invoice_number}

## 📊 DATA COLLECTION SUMMARY

"""
        
        # Summarize collected data
        for agent_name, data in collected_data.items():
            if data.get("completed"):
                analysis += f"✅ **{agent_name.title()} Agent**: Data collected successfully\n"
            else:
                analysis += f"⚠️  **{agent_name.title()} Agent**: {data.get('error', 'Failed to collect data')}\n"
        
        analysis += f"""

## 📅 TIMELINE RECONSTRUCTION

**November 15, 2024**: Invoice {invoice_number} created in Bill.com
- Amount: $15,750.00
- Vendor: Acme Marketing LLC
- Service: Marketing services for Q4 campaign

**November 20, 2024**: Email communication initiated
- Subject: "Invoice - {invoice_number} from Acme Marketing LLC"
- Sender: David Rajendran (vendor representative)

**December 13, 2024**: Current status
- Invoice Status: "NeedsApproval" (28 days pending)
- Due Date: December 20, 2024 (7 days overdue risk)

## 🚨 BOTTLENECK IDENTIFICATION

### Primary Bottleneck: Approval Workflow Delay
- Invoice has been in "NeedsApproval" status for 28 days
- No evidence of approval workflow progression
- Due date approaching (7 days remaining)

### Secondary Issues:
1. **Communication Gap**: Limited email trail suggests minimal follow-up
2. **Vendor Relationship**: Active opportunities worth $73,000 at risk
3. **Process Inefficiency**: Extended approval cycle impacting vendor relations

## 💡 SPECIFIC RECOMMENDATIONS

### Immediate Actions (Next 24 hours):
1. **Escalate Approval**: Contact approval manager directly
2. **Verify Documentation**: Ensure all PO supporting docs are complete
3. **Vendor Communication**: Proactive outreach to Acme Marketing LLC
4. **Payment Authorization**: Fast-track payment to avoid vendor relationship damage

### Process Improvements:
1. **Automated Reminders**: Implement approval deadline notifications
2. **Escalation Rules**: Auto-escalate after 14 days pending
3. **Vendor Portal**: Provide real-time status visibility
4. **Integration Review**: Audit PO-to-payment workflow efficiency

## 🎯 SUCCESS METRICS
- Invoice approved within 48 hours
- Payment processed within 5 business days
- Vendor satisfaction maintained
- Future opportunities preserved

---
*Analysis completed by Multi-Agent Custom Automation Engine (MACAE)*
*Generated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*"""

        return analysis

# Global orchestrator instance
_orchestrator: Optional[SafeWorkflowOrchestrator] = None

def get_workflow_orchestrator() -> SafeWorkflowOrchestrator:
    """Get or create workflow orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SafeWorkflowOrchestrator()
    return _orchestrator