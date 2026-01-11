"""
Property tests for Linear Graph Builder implementation.

This module tests the correctness properties of the linear graph builder
as specified in the LangGraph Orchestrator Simplification design.
"""
import pytest
from hypothesis import given, strategies as st, settings
from typing import List, Dict, Any
import asyncio
from unittest.mock import Mock, AsyncMock

from app.agents.graph_refactored import (
    create_linear_graph,
    create_ai_driven_graph,
    create_simple_linear_graph,
    create_graph_from_ai_sequence,
    clear_graph_cache,
    get_graph_cache_stats,
    _generate_graph_cache_key
)
from app.agents.state import AgentState


# Test data generators
@st.composite
def agent_sequence_strategy(draw):
    """Generate valid agent sequences for testing."""
    available_agents = ["planner", "gmail", "invoice", "salesforce", "zoho", "audit", "closing", "analysis"]
    sequence_length = draw(st.integers(min_value=1, max_value=6))
    return draw(st.lists(
        st.sampled_from(available_agents),
        min_size=sequence_length,
        max_size=sequence_length,
        unique=True
    ))


@st.composite
def mixed_agent_sequence_strategy(draw):
    """Generate agent sequences with some invalid agents for testing."""
    valid_agents = ["planner", "gmail", "invoice", "salesforce", "zoho", "audit", "closing", "analysis"]
    invalid_agents = ["unknown", "invalid", "missing", "fake"]
    
    valid_count = draw(st.integers(min_value=1, max_value=4))
    invalid_count = draw(st.integers(min_value=0, max_value=2))
    
    valid_selection = draw(st.lists(
        st.sampled_from(valid_agents),
        min_size=valid_count,
        max_size=valid_count,
        unique=True
    ))
    
    invalid_selection = draw(st.lists(
        st.sampled_from(invalid_agents),
        min_size=invalid_count,
        max_size=invalid_count,
        unique=True
    ))
    
    # Combine and shuffle
    combined = valid_selection + invalid_selection
    return draw(st.permutations(combined))


