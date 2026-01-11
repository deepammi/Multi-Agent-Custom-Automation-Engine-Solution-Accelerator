"""
Test enhanced Human-in-the-Loop (HITL) process implementation.

This test validates the enhanced plan approval workflow with improved presentation
formats, plan modification capabilities, and comprehensive workflow logging.
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.hitl_interface import (
    HITLInterface, 
    ApprovalStatus, 
    ModificationType,
    PlanModification,
    EnhancedPlanPresentation
)
from app.services.workflow_logger import get_workflow_logger, reset_workflow_logger
from app.models.ai_planner import AgentSequence, TaskAnalysis


class MockWebSocketManager:
    """Mock WebSocket manager for testing."""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, plan_id: str, message: dict):
        """Mock send message method."""
        self.messages.append({
            "plan_id": plan_id,
            "message": message,
            "timestamp": datetime.utcnow()
        })


class TestEnhancedHITLProcess:
    """Test enhanced HITL process functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Reset workflow logger for clean test state
        reset_workflow_logger()
        
        # Create HITL interface
        self.hitl = HITLInterface(default_timeout=5)  # Short timeout for testing
        
        # Create mock WebSocket manager
        self.websocket_manager = MockWebSocketManager()
        
        # Create test task analysis
        self.test_task_analysis = TaskAnalysis(
            complexity="medium",
            required_systems=["email", "crm", "erp"],
            business_context="Invoice analysis workflow",
            data_sources_needed=["emails", "billing_data", "customer_data"],
            estimated_agents=["gmail", "invoice", "salesforce", "analysis"],
            confidence_score=0.85,
            reasoning="Multi-system invoice analysis requires email, AP, and CRM data"
        )
        
        # Create test agent sequence
        self.test_sequence = AgentSequence(
            agents=["gmail", "invoice", "salesforce", "analysis"],
            reasoning={
                "gmail": "Search for invoice-related emails",
                "invoice": "Retrieve bill and payment data",
                "salesforce": "Get customer relationship data",
                "analysis": "Generate comprehensive analysis"
            },
            estimated_duration=120,
            complexity_score=0.7,
            task_analysis=self.test_task_analysis
        )
    
    @pytest.mark.asyncio
    async def test_enhanced_plan_presentation(self):
        """Test enhanced plan presentation format."""
        print("\n🧪 Testing Enhanced Plan Presentation")
        
        # Create enhanced presentation
        presentation = EnhancedPlanPresentation(
            plan_id="test-plan-001",
            task_description="Analyze invoices for Acme Marketing",
            agent_sequence=self.test_sequence
        )
        
        # Get human-readable format
        human_readable = presentation.to_human_readable_format()
        
        # Validate presentation structure
        assert "plan_overview" in human_readable
        assert "execution_sequence" in human_readable
        assert "risk_assessment" in human_readable
        assert "resource_requirements" in human_readable
        assert "modification_options" in human_readable
        assert "approval_recommendations" in human_readable
        
        # Validate plan overview
        overview = human_readable["plan_overview"]
        assert overview["plan_id"] == "test-plan-001"
        assert overview["task_description"] == "Analyze invoices for Acme Marketing"
        assert overview["total_agents"] == 4
        assert overview["complexity_score"] == 0.7
        
        # Validate execution sequence
        sequence = human_readable["execution_sequence"]
        assert len(sequence) == 4
        assert sequence[0]["agent_name"] == "gmail"
        assert sequence[0]["step_number"] == 1
        assert "risk_level" in sequence[0]
        
        # Validate risk assessment
        risk = human_readable["risk_assessment"]
        assert "overall_risk" in risk
        assert "potential_issues" in risk
        assert "mitigation_strategies" in risk
        
        print(f"✅ Enhanced presentation created with {len(sequence)} agents")
        print(f"   Overall risk level: {risk['overall_risk']}")
        print(f"   Modification options: {len(human_readable['modification_options'])}")
    
    @pytest.mark.asyncio
    async def test_plan_approval_with_logging(self):
        """Test plan approval workflow with comprehensive logging."""
        print("\n🧪 Testing Plan Approval with Logging")
        
        plan_id = "test-plan-002"
        
        # Start approval request (this will run in background)
        approval_task = asyncio.create_task(
            self.hitl.request_plan_approval(
                plan_id=plan_id,
                agent_sequence=self.test_sequence,
                task_description="Test invoice analysis",
                websocket_manager=self.websocket_manager,
                timeout_seconds=2,  # Short timeout for testing
                reviewer_id="test-reviewer"
            )
        )
        
        # Wait a bit for the request to be processed
        await asyncio.sleep(0.1)
        
        # Verify approval request was logged
        workflow_logger = get_workflow_logger()
        logs = workflow_logger.get_logs_by_plan(plan_id)
        
        # Should have at least HITL_REQUEST and PLAN_APPROVAL logs
        assert len(logs) >= 2
        
        hitl_request_logs = [log for log in logs if log.event_type.value == "hitl_request"]
        assert len(hitl_request_logs) >= 1
        
        request_log = hitl_request_logs[0]
        assert request_log.plan_id == plan_id
        assert request_log.metadata.get("agent_count") == 4
        assert request_log.metadata.get("reviewer_id") == "test-reviewer"
        
        # Verify WebSocket message was sent
        assert len(self.websocket_manager.messages) >= 1
        
        ws_message = self.websocket_manager.messages[0]
        assert ws_message["plan_id"] == plan_id
        assert ws_message["message"]["type"] == "enhanced_plan_approval_request"
        assert "presentation" in ws_message["message"]["data"]
        
        # Submit approval response
        success = await self.hitl.submit_approval_response(
            plan_id=plan_id,
            approved=True,
            feedback="Plan looks good",
            reviewer_id="test-reviewer",
            approval_confidence="high"
        )
        
        assert success is True
        
        # Wait for approval task to complete
        result = await approval_task
        
        # Verify approval result
        assert result.approved is True
        assert result.status == ApprovalStatus.APPROVED
        assert result.feedback == "Plan looks good"
        assert result.reviewer_id == "test-reviewer"
        assert result.approval_confidence == "high"
        
        # Verify response was logged
        logs = workflow_logger.get_logs_by_plan(plan_id)
        response_logs = [log for log in logs if log.event_type.value == "hitl_response"]
        assert len(response_logs) >= 1
        
        response_log = response_logs[-1]  # Get the latest response log
        assert response_log.success is True
        assert response_log.metadata.get("reviewer_id") == "test-reviewer"
        assert response_log.metadata.get("approval_confidence") == "high"
        
        print(f"✅ Plan approval completed successfully")
        print(f"   Total logs generated: {len(logs)}")
        print(f"   Approval time: {result.timeout_seconds:.2f}s")
        print(f"   WebSocket messages sent: {len(self.websocket_manager.messages)}")
    
    @pytest.mark.asyncio
    async def test_plan_modification_workflow(self):
        """Test plan modification capabilities."""
        print("\n🧪 Testing Plan Modification Workflow")
        
        plan_id = "test-plan-003"
        
        # Start approval request
        approval_task = asyncio.create_task(
            self.hitl.request_plan_approval(
                plan_id=plan_id,
                agent_sequence=self.test_sequence,
                task_description="Test modification workflow",
                websocket_manager=self.websocket_manager,
                timeout_seconds=3
            )
        )
        
        await asyncio.sleep(0.1)
        
        # Create modifications
        modifications = [
            PlanModification(
                modification_type=ModificationType.AGENT_REMOVAL,
                description="Remove Salesforce agent to reduce complexity",
                original_value="salesforce",
                new_value=None,
                affected_agents=["salesforce"],
                justification="Salesforce data not critical for this analysis"
            ),
            PlanModification(
                modification_type=ModificationType.PARAMETER_CHANGE,
                description="Increase timeout for email search",
                original_value=30.0,
                new_value=60.0,
                affected_agents=["gmail"],
                justification="Need more time for comprehensive email search"
            )
        ]
        
        # Submit approval with modifications
        success = await self.hitl.submit_approval_response(
            plan_id=plan_id,
            approved=True,
            feedback="Approved with modifications",
            modifications=modifications,
            reviewer_id="test-reviewer",
            approval_confidence="medium"
        )
        
        assert success is True
        
        # Wait for approval task to complete
        result = await approval_task
        
        # Verify modification result
        assert result.approved is True
        assert result.status == ApprovalStatus.APPROVED  # Will be MODIFIED if modified_sequence provided
        assert len(result.modifications) == 2
        
        # Verify modifications were logged
        workflow_logger = get_workflow_logger()
        logs = workflow_logger.get_logs_by_plan(plan_id)
        
        modification_logs = [log for log in logs if log.event_type.value == "plan_modification"]
        assert len(modification_logs) >= 2  # One for validation, one for each modification
        
        # Check modification details in logs
        mod_log = modification_logs[-1]  # Get latest modification log
        assert mod_log.metadata.get("modification_type") in ["agent_removal", "parameter_change"]
        
        print(f"✅ Plan modification completed successfully")
        print(f"   Modifications applied: {len(result.modifications)}")
        print(f"   Modification logs: {len(modification_logs)}")
    
    @pytest.mark.asyncio
    async def test_approval_timeout_handling(self):
        """Test approval timeout handling with logging."""
        print("\n🧪 Testing Approval Timeout Handling")
        
        plan_id = "test-plan-timeout"
        
        # Start approval request with very short timeout
        result = await self.hitl.request_plan_approval(
            plan_id=plan_id,
            agent_sequence=self.test_sequence,
            task_description="Test timeout handling",
            websocket_manager=self.websocket_manager,
            timeout_seconds=0.1  # Very short timeout
        )
        
        # Verify timeout result
        assert result.approved is False
        assert result.status == ApprovalStatus.TIMEOUT
        assert result.timeout_seconds is not None
        assert result.timeout_seconds >= 0.1
        
        # Verify timeout was logged
        workflow_logger = get_workflow_logger()
        logs = workflow_logger.get_logs_by_plan(plan_id)
        
        # Should have request log but no response log (due to timeout)
        request_logs = [log for log in logs if log.event_type.value == "hitl_request"]
        assert len(request_logs) >= 1
        
        print(f"✅ Timeout handling working correctly")
        print(f"   Timeout after: {result.timeout_seconds:.3f}s")
        print(f"   Logs generated: {len(logs)}")
    
    def test_approval_statistics(self):
        """Test approval statistics and metrics."""
        print("\n🧪 Testing Approval Statistics")
        
        # Get initial stats
        initial_stats = self.hitl.get_approval_stats()
        assert initial_stats["total_requests"] == 0
        
        # Add some mock approval history
        from app.services.hitl_interface import ApprovalResult
        
        # Create mock approval results
        mock_results = [
            ApprovalResult("plan-1", ApprovalStatus.APPROVED, True, timeout_seconds=5.2),
            ApprovalResult("plan-2", ApprovalStatus.REJECTED, False, timeout_seconds=3.1),
            ApprovalResult("plan-3", ApprovalStatus.MODIFIED, True, timeout_seconds=8.7),
            ApprovalResult("plan-4", ApprovalStatus.TIMEOUT, False, timeout_seconds=300.0)
        ]
        
        # Add to approval history
        for i, result in enumerate(mock_results):
            plan_id = f"plan-{i+1}"
            self.hitl.approval_history[plan_id] = [result]
        
        # Get updated stats
        stats = self.hitl.get_approval_stats()
        
        assert stats["total_requests"] == 4
        assert stats["approved_requests"] == 1
        assert stats["rejected_requests"] == 1
        assert stats["modified_requests"] == 1
        assert stats["timeout_requests"] == 1
        assert stats["approval_rate"] == 25.0  # 1/4 * 100
        assert stats["modification_rate"] == 25.0  # 1/4 * 100
        assert stats["timeout_rate"] == 25.0  # 1/4 * 100
        assert stats["average_response_time"] > 0
        
        print(f"✅ Statistics calculated correctly")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Approval rate: {stats['approval_rate']}%")
        print(f"   Average response time: {stats['average_response_time']:.2f}s")
    
    def test_audit_trail_generation(self):
        """Test audit trail generation."""
        print("\n🧪 Testing Audit Trail Generation")
        
        plan_id = "audit-test-plan"
        
        # Add mock approval to history
        from app.services.hitl_interface import ApprovalResult
        mock_result = ApprovalResult(
            plan_id, 
            ApprovalStatus.APPROVED, 
            True, 
            feedback="Test approval",
            timeout_seconds=5.0,
            reviewer_id="test-auditor"
        )
        self.hitl.approval_history[plan_id] = [mock_result]
        
        # Add some workflow logs
        workflow_logger = get_workflow_logger()
        from app.services.workflow_logger import EventType
        workflow_logger.log_event(
            event_type=EventType.HITL_REQUEST,
            message="Test audit log",
            plan_id=plan_id,
            correlation_id="audit-test-corr"
        )
        
        # Get audit trail
        audit_trail = self.hitl.get_audit_trail(plan_id)
        
        assert audit_trail["plan_id"] == plan_id
        assert len(audit_trail["approval_history"]) == 1
        assert len(audit_trail["workflow_logs"]) >= 1
        assert audit_trail["pending_approval"]["exists"] is False
        assert audit_trail["summary"]["total_approvals"] == 1
        assert audit_trail["summary"]["total_log_entries"] >= 1
        
        # Verify approval history details
        approval_data = audit_trail["approval_history"][0]
        assert approval_data["approved"] is True
        assert approval_data["reviewer_id"] == "test-auditor"
        assert approval_data["feedback"] == "Test approval"
        
        print(f"✅ Audit trail generated successfully")
        print(f"   Approval records: {len(audit_trail['approval_history'])}")
        print(f"   Log entries: {len(audit_trail['workflow_logs'])}")


async def main():
    """Run enhanced HITL process tests."""
    print("🚀 Starting Enhanced HITL Process Tests")
    print("=" * 60)
    
    test_instance = TestEnhancedHITLProcess()
    
    try:
        # Run all tests
        test_instance.setup_method()
        await test_instance.test_enhanced_plan_presentation()
        
        test_instance.setup_method()
        await test_instance.test_plan_approval_with_logging()
        
        test_instance.setup_method()
        await test_instance.test_plan_modification_workflow()
        
        test_instance.setup_method()
        await test_instance.test_approval_timeout_handling()
        
        test_instance.setup_method()
        test_instance.test_approval_statistics()
        
        test_instance.setup_method()
        test_instance.test_audit_trail_generation()
        
        print("\n" + "=" * 60)
        print("✅ All Enhanced HITL Process Tests Passed!")
        
        # Get final workflow logger stats
        workflow_logger = get_workflow_logger()
        final_stats = workflow_logger.get_performance_summary()
        
        print(f"\n📊 Final Workflow Logger Statistics:")
        print(f"   Total log entries: {final_stats['total_log_entries']}")
        print(f"   Active correlations: {final_stats['active_correlations']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)