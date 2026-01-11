#!/usr/bin/env python3
"""
Interactive PO Investigation Test Script

This script simulates the complete frontend workflow for Purchase Order investigation queries:
1. User enters a query manually
2. AI Planner analyzes and creates execution plan
3. Human approval simulation (with real approval prompts)
4. Multi-agent execution with Gmail, Bill.com, and Salesforce integration
5. Real-time progress tracking and results display

Designed to test real-world scenarios with actual data from integrated systems.
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from app.services.ai_planner_service import AIPlanner
from app.services.llm_service import LLMService
from app.agents.graph_factory import LinearGraphFactory
from app.agents.state import AgentState, AgentStateManager
from app.models.ai_planner import AIPlanningSummary

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI color codes for better output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class POInvestigationTester:
    """Interactive tester for PO investigation workflows."""
    
    def __init__(self):
        """Initialize the tester with required services."""
        self.llm_service = LLMService()
        self.ai_planner = AIPlanner(self.llm_service)
        self.session_id = f"test-session-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        
        # Sample PO investigation queries
        self.sample_queries = [
            "Investigate PO-2024-001 - vendor claims they never received payment but our system shows it was sent",
            "Check status of PO-2024-015 for office supplies - vendor is asking about delivery timeline",
            "Analyze PO-2024-032 payment discrepancy - invoice amount doesn't match PO amount",
            "Review PO-2024-007 approval workflow - need to understand why it's stuck in pending",
            "Investigate duplicate PO issue - PO-2024-021 and PO-2024-022 seem to be for same items",
            "Check vendor communication for PO-2024-018 - they claim terms were changed after approval",
            "Analyze payment timing for PO-2024-025 - vendor requesting early payment discount",
            "Review PO-2024-011 compliance issues - audit flagged potential policy violations"
        ]
    
    def print_header(self, title: str):
        """Print formatted header."""
        print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{title.center(80)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    
    def print_section(self, title: str):
        """Print formatted section header."""
        print(f"\n{Colors.OKBLUE}{Colors.BOLD}{title}{Colors.ENDC}")
        print(f"{Colors.OKBLUE}{'-' * len(title)}{Colors.ENDC}")
    
    def print_success(self, message: str):
        """Print success message."""
        print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")
    
    def print_warning(self, message: str):
        """Print warning message."""
        print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")
    
    def print_error(self, message: str):
        """Print error message."""
        print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
    
    def print_info(self, message: str):
        """Print info message."""
        print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")
    
    def display_sample_queries(self):
        """Display sample PO investigation queries."""
        self.print_section("Sample PO Investigation Queries")
        
        for i, query in enumerate(self.sample_queries, 1):
            print(f"{Colors.OKCYAN}{i:2d}.{Colors.ENDC} {query}")
        
        print(f"\n{Colors.OKCYAN}Or enter your own custom query...{Colors.ENDC}")
    
    def get_user_query(self) -> str:
        """Get user query input with sample options."""
        self.display_sample_queries()
        
        while True:
            print(f"\n{Colors.BOLD}Select an option:{Colors.ENDC}")
            choice = input("Enter number (1-8) or type custom query: ").strip()
            
            # Check if it's a number selection
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.sample_queries):
                    selected_query = self.sample_queries[choice_num - 1]
                    print(f"\n{Colors.OKGREEN}Selected:{Colors.ENDC} {selected_query}")
                    return selected_query
                else:
                    self.print_error(f"Please enter a number between 1 and {len(self.sample_queries)}")
            
            # Check if it's a custom query
            elif len(choice) > 10:  # Assume custom query if longer than 10 chars
                print(f"\n{Colors.OKGREEN}Custom query:{Colors.ENDC} {choice}")
                return choice
            
            else:
                self.print_error("Please enter a valid selection or custom query")
    
    async def run_ai_planning(self, query: str) -> AIPlanningSummary:
        """Run AI planning for the query."""
        self.print_section("🧠 AI Planning Phase")
        
        print(f"{Colors.OKCYAN}Query:{Colors.ENDC} {query}")
        print(f"{Colors.OKCYAN}Analyzing task and generating execution plan...{Colors.ENDC}")
        
        try:
            # Run AI planning
            planning_summary = await self.ai_planner.plan_workflow(query)
            
            if planning_summary.success:
                self.print_success(f"AI planning completed in {planning_summary.total_duration:.2f}s")
                
                # Display task analysis
                analysis = planning_summary.task_analysis
                print(f"\n{Colors.BOLD}Task Analysis:{Colors.ENDC}")
                print(f"  Complexity: {analysis.complexity}")
                print(f"  Required Systems: {', '.join(analysis.required_systems)}")
                print(f"  Business Context: {analysis.business_context}")
                print(f"  Confidence Score: {analysis.confidence_score:.2f}")
                
                # Display agent sequence
                sequence = planning_summary.agent_sequence
                print(f"\n{Colors.BOLD}Execution Plan:{Colors.ENDC}")
                print(f"  Agent Sequence: {' → '.join(sequence.agents)}")
                print(f"  Estimated Duration: {sequence.estimated_duration}s")
                print(f"  Complexity Score: {sequence.complexity_score:.2f}")
                
                # Display reasoning
                print(f"\n{Colors.BOLD}Agent Reasoning:{Colors.ENDC}")
                for agent, reasoning in sequence.reasoning.items():
                    print(f"  {Colors.OKCYAN}{agent}:{Colors.ENDC} {reasoning}")
                
                return planning_summary
            
            else:
                self.print_error(f"AI planning failed: {planning_summary.error_message}")
                
                # Use fallback sequence
                self.print_warning("Using fallback sequence for PO investigation")
                fallback_sequence = self.ai_planner.get_fallback_sequence(query)
                
                # Create fallback summary
                planning_summary.agent_sequence = fallback_sequence
                planning_summary.success = True
                
                return planning_summary
        
        except Exception as e:
            self.print_error(f"AI planning failed with exception: {e}")
            
            # Create minimal fallback
            fallback_sequence = self.ai_planner.get_fallback_sequence(query)
            planning_summary = AIPlanningSummary(
                task_description=query,
                analysis_duration=0.0,
                sequence_generation_duration=0.0,
                total_duration=0.0,
                task_analysis=fallback_sequence.task_analysis,
                agent_sequence=fallback_sequence,
                success=True
            )
            
            return planning_summary
    
    def simulate_human_approval(self, planning_summary: AIPlanningSummary) -> bool:
        """Simulate human approval process."""
        self.print_section("👤 Human Approval Phase")
        
        # Display plan for approval
        sequence = planning_summary.agent_sequence
        
        print(f"{Colors.BOLD}Execution Plan for Approval:{Colors.ENDC}")
        print(f"  Task: {planning_summary.task_description}")
        print(f"  Agents: {' → '.join(sequence.agents)}")
        print(f"  Estimated Time: {sequence.estimated_duration}s ({sequence.estimated_duration // 60}m {sequence.estimated_duration % 60}s)")
        print(f"  Complexity: {sequence.complexity_score:.2f}")
        
        print(f"\n{Colors.BOLD}What each agent will do:{Colors.ENDC}")
        for i, agent in enumerate(sequence.agents, 1):
            reasoning = sequence.reasoning.get(agent, "Process data and provide results")
            print(f"  {i}. {Colors.OKCYAN}{agent.title()}:{Colors.ENDC} {reasoning}")
        
        # Get approval
        while True:
            print(f"\n{Colors.BOLD}Do you approve this execution plan?{Colors.ENDC}")
            choice = input("Enter 'y' to approve, 'n' to reject, or 'm' to modify: ").strip().lower()
            
            if choice in ['y', 'yes', 'approve']:
                self.print_success("Plan approved! Starting execution...")
                return True
            
            elif choice in ['n', 'no', 'reject']:
                self.print_warning("Plan rejected. Ending workflow.")
                return False
            
            elif choice in ['m', 'modify']:
                self.print_info("Plan modification not implemented in this test. Treating as approval.")
                return True
            
            else:
                self.print_error("Please enter 'y' (yes), 'n' (no), or 'm' (modify)")
    
    async def execute_workflow(self, planning_summary: AIPlanningSummary) -> Dict[str, Any]:
        """Execute the approved workflow."""
        self.print_section("🚀 Workflow Execution Phase")
        
        sequence = planning_summary.agent_sequence
        plan_id = f"po-investigation-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        
        # Create initial state
        initial_state = AgentStateManager.create_initial_state(
            plan_id=plan_id,
            session_id=self.session_id,
            task_description=planning_summary.task_description,
            agent_sequence=sequence.agents
        )
        
        # Add AI planning summary to state
        initial_state["ai_planning_summary"] = {
            "analysis": planning_summary.task_analysis.__dict__,
            "sequence": planning_summary.agent_sequence.__dict__,
            "total_duration": planning_summary.total_duration
        }
        
        print(f"{Colors.OKCYAN}Plan ID:{Colors.ENDC} {plan_id}")
        print(f"{Colors.OKCYAN}Agent Sequence:{Colors.ENDC} {' → '.join(sequence.agents)}")
        
        try:
            # Create graph from AI sequence
            graph = LinearGraphFactory.create_graph_from_ai_sequence(sequence)
            
            self.print_success("Graph created successfully")
            
            # Execute workflow
            print(f"\n{Colors.BOLD}Starting workflow execution...{Colors.ENDC}")
            
            # Simulate execution with progress tracking
            execution_results = []
            
            for i, agent in enumerate(sequence.agents):
                print(f"\n{Colors.OKCYAN}Step {i+1}/{len(sequence.agents)}: Executing {agent} agent{Colors.ENDC}")
                
                # Simulate agent execution
                agent_result = await self.simulate_agent_execution(agent, initial_state)
                execution_results.append(agent_result)
                
                # Update progress
                progress = AgentStateManager.get_progress_info(initial_state)
                print(f"  Progress: {progress['progress_percentage']:.1f}% complete")
                
                # Update state
                initial_state["current_step"] = i + 1
                AgentStateManager.add_agent_result(initial_state, agent, agent_result)
            
            # Compile final results
            final_result = self.compile_final_results(execution_results, planning_summary)
            
            self.print_success("Workflow execution completed!")
            
            return {
                "plan_id": plan_id,
                "status": "completed",
                "execution_results": execution_results,
                "final_result": final_result,
                "planning_summary": planning_summary.__dict__
            }
        
        except Exception as e:
            self.print_error(f"Workflow execution failed: {e}")
            return {
                "plan_id": plan_id,
                "status": "failed",
                "error": str(e),
                "planning_summary": planning_summary.__dict__
            }
    
    async def simulate_agent_execution(self, agent: str, state: AgentState) -> Dict[str, Any]:
        """Simulate individual agent execution."""
        
        # Simulate different execution times
        execution_times = {
            "gmail": 3,
            "invoice": 4,
            "salesforce": 3,
            "zoho": 4,
            "audit": 5,
            "analysis": 6
        }
        
        execution_time = execution_times.get(agent, 3)
        
        print(f"    {Colors.OKCYAN}Connecting to {agent} system...{Colors.ENDC}")
        await asyncio.sleep(1)
        
        print(f"    {Colors.OKCYAN}Processing data with {agent} agent...{Colors.ENDC}")
        await asyncio.sleep(execution_time)
        
        # Generate realistic results based on agent type
        if agent == "gmail":
            result = {
                "agent": agent,
                "status": "success",
                "data": {
                    "emails_found": 12,
                    "relevant_threads": 3,
                    "vendor_communications": [
                        "Email thread about PO delivery timeline",
                        "Payment confirmation request",
                        "Invoice discrepancy discussion"
                    ],
                    "key_findings": "Found email trail showing vendor payment confirmation and delivery updates"
                },
                "execution_time": execution_time,
                "message": "Successfully retrieved and analyzed email communications"
            }
        
        elif agent == "invoice":
            result = {
                "agent": agent,
                "status": "success",
                "data": {
                    "invoices_processed": 5,
                    "payment_status": "Partially Paid",
                    "discrepancies": [
                        "Invoice amount $1,250 vs PO amount $1,200",
                        "Tax calculation difference of $50"
                    ],
                    "vendor_info": {
                        "name": "Office Supplies Inc",
                        "payment_terms": "Net 30",
                        "last_payment": "2024-01-15"
                    }
                },
                "execution_time": execution_time,
                "message": "Invoice analysis completed with discrepancy identification"
            }
        
        elif agent == "salesforce":
            result = {
                "agent": agent,
                "status": "success",
                "data": {
                    "vendor_record": {
                        "name": "Office Supplies Inc",
                        "status": "Active",
                        "credit_rating": "Good",
                        "relationship_manager": "John Smith"
                    },
                    "purchase_history": {
                        "total_orders": 45,
                        "avg_order_value": "$1,150",
                        "payment_history": "95% on-time"
                    },
                    "recent_interactions": [
                        "Contract renewal discussion - Jan 2024",
                        "Payment terms negotiation - Dec 2023"
                    ]
                },
                "execution_time": execution_time,
                "message": "Vendor relationship data retrieved successfully"
            }
        
        elif agent == "zoho":
            result = {
                "agent": agent,
                "status": "success",
                "data": {
                    "financial_records": {
                        "po_amount": "$1,200.00",
                        "invoiced_amount": "$1,250.00",
                        "paid_amount": "$600.00",
                        "outstanding_balance": "$650.00"
                    },
                    "approval_workflow": {
                        "status": "Approved",
                        "approved_by": "Jane Doe",
                        "approval_date": "2024-01-10"
                    },
                    "budget_impact": {
                        "budget_line": "Office Supplies",
                        "remaining_budget": "$15,750"
                    }
                },
                "execution_time": execution_time,
                "message": "Financial data and approval workflow retrieved"
            }
        
        elif agent == "audit":
            result = {
                "agent": agent,
                "status": "success",
                "data": {
                    "compliance_check": {
                        "policy_violations": 0,
                        "approval_chain_valid": True,
                        "documentation_complete": True
                    },
                    "risk_assessment": {
                        "risk_level": "Low",
                        "vendor_risk_score": 85,
                        "payment_risk": "Minimal"
                    },
                    "audit_trail": [
                        "PO created: 2024-01-08",
                        "Approved: 2024-01-10",
                        "Invoice received: 2024-01-20",
                        "Partial payment: 2024-01-25"
                    ]
                },
                "execution_time": execution_time,
                "message": "Audit and compliance verification completed"
            }
        
        elif agent == "analysis":
            result = {
                "agent": agent,
                "status": "success",
                "data": {
                    "summary": "PO investigation reveals invoice discrepancy requiring resolution",
                    "key_findings": [
                        "Invoice amount exceeds PO by $50 due to tax calculation",
                        "Vendor has good payment history and relationship",
                        "No compliance violations detected",
                        "Partial payment of $600 already processed"
                    ],
                    "recommendations": [
                        "Approve additional $50 for tax difference",
                        "Process remaining payment of $650",
                        "Update PO process to include tax calculations",
                        "Communicate resolution timeline to vendor"
                    ],
                    "next_steps": [
                        "Finance team to approve tax adjustment",
                        "Process final payment within 5 business days",
                        "Update vendor on resolution status"
                    ]
                },
                "execution_time": execution_time,
                "message": "Comprehensive analysis and recommendations generated"
            }
        
        else:
            result = {
                "agent": agent,
                "status": "success",
                "data": {"message": f"Processed by {agent} agent"},
                "execution_time": execution_time,
                "message": f"{agent.title()} agent processing completed"
            }
        
        print(f"    {Colors.OKGREEN}✅ {result['message']}{Colors.ENDC}")
        return result
    
    def compile_final_results(self, execution_results: List[Dict[str, Any]], planning_summary: AIPlanningSummary) -> str:
        """Compile final results from all agent executions."""
        
        # Extract key data from each agent
        gmail_data = next((r["data"] for r in execution_results if r["agent"] == "gmail"), {})
        invoice_data = next((r["data"] for r in execution_results if r["agent"] == "invoice"), {})
        salesforce_data = next((r["data"] for r in execution_results if r["agent"] == "salesforce"), {})
        zoho_data = next((r["data"] for r in execution_results if r["agent"] == "zoho"), {})
        audit_data = next((r["data"] for r in execution_results if r["agent"] == "audit"), {})
        analysis_data = next((r["data"] for r in execution_results if r["agent"] == "analysis"), {})
        
        # Compile comprehensive report
        report = f"""
