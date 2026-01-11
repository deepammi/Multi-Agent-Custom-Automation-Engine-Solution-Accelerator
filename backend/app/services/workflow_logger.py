"""
Comprehensive workflow logging service for multi-agent invoice analysis.

This module provides structured logging with correlation IDs, agent execution
tracking, success rate monitoring, and comprehensive audit trails for all
workflow steps and HITL interactions.
"""
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading
from collections import defaultdict

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for workflow events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(Enum):
    """Types of workflow events."""
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"
    HITL_REQUEST = "hitl_request"
    HITL_RESPONSE = "hitl_response"
    PLAN_APPROVAL = "plan_approval"
    PLAN_MODIFICATION = "plan_modification"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    DATA_CORRELATION = "data_correlation"
    WEBSOCKET_MESSAGE = "websocket_message"
    ERROR_RECOVERY = "error_recovery"
    PERFORMANCE_METRIC = "performance_metric"


@dataclass
class LogEntry:
    """Structured log entry for workflow events."""
    timestamp: str
    correlation_id: str
    event_type: EventType
    level: LogLevel
    message: str
    plan_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None
    execution_time: Optional[float] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class AgentExecutionMetrics:
    """Metrics for individual agent execution."""
    agent_name: str
    agent_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    tool_calls: int = 0
    data_retrieved: int = 0
    correlation_id: Optional[str] = None
    
    def complete(self, success: bool, error_message: Optional[str] = None):
        """Mark agent execution as complete."""
        self.end_time = datetime.utcnow()
        self.execution_time = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error_message = error_message


@dataclass
class WorkflowExecutionMetrics:
    """Metrics for complete workflow execution."""
    workflow_id: str
    plan_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_execution_time: Optional[float] = None
    agents_executed: List[AgentExecutionMetrics] = None
    success: bool = False
    hitl_interactions: int = 0
    approval_time: Optional[float] = None
    error_count: int = 0
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.agents_executed is None:
            self.agents_executed = []
    
    def complete(self, success: bool):
        """Mark workflow execution as complete."""
        self.end_time = datetime.utcnow()
        self.total_execution_time = (self.end_time - self.start_time).total_seconds()
        self.success = success


