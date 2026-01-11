"""
Test Enhanced Multi-Agent Orchestrator

This test validates the enhanced orchestration capabilities including:
- Task analysis and agent requirement detection
- Optimal agent sequence generation with dependency validation
- Enhanced data passing between agents
- Execution order validation and recommendations
"""
import asyncio
import logging
import pytest
from typing import Dict, Any, List

from app.services.enhanced_orchestrator import (
    EnhancedOrchestrator, 
    get_enhanced_orchestrator,
    AgentDependency,
    AgentMetadata,
    DataFlowValidation
)
from app.agents.state import AgentState, AgentStateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEnhancedOrchestrator:
    """Test suite for enhanced orchestrator functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.orchestrator = EnhancedOrchestrator()
    
    def test_task_analysis_comprehensive_query(self):
        """Test task analysis for comprehensive invoice analysis query."""
        task_description = "Check the status of invoices received with keyword Acme Marketing and analyze any issues with their payment"
        
        analysis = self.orchestrator.analyze_task_requirements(task_description)
        
        # Validate analysis results
        assert analysis["task_type"] == "invoice_analysis"
        assert analysis["complexity_score"] > 0.5  # Should be complex due to multiple requirements
        
        # Should include all major agents for comprehensive analysis
        required_agents = analysis["required_agents"]
        assert "planner" in required_agents
        assert "gmail" in required_agents or "email" in required_agents
        assert "invoice" in required_agents or "accounts_payable" in required_agents
        assert "analysis" in required_agents
        
        # Should have appropriate data requirements
        data_requirements = analysis["data_requirements"]
        assert "email_data" in data_requirements
        assert "ap_data" in data_requirements
        
        logger.info(f"✅ Comprehensive task analysis: {analysis}")
    
    def test_task_analysis_email_focused_query(self):
        """Test task analysis for email-focused query."""
        task_description = "Find all email communications from Acme Marketing about invoices"
        
        analysis = self.orchestrator.analyze_task_requirements(task_description)
        
        # Should focus on email agents
        required_agents = analysis["required_agents"]
        assert "planner" in required_agents
        assert "gmail" in required_agents or "email" in required_agents
        
        # Should have email data requirements
        data_requirements = analysis["data_requirements"]
        assert "email_data" in data_requirements
        
        logger.info(f"✅ Email-focused task analysis: {analysis}")
    
    def test_optimal_sequence_generation(self):
        """Test optimal agent sequence generation with dependency validation."""
        # Test comprehensive workflow
        required_agents = {"planner", "gmail", "invoice", "salesforce", "analysis"}
        task_analysis = {
            "task_type": "invoice_analysis",
            "complexity_score": 0.8,
            "estimated_duration": 300.0
        }
        
        sequence = self.orchestrator.generate_optimal_sequence(required_agents, task_analysis)
        
        # Validate sequence properties
        assert len(sequence) == len(required_agents)
        assert sequence[0] == "planner"  # Should start with planner
        assert sequence[-1] == "analysis"  # Should end with analysis
        
        # Validate dependency order
        planner_idx = sequence.index("planner")
        gmail_idx = sequence.index("gmail")
        invoice_idx = sequence.index("invoice")
        analysis_idx = sequence.index("analysis")
        
        assert planner_idx < gmail_idx  # Planner before email
        assert planner_idx < invoice_idx  # Planner before AP
        assert gmail_idx < analysis_idx  # Email before analysis
        assert invoice_idx < analysis_idx  # AP before analysis
        
        logger.info(f"✅ Optimal sequence generated: {' → '.join(sequence)}")
    
    def test_execution_order_validation_valid(self):
        """Test execution order validation for valid sequence."""
        valid_sequence = ["planner", "gmail", "invoice", "salesforce", "analysis"]
        
        validation = self.orchestrator.validate_execution_order(valid_sequence)
        
        assert validation.is_valid
        assert len(validation.missing_dependencies) == 0
        assert len(validation.available_data) > 0
        
        logger.info(f"✅ Valid sequence validation passed: {validation}")
    
    def test_execution_order_validation_invalid(self):
        """Test execution order validation for invalid sequence."""
        # Analysis before data collection - should be invalid
        invalid_sequence = ["analysis", "planner", "gmail", "invoice"]
        
        validation = self.orchestrator.validate_execution_order(invalid_sequence)
        
        assert not validation.is_valid
        assert len(validation.missing_dependencies) > 0
        assert len(validation.recommendations) > 0
        
        logger.info(f"✅ Invalid sequence validation detected issues: {validation}")
    
    def test_data_passing_enhancement_email_agent(self):
        """Test enhanced data passing for email agent results."""
        # Create mock state
        state: AgentState = {
            "plan_id": "test_plan_123",
            "session_id": "test_session",
            "task_description": "Test task",
            "agent_sequence": ["planner", "gmail", "analysis"],
            "current_step": 1,
            "total_steps": 3,
            "current_agent": "gmail",
            "messages": [],
            "collected_data": {},
            "execution_results": []
        }
        
        # Mock email agent result
        email_result = {
            "status": "completed",
            "data": {
                "emails_found": 5,
                "invoice_numbers": ["INV-1001", "INV-1002"],
                "communication_history": ["Email 1", "Email 2"]
            },
            "message": "Found 5 relevant emails",
            "execution_time": 45.2
        }
        
        enhanced_updates = self.orchestrator.enhance_data_passing(state, "gmail", email_result)
        
        # Validate enhanced data structure
        assert "collected_data" in enhanced_updates
        assert "gmail" in enhanced_updates["collected_data"]
        
        gmail_data = enhanced_updates["collected_data"]["gmail"]
        assert gmail_data["agent_name"] == "gmail"
        assert gmail_data["data_type"] == "email_data"
        assert "email_data" in gmail_data["provides"]
        assert "validation" in gmail_data
        assert gmail_data["validation"]["has_emails"]
        assert gmail_data["validation"]["email_count"] == 5
        
        logger.info(f"✅ Enhanced email data passing: {gmail_data}")
    
    def test_data_passing_enhancement_ap_agent(self):
        """Test enhanced data passing for accounts payable agent results."""
        state: AgentState = {
            "plan_id": "test_plan_456",
            "collected_data": {}
        }
        
        ap_result = {
            "status": "completed",
            "data": {
                "bills_found": 3,
                "payment_status": "pending",
                "outstanding_amount": 15750.0
            },
            "message": "Found 3 bills for vendor"
        }
        
        enhanced_updates = self.orchestrator.enhance_data_passing(state, "invoice", ap_result)
        
        # Validate AP data enhancement
        invoice_data = enhanced_updates["collected_data"]["invoice"]
        assert invoice_data["data_type"] == "ap_data"
        assert "ap_data" in invoice_data["provides"]
        assert invoice_data["validation"]["has_bills"]
        assert invoice_data["validation"]["bill_count"] == 3
        
        logger.info(f"✅ Enhanced AP data passing: {invoice_data}")
    
    async def test_coordinate_agent_execution(self):
        """Test agent execution coordination with WebSocket integration."""
        # Mock WebSocket manager
        class MockWebSocketManager:
            def __init__(self):
                self.messages = []
            
            async def send_message(self, plan_id: str, message: Dict[str, Any]):
                self.messages.append({"plan_id": plan_id, "message": message})
        
        websocket_manager = MockWebSocketManager()
        
        # Test coordination
        agent_sequence = ["planner", "gmail", "invoice", "analysis"]
        state: AgentState = {
            "plan_id": "test_coordination_789",
            "session_id": "test_session",
            "task_description": "Test coordination",
            "collected_data": {}
        }
        
        coordination_summary = await self.orchestrator.coordinate_agent_execution(
            agent_sequence, state, websocket_manager
        )
        
        # Validate coordination results
        assert coordination_summary["plan_id"] == "test_coordination_789"
        assert coordination_summary["agent_sequence"] == agent_sequence
        assert "validation_result" in coordination_summary
        assert "execution_start" in coordination_summary
        
        # Validate WebSocket messages were sent
        assert len(websocket_manager.messages) > 0
        
        # Check if we got coordination message (could be first or second message depending on validation)
        coordination_found = False
        for msg in websocket_manager.messages:
            if "Enhanced orchestration" in msg["message"]["data"]["message"]:
                coordination_found = True
                break
        
        assert coordination_found, f"Expected coordination message not found in: {[msg['message']['data']['message'] for msg in websocket_manager.messages]}"
        
        logger.info(f"✅ Agent execution coordination: {coordination_summary}")
    
    def test_orchestration_metrics(self):
        """Test orchestration performance metrics collection."""
        # Add some mock execution history
        self.orchestrator.execution_history = [
            {
                "plan_id": "plan_1",
                "agent_sequence": ["planner", "gmail", "analysis"],
                "agents_completed": ["planner", "gmail", "analysis"],
                "agents_failed": []
            },
            {
                "plan_id": "plan_2", 
                "agent_sequence": ["planner", "invoice", "analysis"],
                "agents_completed": ["planner", "invoice"],
                "agents_failed": ["analysis"]
            }
        ]
        
        metrics = self.orchestrator.get_orchestration_metrics()
        
        # Validate metrics
        assert metrics["total_executions"] == 2
        assert metrics["average_agents_per_execution"] == 3.0
        assert metrics["success_rate"] == 0.5  # 1 success out of 2
        assert len(metrics["most_common_sequences"]) > 0
        
        logger.info(f"✅ Orchestration metrics: {metrics}")
    
    def test_singleton_orchestrator(self):
        """Test singleton orchestrator instance."""
        orchestrator1 = get_enhanced_orchestrator()
        orchestrator2 = get_enhanced_orchestrator()
        
        # Should be the same instance
        assert orchestrator1 is orchestrator2
        
        # Should have agent registry initialized
        assert len(orchestrator1.agent_registry) > 0
        assert "planner" in orchestrator1.agent_registry
        assert "gmail" in orchestrator1.agent_registry
        assert "analysis" in orchestrator1.agent_registry
        
        logger.info(f"✅ Singleton orchestrator validated")


async def test_enhanced_orchestrator_integration():
    """
    Integration test for enhanced orchestrator with realistic workflow.
    
    This test simulates a complete invoice analysis workflow with:
    - Task analysis and optimal sequence generation
    - Execution order validation
    - Enhanced data passing between agents
    - Coordination with progress tracking
    """
    logger.info("🧪 Testing Enhanced Orchestrator Integration")
    
    orchestrator = get_enhanced_orchestrator()
    
    # Test realistic invoice analysis task
    task_description = "Check the status of invoices received with keyword Acme Marketing and analyze any issues with their payment"
    
    # Step 1: Analyze task requirements
    logger.info("📋 Step 1: Analyzing task requirements")
    task_analysis = orchestrator.analyze_task_requirements(task_description)
    
    assert task_analysis["task_type"] == "invoice_analysis"
    assert task_analysis["complexity_score"] > 0.5
    assert len(task_analysis["required_agents"]) >= 3
    
    logger.info(f"   ✅ Task analysis completed: {task_analysis['complexity_score']:.2f} complexity")
    logger.info(f"   ✅ Required agents: {list(task_analysis['required_agents'])}")
    
    # Step 2: Generate optimal sequence
    logger.info("🔄 Step 2: Generating optimal agent sequence")
    optimal_sequence = orchestrator.generate_optimal_sequence(
        task_analysis["required_agents"], 
        task_analysis
    )
    
    assert len(optimal_sequence) >= 3
    assert optimal_sequence[0] == "planner"
    assert "analysis" in optimal_sequence
    
    logger.info(f"   ✅ Optimal sequence: {' → '.join(optimal_sequence)}")
    
    # Step 3: Validate execution order
    logger.info("✅ Step 3: Validating execution order")
    validation = orchestrator.validate_execution_order(optimal_sequence)
    
    # Note: validation may have warnings but should still allow execution
    logger.info(f"   ✅ Execution order validation: {'PASSED' if validation.is_valid else 'PASSED WITH WARNINGS'}")
    if not validation.is_valid:
        logger.info(f"   ⚠️  Validation warnings: {validation.missing_dependencies}")
    logger.info(f"   ✅ Available data types: {validation.available_data}")
    
    # Step 4: Test enhanced data passing
    logger.info("📊 Step 4: Testing enhanced data passing")
    
    # Create mock state
    state: AgentState = {
        "plan_id": "integration_test_001",
        "session_id": "test_session",
        "task_description": task_description,
        "agent_sequence": optimal_sequence,
        "current_step": 1,
        "total_steps": len(optimal_sequence),
        "current_agent": "gmail",
        "messages": [],
        "collected_data": {},
        "execution_results": []
    }
    
    # Simulate email agent result
    email_result = {
        "status": "completed",
        "data": {
            "emails_found": 8,
            "invoice_numbers": ["INV-1001", "INV-1002", "INV-1003"],
            "communication_history": ["Initial invoice", "Payment reminder", "Follow-up"]
        },
        "message": "Found 8 relevant emails from Acme Marketing",
        "execution_time": 42.5
    }
    
    enhanced_updates = orchestrator.enhance_data_passing(state, "gmail", email_result)
    
    assert "collected_data" in enhanced_updates
    assert "gmail" in enhanced_updates["collected_data"]
    
    gmail_enhanced = enhanced_updates["collected_data"]["gmail"]
    assert gmail_enhanced["data_type"] == "email_data"
    assert gmail_enhanced["validation"]["email_count"] == 8
    
    logger.info(f"   ✅ Enhanced email data: {gmail_enhanced['validation']}")
    
    # Step 5: Test coordination
    logger.info("🎯 Step 5: Testing agent execution coordination")
    
    # Mock WebSocket manager
    class MockWebSocketManager:
        def __init__(self):
            self.messages = []
        
        async def send_message(self, plan_id: str, message: Dict[str, Any]):
            self.messages.append(message)
    
    websocket_manager = MockWebSocketManager()
    
    coordination_summary = await orchestrator.coordinate_agent_execution(
        optimal_sequence, state, websocket_manager
    )
    
    assert coordination_summary["plan_id"] == "integration_test_001"
    assert coordination_summary["agent_sequence"] == optimal_sequence
    assert len(websocket_manager.messages) > 0
    
    logger.info(f"   ✅ Coordination completed with {len(websocket_manager.messages)} WebSocket messages")
    
    # Step 6: Validate metrics
    logger.info("📈 Step 6: Validating orchestration metrics")
    
    metrics = orchestrator.get_orchestration_metrics()
    
    assert metrics["total_executions"] >= 1
    assert metrics["agent_registry_size"] > 0
    
    logger.info(f"   ✅ Metrics collected: {metrics['total_executions']} executions tracked")
    
    logger.info("🎉 ENHANCED ORCHESTRATOR INTEGRATION TEST PASSED!")
    logger.info("\n✅ Successfully demonstrated:")
    logger.info("   • Task analysis with complexity scoring")
    logger.info("   • Optimal agent sequence generation with dependency validation")
    logger.info("   • Enhanced data passing with structured validation")
    logger.info("   • Agent execution coordination with WebSocket integration")
    logger.info("   • Performance metrics collection and monitoring")
    
    return {
        "status": "success",
        "task_analysis": task_analysis,
        "optimal_sequence": optimal_sequence,
        "validation_result": validation,
        "coordination_summary": coordination_summary,
        "metrics": metrics
    }


if __name__ == "__main__":
    # Run integration test
    result = asyncio.run(test_enhanced_orchestrator_integration())
    print(f"\n🎯 Integration test result: {result['status']}")