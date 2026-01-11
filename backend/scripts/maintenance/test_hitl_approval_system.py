"""
Tests for HITL Approval System implementation.

This module tests the Human-in-the-Loop approval functionality including
plan approval, result approval, WebSocket messaging, and state management.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from app.services.hitl_interface import (
    HITLInterface,
    ApprovalStatus,
    ApprovalResult,
    get_hitl_interface,
    reset_hitl_interface
)
from app.services.websocket_service import (
    WebSocketManager,
    MockWebSocketConnection,
    get_websocket_manager,
    reset_websocket_manager
)
from app.services.approval_state_manager import (
    ApprovalStateManager,
    WorkflowState,
    get_approval_state_manager,
    reset_approval_state_manager
)
from app.models.ai_planner import AgentSequence, TaskAnalysis


class TestHITLInterface:
    """Test suite for HITL Interface functionality."""
    
    def setup_method(self):
        """Reset services before each test."""
        reset_hitl_interface()
        reset_websocket_manager()
        reset_approval_state_manager()
    
    @pytest.mark.asyncio
    async def test_plan_approval_request(self):
        """Test requesting plan approval."""
        hitl = HITLInterface(default_timeout=1)  # Short timeout for testing
        
        # Create test data
        task_analysis = TaskAnalysis(
            complexity="medium",
            required_systems=["email", "erp"],
            business_context="Test task",
            data_sources_needed=["gmail", "invoice"],
            estimated_agents=["gmail", "invoice", "analysis"],
            confidence_score=0.8,
            reasoning="Test reasoning"
        )
        
        agent_sequence = AgentSequence(
            agents=["gmail", "invoice", "analysis"],
            reasoning={
                "gmail": "Search emails",
                "invoice": "Process invoices", 
                "analysis": "Analyze data"
            },
            estimated_duration=300,
            complexity_score=0.6,
            task_analysis=task_analysis
        )
        
        # Create WebSocket manager and mock connection
        ws_manager = WebSocketManager()
        mock_websocket = MockWebSocketConnection("test_plan_123")
        await ws_manager.connect(mock_websocket, "test_plan_123")
        
        # Start approval request in background (will timeout)
        approval_task = asyncio.create_task(
            hitl.request_plan_approval(
                plan_id="test_plan_123",
                agent_sequence=agent_sequence,
                task_description="Test task description",
                websocket_manager=ws_manager,
                timeout_seconds=1
            )
        )
        
        # Wait for timeout
        result = await approval_task
        
        # Verify timeout result
        assert result.plan_id == "test_plan_123"
        assert result.status == ApprovalStatus.TIMEOUT
        assert not result.approved
        assert result.timeout_seconds >= 1.0
        
        # Verify WebSocket message was sent
        assert len(mock_websocket.messages) > 0
        # Find the approval request message
        approval_messages = [msg for msg in mock_websocket.messages if msg.get("type") == "plan_approval_request"]
        assert len(approval_messages) > 0
        approval_message = approval_messages[0]
        # The message has nested data structure
        assert approval_message["data"]["data"]["plan_id"] == "test_plan_123"
    
    @pytest.mark.asyncio
    async def test_plan_approval_with_response(self):
        """Test plan approval with HITL response."""
        hitl = HITLInterface(default_timeout=5)
        
        # Create test data
        task_analysis = TaskAnalysis(
            complexity="simple",
            required_systems=["crm"],
            business_context="Simple test",
            data_sources_needed=["salesforce"],
            estimated_agents=["salesforce", "analysis"],
            confidence_score=0.9,
            reasoning="Simple task reasoning"
        )
        
        agent_sequence = AgentSequence(
            agents=["salesforce", "analysis"],
            reasoning={
                "salesforce": "Get customer data",
                "analysis": "Analyze results"
            },
            estimated_duration=180,
            complexity_score=0.3,
            task_analysis=task_analysis
        )
        
        # Create WebSocket manager and mock connection
        ws_manager = WebSocketManager()
        mock_websocket = MockWebSocketConnection("test_plan_456")
        await ws_manager.connect(mock_websocket, "test_plan_456")
        
        # Start approval request
        approval_task = asyncio.create_task(
            hitl.request_plan_approval(
                plan_id="test_plan_456",
                agent_sequence=agent_sequence,
                task_description="Simple test task",
                websocket_manager=ws_manager
            )
        )
        
        # Wait a bit then submit approval
        await asyncio.sleep(0.1)
        success = await hitl.submit_approval_response(
            plan_id="test_plan_456",
            approved=True,
            feedback="Looks good!"
        )
        
        assert success
        
        # Wait for approval result
        result = await approval_task
        
        # Verify approval result
        assert result.plan_id == "test_plan_456"
        assert result.status == ApprovalStatus.APPROVED
        assert result.approved
        assert result.feedback == "Looks good!"
        assert result.timeout_seconds < 1.0  # Should be quick
    
    @pytest.mark.asyncio
    async def test_plan_approval_with_modification(self):
        """Test plan approval with sequence modification."""
        hitl = HITLInterface(default_timeout=5)
        
        # Create original sequence
        task_analysis = TaskAnalysis(
            complexity="complex",
            required_systems=["email", "erp", "crm"],
            business_context="Complex workflow",
            data_sources_needed=["gmail", "invoice", "salesforce"],
            estimated_agents=["gmail", "invoice", "salesforce", "analysis"],
            confidence_score=0.7,
            reasoning="Complex task reasoning"
        )
        
        original_sequence = AgentSequence(
            agents=["gmail", "invoice", "salesforce", "analysis"],
            reasoning={
                "gmail": "Search emails",
                "invoice": "Process invoices",
                "salesforce": "Get CRM data",
                "analysis": "Analyze all data"
            },
            estimated_duration=480,
            complexity_score=0.8,
            task_analysis=task_analysis
        )
        
        # Create modified sequence
        modified_sequence = AgentSequence(
            agents=["gmail", "salesforce", "analysis"],  # Skip invoice
            reasoning={
                "gmail": "Search emails",
                "salesforce": "Get CRM data",
                "analysis": "Analyze data"
            },
            estimated_duration=360,
            complexity_score=0.6,
            task_analysis=task_analysis
        )
        
        # Create WebSocket manager and mock connection
        ws_manager = WebSocketManager()
        mock_websocket = MockWebSocketConnection("test_plan_789")
        await ws_manager.connect(mock_websocket, "test_plan_789")
        
        # Start approval request
        approval_task = asyncio.create_task(
            hitl.request_plan_approval(
                plan_id="test_plan_789",
                agent_sequence=original_sequence,
                task_description="Complex workflow task",
                websocket_manager=ws_manager
            )
        )
        
        # Submit modification
        await asyncio.sleep(0.1)
        success = await hitl.submit_approval_response(
            plan_id="test_plan_789",
            approved=True,
            feedback="Modified to skip invoice step",
            modified_sequence=modified_sequence
        )
        
        assert success
        
        # Wait for result
        result = await approval_task
        
        # Verify modification result
        assert result.plan_id == "test_plan_789"
        assert result.status == ApprovalStatus.MODIFIED
        assert result.approved
        assert result.feedback == "Modified to skip invoice step"
        assert result.modified_sequence is not None
        assert result.modified_sequence.agents == ["gmail", "salesforce", "analysis"]
    
    @pytest.mark.asyncio
    async def test_result_approval(self):
        """Test result approval workflow."""
        hitl = HITLInterface(default_timeout=5)
        
        final_results = {
            "analysis_complete": True,
            "findings": "Test findings",
            "recommendations": ["Action 1", "Action 2"],
            "confidence": 0.85
        }
        
        # Create WebSocket manager and mock connection
        ws_manager = WebSocketManager()
        mock_websocket = MockWebSocketConnection("test_result_123")
        await ws_manager.connect(mock_websocket, "test_result_123")
        
        # Start result approval request
        approval_task = asyncio.create_task(
            hitl.request_result_approval(
                plan_id="test_result_123",
                final_results=final_results,
                websocket_manager=ws_manager
            )
        )
        
        # Submit approval
        await asyncio.sleep(0.1)
        success = await hitl.submit_approval_response(
            plan_id="test_result_123",
            approved=True,
            feedback="Results look accurate"
        )
        
        assert success
        
        # Wait for result
        result = await approval_task
        
        # Verify result approval
        assert result.plan_id == "test_result_123"
        assert result.status == ApprovalStatus.APPROVED
        assert result.approved
        assert result.feedback == "Results look accurate"
        
        # Verify WebSocket message
        assert len(mock_websocket.messages) > 0
        # Find the result approval request message
        result_messages = [msg for msg in mock_websocket.messages if msg.get("type") == "result_approval_request"]
        assert len(result_messages) > 0
        result_message = result_messages[0]
        # The message has nested data structure
        assert result_message["data"]["data"]["plan_id"] == "test_result_123"
    
    @pytest.mark.asyncio
    async def test_progress_updates(self):
        """Test progress update functionality."""
        hitl = HITLInterface()
        
        # Create WebSocket manager and mock connection
        ws_manager = WebSocketManager()
        mock_websocket = MockWebSocketConnection("test_progress_123")
        await ws_manager.connect(mock_websocket, "test_progress_123")
        
        # Send progress updates
        await hitl.send_progress_update(
            plan_id="test_progress_123",
            current_step=1,
            total_steps=3,
            current_agent="gmail",
            websocket_manager=ws_manager
        )
        
        await hitl.send_progress_update(
            plan_id="test_progress_123",
            current_step=2,
            total_steps=3,
            current_agent="invoice",
            websocket_manager=ws_manager
        )
        
        # Verify progress messages (filter out connection message)
        progress_messages = [msg for msg in mock_websocket.messages if msg.get("type") == "progress_update"]
        assert len(progress_messages) == 2
        
        first_update = progress_messages[0]
        assert first_update["type"] == "progress_update"
        # The message has nested data structure
        assert first_update["data"]["data"]["current_step"] == 1
        assert first_update["data"]["data"]["total_steps"] == 3
        assert first_update["data"]["data"]["current_agent"] == "gmail"
        assert first_update["data"]["data"]["progress_percentage"] == 33.3
        
        second_update = progress_messages[1]
        assert second_update["data"]["data"]["current_step"] == 2
        assert second_update["data"]["data"]["current_agent"] == "invoice"
        assert second_update["data"]["data"]["progress_percentage"] == 66.7
    
    def test_approval_history_tracking(self):
        """Test approval history tracking."""
        hitl = HITLInterface()
        
        # Initially no history
        assert not hitl.is_plan_approved("test_history_123")
        assert hitl.get_approved_sequence("test_history_123") is None
        
        # Create mock approval result
        result = ApprovalResult(
            plan_id="test_history_123",
            status=ApprovalStatus.APPROVED,
            approved=True,
            feedback="Test approval"
        )
        
        # Add to history
        hitl.approval_history["test_history_123"] = [result]
        
        # Verify history
        assert hitl.is_plan_approved("test_history_123")
    
    def test_approval_statistics(self):
        """Test approval statistics generation."""
        hitl = HITLInterface()
        
        # Add mock approval history
        hitl.approval_history = {
            "plan_1": [ApprovalResult("plan_1", ApprovalStatus.APPROVED, True)],
            "plan_2": [ApprovalResult("plan_2", ApprovalStatus.REJECTED, False)],
            "plan_3": [ApprovalResult("plan_3", ApprovalStatus.MODIFIED, True)]
        }
        
        stats = hitl.get_approval_stats()
        
        assert stats["total_requests"] == 3
        assert stats["approved_requests"] == 2  # APPROVED + MODIFIED
        assert stats["approval_rate"] == 66.7
        assert stats["pending_requests"] == 0


class TestWebSocketManager:
    """Test suite for WebSocket Manager functionality."""
    
    def setup_method(self):
        """Reset WebSocket manager before each test."""
        reset_websocket_manager()
    
    @pytest.mark.asyncio
    async def test_connection_management(self):
        """Test WebSocket connection management."""
        manager = WebSocketManager()
        mock_ws = MockWebSocketConnection("test_plan_123", "user_123")
        
        # Connect
        await manager.connect(mock_ws, "test_plan_123", "user_123")
        
        assert manager.get_connection_count("test_plan_123") == 1
        assert manager.get_connection_count() == 1
        assert "test_plan_123" in manager.get_connected_plans()
        
        # Disconnect
        await manager.disconnect(mock_ws)
        
        assert manager.get_connection_count("test_plan_123") == 0
        assert manager.get_connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_message_sending(self):
        """Test message sending to connections."""
        manager = WebSocketManager()
        mock_ws1 = MockWebSocketConnection("test_plan_456", "user_1")
        mock_ws2 = MockWebSocketConnection("test_plan_456", "user_2")
        
        # Connect multiple clients
        await manager.connect(mock_ws1, "test_plan_456", "user_1")
        await manager.connect(mock_ws2, "test_plan_456", "user_2")
        
        # Send message
        await manager.send_message("test_plan_456", {
            "type": "test_message",
            "content": "Hello WebSocket!"
        })
        
        # Verify both connections received message
        assert len(mock_ws1.messages) >= 2  # Connection + test message
        assert len(mock_ws2.messages) >= 2
        
        # Find test message
        test_msg1 = next(msg for msg in mock_ws1.messages if msg.get("type") == "test_message")
        test_msg2 = next(msg for msg in mock_ws2.messages if msg.get("type") == "test_message")
        
        assert test_msg1["data"]["content"] == "Hello WebSocket!"
        assert test_msg2["data"]["content"] == "Hello WebSocket!"
    
    @pytest.mark.asyncio
    async def test_user_messaging(self):
        """Test sending messages to specific users."""
        manager = WebSocketManager()
        mock_ws1 = MockWebSocketConnection("plan_1", "user_target")
        mock_ws2 = MockWebSocketConnection("plan_2", "user_other")
        
        await manager.connect(mock_ws1, "plan_1", "user_target")
        await manager.connect(mock_ws2, "plan_2", "user_other")
        
        # Send message to specific user
        await manager.send_to_user("user_target", {
            "type": "user_message",
            "content": "Message for target user"
        })
        
        # Verify only target user received message
        target_msgs = [msg for msg in mock_ws1.messages if msg.get("type") == "user_message"]
        other_msgs = [msg for msg in mock_ws2.messages if msg.get("type") == "user_message"]
        
        assert len(target_msgs) == 1
        assert len(other_msgs) == 0
        assert target_msgs[0]["data"]["content"] == "Message for target user"
    
    def test_connection_statistics(self):
        """Test connection statistics generation."""
        manager = WebSocketManager()
        
        # Add mock connections and messages
        manager.connections = {
            "plan_1": {Mock(), Mock()},
            "plan_2": {Mock()}
        }
        manager.message_history = {
            "plan_1": [Mock(), Mock(), Mock()],
            "plan_2": [Mock()]
        }
        
        stats = manager.get_connection_stats()
        
        assert stats["active_plans"] == 2
        assert stats["connections_per_plan"]["plan_1"] == 2
        assert stats["connections_per_plan"]["plan_2"] == 1
        assert stats["messages_per_plan"]["plan_1"] == 3
        assert stats["messages_per_plan"]["plan_2"] == 1
        assert stats["total_messages"] == 4


class TestApprovalStateManager:
    """Test suite for Approval State Manager functionality."""
    
    def setup_method(self):
        """Reset approval state manager before each test."""
        reset_approval_state_manager()
    
    def test_workflow_state_management(self):
        """Test workflow state transitions."""
        manager = ApprovalStateManager()
        
        # Initial state
        assert manager.get_workflow_state("test_plan") is None
        
        # Set states
        manager.set_workflow_state("test_plan", WorkflowState.PLANNING)
        assert manager.get_workflow_state("test_plan") == WorkflowState.PLANNING
        
        manager.set_workflow_state("test_plan", WorkflowState.AWAITING_PLAN_APPROVAL)
        assert manager.get_workflow_state("test_plan") == WorkflowState.AWAITING_PLAN_APPROVAL
        
        manager.set_workflow_state("test_plan", WorkflowState.PLAN_APPROVED)
        assert manager.get_workflow_state("test_plan") == WorkflowState.PLAN_APPROVED
    
    def test_execution_permission(self):
        """Test execution permission logic."""
        manager = ApprovalStateManager()
        
        # Not allowed without approval
        assert not manager.is_execution_allowed("test_plan")
        
        # Set to approved state
        manager.set_workflow_state("test_plan", WorkflowState.PLAN_APPROVED)
        assert manager.is_execution_allowed("test_plan")
        
        # Not allowed if already executing
        manager.acquire_execution_lock("test_plan")
        assert not manager.is_execution_allowed("test_plan")
        
        # Allowed again after release
        manager.release_execution_lock("test_plan")
        assert manager.is_execution_allowed("test_plan")
    
    def test_execution_locks(self):
        """Test execution lock management."""
        manager = ApprovalStateManager()
        manager.set_workflow_state("test_plan", WorkflowState.PLAN_APPROVED)
        
        # Acquire lock
        assert manager.acquire_execution_lock("test_plan")
        assert manager.get_workflow_state("test_plan") == WorkflowState.EXECUTING
        
        # Cannot acquire again
        assert not manager.acquire_execution_lock("test_plan")
        
        # Release lock
        manager.release_execution_lock("test_plan")
        assert manager.acquire_execution_lock("test_plan")  # Can acquire again
    
    def test_approval_data_storage(self):
        """Test approval data storage and retrieval."""
        manager = ApprovalStateManager()
        
        # Create test sequence
        task_analysis = TaskAnalysis(
            complexity="medium",
            required_systems=["email"],
            business_context="Test",
            data_sources_needed=["gmail"],
            estimated_agents=["gmail", "analysis"],
            confidence_score=0.8,
            reasoning="Test reasoning"
        )
        
        agent_sequence = AgentSequence(
            agents=["gmail", "analysis"],
            reasoning={"gmail": "Search", "analysis": "Analyze"},
            estimated_duration=240,
            complexity_score=0.5,
            task_analysis=task_analysis
        )
        
        # Store plan approval
        manager.store_plan_approval(
            plan_id="test_plan",
            approved=True,
            agent_sequence=agent_sequence,
            feedback="Approved!"
        )
        
        # Verify storage
        assert manager.is_plan_approved("test_plan")
        assert manager.get_workflow_state("test_plan") == WorkflowState.PLAN_APPROVED
        
        history = manager.get_approval_history("test_plan")
        assert history is not None
        assert history["plan_approval"]["plan_approved"] is True
        assert history["plan_approval"]["feedback"] == "Approved!"
    
    def test_state_statistics(self):
        """Test state statistics generation."""
        manager = ApprovalStateManager()
        
        # Add various states
        manager.set_workflow_state("plan_1", WorkflowState.PLANNING)
        manager.set_workflow_state("plan_2", WorkflowState.PLAN_APPROVED)
        manager.set_workflow_state("plan_3", WorkflowState.EXECUTING)
        manager.acquire_execution_lock("plan_3")
        
        stats = manager.get_state_statistics()
        
        assert stats["total_workflows"] == 3
        assert stats["active_executions"] == 1
        assert stats["state_counts"]["planning"] == 1
        assert stats["state_counts"]["plan_approved"] == 1
        assert stats["state_counts"]["executing"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])