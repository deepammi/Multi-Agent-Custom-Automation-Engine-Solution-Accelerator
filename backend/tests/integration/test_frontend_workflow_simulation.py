#!/usr/bin/env python3
"""
Frontend Workflow Simulation Test

This script exactly simulates how the frontend sends queries and processes responses:
1. User enters query (like frontend form submission)
2. POST /api/v3/process_request (AI Planner creates execution plan)
3. Human approval via plan_approval_request WebSocket message
4. POST /api/v3/plan_approval (user approves/rejects)
5. Multi-agent execution with real-time WebSocket updates
6. Final results display

This is the most accurate simulation of the actual frontend workflow.
"""

import asyncio
import sys
import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required services
from app.services.ai_planner_service import AIPlanner
from app.services.llm_service import LLMService
from app.agents.graph_factory import LinearGraphFactory
from app.agents.state import AgentState, AgentStateManager
from app.models.ai_planner import AIPlanningSummary

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketMessageSimulator:
    """Simulates WebSocket messages that would be sent to frontend."""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, message_type: str, data: Dict[str, Any]):
        """Simulate sending WebSocket message."""
        message = {
            "type": message_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        self.messages.append(message)
        
        # Print message like frontend would receive it
        print(f"📡 WebSocket Message: {message_type}")
        if message_type == "plan_approval_request":
            print(f"   Plan: {data.get('plan_summary', 'No summary')}")
        elif message_type == "agent_message":
            print(f"   Agent: {data.get('agent', 'Unknown')}")
            print(f"   Message: {data.get('content', 'No content')[:100]}...")
        elif message_type == "final_result_message":
            print(f"   Status: {data.get('status', 'Unknown')}")
        
        # Simulate network delay
        await asyncio.sleep(0.1)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages sent."""
        return self.messages.copy()


class FrontendWorkflowSimulator:
    """Simulates the complete frontend workflow."""
    
    def __init__(self, verbose_debug: bool = False):
        """Initialize simulator."""
        self.llm_service = LLMService()
        self.ai_planner = AIPlanner(self.llm_service)
        self.websocket_sim = WebSocketMessageSimulator()
        self.verbose_debug = verbose_debug
        
        # PO investigation queries that would come from frontend
        self.po_queries = [
            {
                "title": "Payment Dispute Investigation",
                "query": "Investigate PO-2024-001 - vendor claims payment not received but our records show it was sent. Need to check email communications, payment status in Bill.com, and vendor relationship in Salesforce.",
                "expected_agents": ["gmail", "invoice", "salesforce", "analysis"]
            },
            {
                "title": "Invoice Discrepancy Analysis", 
                "query": "Analyze PO-2024-015 invoice discrepancy - invoice amount $1,250 vs PO amount $1,200. Check email trail, validate invoice in Bill.com, and review vendor terms in Salesforce.",
                "expected_agents": ["gmail", "invoice", "salesforce", "analysis"]
            },
            {
                "title": "Vendor Communication Review",
                "query": "Review PO-2024-032 vendor communications - they're requesting payment terms change. Find email history, check current payment status, and analyze vendor relationship.",
                "expected_agents": ["gmail", "salesforce", "invoice", "analysis"]
            },
            {
                "title": "Overdue Payment Investigation",
                "query": "Investigate overdue payments for Office Supplies Inc - find recent email communications, check all outstanding invoices in Bill.com, and review payment history in Salesforce.",
                "expected_agents": ["gmail", "invoice", "salesforce", "analysis"]
            },
            {
                "title": "Duplicate PO Analysis",
                "query": "Analyze potential duplicate POs - PO-2024-021 and PO-2024-022 for same vendor and similar amounts. Check email approvals, validate in Bill.com, and review in Salesforce.",
                "expected_agents": ["gmail", "invoice", "salesforce", "analysis"]
            }
        ]
    
    def print_header(self, title: str):
        """Print formatted header."""
        print(f"\n{'=' * 80}")
        print(f"🌐 {title}")
        print(f"{'=' * 80}")
    
    def print_step(self, step: str, description: str):
        """Print workflow step."""
        print(f"\n🔸 Step: {step}")
        print(f"   {description}")
    
    def display_query_options(self):
        """Display available PO investigation queries."""
        print(f"\n📋 Available PO Investigation Scenarios:")
        print(f"{'=' * 50}")
        
        for i, scenario in enumerate(self.po_queries, 1):
            print(f"\n{i}. {scenario['title']}")
            print(f"   Query: {scenario['query']}")
            print(f"   Expected: {' → '.join(scenario['expected_agents'])}")
        
        print(f"\n{len(self.po_queries) + 1}. Enter custom query")
    
    def get_user_query(self) -> Dict[str, Any]:
        """Get user query selection."""
        self.display_query_options()
        
        while True:
            choice = input(f"\nSelect scenario (1-{len(self.po_queries) + 1}): ").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.po_queries):
                    scenario = self.po_queries[choice_num - 1]
                    print(f"\n✅ Selected: {scenario['title']}")
                    return scenario
                elif choice_num == len(self.po_queries) + 1:
                    custom_query = input("Enter your custom query: ").strip()
                    if len(custom_query) > 10:
                        return {
                            "title": "Custom Query",
                            "query": custom_query,
                            "expected_agents": ["gmail", "invoice", "salesforce", "analysis"]
                        }
                    else:
                        print("Query too short. Please enter a detailed query.")
                else:
                    print(f"Please enter 1-{len(self.po_queries) + 1}")
            else:
                print("Please enter a valid number")
    
    async def simulate_process_request(self, query: str) -> Dict[str, Any]:
        """
        Simulate POST /api/v3/process_request
        This is what the frontend calls when user submits a query.
        """
        self.print_step("POST /api/v3/process_request", "Frontend submits user query for processing")
        
        # Generate IDs like the real API would
        plan_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        print(f"   Request: {{\"description\": \"{query[:50]}...\"}}")
        print(f"   Generated Plan ID: {plan_id}")
        print(f"   Generated Session ID: {session_id}")
        
        # Simulate AI planning (this happens in the backend)
        print(f"   🧠 Running AI Planner...")
        planning_summary = await self.ai_planner.plan_workflow(query)
        
        if planning_summary.success:
            print(f"   ✅ AI Planning successful")
            print(f"   📋 Plan: {' → '.join(planning_summary.agent_sequence.agents)}")
            
            # Send plan approval request via WebSocket (like real backend)
            await self.websocket_sim.send_message("plan_approval_request", {
                "plan_id": plan_id,
                "plan_summary": {
                    "task": query,
                    "agents": planning_summary.agent_sequence.agents,
                    "reasoning": planning_summary.agent_sequence.reasoning,
                    "estimated_duration": planning_summary.agent_sequence.estimated_duration
                }
            })
            
            return {
                "plan_id": plan_id,
                "session_id": session_id,
                "status": "pending_approval",
                "planning_summary": planning_summary
            }
        else:
            print(f"   ❌ AI Planning failed: {planning_summary.error_message}")
            return {
                "plan_id": plan_id,
                "session_id": session_id,
                "status": "failed",
                "error": planning_summary.error_message
            }
    
    def simulate_human_approval(self, plan_data: Dict[str, Any]) -> bool:
        """
        Simulate human approval process.
        This is what happens when user sees the plan approval request.
        """
        self.print_step("Human Approval", "User reviews and approves/rejects the execution plan")
        
        planning_summary = plan_data["planning_summary"]
        sequence = planning_summary.agent_sequence
        
        print(f"\n📋 Execution Plan for Approval:")
        print(f"   Task: {planning_summary.task_description}")
        print(f"   Agents: {' → '.join(sequence.agents)}")
        print(f"   Duration: ~{sequence.estimated_duration}s")
        print(f"   Complexity: {sequence.complexity_score:.2f}")
        
        print(f"\n🤖 Agent Roles:")
        for agent, reasoning in sequence.reasoning.items():
            print(f"   • {agent.title()}: {reasoning}")
        
        # Get user approval
        while True:
            choice = input(f"\n❓ Approve this plan? (y/n/details): ").strip().lower()
            
            if choice in ['y', 'yes', 'approve']:
                print(f"   ✅ Plan approved by user")
                return True
            elif choice in ['n', 'no', 'reject']:
                print(f"   ❌ Plan rejected by user")
                return False
            elif choice in ['d', 'details']:
                print(f"\n📊 Detailed Plan Information:")
                print(f"   Analysis Duration: {planning_summary.analysis_duration:.2f}s")
                print(f"   Sequence Generation: {planning_summary.sequence_generation_duration:.2f}s")
                print(f"   Total Planning Time: {planning_summary.total_duration:.2f}s")
                print(f"   Task Complexity: {planning_summary.task_analysis.complexity}")
                print(f"   Required Systems: {', '.join(planning_summary.task_analysis.required_systems)}")
                print(f"   Confidence Score: {planning_summary.task_analysis.confidence_score:.2f}")
            else:
                print("   Please enter 'y' (yes), 'n' (no), or 'details' for more info")
    
    async def simulate_plan_approval(self, plan_id: str, approved: bool) -> Dict[str, Any]:
        """
        Simulate POST /api/v3/plan_approval
        This is what the frontend calls when user approves/rejects.
        """
        self.print_step("POST /api/v3/plan_approval", f"Frontend sends approval decision: {approved}")
        
        print(f"   Request: {{\"plan_id\": \"{plan_id}\", \"approved\": {approved}}}")
        
        if approved:
            print(f"   ✅ Plan approved - starting execution")
            return {"status": "approved", "message": "Plan approved, starting execution"}
        else:
            print(f"   ❌ Plan rejected - workflow cancelled")
            return {"status": "rejected", "message": "Plan rejected by user"}
    
    async def simulate_agent_execution(self, planning_summary: AIPlanningSummary, plan_id: str) -> Dict[str, Any]:
        """
        Simulate multi-agent execution with WebSocket updates.
        This is what happens in the backend after approval.
        """
        self.print_step("Multi-Agent Execution", "Backend executes agents and sends real-time updates")
        
        sequence = planning_summary.agent_sequence
        
        # Create initial state
        initial_state = AgentStateManager.create_initial_state(
            plan_id=plan_id,
            session_id=str(uuid.uuid4()),
            task_description=planning_summary.task_description,
            agent_sequence=sequence.agents,
            websocket_manager=self.websocket_sim
        )
        
        execution_results = []
        
        # Execute each agent
        for i, agent in enumerate(sequence.agents):
            print(f"\n   🤖 Executing Agent {i+1}/{len(sequence.agents)}: {agent.title()}")
            
            # Send agent start message
            await self.websocket_sim.send_message("agent_message", {
                "agent": agent,
                "content": f"Starting {agent} agent execution...",
                "step": i + 1,
                "total_steps": len(sequence.agents)
            })
            
            # Simulate agent processing
            agent_result = await self.simulate_individual_agent(agent, initial_state)
            execution_results.append(agent_result)
            
            # Send agent completion message
            await self.websocket_sim.send_message("agent_message", {
                "agent": agent,
                "content": agent_result["message"],
                "result": agent_result["data"],
                "step": i + 1,
                "total_steps": len(sequence.agents)
            })
            
            # Update state
            initial_state["current_step"] = i + 1
            AgentStateManager.add_agent_result(initial_state, agent, agent_result)
            
            print(f"      ✅ {agent_result['message']}")
        
        # Compile final results
        final_result = self.compile_investigation_results(execution_results, planning_summary)
        
        # Send final result
        await self.websocket_sim.send_message("final_result_message", {
            "status": "completed",
            "result": final_result,
            "execution_summary": {
                "total_agents": len(execution_results),
                "total_time": sum(r.get("execution_time", 0) for r in execution_results),
                "success_rate": len([r for r in execution_results if r["status"] == "success"]) / len(execution_results)
            }
        })
        
        return {
            "status": "completed",
            "execution_results": execution_results,
            "final_result": final_result
        }
    
    async def simulate_individual_agent(self, agent: str, state: AgentState) -> Dict[str, Any]:
        """Simulate individual agent execution with realistic data."""
        
        # Simulate processing time
        processing_times = {"gmail": 3, "invoice": 4, "salesforce": 3, "accounts_receivable": 4, "audit": 5, "analysis": 6}
        processing_time = processing_times.get(agent, 3)
        
        if self.verbose_debug:
            print(f"      🔍 DEBUG: Starting {agent} agent execution...")
            print(f"      🔍 DEBUG: Processing time: {processing_time}s")
            print(f"      🔍 DEBUG: Task: {state.get('task_description', 'No task')}")
            print(f"      🔍 DEBUG: Verbose mode is ACTIVE - will call real agents")
        
        await asyncio.sleep(processing_time)
        
        # Try to call real agent if verbose debug is enabled
        if self.verbose_debug:
            print(f"      🔍 DEBUG: Verbose mode detected - calling real {agent} agent...")
            real_result = await self.call_real_agent(agent, state)
            if real_result:
                print(f"      🔍 DEBUG: ✅ Real agent result received")
                print(f"      🔍 DEBUG: Status: {real_result.get('status', 'unknown')}")
                print(f"      🔍 DEBUG: Message: {real_result.get('message', 'No message')}")
                print(f"      🔍 DEBUG: Data keys: {list(real_result.get('data', {}).keys())}")
                print(f"      🔍 DEBUG: Full result JSON:")
                print(f"      🔍 DEBUG: {json.dumps(real_result, indent=6, default=str)}")
                return real_result
            else:
                print(f"      🔍 DEBUG: ❌ Real agent call returned None - using simulation")
        
        # Generate realistic results based on agent type (fallback/simulation)
        if agent == "gmail":
            return {
                "agent": agent,
                "status": "success",
                "execution_time": processing_time,
                "message": "Email analysis completed - found relevant communications",
                "data": {
                    "emails_analyzed": 15,
                    "relevant_threads": 4,
                    "key_communications": [
                        "Payment confirmation request from vendor",
                        "Invoice discrepancy discussion thread", 
                        "Delivery timeline clarification emails"
                    ],
                    "summary": "Found email trail showing vendor payment concerns and delivery updates"
                }
            }
        
        elif agent == "invoice":
            return {
                "agent": agent,
                "status": "success", 
                "execution_time": processing_time,
                "message": "Invoice processing completed - identified discrepancies",
                "data": {
                    "invoices_processed": 8,
                    "payment_status": "Partially Paid",
                    "outstanding_amount": "$650.00",
                    "discrepancies": [
                        "Invoice total $1,250 vs PO amount $1,200",
                        "Tax calculation variance of $50"
                    ],
                    "vendor_details": {
                        "name": "Office Supplies Inc",
                        "payment_terms": "Net 30",
                        "last_payment_date": "2024-01-15"
                    }
                }
            }
        
        elif agent == "salesforce":
            return {
                "agent": agent,
                "status": "success",
                "execution_time": processing_time,
                "message": "Vendor relationship analysis completed",
                "data": {
                    "vendor_profile": {
                        "name": "Office Supplies Inc",
                        "status": "Active Vendor",
                        "credit_rating": "Good (85/100)",
                        "relationship_manager": "Sarah Johnson"
                    },
                    "purchase_history": {
                        "total_orders_ytd": 52,
                        "average_order_value": "$1,180",
                        "payment_history": "96% on-time payments"
                    },
                    "recent_interactions": [
                        "Contract renewal discussion - Jan 2024",
                        "Payment terms negotiation - Dec 2023",
                        "Quality issue resolution - Nov 2023"
                    ]
                }
            }
        
        elif agent == "analysis":
            return {
                "agent": agent,
                "status": "success",
                "execution_time": processing_time,
                "message": "Comprehensive analysis completed with recommendations",
                "data": {
                    "investigation_summary": "PO investigation reveals invoice discrepancy requiring approval and payment processing",
                    "key_findings": [
                        "Invoice amount exceeds PO by $50 due to tax calculation difference",
                        "Vendor has excellent payment history and strong relationship",
                        "Email communications show vendor patience but growing concern",
                        "No compliance violations or policy issues identified"
                    ],
                    "recommendations": [
                        "Approve $50 tax adjustment to resolve discrepancy",
                        "Process remaining payment of $650 within 3 business days",
                        "Update PO template to include tax calculation clarity",
                        "Send proactive communication to vendor about resolution timeline"
                    ],
                    "risk_assessment": "Low risk - legitimate discrepancy with trusted vendor",
                    "next_steps": [
                        "Finance approval for tax adjustment",
                        "Payment processing authorization",
                        "Vendor communication update"
                    ]
                }
            }
        
        else:
            return {
                "agent": agent,
                "status": "success",
                "execution_time": processing_time,
                "message": f"{agent.title()} processing completed",
                "data": {"message": f"Processed by {agent} agent"}
            }
    
    async def call_real_agent(self, agent: str, state: AgentState) -> Optional[Dict[str, Any]]:
        """Call real agent and return actual results."""
        try:
            if self.verbose_debug:
                print(f"      🔍 DEBUG: Attempting to call real {agent} agent...")
            
            if agent == "gmail":
                from app.agents.gmail_agent_node import GmailAgentNode
                gmail_agent = GmailAgentNode()
                
                agent_state = {
                    "task": state.get("task_description", ""),
                    "user_request": state.get("task_description", ""),
                    "messages": [],
                    "plan_id": state.get("plan_id", "test"),
                    "session_id": state.get("session_id", "test")
                }
                
                result = await gmail_agent.process(agent_state)
                
                return {
                    "agent": agent,
                    "status": "success" if result else "error",
                    "execution_time": 3,
                    "message": "Real Gmail agent executed",
                    "data": {
                        "real_agent_result": result,
                        "gmail_result": result.get("gmail_result", "No result"),
                        "last_agent": result.get("last_agent", "unknown")
                    }
                }
            
            elif agent == "salesforce":
                from app.agents.salesforce_node import SalesforceAgentNode
                salesforce_agent = SalesforceAgentNode()
                
                # Create proper AgentState for Salesforce
                from app.agents.state import AgentState as ProperAgentState
                agent_state = ProperAgentState(
                    task_description=state.get("task_description", ""),
                    plan_id=state.get("plan_id", "test"),
                    session_id=state.get("session_id", "test"),
                    messages=[],
                    collected_data={},
                    execution_results=[],
                    final_result="",
                    agent_sequence=[agent],
                    current_step=0,
                    total_steps=1,
                    current_agent=agent,
                    approval_required=False,
                    awaiting_user_input=False
                )
                
                result = await salesforce_agent.process(agent_state)
                
                return {
                    "agent": agent,
                    "status": "success" if result else "error",
                    "execution_time": 3,
                    "message": "Real Salesforce agent executed",
                    "data": {
                        "real_agent_result": result,
                        "final_result": result.get("final_result", "No result"),
                        "salesforce_data": result.get("collected_data", {})
                    }
                }
            
            elif agent == "invoice":
                from app.agents.nodes import invoice_agent_node
                
                # Create proper AgentState for Invoice
                from app.agents.state import AgentState as ProperAgentState
                agent_state = ProperAgentState(
                    task_description=state.get("task_description", ""),
                    plan_id=state.get("plan_id", "test"),
                    session_id=state.get("session_id", "test"),
                    messages=[],
                    collected_data={},
                    execution_results=[],
                    final_result="",
                    agent_sequence=[agent],
                    current_step=0,
                    total_steps=1,
                    current_agent=agent,
                    approval_required=False,
                    awaiting_user_input=False
                )
                
                result = await invoice_agent_node(agent_state)
                
                return {
                    "agent": agent,
                    "status": "success" if result else "error",
                    "execution_time": 4,
                    "message": "Real Invoice agent executed",
                    "data": {
                        "real_agent_result": result,
                        "final_result": result.get("final_result", "No result"),
                        "invoice_data": result.get("collected_data", {})
                    }
                }
            
            else:
                if self.verbose_debug:
                    print(f"      🔍 DEBUG: No real agent implementation for {agent}")
                return None
        
        except Exception as e:
            if self.verbose_debug:
                print(f"      🔍 DEBUG: Error calling real {agent} agent: {e}")
                import traceback
                traceback.print_exc()
            return {
                "agent": agent,
                "status": "error",
                "execution_time": 1,
                "message": f"Real {agent} agent failed: {str(e)}",
                "data": {"error": str(e)}
            }
    
    def compile_investigation_results(self, execution_results: List[Dict[str, Any]], planning_summary: AIPlanningSummary) -> str:
        """Compile final investigation report."""
        
        # Extract data from each agent
        gmail_data = next((r["data"] for r in execution_results if r["agent"] == "gmail"), {})
        invoice_data = next((r["data"] for r in execution_results if r["agent"] == "invoice"), {})
        salesforce_data = next((r["data"] for r in execution_results if r["agent"] == "salesforce"), {})
        analysis_data = next((r["data"] for r in execution_results if r["agent"] == "analysis"), {})
        
        report = f"""
PO INVESTIGATION REPORT
=======================

Investigation: {planning_summary.task_description}
Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
Status: COMPLETED

EXECUTIVE SUMMARY
-----------------
{analysis_data.get('investigation_summary', 'Investigation completed successfully')}

Risk Level: {analysis_data.get('risk_assessment', 'Assessment not available')}

KEY FINDINGS
------------
"""
        
        if analysis_data.get('key_findings'):
            for finding in analysis_data['key_findings']:
                report += f"• {finding}\n"
        
        report += f"""
DETAILED ANALYSIS
-----------------

Email Communications:
• Emails Analyzed: {gmail_data.get('emails_analyzed', 0)}
• Relevant Threads: {gmail_data.get('relevant_threads', 0)}
• Summary: {gmail_data.get('summary', 'No email analysis available')}

Invoice Processing:
• Invoices Processed: {invoice_data.get('invoices_processed', 0)}
• Payment Status: {invoice_data.get('payment_status', 'Unknown')}
• Outstanding Amount: {invoice_data.get('outstanding_amount', 'Unknown')}
• Discrepancies Found: {len(invoice_data.get('discrepancies', []))}

Vendor Relationship:
• Vendor: {salesforce_data.get('vendor_profile', {}).get('name', 'Unknown')}
• Status: {salesforce_data.get('vendor_profile', {}).get('status', 'Unknown')}
• Credit Rating: {salesforce_data.get('vendor_profile', {}).get('credit_rating', 'Unknown')}
• Payment History: {salesforce_data.get('purchase_history', {}).get('payment_history', 'Unknown')}

RECOMMENDATIONS
---------------
"""
        
        if analysis_data.get('recommendations'):
            for rec in analysis_data['recommendations']:
                report += f"• {rec}\n"
        
        report += f"""
NEXT STEPS
----------
"""
        
        if analysis_data.get('next_steps'):
            for step in analysis_data['next_steps']:
                report += f"• {step}\n"
        
        report += f"""
EXECUTION SUMMARY
-----------------
• Total Agents Executed: {len(execution_results)}
• Total Processing Time: {sum(r.get('execution_time', 0) for r in execution_results)} seconds
• Success Rate: {len([r for r in execution_results if r['status'] == 'success'])}/{len(execution_results)} agents
• AI Planning Time: {planning_summary.total_duration:.2f} seconds

Report generated by Multi-Agent PO Investigation System
"""
        
        return report.strip()
    
    async def run_complete_workflow(self):
        """Run the complete frontend workflow simulation."""
        self.print_header("Frontend Workflow Simulation")
        
        if self.verbose_debug:
            print("🔍 VERBOSE DEBUG MODE ENABLED")
            print("   - Will call real agents when possible")
            print("   - Will display actual agent responses")
            print("   - Will show detailed execution information")
        
        print("This simulation exactly mirrors the frontend workflow:")
        print("1. User submits query (like frontend form)")
        print("2. Backend processes with AI Planner")
        print("3. WebSocket sends plan approval request")
        print("4. User approves/rejects plan")
        print("5. Backend executes agents with real-time updates")
        print("6. Final results delivered via WebSocket")
        
        try:
            # Step 1: Get user query (like frontend form)
            scenario = self.get_user_query()
            query = scenario["query"]
            
            # Step 2: Simulate process_request API call
            process_result = await self.simulate_process_request(query)
            
            if process_result["status"] == "failed":
                print(f"❌ Workflow failed during planning: {process_result['error']}")
                return
            
            # Step 3: Human approval (like frontend approval dialog)
            approved = self.simulate_human_approval(process_result)
            
            # Step 4: Simulate plan_approval API call
            approval_result = await self.simulate_plan_approval(
                process_result["plan_id"], 
                approved
            )
            
            if not approved:
                print("❌ Workflow cancelled by user")
                return
            
            # Step 5: Execute workflow with WebSocket updates
            execution_result = await self.simulate_agent_execution(
                process_result["planning_summary"],
                process_result["plan_id"]
            )
            
            # Step 6: Display final results (like frontend results page)
            self.print_step("Final Results", "Complete investigation report")
            print(f"\n📊 INVESTIGATION COMPLETE")
            print(f"Status: {execution_result['status']}")
            print(f"\n{execution_result['final_result']}")
            
            # Show WebSocket message summary
            messages = self.websocket_sim.get_messages()
            print(f"\n📡 WebSocket Messages Sent: {len(messages)}")
            for msg in messages:
                print(f"   • {msg['type']} at {msg['timestamp']}")
            
            # Ask to run another test
            print(f"\n❓ Run another investigation? (y/n): ", end="")
            choice = input().strip().lower()
            
            if choice in ['y', 'yes']:
                await self.run_complete_workflow()
            else:
                print("✅ Simulation complete. Thank you!")
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Simulation interrupted. Goodbye!")
        except Exception as e:
            print(f"\n❌ Simulation error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main entry point."""
    print("🌐 Frontend Workflow Simulation")
    print("===============================")
    print("Simulating complete PO investigation workflow")
    print("with Gmail, Bill.com, and Salesforce integration")
    
    # Check for verbose debug flag
    verbose_debug = "--verbose" in sys.argv or "--debug" in sys.argv or "-v" in sys.argv
    
    print(f"\n🔧 Command line args: {sys.argv}")
    print(f"� VerbosEe debug detected: {verbose_debug}")
    
    if verbose_debug:
        print("\n🔍 VERBOSE DEBUG MODE ENABLED")
        print("   ✅ Will call real Gmail, Salesforce, and Invoice agents")
        print("   ✅ Will display actual MCP response data")
        print("   ✅ Will show full JSON responses for debugging")
        print("   ✅ This helps detect AI hallucination")
    else:
        print("\n💡 For verbose debugging with real agent calls:")
        print("   python3 test_frontend_workflow_simulation.py --verbose")
        print("   This will show actual data from your systems")
    
    simulator = FrontendWorkflowSimulator(verbose_debug=verbose_debug)
    await simulator.run_complete_workflow()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)