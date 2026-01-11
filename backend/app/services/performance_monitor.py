"""
Performance monitoring service for LangGraph workflows.

Provides metrics collection, logging, and performance analysis
for the simplified orchestrator system.
"""
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowMetrics:
    """Metrics for a complete workflow execution."""
    plan_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    agent_count: int = 0
    total_duration: Optional[float] = None
    agent_durations: Dict[str, float] = field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate total duration if end_time is set."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class PerformanceMonitor:
    """
    Performance monitoring service for LangGraph workflows.
    
    Tracks:
    - Workflow execution times
    - Agent performance
    - Graph compilation metrics
    - Cache performance
    - Memory usage
    - Error rates
    """
    
    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.workflow_metrics: Dict[str, WorkflowMetrics] = {}
        self.agent_stats: Dict[str, List[float]] = defaultdict(list)
        self.graph_compilation_times: List[float] = []
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }
        
    def start_workflow(self, plan_id: str, agent_count: int) -> None:
        """Start tracking a workflow execution."""
        self.workflow_metrics[plan_id] = WorkflowMetrics(
            plan_id=plan_id,
            start_time=datetime.utcnow(),
            agent_count=agent_count
        )
        logger.debug(f"📊 Started tracking workflow {plan_id} with {agent_count} agents")
    
    def end_workflow(self, plan_id: str, success: bool = True) -> Optional[WorkflowMetrics]:
        """End tracking a workflow execution."""
        if plan_id not in self.workflow_metrics:
            logger.warning(f"No workflow metrics found for plan {plan_id}")
            return None
        
        workflow = self.workflow_metrics[plan_id]
        workflow.end_time = datetime.utcnow()
        
        if success:
            logger.info(
                f"✅ Workflow {plan_id} completed in {workflow.duration:.2f}s "
                f"({workflow.agent_count} agents)"
            )
        else:
            logger.warning(f"❌ Workflow {plan_id} failed after {workflow.duration:.2f}s")
        
        return workflow
    
    def record_agent_execution(
        self,
        plan_id: str,
        agent_name: str,
        duration: float,
        success: bool = True
    ) -> None:
        """Record agent execution metrics."""
        # Update workflow metrics
        if plan_id in self.workflow_metrics:
            self.workflow_metrics[plan_id].agent_durations[agent_name] = duration
        
        # Update agent statistics
        self.agent_stats[agent_name].append(duration)
        
        # Keep only recent metrics
        if len(self.agent_stats[agent_name]) > 100:
            self.agent_stats[agent_name] = self.agent_stats[agent_name][-100:]
        
        # Add to general metrics
        self.add_metric(f"agent.{agent_name}.duration", duration, {
            "plan_id": plan_id,
            "success": success
        })
        
        status = "✅" if success else "❌"
        logger.debug(f"{status} Agent {agent_name} executed in {duration:.2f}s")
    
    def record_graph_compilation(self, duration: float, agent_count: int, cached: bool = False) -> None:
        """Record graph compilation metrics."""
        if not cached:
            self.graph_compilation_times.append(duration)
            
            # Keep only recent compilations
            if len(self.graph_compilation_times) > 50:
                self.graph_compilation_times = self.graph_compilation_times[-50:]
        
        cache_status = "cached" if cached else "compiled"
        self.add_metric("graph.compilation.duration", duration, {
            "agent_count": agent_count,
            "cached": cached
        })
        
        logger.debug(f"📊 Graph {cache_status} in {duration:.3f}s ({agent_count} agents)")
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_stats["hits"] += 1
        self.cache_stats["total_requests"] += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_stats["misses"] += 1
        self.cache_stats["total_requests"] += 1
    
    def add_metric(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a custom performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        self.metrics.append(metric)
    
    def get_agent_stats(self, agent_name: str) -> Dict[str, float]:
        """Get performance statistics for a specific agent."""
        durations = self.agent_stats.get(agent_name, [])
        if not durations:
            return {"count": 0}
        
        return {
            "count": len(durations),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "recent_avg": sum(durations[-10:]) / min(10, len(durations))
        }
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics."""
        completed_workflows = [w for w in self.workflow_metrics.values() if w.end_time]
        
        if not completed_workflows:
            return {"workflows": 0}
        
        durations = [w.duration for w in completed_workflows if w.duration]
        
        cache_hit_rate = (
            self.cache_stats["hits"] / self.cache_stats["total_requests"]
            if self.cache_stats["total_requests"] > 0 else 0.0
        )
        
        return {
            "workflows": {
                "total": len(completed_workflows),
                "avg_duration": sum(durations) / len(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0
            },
            "cache": {
                "hit_rate": cache_hit_rate,
                "hits": self.cache_stats["hits"],
                "misses": self.cache_stats["misses"],
                "total_requests": self.cache_stats["total_requests"]
            },
            "graph_compilation": {
                "avg_duration": (
                    sum(self.graph_compilation_times) / len(self.graph_compilation_times)
                    if self.graph_compilation_times else 0
                ),
                "count": len(self.graph_compilation_times)
            },
            "agents": {
                name: self.get_agent_stats(name)
                for name in self.agent_stats.keys()
            }
        }
    
    def log_performance_summary(self) -> None:
        """Log a performance summary."""
        stats = self.get_overall_stats()
        
        logger.info("📊 Performance Summary:")
        logger.info(f"   Workflows: {stats['workflows']['total']} completed")
        
        if stats['workflows']['total'] > 0:
            logger.info(f"   Avg Duration: {stats['workflows']['avg_duration']:.2f}s")
            logger.info(f"   Cache Hit Rate: {stats['cache']['hit_rate']:.1%}")
            logger.info(f"   Graph Compilations: {stats['graph_compilation']['count']}")
        
        # Log top performing agents
        agent_stats = stats.get('agents', {})
        if agent_stats:
            sorted_agents = sorted(
                agent_stats.items(),
                key=lambda x: x[1].get('avg_duration', 0)
            )
            logger.info("   Top Agents by Speed:")
            for agent_name, agent_data in sorted_agents[:3]:
                if agent_data.get('count', 0) > 0:
                    logger.info(f"     {agent_name}: {agent_data['avg_duration']:.2f}s avg")
    
    def cleanup_old_metrics(self, max_age_hours: int = 24) -> None:
        """Clean up old metrics to prevent memory bloat."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Clean up workflow metrics
        old_workflows = [
            plan_id for plan_id, workflow in self.workflow_metrics.items()
            if workflow.start_time < cutoff_time
        ]
        
        for plan_id in old_workflows:
            del self.workflow_metrics[plan_id]
        
        logger.debug(f"🧹 Cleaned up {len(old_workflows)} old workflow metrics")
    
    async def start_periodic_logging(self, interval_minutes: int = 15) -> None:
        """Start periodic performance logging."""
        while True:
            await asyncio.sleep(interval_minutes * 60)
            self.log_performance_summary()
            self.cleanup_old_metrics()


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def reset_performance_monitor() -> None:
    """Reset the global performance monitor (useful for testing)."""
    global _performance_monitor
    _performance_monitor = None


# Decorator for automatic performance tracking
def track_performance(metric_name: str):
    """Decorator to automatically track function performance."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            monitor = get_performance_monitor()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                monitor.add_metric(metric_name, duration, {"success": True})
                return result
            except Exception as e:
                duration = time.time() - start_time
                monitor.add_metric(metric_name, duration, {"success": False, "error": str(e)})
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            monitor = get_performance_monitor()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                monitor.add_metric(metric_name, duration, {"success": True})
                return result
            except Exception as e:
                duration = time.time() - start_time
                monitor.add_metric(metric_name, duration, {"success": False, "error": str(e)})
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator