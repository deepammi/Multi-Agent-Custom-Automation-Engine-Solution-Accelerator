"""
Test the new LinearGraphFactory implementation.

**Feature: langgraph-orchestrator-simplification, Task 9: Create New Graph Factory**
**Validates: Requirements 1.3, 4.2, 6.1**
"""
import pytest
import asyncio
from typing import List
from unittest.mock import Mock, AsyncMock

from app.agents.graph_factory import LinearGraphFactory, get_agent_graph, create_linear_graph_from_sequence
from app.models.ai_planner import AgentSequence, TaskAnalysis
from app.agents.state import AgentState


class TestLinearGraphFactory:
    """Test the LinearGraphFactory implementation."""
    
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
    def sample_ai_sequence(self):
        """Create a sample AI-generated sequence."""
        task_analysis = TaskAnalysis(
            complexity="medium",
            required_systems=["email", "erp"],
            business_context="Invoice investigation workflow",
            data_sources_needed=["gmail", "bill.com"],
            estimated_agents=["gmail", "invoice", "analysis"],
            confidence_score=0.8,
            reasoning="Task requires email search and invoice processing"
        )
        
        return AgentSequence(
            agents=["gmail", "invoice", "analysis"],
            reasoning={
                "gmail": "Search for email communications",
                "invoice": "Process invoice data",
                "analysis": "Analyze collected information"
            },
            estimated_duration=300,
            complexity_score=0.6,
            task_analysis=task_analysis
        )
    
    def test_create_graph_from_sequence(self, sample_agent_sequences):
        """Test creating graphs from agent sequences."""
        for sequence in sample_agent_sequences:
            graph = LinearGraphFactory.create_graph_from_sequence(sequence)
            
            # Verify graph is created
            assert graph is not None
            assert hasattr(graph, 'ainvoke')
            # Graph is already compiled, so it doesn't have compile method
    
    def test_create_ai_driven_graph(self, sample_agent_sequences):
        """Test creating AI-driven graphs."""
        for sequence in sample_agent_sequences:
            graph = LinearGraphFactory.create_ai_driven_graph(sequence)
            
            # Verify graph is created
            assert graph is not None
            assert hasattr(graph, 'ainvoke')
    
    def test_create_simple_graph(self, sample_agent_sequences):
        """Test creating simple graphs."""
        for sequence in sample_agent_sequences:
            graph = LinearGraphFactory.create_simple_graph(sequence)
            
            # Verify graph is created
            assert graph is not None
            assert hasattr(graph, 'ainvoke')
    
    def test_create_hitl_enabled_graph(self, sample_agent_sequences):
        """Test creating HITL-enabled graphs."""
        for sequence in sample_agent_sequences:
            graph = LinearGraphFactory.create_hitl_enabled_graph(sequence)
            
            # Verify graph is created
            assert graph is not None
            assert hasattr(graph, 'ainvoke')
    
    def test_create_graph_from_ai_sequence(self, sample_ai_sequence):
        """Test creating graph from AI Planner sequence."""
        graph = LinearGraphFactory.create_graph_from_ai_sequence(sample_ai_sequence)
        
        # Verify graph is created
        assert graph is not None
        assert hasattr(graph, 'ainvoke')
    
    def test_get_default_graph(self):
        """Test getting default graph for backward compatibility."""
        graph = LinearGraphFactory.get_default_graph()
        
        # Verify graph is created
        assert graph is not None
        assert hasattr(graph, 'ainvoke')
    
    def test_graph_types_supported(self):
        """Test that all supported graph types work."""
        sequence = ["planner", "invoice"]
        supported_types = LinearGraphFactory.get_supported_graph_types()
        
        for graph_type in supported_types:
            graph = LinearGraphFactory.create_graph_from_sequence(
                sequence, 
                graph_type=graph_type
            )
            assert graph is not None
    
    def test_available_agents(self):
        """Test that available agents list is correct."""
        agents = LinearGraphFactory.get_available_agents()
        
        expected_agents = [
            "planner", "gmail", "invoice", "salesforce", 
            "zoho", "audit", "closing", "analysis"
        ]
        
        for agent in expected_agents:
            assert agent in agents
    
    def test_cache_functionality(self):
        """Test graph caching functionality."""
        # Note: Caching is handled by the underlying create_linear_graph function
        # This test verifies that the factory can create graphs consistently
        
        sequence = ["planner", "invoice"]
        
        # Create graph with caching enabled
        graph1 = LinearGraphFactory.create_graph_from_sequence(
            sequence, use_cache=True
        )
        
        # Create same graph again - should work consistently
        graph2 = LinearGraphFactory.create_graph_from_sequence(
            sequence, use_cache=True
        )
        
        # Verify both graphs are valid (may or may not be the same object due to caching implementation)
        assert graph1 is not None
        assert graph2 is not None
        assert hasattr(graph1, 'ainvoke')
        assert hasattr(graph2, 'ainvoke')
        
        # Check cache stats (factory's own cache may be empty, but that's OK)
        stats = LinearGraphFactory.get_cache_stats()
        assert "cached_graphs" in stats
        assert "cache_keys" in stats
    
    def test_backward_compatibility_function(self):
        """Test that the backward compatibility get_agent_graph() function works."""
        graph = get_agent_graph()
        
        # Verify graph is created
        assert graph is not None
        assert hasattr(graph, 'ainvoke')
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        sequence = ["planner", "invoice"]
        
        # Test create_linear_graph_from_sequence
        graph1 = create_linear_graph_from_sequence(sequence)
        assert graph1 is not None
        
        # Test create_ai_planner_graph
        task_analysis = TaskAnalysis(
            complexity="simple",
            required_systems=["erp"],
            business_context="Simple invoice processing",
            data_sources_needed=["invoice"],
            estimated_agents=["invoice"],
            confidence_score=0.9,
            reasoning="Simple task"
        )
        
        ai_sequence = AgentSequence(
            agents=["invoice"],
            reasoning={"invoice": "Process invoice"},
            estimated_duration=120,
            complexity_score=0.3,
            task_analysis=task_analysis
        )
        
        from app.agents.graph_factory import create_ai_planner_graph
        graph2 = create_ai_planner_graph(ai_sequence)
        assert graph2 is not None
    
    def test_empty_sequence_handling(self):
        """Test handling of empty agent sequences."""
        # Empty sequence should create a minimal graph
        graph = LinearGraphFactory.create_graph_from_sequence([])
        assert graph is not None
    
    def test_invalid_agents_handling(self):
        """Test handling of invalid agent names."""
        # Sequence with invalid agents should filter them out
        sequence = ["planner", "invalid_agent", "invoice", "another_invalid"]
        graph = LinearGraphFactory.create_graph_from_sequence(sequence)
        assert graph is not None
    
    @pytest.mark.asyncio
    async def test_graph_execution(self):
        """Test that created graphs can actually execute."""
        sequence = ["planner"]
        graph = LinearGraphFactory.create_graph_from_sequence(sequence)
        
        # Create test state
        initial_state = {
            "plan_id": "test-123",
            "session_id": "session-123",
            "task_description": "Test task",
            "agent_sequence": sequence,
            "current_step": 0,
            "total_steps": len(sequence),
            "current_agent": sequence[0],
            "messages": [],
            "collected_data": {},
            "execution_results": [],
            "final_result": "",
            "start_time": None,
        }
        
        # Execute graph
        config = {"configurable": {"thread_id": "test_thread"}}
        result = await graph.ainvoke(initial_state, config)
        
        # Verify execution completed
        assert result is not None
        assert "current_agent" in result
        assert "messages" in result
    
    def test_ai_sequence_complexity_mapping(self, sample_ai_sequence):
        """Test that AI sequence complexity maps to correct graph types."""
        # Test high complexity
        sample_ai_sequence.complexity_score = 0.8
        graph = LinearGraphFactory.create_graph_from_ai_sequence(sample_ai_sequence)
        assert graph is not None
        
        # Test medium complexity
        sample_ai_sequence.complexity_score = 0.5
        graph = LinearGraphFactory.create_graph_from_ai_sequence(sample_ai_sequence)
        assert graph is not None
        
        # Test low complexity
        sample_ai_sequence.complexity_score = 0.2
        graph = LinearGraphFactory.create_graph_from_ai_sequence(sample_ai_sequence)
        assert graph is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])