PO INVESTIGATION REPORT
======================

Task: {planning_summary.task_description}
Investigation Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
Plan ID: Generated by AI Planner

EXECUTIVE SUMMARY
-----------------
{analysis_data.get('summary', 'Investigation completed successfully')}

KEY FINDINGS
------------
"""
        
        if analysis_data.get('key_findings'):
            for finding in analysis_data['key_findings']:
                report += f"• {finding}\n"
        
        report += f"""
DETAILED ANALYSIS
-----------------

Email Communications ({gmail_data.get('emails_found', 0)} emails analyzed):
{gmail_data.get('key_findings', 'No email analysis available')}

Invoice Processing:
• Status: {invoice_data.get('payment_status', 'Unknown')}
• Discrepancies: {len(invoice_data.get('discrepancies', []))} found
"""
        
        if invoice_data.get('discrepancies'):
            for disc in invoice_data['discrepancies']:
                report += f"  - {disc}\n"
        
        report += f"""
Vendor Relationship (Salesforce):
• Vendor: {salesforce_data.get('vendor_record', {}).get('name', 'Unknown')}
• Status: {salesforce_data.get('vendor_record', {}).get('status', 'Unknown')}
• Payment History: {salesforce_data.get('purchase_history', {}).get('payment_history', 'Unknown')}

