"""
Test Task 13: Error Handling and Recovery
Tests minimal error handling with graceful failure messages and restart workflow functionality.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.agent_coordinator import AgentCoordinator, AgentExecutionStatus
from app.models.ai_planner import AgentSequence, TaskAnalysis
from app.agents.state import AgentState


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery functionality."""
    
    @pytest.fixture
    def agent_coordinator(self):
        """Create agent coordinator instance."""
        coordinator = AgentCoordinator()
        # Mock websocket manager to avoid connection issues
        coordinator._websocket_manager = AsyncMock()
        return coordinator
    
    @pytest.fixture
    def sample_task_analysis(self):
        """Create sample task analysis."""
        return TaskAnalysis(
            task_type="invoice_processing",
            complexity_level="medium",
            required_agents=["Gmail", "Accounts_Payable", "CRM"],
            estimated_duration=300,
            dependencies=[]
        )
    
    @pytest.fixture
    def sample_agent_sequence(self, sample_task_analysis):
        """Create sample agent sequence."""
        return AgentSequence(
            agents=["Gmail", "Accounts_Payable", "CRM"],
            reasoning={
                "Gmail": "Extract invoice from email",
                "Accounts_Payable": "Process invoice data",
                "CRM": "Update customer records"
            },
            estimated_duration=300,
            complexity_score=0.7,
            task_analysis=sample_task_analysis
        )
    
    @pytest.fixture
    def sample_state(self):
        """Create sample agent state."""
        return AgentState(
            plan_id="test-plan-123",
            session_id="test-session-456",
            task_description="Test task",
            messages=[],
            context={}
        )
    
    @pytest.mark.asyncio
    async def test_send_workflow_error_method(self, agent_coordinator):
        """Test the _send_workflow_error method directly."""
        plan_id = "test-plan-123"
        error_message = "Test error message"
        error_title = "Test Error Title"
        
        await agent_coordinator._send_workflow_error(
            plan_id=plan_id,
            error_message=error_message,
            error_title=error_title
        )
        
        # Verify WebSocket message was sent
        agent_coordinator.websocket_manager.send_message.assert_called_once()
        call_args = agent_coordinator.websocket_manager.send_message.call_args
        
        assert call_args[0][0] == plan_id
        message = call_args[0][1]
        assert message["type"] == "workflow_error"
        assert message["data"]["plan_id"] == plan_id
        assert message["data"]["title"] == error_title
        assert error_message in message["data"]["message"]
    
    @pytest.mark.asyncio
    async def test_graceful_error_handling_no_crash(self, agent_coordinator):
        """Test that error handling doesn't crash when WebSocket fails."""
        plan_id = "test-plan-123"
        error_message = "Test error"
        
        # Mock WebSocket to raise exception
        agent_coordinator.websocket_manager.send_message = AsyncMock(side_effect=Exception("WebSocket failed"))
        
        # Should not raise exception - error should be logged and handled gracefully
        await agent_coordinator._send_workflow_error(
            plan_id=plan_id,
            error_message=error_message
        )
        
        # Verify WebSocket was attempted
        agent_coordinator.websocket_manager.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_message_format(self, agent_coordinator):
        """Test that error messages are properly formatted."""
        plan_id = "test-plan-123"
        error_message = "Agent execution failed"
        error_title = "Custom Error Title"
        
        await agent_coordinator._send_workflow_error(
            plan_id=plan_id,
            error_message=error_message,
            error_title=error_title
        )
        
        call_args = agent_coordinator.websocket_manager.send_message.call_args
        message_data = call_args[0][1]["data"]
        
        # Check message format
        expected_message = f"The workflow encountered an error: {error_message}. Please start a new task to continue."
        assert message_data["message"] == expected_message
        assert message_data["title"] == error_title
        assert "timestamp" in message_data
    
    @pytest.mark.asyncio
    async def test_default_error_title(self, agent_coordinator):
        """Test that default error title is used when not provided."""
        plan_id = "test-plan-123"
        error_message = "Test error"
        
        await agent_coordinator._send_workflow_error(
            plan_id=plan_id,
            error_message=error_message
        )
        
        call_args = agent_coordinator.websocket_manager.send_message.call_args
        message_data = call_args[0][1]["data"]
        
        assert message_data["title"] == "Workflow Error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])