class WorkflowLogger:
    """
    Comprehensive workflow logging service.
    
    Provides structured logging with correlation IDs, agent execution tracking,
    success rate monitoring, and audit trails for multi-agent workflows.
    """
    
    def __init__(self, enable_performance_tracking: bool = True):
        self.enable_performance_tracking = enable_performance_tracking
        self.log_entries: List[LogEntry] = []
        self.workflow_metrics: Dict[str, WorkflowExecutionMetrics] = {}
        self.agent_metrics: Dict[str, List[AgentExecutionMetrics]] = defaultdict(list)
        self.correlation_contexts: Dict[str, Dict[str, Any]] = {}
        self.success_rates: Dict[str, List[bool]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Performance tracking
        self.performance_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0,
            "agent_success_rates": defaultdict(list),
            "hitl_approval_rates": defaultdict(list)
        }
    
    def create_correlation_id(self, prefix: str = "wf") -> str:
        """Create a new correlation ID for tracking related events."""
        correlation_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        self.correlation_contexts[correlation_id] = {
            "created_at": datetime.utcnow(),
            "events": []
        }
        return correlation_id
    
    @contextmanager
    def correlation_context(self, correlation_id: str, **context_data):
        """Context manager for correlation ID tracking."""
        old_context = getattr(self._local, 'correlation_context', None)
        self._local = threading.local()
        self._local.correlation_context = {
            "correlation_id": correlation_id,
            **context_data
        }
        try:
            yield correlation_id
        finally:
            self._local.correlation_context = old_context
    
    def _get_current_correlation_id(self) -> Optional[str]:
        """Get current correlation ID from thread-local storage."""
        context = getattr(getattr(self, '_local', None), 'correlation_context', None)
        return context.get('correlation_id') if context else None
    
    def log_event(
        self,
        event_type: EventType,
        message: str,
        level: LogLevel = LogLevel.INFO,
        correlation_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        agent_type: Optional[str] = None,
        execution_time: Optional[float] = None,
        success: Optional[bool] = None,
        error_message: Optional[str] = None,
        **metadata
    ) -> LogEntry:
        """
        Log a workflow event with structured data.
        
        Args:
            event_type: Type of event being logged
            message: Human-readable message
            level: Log level
            correlation_id: Correlation ID for tracking related events
            plan_id: Plan identifier
            session_id: Session identifier
            user_id: User identifier
            agent_name: Name of the agent (if applicable)
            agent_type: Type of the agent (if applicable)
            execution_time: Execution time in seconds
            success: Whether the operation was successful
            error_message: Error message if operation failed
            **metadata: Additional metadata
            
        Returns:
            LogEntry object
        """
        # Use current correlation ID if not provided
        if correlation_id is None:
            correlation_id = self._get_current_correlation_id()
        
        # Create log entry
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            correlation_id=correlation_id or "unknown",
            event_type=event_type,
            level=level,
            message=message,
            plan_id=plan_id,
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            agent_type=agent_type,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
        
        # Store log entry
        with self._lock:
            self.log_entries.append(entry)
            
            # Add to correlation context
            if correlation_id and correlation_id in self.correlation_contexts:
                self.correlation_contexts[correlation_id]["events"].append(entry)
        
        # Log to standard logger
        log_func = getattr(logger, level.value)
        log_func(f"[{correlation_id}] {event_type.value}: {message}")
        
        return entry
    
    def start_workflow_tracking(
        self,
        workflow_id: str,
        plan_id: str,
        session_id: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Start tracking a workflow execution.
        
        Args:
            workflow_id: Unique workflow identifier
            plan_id: Plan identifier
            session_id: Session identifier
            correlation_id: Optional correlation ID
            
        Returns:
            Correlation ID for the workflow
        """
        if correlation_id is None:
            correlation_id = self.create_correlation_id("workflow")
        
        # Create workflow metrics
        metrics = WorkflowExecutionMetrics(
            workflow_id=workflow_id,
            plan_id=plan_id,
            session_id=session_id,
            start_time=datetime.utcnow(),
            correlation_id=correlation_id
        )
        
        with self._lock:
            self.workflow_metrics[workflow_id] = metrics
            self.performance_metrics["total_workflows"] += 1
        
        # Log workflow start
        self.log_event(
            event_type=EventType.WORKFLOW_START,
            message=f"Started workflow execution for plan {plan_id}",
            correlation_id=correlation_id,
            plan_id=plan_id,
            session_id=session_id,
            workflow_id=workflow_id
        )
        
        return correlation_id
    
    def end_workflow_tracking(
        self,
        workflow_id: str,
        success: bool,
        error_message: Optional[str] = None
    ) -> Optional[WorkflowExecutionMetrics]:
        """
        End tracking for a workflow execution.
        
        Args:
            workflow_id: Workflow identifier
            success: Whether the workflow succeeded
            error_message: Error message if workflow failed
            
        Returns:
            WorkflowExecutionMetrics or None if workflow not found
        """
        with self._lock:
            if workflow_id not in self.workflow_metrics:
                logger.warning(f"Workflow {workflow_id} not found in tracking")
                return None
            
            metrics = self.workflow_metrics[workflow_id]
            metrics.complete(success)
            
            # Update performance metrics
            if success:
                self.performance_metrics["successful_workflows"] += 1
            else:
                self.performance_metrics["failed_workflows"] += 1
            
            # Update average execution time
            total_time = sum(
                m.total_execution_time for m in self.workflow_metrics.values()
                if m.total_execution_time is not None
            )
            total_count = len([
                m for m in self.workflow_metrics.values()
                if m.total_execution_time is not None
            ])
            if total_count > 0:
                self.performance_metrics["average_execution_time"] = total_time / total_count
        
        # Log workflow end
        self.log_event(
            event_type=EventType.WORKFLOW_END,
            message=f"Completed workflow execution for plan {metrics.plan_id}",
            level=LogLevel.INFO if success else LogLevel.ERROR,
            correlation_id=metrics.correlation_id,
            plan_id=metrics.plan_id,
            session_id=metrics.session_id,
            execution_time=metrics.total_execution_time,
            success=success,
            error_message=error_message,
            workflow_id=workflow_id
        )
        
        return metrics
    
    def start_agent_tracking(
        self,
        agent_name: str,
        agent_type: str,
        correlation_id: Optional[str] = None
    ) -> AgentExecutionMetrics:
        """
        Start tracking an agent execution.
        
        Args:
            agent_name: Name of the agent
            agent_type: Type of the agent
            correlation_id: Correlation ID for tracking
            
        Returns:
            AgentExecutionMetrics object
        """
        if correlation_id is None:
            correlation_id = self._get_current_correlation_id()
        
        metrics = AgentExecutionMetrics(
            agent_name=agent_name,
            agent_type=agent_type,
            start_time=datetime.utcnow(),
            correlation_id=correlation_id
        )
        
        with self._lock:
            self.agent_metrics[agent_name].append(metrics)
        
        # Log agent start
        self.log_event(
            event_type=EventType.AGENT_START,
            message=f"Started {agent_type} agent: {agent_name}",
            correlation_id=correlation_id,
            agent_name=agent_name,
            agent_type=agent_type
        )
        
        return metrics
    
    def end_agent_tracking(
        self,
        agent_name: str,
        success: bool,
        error_message: Optional[str] = None,
        tool_calls: int = 0,
        data_retrieved: int = 0
    ) -> Optional[AgentExecutionMetrics]:
        """
        End tracking for an agent execution.
        
        Args:
            agent_name: Name of the agent
            success: Whether the agent succeeded
            error_message: Error message if agent failed
            tool_calls: Number of tool calls made
            data_retrieved: Amount of data retrieved
            
        Returns:
            AgentExecutionMetrics or None if agent not found
        """
        with self._lock:
            if agent_name not in self.agent_metrics or not self.agent_metrics[agent_name]:
                logger.warning(f"Agent {agent_name} not found in tracking")
                return None
            
            # Get the most recent metrics for this agent
            metrics = self.agent_metrics[agent_name][-1]
            metrics.complete(success, error_message)
            metrics.tool_calls = tool_calls
            metrics.data_retrieved = data_retrieved
            
            # Update agent success rates
            self.performance_metrics["agent_success_rates"][agent_name].append(success)
        
        # Log agent end
        self.log_event(
            event_type=EventType.AGENT_END,
            message=f"Completed {metrics.agent_type} agent: {agent_name}",
            level=LogLevel.INFO if success else LogLevel.ERROR,
            correlation_id=metrics.correlation_id,
            agent_name=agent_name,
            agent_type=metrics.agent_type,
            execution_time=metrics.execution_time,
            success=success,
            error_message=error_message,
            tool_calls=tool_calls,
            data_retrieved=data_retrieved
        )
        
        return metrics
    
    def log_hitl_interaction(
        self,
        interaction_type: str,
        plan_id: str,
        approved: Optional[bool] = None,
        feedback: Optional[str] = None,
        response_time: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> LogEntry:
        """
        Log human-in-the-loop interaction.
        
        Args:
            interaction_type: Type of HITL interaction
            plan_id: Plan identifier
            approved: Whether the request was approved
            feedback: Human feedback
            response_time: Time taken for human response
            correlation_id: Correlation ID
            
        Returns:
            LogEntry object
        """
        if correlation_id is None:
            correlation_id = self._get_current_correlation_id()
        
        # Update HITL approval rates
        if approved is not None:
            with self._lock:
                self.performance_metrics["hitl_approval_rates"][interaction_type].append(approved)
        
        return self.log_event(
            event_type=EventType.HITL_REQUEST if approved is None else EventType.HITL_RESPONSE,
            message=f"HITL {interaction_type}: {'approved' if approved else 'rejected' if approved is False else 'requested'}",
            correlation_id=correlation_id,
            plan_id=plan_id,
            execution_time=response_time,
            success=approved,
            interaction_type=interaction_type,
            feedback=feedback
        )
    
    def log_tool_call(
        self,
        tool_name: str,
        agent_name: str,
        success: bool,
        execution_time: float,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None,
        **tool_metadata
    ) -> LogEntry:
        """
        Log tool call execution.
        
        Args:
            tool_name: Name of the tool called
            agent_name: Name of the calling agent
            success: Whether the tool call succeeded
            execution_time: Tool execution time
            error_message: Error message if tool call failed
            correlation_id: Correlation ID
            **tool_metadata: Additional tool-specific metadata
            
        Returns:
            LogEntry object
        """
        if correlation_id is None:
            correlation_id = self._get_current_correlation_id()
        
        return self.log_event(
            event_type=EventType.TOOL_CALL,
            message=f"Tool call: {tool_name} by {agent_name}",
            level=LogLevel.INFO if success else LogLevel.ERROR,
            correlation_id=correlation_id,
            agent_name=agent_name,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            tool_name=tool_name,
            **tool_metadata
        )
    
    def get_workflow_metrics(self, workflow_id: str) -> Optional[WorkflowExecutionMetrics]:
        """Get metrics for a specific workflow."""
        return self.workflow_metrics.get(workflow_id)
    
    def get_agent_success_rate(self, agent_name: str) -> float:
        """Get success rate for a specific agent."""
        with self._lock:
            successes = self.performance_metrics["agent_success_rates"].get(agent_name, [])
            if not successes:
                return 0.0
            return sum(successes) / len(successes)
    
    def get_overall_success_rate(self) -> float:
        """Get overall workflow success rate."""
        total = self.performance_metrics["total_workflows"]
        if total == 0:
            return 0.0
        successful = self.performance_metrics["successful_workflows"]
        return successful / total
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            agent_success_rates = {
                agent: sum(successes) / len(successes) if successes else 0.0
                for agent, successes in self.performance_metrics["agent_success_rates"].items()
            }
            
            hitl_approval_rates = {
                interaction: sum(approvals) / len(approvals) if approvals else 0.0
                for interaction, approvals in self.performance_metrics["hitl_approval_rates"].items()
            }
            
            return {
                "total_workflows": self.performance_metrics["total_workflows"],
                "successful_workflows": self.performance_metrics["successful_workflows"],
                "failed_workflows": self.performance_metrics["failed_workflows"],
                "overall_success_rate": self.get_overall_success_rate(),
                "average_execution_time": self.performance_metrics["average_execution_time"],
                "agent_success_rates": agent_success_rates,
                "hitl_approval_rates": hitl_approval_rates,
                "total_log_entries": len(self.log_entries),
                "active_correlations": len(self.correlation_contexts)
            }
    
    def get_logs_by_correlation(self, correlation_id: str) -> List[LogEntry]:
        """Get all log entries for a specific correlation ID."""
        return [
            entry for entry in self.log_entries
            if entry.correlation_id == correlation_id
        ]
    
    def get_logs_by_plan(self, plan_id: str) -> List[LogEntry]:
        """Get all log entries for a specific plan."""
        return [
            entry for entry in self.log_entries
            if entry.plan_id == plan_id
        ]
    
    def export_logs(
        self,
        format_type: str = "json",
        correlation_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Export logs in specified format with optional filtering.
        
        Args:
            format_type: Export format ("json", "dict")
            correlation_id: Filter by correlation ID
            plan_id: Filter by plan ID
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            Exported logs in specified format
        """
        # Filter logs
        filtered_logs = self.log_entries
        
        if correlation_id:
            filtered_logs = [log for log in filtered_logs if log.correlation_id == correlation_id]
        
        if plan_id:
            filtered_logs = [log for log in filtered_logs if log.plan_id == plan_id]
        
        if start_time:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log.timestamp.replace('Z', '+00:00')) >= start_time
            ]
        
        if end_time:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log.timestamp.replace('Z', '+00:00')) <= end_time
            ]
        
        # Convert to requested format
        log_dicts = [log.to_dict() for log in filtered_logs]
        
        if format_type == "json":
            return json.dumps(log_dicts, indent=2, default=str)
        else:
            return log_dicts
    
    def cleanup_old_logs(self, retention_days: int = 30) -> int:
        """
        Clean up logs older than retention period.
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            Number of logs removed
        """
        cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
        
        with self._lock:
            original_count = len(self.log_entries)
            
            # Remove old log entries
            self.log_entries = [
                log for log in self.log_entries
                if datetime.fromisoformat(log.timestamp.replace('Z', '+00:00')) > cutoff_time
            ]
            
            # Remove old correlation contexts
            old_correlations = [
                corr_id for corr_id, context in self.correlation_contexts.items()
                if context["created_at"] < cutoff_time
            ]
            for corr_id in old_correlations:
                del self.correlation_contexts[corr_id]
            
            removed_count = original_count - len(self.log_entries)
        
        logger.info(f"Cleaned up {removed_count} old log entries")
        return removed_count