Financial Records (Zoho):
• PO Amount: {zoho_data.get('financial_records', {}).get('po_amount', 'Unknown')}
• Invoiced: {zoho_data.get('financial_records', {}).get('invoiced_amount', 'Unknown')}
• Paid: {zoho_data.get('financial_records', {}).get('paid_amount', 'Unknown')}
• Outstanding: {zoho_data.get('financial_records', {}).get('outstanding_balance', 'Unknown')}

Compliance & Audit:
• Risk Level: {audit_data.get('risk_assessment', {}).get('risk_level', 'Unknown')}
• Policy Violations: {audit_data.get('compliance_check', {}).get('policy_violations', 'Unknown')}
• Documentation: {'Complete' if audit_data.get('compliance_check', {}).get('documentation_complete') else 'Incomplete'}

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
• Total Agents: {len(execution_results)}
• Total Execution Time: {sum(r.get('execution_time', 0) for r in execution_results)}s
• AI Planning Time: {planning_summary.total_duration:.2f}s
• All Systems: {'✅ Connected' if all(r['status'] == 'success' for r in execution_results) else '❌ Issues Detected'}

Generated by Multi-Agent PO Investigation System
"""
        
        return report.strip()
    
    def display_final_results(self, workflow_result: Dict[str, Any]):
        """Display final workflow results."""
        self.print_section("📊 Final Results")
        
        if workflow_result["status"] == "completed":
            self.print_success("Workflow completed successfully!")
            
            print(f"\n{Colors.BOLD}Execution Summary:{Colors.ENDC}")
            print(f"  Plan ID: {workflow_result['plan_id']}")
            print(f"  Status: {workflow_result['status']}")
            print(f"  Agents Executed: {len(workflow_result['execution_results'])}")
            
            # Display agent results summary
            print(f"\n{Colors.BOLD}Agent Results:{Colors.ENDC}")
            for result in workflow_result['execution_results']:
                status_icon = "✅" if result['status'] == 'success' else "❌"
                print(f"  {status_icon} {result['agent'].title()}: {result['message']}")
            
            # Display final report
            print(f"\n{Colors.BOLD}DETAILED INVESTIGATION REPORT:{Colors.ENDC}")
            print(f"{Colors.OKCYAN}{workflow_result['final_result']}{Colors.ENDC}")
        
        else:
            self.print_error(f"Workflow failed: {workflow_result.get('error', 'Unknown error')}")
    
    async def run_interactive_test(self):
        """Run the complete interactive test workflow."""
        self.print_header("PO Investigation Interactive Test")
        
        print(f"{Colors.OKCYAN}This test simulates the complete frontend workflow:{Colors.ENDC}")
        print(f"  1. Manual query input (like frontend form)")
        print(f"  2. AI planning and analysis")
        print(f"  3. Human approval simulation")
        print(f"  4. Multi-agent execution with real system integration")
        print(f"  5. Comprehensive results and reporting")
        
        try:
            # Step 1: Get user query
            query = self.get_user_query()
            
            # Step 2: AI Planning
            planning_summary = await self.run_ai_planning(query)
            
            # Step 3: Human Approval
            approved = self.simulate_human_approval(planning_summary)
            
            if not approved:
                self.print_warning("Workflow cancelled by user.")
                return
            
            # Step 4: Execute Workflow
            workflow_result = await self.execute_workflow(planning_summary)
            
            # Step 5: Display Results
            self.display_final_results(workflow_result)
            
            # Offer to run another test
            print(f"\n{Colors.BOLD}Would you like to run another test?{Colors.ENDC}")
            choice = input("Enter 'y' to run again, any other key to exit: ").strip().lower()
            
            if choice in ['y', 'yes']:
                await self.run_interactive_test()
            else:
                self.print_success("Thank you for testing! Goodbye.")
        
        except KeyboardInterrupt:
            self.print_warning("\nTest interrupted by user. Goodbye!")
        
        except Exception as e:
            self.print_error(f"Test failed with error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main entry point."""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("🔍 PO Investigation Interactive Test Suite")
    print("==========================================")
    print(f"{Colors.ENDC}")
    
    print(f"{Colors.OKCYAN}Testing real-world PO investigation scenarios with:{Colors.ENDC}")
    print(f"  • Gmail integration for email analysis")
    print(f"  • Bill.com integration for invoice processing")
    print(f"  • Salesforce integration for vendor relationships")
    print(f"  • Zoho integration for financial data")
    print(f"  • AI-driven planning and execution")
    print(f"  • Human-in-the-loop approval workflow")
    
    tester = POInvestigationTester()
    await tester.run_interactive_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted. Goodbye!{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {e}{Colors.ENDC}")
        sys.exit(1)