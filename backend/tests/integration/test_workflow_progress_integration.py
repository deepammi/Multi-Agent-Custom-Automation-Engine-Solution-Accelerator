"""
Integration test for workflow progress display functionality.
Tests the end-to-end workflow progress updates from backend to frontend.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.agent_coordinator import AgentCoordinator, CoordinationStrategy
from app.models.ai_planner import AgentSequence, TaskAnalysis
from app.agents.state import AgentState


class MockWebSocketManager:
    """Mock WebSocket manager for testing."""
    
    def __init__(self):
        self.messages = []
        self.connections = {}
    
    async def send_message(self, plan_id: str, message: dict):
        """Mock send message method."""
        self.messages.append({
            "plan_id": plan_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        print(f"📤 Mock WebSocket sent: {message['type']} for plan {plan_id}")


@pytest.mark.asyncio
class TestWorkflowProgressIntegration:
    """Test workflow progress integration."""
    
    def create_test_agent_sequence(self, agents: list) -> AgentSequence:
        """Create a test agent sequence with all required fields."""
        task_analysis = TaskAnalysis(
            task_type="multi_agent_workflow",
            complexity="medium",
            estimated_duration=300,
            required_agents=agents,
            dependencies=[]
        )
        
        return AgentSequence(
            agents=agents,
            reasoning={agent: f"Agent {agent} is needed for processing" for agent in agents},
            estimated_duration=300,
            complexity_score=0.5,
            task_analysis=task_analysis
        )
    
    async def test_workflow_progress_updates(self):
        """Test that workflow progress updates are sent correctly."""
        # Setup
        coordinator = AgentCoordinator()
        mock_ws_manager = MockWebSocketManager()
        coordinator._websocket_manager = mock_ws_manager
        
        # Create test data
        plan_id = "test_progress_plan_123"
        session_id = "test_session_123"
        task_description = "Test multi-agent workflow with progress tracking"
        
        agent_sequence = self.create_test_agent_sequence(["Gmail", "Accounts_Payable", "CRM", "Analysis"])
        state = AgentState(
            plan_id=plan_id,
            session_id=session_id,
            task_description=task_description
        )
        
        # Execute coordination
        result = await coordinator.coordinate_dynamic_execution(
            plan_id=plan_id,
            session_id=session_id,
            task_description=task_description,
            agent_sequence=agent_sequence,
            state=state,
            coordination_strategy=CoordinationStrategy.SEQUENTIAL
        )
        
        # Verify execution result
        assert result["status"] == "completed"
        assert result["plan_id"] == plan_id
        assert result["total_agents"] == 4
        assert result["successful_agents"] == 4
        assert len(result["execution_results"]) == 4
        
        # Verify progress messages were sent
        progress_messages = [msg for msg in mock_ws_manager.messages 
                           if msg["message"]["type"] == "workflow_progress_update"]
        
        # Should have initial + 4 agent updates + final completion = 6 messages
        assert len(progress_messages) >= 5, f"Expected at least 5 progress messages, got {len(progress_messages)}"
        
        # Verify initial progress message
        initial_msg = progress_messages[0]["message"]["data"]
        assert initial_msg["plan_id"] == plan_id
        assert initial_msg["progress_percentage"] == 0.0
        assert initial_msg["current_agent"] == "Gmail"
        assert initial_msg["completed_agents"] == []
        assert len(initial_msg["pending_agents"]) == 4
        
        # Verify final completion message
        final_msg = progress_messages[-1]["message"]["data"]
        assert final_msg["plan_id"] == plan_id
        assert final_msg["progress_percentage"] == 100.0
        assert final_msg["current_stage"] == "completed"
        assert final_msg["current_agent"] is None
        assert len(final_msg["completed_agents"]) == 4
        assert len(final_msg["pending_agents"]) == 0
        
        # Verify progress increases over time
        percentages = [msg["message"]["data"]["progress_percentage"] for msg in progress_messages]
        for i in range(1, len(percentages)):
            assert percentages[i] >= percentages[i-1], "Progress should be non-decreasing"
        
        print("✅ Workflow progress integration test passed")
    
    async def test_workflow_progress_message_format(self):
        """Test that progress messages match frontend expectations."""
        # Setup
        coordinator = AgentCoordinator()
        mock_ws_manager = MockWebSocketManager()
        coordinator._websocket_manager = mock_ws_manager
        
        # Create minimal test data
        plan_id = "test_format_plan_456"
        agent_sequence = self.create_test_agent_sequence(["Gmail", "Analysis"])
        state = AgentState(plan_id=plan_id, session_id="test_session")
        
        # Execute coordination
        await coordinator.coordinate_dynamic_execution(
            plan_id=plan_id,
            session_id="test_session",
            task_description="Test message format",
            agent_sequence=agent_sequence,
            state=state
        )
        
        # Get a progress message
        progress_messages = [msg for msg in mock_ws_manager.messages 
                           if msg["message"]["type"] == "workflow_progress_update"]
        assert len(progress_messages) > 0
        
        # Verify message structure matches frontend expectations
        msg_data = progress_messages[0]["message"]["data"]
        
        # Required fields for WorkflowProgressUpdate interface
        required_fields = [
            "plan_id", "current_stage", "progress_percentage", 
            "completed_agents", "pending_agents"
        ]
        
        for field in required_fields:
            assert field in msg_data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(msg_data["plan_id"], str)
        assert isinstance(msg_data["current_stage"], str)
        assert isinstance(msg_data["progress_percentage"], (int, float))
        assert isinstance(msg_data["completed_agents"], list)
        assert isinstance(msg_data["pending_agents"], list)
        
        # Verify stage values are valid
        valid_stages = [
            "plan_creation", "plan_approval", "gmail_execution", 
            "ap_execution", "crm_execution", "analysis_execution",
            "results_compilation", "final_approval", "completed"
        ]
        assert msg_data["current_stage"] in valid_stages
        
        print("✅ Workflow progress message format test passed")
    
    async def test_workflow_progress_stage_mapping(self):
        """Test that agent names are correctly mapped to stages."""
        coordinator = AgentCoordinator()
        
        # Test stage mapping
        test_cases = [
            ("Gmail", 0, 4, "gmail_execution"),
            ("Accounts_Payable", 1, 4, "ap_execution"),
            ("CRM", 2, 4, "crm_execution"),
            ("Analysis", 3, 4, "analysis_execution"),
            ("Unknown_Agent", 0, 2, "gmail_execution"),  # Fallback
        ]
        
        for agent_name, index, total, expected_stage in test_cases:
            stage = coordinator._get_stage_for_agent(agent_name, index, total)
            assert stage == expected_stage, f"Agent {agent_name} at index {index} should map to {expected_stage}, got {stage}"
        
        print("✅ Workflow progress stage mapping test passed")


if __name__ == "__main__":
    # Run tests directly
    async def run_tests():
        test_instance = TestWorkflowProgressIntegration()
        await test_instance.test_workflow_progress_updates()
        await test_instance.test_workflow_progress_message_format()
        await test_instance.test_workflow_progress_stage_mapping()
        print("🎉 All workflow progress tests passed!")
    
    asyncio.run(run_tests())