# Global workflow logger instance
_workflow_logger: Optional[WorkflowLogger] = None


def get_workflow_logger() -> WorkflowLogger:
    """
    Get or create the global workflow logger instance.
    
    Returns:
        WorkflowLogger instance
    """
    global _workflow_logger
    if _workflow_logger is None:
        _workflow_logger = WorkflowLogger()
    return _workflow_logger


def reset_workflow_logger() -> None:
    """Reset the global workflow logger (useful for testing)."""
    global _workflow_logger
    _workflow_logger = None


# Convenience functions for common logging operations
def log_workflow_start(plan_id: str, session_id: str, correlation_id: Optional[str] = None) -> str:
    """Convenience function to start workflow logging."""
    logger = get_workflow_logger()
    workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
    return logger.start_workflow_tracking(workflow_id, plan_id, session_id, correlation_id)


def log_workflow_end(workflow_id: str, success: bool, error_message: Optional[str] = None):
    """Convenience function to end workflow logging."""
    logger = get_workflow_logger()
    return logger.end_workflow_tracking(workflow_id, success, error_message)


def log_agent_execution(agent_name: str, agent_type: str, success: bool, 
                       execution_time: float, error_message: Optional[str] = None):
    """Convenience function to log agent execution."""
    logger = get_workflow_logger()
    metrics = logger.start_agent_tracking(agent_name, agent_type)
    return logger.end_agent_tracking(agent_name, success, error_message)


def log_hitl_approval(plan_id: str, approved: bool, response_time: float, 
                     feedback: Optional[str] = None):
    """Convenience function to log HITL approval."""
    logger = get_workflow_logger()
    return logger.log_hitl_interaction("plan_approval", plan_id, approved, feedback, response_time)