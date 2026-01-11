"""
New Graph Factory for Linear LangGraph Workflows
Replaces get_agent_graph() with create_linear_graph(sequence) approach
"""
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph

from app.agents.graph_refactored import create_linear_graph, create_ai_driven_graph, create_simple_linear_graph
from app.models.ai_planner import AgentSequence
from app.services.performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Performance monitoring for graph operations."""
    
    @staticmethod
    def log_graph_creation(graph_type: str, agent_count: int, duration: float, cached: bool = False):
        """Log graph creation performance metrics."""
        cache_status = "cached" if cached else "created"
        logger.info(
            f"📊 Graph {cache_status}: type={graph_type}, agents={agent_count}, "
            f"duration={duration:.3f}s"
        )
    
    @staticmethod
    def log_cache_stats(cache_size: int, hit_rate: float):
        """Log cache performance statistics."""
        logger.info(f"📈 Graph cache: size={cache_size}, hit_rate={hit_rate:.2%}")
    
    @staticmethod
    def log_memory_usage():
        """Log memory usage statistics."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            logger.info(f"💾 Memory usage: {memory_mb:.1f} MB")
        except ImportError:
            logger.debug("psutil not available for memory monitoring")


class LinearGraphFactory:
    """
    Factory for creating linear LangGraph workflows based on agent sequences.
    
    This replaces the old get_agent_graph() function with a more flexible approach
    that supports:
    - Dynamic agent sequences from AI Planner
    - Multiple graph types (default, ai_driven, simple, hitl_enabled)
    - Graph caching for performance
    - Integration with HITL approval workflows
    """
    
    # Graph cache for performance optimization
    _graph_cache: Dict[str, StateGraph] = {}
    _cache_hits: int = 0
    _cache_misses: int = 0
    
    @classmethod
    def create_graph_from_sequence(
        cls,
        agent_sequence: List[str],
        graph_type: str = "default",
        enable_hitl: bool = False,
        use_cache: bool = True
    ) -> StateGraph:
        """
        Create a linear graph from an agent sequence.
        
        This is the main replacement for get_agent_graph().
        
        Args:
            agent_sequence: Ordered list of agent names to execute
            graph_type: Type of graph (default, ai_driven, simple, hitl_enabled)
            enable_hitl: Whether to enable human-in-the-loop interrupts
            use_cache: Whether to use cached graphs for performance
            
        Returns:
            Compiled StateGraph with linear connections
        """
        start_time = time.time()
        
        # Generate cache key
        cache_key = cls._generate_cache_key(agent_sequence, graph_type, enable_hitl)
        
        # Check cache first
        if use_cache and cache_key in cls._graph_cache:
            cls._cache_hits += 1
            duration = time.time() - start_time
            PerformanceMonitor.log_graph_creation(graph_type, len(agent_sequence), duration, cached=True)
            
            # Record cache hit
            monitor = get_performance_monitor()
            monitor.record_cache_hit()
            monitor.record_graph_compilation(duration, len(agent_sequence), cached=True)
            
            logger.debug(f"📋 Using cached graph for sequence: {agent_sequence}")
            return cls._graph_cache[cache_key]
        
        # Create new graph
        cls._cache_misses += 1
        logger.info(f"🔧 Creating linear graph for sequence: {agent_sequence}, type: {graph_type}")
        
        # Record cache miss
        monitor = get_performance_monitor()
        monitor.record_cache_miss()
        
        graph = create_linear_graph(
            agent_sequence=agent_sequence,
            graph_type=graph_type,
            enable_hitl=enable_hitl,
            use_cache=use_cache
        )
        
        # Cache the graph
        if use_cache:
            cls._graph_cache[cache_key] = graph
            
        duration = time.time() - start_time
        PerformanceMonitor.log_graph_creation(graph_type, len(agent_sequence), duration, cached=False)
        monitor.record_graph_compilation(duration, len(agent_sequence), cached=False)
        
        # Log cache statistics periodically
        if (cls._cache_hits + cls._cache_misses) % 10 == 0:
            cls._log_cache_stats()
        
        return graph
    
    @classmethod
    def create_ai_driven_graph(cls, agent_sequence: List[str]) -> StateGraph:
        """
        Create AI-driven linear graph optimized for AI Planner integration.
        
        Args:
            agent_sequence: AI-generated ordered list of agent names
            
        Returns:
            Compiled StateGraph optimized for AI-driven workflows
        """
        logger.info(f"Creating AI-driven graph for sequence: {agent_sequence}")
        
        return create_ai_driven_graph(agent_sequence)
    
    @classmethod
    def create_simple_graph(cls, agent_sequence: List[str]) -> StateGraph:
        """
        Create simple linear graph for basic workflows.
        
        Args:
            agent_sequence: Ordered list of agent names
            
        Returns:
            Compiled StateGraph for simple workflows
        """
        logger.info(f"Creating simple graph for sequence: {agent_sequence}")
        
        return create_simple_linear_graph(agent_sequence)
    
    @classmethod
    def create_hitl_enabled_graph(cls, agent_sequence: List[str]) -> StateGraph:
        """
        Create HITL-enabled graph with approval checkpoints.
        
        Args:
            agent_sequence: Ordered list of agent names
            
        Returns:
            Compiled StateGraph with HITL approval points
        """
        logger.info(f"Creating HITL-enabled graph for sequence: {agent_sequence}")
        
        return create_linear_graph(
            agent_sequence=agent_sequence,
            graph_type="hitl_enabled",
            enable_hitl=True,
            use_cache=True
        )
    
    @classmethod
    def create_graph_from_ai_sequence(cls, ai_sequence: AgentSequence, enable_hitl: bool = False) -> StateGraph:
        """
        Create graph from AI Planner's AgentSequence model.
        
        This integrates directly with the AI Planner for dynamic graph creation.
        
        Args:
            ai_sequence: AgentSequence from AI Planner with agents and reasoning
            enable_hitl: Whether to enable HITL interrupts (defaults to False for testing)
            
        Returns:
            Compiled StateGraph optimized for AI-generated sequences
        """
        logger.info(f"Creating graph from AI sequence: {ai_sequence.agents}")
        logger.info(f"AI reasoning: {ai_sequence.reasoning}")
        
        # Determine graph type based on complexity
        if ai_sequence.complexity_score >= 0.7:
            graph_type = "ai_driven"
        elif ai_sequence.complexity_score >= 0.4:
            graph_type = "default"
        else:
            graph_type = "simple"
        
        # Use the provided enable_hitl parameter instead of auto-enabling
        logger.info(f"HITL enabled: {enable_hitl} (complexity: {ai_sequence.complexity_score})")
        
        return cls.create_graph_from_sequence(
            agent_sequence=ai_sequence.agents,
            graph_type=graph_type,
            enable_hitl=enable_hitl,
            use_cache=True
        )
    
    @classmethod
    def get_default_graph(cls) -> StateGraph:
        """
        Get default graph for backward compatibility.
        
        This provides a fallback when no specific sequence is provided.
        
        Returns:
            Default linear graph with common agent sequence
        """
        default_sequence = ["planner", "invoice"]
        logger.info("Creating default graph for backward compatibility")
        
        return cls.create_graph_from_sequence(
            agent_sequence=default_sequence,
            graph_type="default",
            enable_hitl=False,
            use_cache=True
        )
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the graph cache."""
        cls._graph_cache.clear()
        logger.info("Graph cache cleared")
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_graphs": len(cls._graph_cache),
            "cache_keys": list(cls._graph_cache.keys())
        }
    
    @classmethod
    def _generate_cache_key(cls, agent_sequence: List[str], graph_type: str, enable_hitl: bool) -> str:
        """Generate cache key for graph configuration."""
        key_data = f"{'-'.join(agent_sequence)}:{graph_type}:{enable_hitl}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @classmethod
    def _log_cache_stats(cls) -> None:
        """Log cache performance statistics."""
        total_requests = cls._cache_hits + cls._cache_misses
        hit_rate = cls._cache_hits / total_requests if total_requests > 0 else 0.0
        PerformanceMonitor.log_cache_stats(len(cls._graph_cache), hit_rate)
    
    @classmethod
    def get_performance_stats(cls) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        total_requests = cls._cache_hits + cls._cache_misses
        hit_rate = cls._cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "cache_hits": cls._cache_hits,
            "cache_misses": cls._cache_misses,
            "hit_rate": hit_rate,
            "cached_graphs": len(cls._graph_cache),
            "total_requests": total_requests
        }
    
    @classmethod
    def get_supported_graph_types(cls) -> List[str]:
        """
        Get list of supported graph types.
        
        Returns:
            List of supported graph type names
        """
        return ["default", "ai_driven", "simple", "hitl_enabled"]
    
    @classmethod
    def get_available_agents(cls) -> List[str]:
        """
        Get list of available agent names.
        
        Returns:
            List of available agent names
        """
        return [
            "planner",
            "gmail", 
            "invoice",
            "salesforce",
            "analysis"
        ]


# Backward compatibility function
def get_agent_graph() -> StateGraph:
    """
    Backward compatibility function that replaces the old get_agent_graph().
    
    This function is deprecated. Use LinearGraphFactory.create_graph_from_sequence() instead.
    
    Returns:
        Default linear graph for backward compatibility
    """
    logger.warning("get_agent_graph() is deprecated. Use LinearGraphFactory.create_graph_from_sequence() instead.")
    return LinearGraphFactory.get_default_graph()


# Convenience functions for common use cases
def create_linear_graph_from_sequence(agent_sequence: List[str]) -> StateGraph:
    """
    Convenience function to create linear graph from sequence.
    
    Args:
        agent_sequence: Ordered list of agent names
        
    Returns:
        Compiled StateGraph
    """
    return LinearGraphFactory.create_graph_from_sequence(agent_sequence)


def create_ai_planner_graph(ai_sequence: AgentSequence) -> StateGraph:
    """
    Convenience function to create graph from AI Planner sequence.
    
    Args:
        ai_sequence: AgentSequence from AI Planner
        
    Returns:
        Compiled StateGraph optimized for AI workflows
    """
    return LinearGraphFactory.create_graph_from_ai_sequence(ai_sequence)