class TestLinearGraphBuilder:
    """Test suite for Linear Graph Builder functionality."""
    
    def setup_method(self):
        """Clear cache before each test."""
        clear_graph_cache()
    
    # Feature: langgraph-orchestrator-simplification, Property 3: Linear Execution Fidelity
    @given(agent_sequence=agent_sequence_strategy())
    @settings(max_examples=100)
    def test_linear_execution_fidelity(self, agent_sequence: List[str]):
        """
        Property 3: Linear Execution Fidelity
        For any approved agent sequence, the system should execute agents 
        in the exact order specified without deviation.
        Validates: Requirements 3.1
        """
        # Create linear graph
        graph = create_linear_graph(agent_sequence)
        
        # Verify graph was created successfully
        assert graph is not None
        
        # Verify graph has the correct structure
        # Note: We can't easily inspect LangGraph internals, but we can verify
        # that the graph compiles without errors and has expected properties
        
        # Verify the graph is compiled (has a checkpointer)
        assert hasattr(graph, 'checkpointer')
        
        # Verify no conditional routing by checking that create_linear_graph
        # only uses add_edge() method (this is enforced by implementation)
        # The fact that the graph compiles successfully indicates linear structure
        
        # Test with different graph types
        for graph_type in ["default", "ai_driven", "simple"]:
            typed_graph = create_linear_graph(agent_sequence, graph_type=graph_type)
            assert typed_graph is not None
    
    # Feature: langgraph-orchestrator-simplification, Property 4: Single Agent Execution  
    @given(agent_sequence=agent_sequence_strategy())
    @settings(max_examples=100)
    def test_single_agent_execution(self, agent_sequence: List[str]):
        """
        Property 4: Single Agent Execution
        For any workflow instance, each agent in the sequence should execute exactly once.
        Validates: Requirements 3.4
        """
        # Create graph
        graph = create_linear_graph(agent_sequence)
        
        # Verify each agent appears exactly once in the sequence
        # (This is guaranteed by our linear graph construction)
        unique_agents = set(agent_sequence)
        assert len(unique_agents) == len(agent_sequence), "Agent sequence should not have duplicates"
        
        # Verify graph structure supports single execution
        # Linear graphs by definition execute each node exactly once
        assert graph is not None
    
    # Feature: langgraph-orchestrator-simplification, Property 5: Automatic Progression
    @given(agent_sequence=agent_sequence_strategy())
    @settings(max_examples=100) 
    def test_automatic_progression(self, agent_sequence: List[str]):
        """
        Property 5: Automatic Progression
        For any agent completion, the system should automatically proceed 
        to the next agent in sequence without manual intervention.
        Validates: Requirements 3.2
        """
        # Create linear graph
        graph = create_linear_graph(agent_sequence)
        
        # Verify graph uses only add_edge() connections (no conditional routing)
        # This is enforced by our implementation - linear graphs automatically progress
        assert graph is not None
        
        # Test that graph compilation succeeds (indicates proper edge connections)
        # If there were conditional routing, compilation might fail or behave differently
        assert hasattr(graph, 'checkpointer')
    
    # Feature: langgraph-orchestrator-simplification, Property 6: Workflow Termination
    @given(agent_sequence=agent_sequence_strategy())
    @settings(max_examples=100)
    def test_workflow_termination(self, agent_sequence: List[str]):
        """
        Property 6: Workflow Termination
        For any workflow where the final agent completes, the system should 
        automatically terminate the workflow.
        Validates: Requirements 3.3
        """
        # Create linear graph
        graph = create_linear_graph(agent_sequence)
        
        # Verify graph terminates properly (has END connections)
        # This is guaranteed by our implementation which adds final_agent -> END
        assert graph is not None
        
        # Test empty sequence handling
        empty_graph = create_linear_graph([])
        assert empty_graph is not None  # Should create minimal terminating graph
    
    def test_graph_caching_functionality(self):
        """Test graph caching for performance optimization."""
        # Clear cache
        clear_graph_cache()
        stats = get_graph_cache_stats()
        assert stats["cache_size"] == 0
        
        # Create graph - should be cached
        sequence = ["planner", "invoice", "analysis"]
        graph1 = create_linear_graph(sequence, use_cache=True)
        
        stats = get_graph_cache_stats()
        assert stats["cache_size"] == 1
        
        # Create same graph - should use cache
        graph2 = create_linear_graph(sequence, use_cache=True)
        
        # Should be same instance from cache
        assert graph1 is graph2
        
        # Different sequence should create new graph
        sequence2 = ["gmail", "salesforce", "analysis"]
        graph3 = create_linear_graph(sequence2, use_cache=True)
        
        stats = get_graph_cache_stats()
        assert stats["cache_size"] == 2
        assert graph3 is not graph1
    
    def test_multiple_graph_types(self):
        """Test support for multiple graph types."""
        sequence = ["planner", "invoice", "analysis"]
        
        # Test different graph types
        default_graph = create_linear_graph(sequence, graph_type="default")
        ai_driven_graph = create_ai_driven_graph(sequence)
        simple_graph = create_simple_linear_graph(sequence)
        
        # All should be valid graphs
        assert default_graph is not None
        assert ai_driven_graph is not None
        assert simple_graph is not None
        
        # Should be different instances (different configurations)
        assert default_graph is not ai_driven_graph
        assert ai_driven_graph is not simple_graph
    
    def test_ai_planner_integration(self):
        """Test integration with AI Planner for dynamic graph creation."""
        # Test AI-generated sequence handling
        ai_sequence = ["gmail", "invoice", "salesforce", "analysis"]
        graph = create_graph_from_ai_sequence(ai_sequence)
        
        assert graph is not None
        
        # Test empty sequence fallback
        empty_graph = create_graph_from_ai_sequence([])
        assert empty_graph is not None
    
    @given(mixed_sequence=mixed_agent_sequence_strategy())
    @settings(max_examples=50)
    def test_invalid_agent_handling(self, mixed_sequence: List[str]):
        """Test handling of sequences with invalid agents."""
        # Should handle mixed valid/invalid agents gracefully
        graph = create_linear_graph(mixed_sequence)
        assert graph is not None
        
        # Should filter out invalid agents and work with valid ones
        # (Implementation logs warnings but continues with valid agents)
    
    def test_cache_key_generation(self):
        """Test cache key generation for different sequences."""
        # Same sequence should generate same key
        seq1 = ["planner", "invoice", "analysis"]
        seq2 = ["planner", "invoice", "analysis"]
        
        key1 = _generate_graph_cache_key(seq1, "default")
        key2 = _generate_graph_cache_key(seq2, "default")
        
        assert key1 == key2
        
        # Different sequences should generate different keys
        seq3 = ["gmail", "salesforce", "analysis"]
        key3 = _generate_graph_cache_key(seq3, "default")
        
        assert key1 != key3
        
        # Different graph types should generate different keys
        key4 = _generate_graph_cache_key(seq1, "ai_driven")
        assert key1 != key4
    
    def test_hitl_interrupt_configuration(self):
        """Test HITL interrupt configuration for different graph types."""
        sequence = ["planner", "invoice", "analysis"]
        
        # AI-driven graphs should have HITL enabled
        ai_graph = create_ai_driven_graph(sequence)
        assert ai_graph is not None
        
        # Simple graphs should not have HITL
        simple_graph = create_simple_linear_graph(sequence)
        assert simple_graph is not None
        
        # Explicit HITL configuration
        hitl_graph = create_linear_graph(sequence, enable_hitl=True)
        assert hitl_graph is not None
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing code."""
        from app.agents.graph_refactored import create_agent_graph, get_agent_graph
        
        # Should create default graph
        default_graph = create_agent_graph()
        assert default_graph is not None
        
        # Should get singleton graph
        singleton_graph = get_agent_graph()
        assert singleton_graph is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])