"""
Property test for routing logic elimination.

**Feature: langgraph-orchestrator-simplification, Property 7: Routing Logic Elimination**
**Validates: Requirements 4.2**

This test validates that all next_agent routing logic has been eliminated
from agent implementations and that agents work with simplified AgentState.
"""
import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

from app.agents.state import AgentState, AgentStateManager
from app.agents.nodes import (
    planner_node,
    invoice_agent_node,
    approval_checkpoint_node,
    hitl_agent_node
)
from app.agents.salesforce_node import salesforce_agent_node
from app.agents.gmail_agent_node import gmail_agent_node
from app.agents.graph_refactored import analysis_agent_node


class TestRoutingLogicElimination:
    """Property tests for routing logic elimination."""
    
    @pytest.fixture
    def sample_agent_sequences(self):
        """Generate various agent sequences for testing."""
        return [
            ["planner"],
            ["planner", "invoice"],
            ["planner", "gmail", "invoice"],
            ["planner", "salesforce", "audit"],
            ["planner", "gmail", "invoice", "salesforce", "analysis"],
            ["planner", "zoho", "closing"],
        ]
    
    @pytest.fixture
    def sample_tasks(self):
        """Generate various task descriptions for testing."""
        return [
            "Process invoice INV-12345",
            "Find emails about vendor payment",
            "Check Salesforce opportunities",
            "Audit compliance for Q4",
            "Investigate PO stuck in approval",
            "Analyze Zoho invoice data"
        ]
    
    def test_planner_node_no_routing_logic(self, sample_tasks):
        """
        Property 7: Routing Logic Elimination - Planner Node
        For any task input, the planner node should not return next_agent routing logic.
        """
        for task in sample_tasks:
            # Create initial state
            state = AgentStateManager.create_initial_state(
                plan_id=f"test-{hash(task)}",
                session_id="test-session",
                task_description=task,
                agent_sequence=["planner", "invoice"]
            )
            
            # Execute planner node
            result = planner_node(state)
            
            # Verify no routing logic
            assert "next_agent" not in result, f"Planner returned next_agent for task: {task}"
            assert "workflow_type" not in result, f"Planner returned workflow_type for task: {task}"
            
            # Verify simplified state structure
            assert "current_agent" in result
            assert "collected_data" in result
            assert "execution_results" in result
            assert result["current_agent"] == "Planner"
    
    @pytest.mark.asyncio
    async def test_invoice_agent_no_routing_logic(self, sample_tasks):
        """
        Property 7: Routing Logic Elimination - Invoice Agent
        For any task input, the invoice agent should not return next_agent routing logic.
        """
        for task in sample_tasks:
            # Create state with invoice agent
            state = AgentStateManager.create_initial_state(
                plan_id=f"test-invoice-{hash(task)}",
                session_id="test-session",
                task_description=task,
                agent_sequence=["invoice"]
            )
            
            # Mock websocket manager to avoid async issues
            state["websocket_manager"] = AsyncMock()
            
            # Execute invoice agent
            result = await invoice_agent_node(state)
            
            # Verify no routing logic
            assert "next_agent" not in result, f"Invoice agent returned next_agent for task: {task}"
            assert "workflow_type" not in result, f"Invoice agent returned workflow_type for task: {task}"
            
            # Verify simplified state structure
            assert "current_agent" in result
            assert "collected_data" in result
            assert "execution_results" in result
            assert result["current_agent"] == "Invoice"
    
    def test_closing_agent_no_routing_logic(self, sample_tasks):
        """
        Property 7: Routing Logic Elimination - Closing Agent
        For any task input, the closing agent should not return next_agent routing logic.
        """
        for task in sample_tasks:
            # Create state with closing agent
            state = AgentStateManager.create_initial_state(
                plan_id=f"test-closing-{hash(task)}",
                session_id="test-session",
                task_description=task,
                agent_sequence=["closing"]
            )
            
            # Execute closing agent
            result = closing_agent_node(state)
            
            # Verify no routing logic
            assert "next_agent" not in result, f"Closing agent returned next_agent for task: {task}"
            assert "workflow_type" not in result, f"Closing agent returned workflow_type for task: {task}"
            
            # Verify simplified state structure
            assert "current_agent" in result
            assert "collected_data" in result
            assert "execution_results" in result
            assert result["current_agent"] == "Closing"
    
    @pytest.mark.asyncio
    async def test_audit_agent_no_routing_logic(self, sample_tasks):
        """
        Property 7: Routing Logic Elimination - Audit Agent
        For any task input, the audit agent should not return next_agent routing logic.
        """
        for task in sample_tasks:
            # Create state with audit agent
            state = AgentStateManager.create_initial_state(
                plan_id=f"test-audit-{hash(task)}",
                session_id="test-session",
                task_description=task,
                agent_sequence=["audit"]
            )
            
            # Mock websocket manager
            state["websocket_manager"] = AsyncMock()
            
            # Execute audit agent
            result = await audit_agent_node(state)
            
            # Verify no routing logic
            assert "next_agent" not in result, f"Audit agent returned next_agent for task: {task}"
            assert "workflow_type" not in result, f"Audit agent returned workflow_type for task: {task}"
            
            # Verify simplified state structure
            assert "current_agent" in result
            assert "collected_data" in result
            assert "execution_results" in result
            assert result["current_agent"] == "Audit"
    
    @pytest.mark.asyncio
    async def test_salesforce_agent_no_routing_logic(self, sample_tasks):
        """
        Property 7: Routing Logic Elimination - Salesforce Agent
        For any task input, the Salesforce agent should not return next_agent routing logic.
        """
        for task in sample_tasks:
            # Create state with Salesforce agent
            state = AgentStateManager.create_initial_state(
                plan_id=f"test-sf-{hash(task)}",
                session_id="test-session",
                task_description=task,
                agent_sequence=["salesforce"]
            )
            
            # Mock websocket manager
            state["websocket_manager"] = AsyncMock()
            
            # Execute Salesforce agent
            result = await salesforce_agent_node(state)
            
            # Verify no routing logic
            assert "next_agent" not in result, f"Salesforce agent returned next_agent for task: {task}"
            assert "workflow_type" not in result, f"Salesforce agent returned workflow_type for task: {task}"
            
            # Verify simplified state structure
            assert "current_agent" in result
            assert "collected_data" in result
            assert "execution_results" in result
            assert result["current_agent"] == "Salesforce"
    
    @pytest.mark.asyncio
    async def test_zoho_agent_no_routing_logic(self, sample_tasks):
        """
        Property 7: Routing Logic Elimination - Zoho Agent
        For any task input, the Zoho agent should not return next_agent routing logic.
        """
        for task in sample_tasks:
            # Create state with Zoho agent
            state = AgentStateManager.create_initial_state(
                plan_id=f"test-zoho-{hash(task)}",
                session_id="test-session",
                task_description=task,
                agent_sequence=["zoho"]
            )
            
            # Mock websocket manager
            state["websocket_manager"] = AsyncMock()
            
            # Execute Zoho agent
            result = await zoho_agent_node(state)
            
            # Verify no routing logic
            assert "next_agent" not in result, f"Zoho agent returned next_agent for task: {task}"
            assert "workflow_type" not in result, f"Zoho agent returned workflow_type for task: {task}"
            
            # Verify simplified state structure
            assert "current_agent" in result
            assert "collected_data" in result
            assert "execution_results" in result
            assert result["current_agent"] == "Zoho Invoice"
    
    @pytest.mark.asyncio
    async def test_gmail_agent_no_routing_logic(self, sample_tasks):
        """
        Property 7: Routing Logic Elimination - Gmail Agent
        For any task input, the Gmail agent should not return next_agent routing logic.
        """
        for task in sample_tasks:
            # Create state with Gmail agent
            state = AgentStateManager.create_initial_state(
                plan_id=f"test-gmail-{hash(task)}",
                session_id="test-session",
                task_description=task,
                agent_sequence=["gmail"]
            )
            
            # Mock websocket manager
            state["websocket_manager"] = AsyncMock()
            
            # Execute Gmail agent
            result = await gmail_agent_node(state)
            
            # Verify no routing logic
            assert "next_agent" not in result, f"Gmail agent returned next_agent for task: {task}"
            assert "workflow_type" not in result, f"Gmail agent returned workflow_type for task: {task}"
            
            # Verify simplified state structure
            assert "collected_data" in result
            assert "execution_results" in result
    
    @pytest.mark.asyncio
    async def test_analysis_agent_no_routing_logic(self, sample_tasks):
        """
        Property 7: Routing Logic Elimination - Analysis Agent
        For any task input, the analysis agent should not return next_agent routing logic.
        """
        for task in sample_tasks:
            # Create state with analysis agent
            state = AgentStateManager.create_initial_state(
                plan_id=f"test-analysis-{hash(task)}",
                session_id="test-session",
                task_description=task,
                agent_sequence=["analysis"]
            )
            
            # Mock websocket manager
            state["websocket_manager"] = AsyncMock()
            
            # Execute analysis agent
            result = await analysis_agent_node(state)
            
            # Verify no routing logic
            assert "next_agent" not in result, f"Analysis agent returned next_agent for task: {task}"
            assert "workflow_type" not in result, f"Analysis agent returned workflow_type for task: {task}"
            
            # Verify simplified state structure
            assert "current_agent" in result
            assert "collected_data" in result
            assert "execution_results" in result
            assert result["current_agent"] == "Analysis"
    
    def test_approval_checkpoint_no_routing_logic(self):
        """
        Property 7: Routing Logic Elimination - Approval Checkpoint
        The approval checkpoint should not return next_agent routing logic.
        """
        # Create state
        state = AgentStateManager.create_initial_state(
            plan_id="test-approval",
            session_id="test-session",
            task_description="Test approval checkpoint",
            agent_sequence=["approval"]
        )
        
        # Execute approval checkpoint
        result = approval_checkpoint_node(state)
        
        # Verify no routing logic
        assert "next_agent" not in result, "Approval checkpoint returned next_agent"
        assert "workflow_type" not in result, "Approval checkpoint returned workflow_type"
        
        # Verify simplified state structure
        assert "current_agent" in result
        assert "collected_data" in result
        assert "execution_results" in result
        assert result["current_agent"] == "Approval"
    
    def test_hitl_agent_no_routing_logic(self):
        """
        Property 7: Routing Logic Elimination - HITL Agent
        The HITL agent should not return next_agent routing logic.
        """
        # Create state with some execution results
        state = AgentStateManager.create_initial_state(
            plan_id="test-hitl",
            session_id="test-session",
            task_description="Test HITL agent",
            agent_sequence=["hitl"]
        )
        
        # Add some mock execution results
        state["execution_results"] = [{
            "agent": "Invoice",
            "step": 0,
            "result": {"message": "Invoice processed successfully"},
            "timestamp": "2024-01-01T00:00:00"
        }]
        
        # Execute HITL agent
        result = hitl_agent_node(state)
        
        # Verify no routing logic
        assert "next_agent" not in result, "HITL agent returned next_agent"
        assert "workflow_type" not in result, "HITL agent returned workflow_type"
        
        # Verify simplified state structure
        assert "current_agent" in result
        assert "collected_data" in result
        assert "execution_results" in result
        assert result["current_agent"] == "HITL"
    
    def test_agent_state_preserves_collected_data(self, sample_agent_sequences, sample_tasks):
        """
        Property 7: Data Preservation
        For any agent sequence and task, agents should preserve collected_data for subsequent agents.
        """
        for sequence in sample_agent_sequences:
            for task in sample_tasks:
                # Create initial state with some collected data
                state = AgentStateManager.create_initial_state(
                    plan_id=f"test-data-{hash(task)}-{hash(str(sequence))}",
                    session_id="test-session",
                    task_description=task,
                    agent_sequence=sequence
                )
                
                # Add some initial collected data
                initial_data = {"test_key": "test_value", "sequence": sequence}
                state["collected_data"] = initial_data
                
                # Test planner node (sync)
                if "planner" in sequence:
                    result = planner_node(state)
                    
                    # Verify collected_data is preserved
                    assert "collected_data" in result
                    assert result["collected_data"]["test_key"] == "test_value"
                    assert result["collected_data"]["sequence"] == sequence
    
    def test_supervisor_router_deprecated(self):
        """
        Property 7: Supervisor Router Elimination
        The supervisor_router function should be deprecated and not perform routing.
        """
        from app.agents.supervisor import supervisor_router
        
        # Create test state
        state = AgentStateManager.create_initial_state(
            plan_id="test-supervisor",
            session_id="test-session",
            task_description="Test supervisor deprecation",
            agent_sequence=["planner", "invoice"]
        )
        
        # Add next_agent to test deprecated behavior
        state["next_agent"] = "invoice"
        
        # Execute supervisor router
        result = supervisor_router(state)
        
        # Should always return "end" since it's deprecated
        assert result == "end", "Supervisor router should always return 'end' when deprecated"
    
    def test_agent_state_manager_linear_progression(self, sample_agent_sequences):
        """
        Property 7: Linear Progression
        For any agent sequence, AgentStateManager should support linear progression without routing methods.
        The linear executor handles progression automatically, so we test state structure only.
        """
        for sequence in sample_agent_sequences:
            if not sequence:  # Skip empty sequences
                continue
                
            # Create initial state
            state = AgentStateManager.create_initial_state(
                plan_id=f"test-linear-{hash(str(sequence))}",
                session_id="test-session",
                task_description="Test linear progression",
                agent_sequence=sequence
            )
            
            # Verify initial state structure (no routing methods needed)
            assert state["current_step"] == 0
            assert state["current_agent"] == sequence[0]
            assert state["total_steps"] == len(sequence)
            assert state["agent_sequence"] == sequence
            
            # Verify current agent can be retrieved
            current_agent = AgentStateManager.get_current_agent(state)
            assert current_agent == sequence[0], f"Initial agent should be {sequence[0]}, got {current_agent}"
            
            # Verify state has required fields for linear execution
            assert "collected_data" in state
            assert "execution_results" in state
            assert isinstance(state["collected_data"], dict)
            assert isinstance(state["execution_results"], list)
            
            # Verify workflow completion detection works
            # Simulate completion by setting current_step to total_steps
            completed_state = state.copy()
            completed_state["current_step"] = len(sequence)
            assert AgentStateManager.is_workflow_complete(completed_state), f"Workflow should be complete when current_step >= total_steps"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])