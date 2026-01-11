"""
Error Handling and Recovery Service for LangGraph Orchestrator.

This module provides comprehensive error handling, logging, and recovery
mechanisms for workflow execution failures with environment-controlled mock mode support.
"""
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass

from app.services.websocket_service import WebSocketManager
from app.services.hitl_interface import HITLInterface
from app.config.environment import get_environment_config

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    AGENT_FAILURE = "agent_failure"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    RESOURCE = "resource"
    NETWORK = "network"
    SYSTEM = "system"
    USER_INPUT = "user_input"


@dataclass
class ErrorEvent:
    """Structured error event for logging and tracking."""
    plan_id: str
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    agent_name: Optional[str]
    error_message: str
    error_type: str
    stack_trace: Optional[str]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error event to dictionary for logging."""
        return {
            "plan_id": self.plan_id,
            "error_id": self.error_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "agent_name": self.agent_name,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "context": self.context or {}
        }


class WorkflowErrorHandler:
    """
    Comprehensive error handling service for workflow execution.
    
    Provides centralized error handling, logging, notification, and recovery
    mechanisms for the LangGraph orchestrator system.
    """
    
    def __init__(
        self,
        websocket_manager: WebSocketManager,
        hitl_interface: HITLInterface,
        max_error_history: int = 1000
    ):
        self.websocket_manager = websocket_manager
        self.hitl_interface = hitl_interface
        self.max_error_history = max_error_history
        
        # Error tracking
        self.error_history: List[ErrorEvent] = []
        self.error_counts: Dict[str, int] = {}  # plan_id -> error_count
        self.last_errors: Dict[str, ErrorEvent] = {}  # plan_id -> last_error
        
        # System stability tracking
        self.system_error_count = 0
        self.system_error_window_start = datetime.utcnow()
        self.system_error_threshold = 50  # Max errors per hour
        
        logger.info("WorkflowErrorHandler initialized")
    
    async def handle_agent_failure(
        self,
        plan_id: str,
        agent_name: str,
        error: Exception,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorEvent:
        """
        Handle agent execution failures with comprehensive error processing.
        
        Args:
            plan_id: Workflow plan identifier
            agent_name: Name of the failed agent
            error: Exception that caused the failure
            user_id: User identifier
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            ErrorEvent with failure details
        """
        # Create error event
        error_event = self._create_error_event(
            plan_id=plan_id,
            category=ErrorCategory.AGENT_FAILURE,
            severity=self._determine_error_severity(error),
            agent_name=agent_name,
            error=error,
            user_id=user_id,
            session_id=session_id,
            context=context
        )
        
        # Log the error
        await self._log_error_event(error_event)
        
        # Send notifications
        await self._send_error_notifications(error_event)
        
        # Update error tracking
        self._update_error_tracking(error_event)
        
        # Check system stability
        await self._check_system_stability()
        
        logger.error(
            f"Agent failure handled: {agent_name} in workflow {plan_id} - {str(error)}"
        )
        
        return error_event
    
    async def handle_workflow_timeout(
        self,
        plan_id: str,
        timeout_duration: int,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorEvent:
        """
        Handle workflow timeout errors.
        
        Args:
            plan_id: Workflow plan identifier
            timeout_duration: Timeout duration in seconds
            user_id: User identifier
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            ErrorEvent with timeout details
        """
        timeout_error = TimeoutError(f"Workflow timed out after {timeout_duration} seconds")
        
        error_event = self._create_error_event(
            plan_id=plan_id,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.HIGH,
            agent_name=None,
            error=timeout_error,
            user_id=user_id,
            session_id=session_id,
            context={**(context or {}), "timeout_duration": timeout_duration}
        )
        
        await self._log_error_event(error_event)
        await self._send_error_notifications(error_event)
        self._update_error_tracking(error_event)
        
        logger.warning(f"Workflow timeout handled: {plan_id} after {timeout_duration}s")
        
        return error_event
    
    async def handle_validation_error(
        self,
        plan_id: str,
        validation_message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorEvent:
        """
        Handle validation errors (e.g., invalid agent sequences, malformed input).
        
        Args:
            plan_id: Workflow plan identifier
            validation_message: Validation error message
            user_id: User identifier
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            ErrorEvent with validation details
        """
        validation_error = ValueError(validation_message)
        
        error_event = self._create_error_event(
            plan_id=plan_id,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            agent_name=None,
            error=validation_error,
            user_id=user_id,
            session_id=session_id,
            context=context
        )
        
        await self._log_error_event(error_event)
        await self._send_error_notifications(error_event)
        self._update_error_tracking(error_event)
        
        logger.warning(f"Validation error handled: {plan_id} - {validation_message}")
        
        return error_event
    
    async def handle_mcp_service_error(
        self,
        plan_id: str,
        service_name: str,
        error: Exception,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorEvent:
        """
        Handle MCP service errors with environment-controlled mock mode fallback.
        
        This method implements NFR3.2 by only using mock data when USE_MOCK_MODE=true.
        When mock mode is disabled, real service failures propagate as expected.
        
        Args:
            plan_id: Workflow plan identifier
            service_name: Name of the MCP service (gmail, salesforce, bill_com)
            error: Exception that caused the failure
            user_id: User identifier
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            ErrorEvent with failure details and mock mode information
        """
        env_config = get_environment_config()
        
        # Create error event
        error_event = self._create_error_event(
            plan_id=plan_id,
            category=ErrorCategory.NETWORK,
            severity=self._determine_error_severity(error),
            agent_name=service_name,
            error=error,
            user_id=user_id,
            session_id=session_id,
            context={
                **(context or {}),
                "service_name": service_name,
                "mock_mode_enabled": env_config.is_mock_mode_enabled(),
                "error_type": "mcp_service_error"
            }
        )
        
        # Log the error with mock mode context
        await self._log_error_event(error_event)
        
        # Check if mock mode is enabled via environment variable
        if env_config.is_mock_mode_enabled():
            logger.info(
                f"🎭 Mock mode enabled for MCP service '{service_name}' - error will be handled with mock data",
                extra={
                    "service_name": service_name,
                    "error_message": str(error),
                    "mock_mode_reason": "USE_MOCK_MODE=true in environment"
                }
            )
            
            # Add mock mode information to error event
            error_event.context["mock_fallback_used"] = True
            error_event.context["mock_fallback_reason"] = "Environment variable USE_MOCK_MODE=true"
        else:
            logger.error(
                f"❌ MCP service '{service_name}' failed and mock mode disabled - error will propagate",
                extra={
                    "service_name": service_name,
                    "error_message": str(error),
                    "mock_mode_status": "disabled"
                }
            )
            
            # Add propagation information to error event
            error_event.context["mock_fallback_used"] = False
            error_event.context["error_propagation"] = "Mock mode disabled, real service failure propagated"
        
        # Send notifications
        await self._send_error_notifications(error_event)
        
        # Update error tracking
        self._update_error_tracking(error_event)
        
        logger.info(
            f"MCP service error handled: {service_name} in workflow {plan_id} - mock_mode={env_config.is_mock_mode_enabled()}"
        )
        
        return error_event
    
    async def handle_llm_service_error(
        self,
        plan_id: str,
        error: Exception,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorEvent:
        """
        Handle LLM service errors with environment-controlled mock mode fallback.
        
        This method implements NFR3.2 by only using mock LLM responses when USE_MOCK_LLM=true.
        When mock mode is disabled, real LLM service failures propagate as expected.
        
        Args:
            plan_id: Workflow plan identifier
            error: Exception that caused the failure
            user_id: User identifier
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            ErrorEvent with failure details and mock mode information
        """
        env_config = get_environment_config()
        
        # Create error event
        error_event = self._create_error_event(
            plan_id=plan_id,
            category=ErrorCategory.NETWORK,
            severity=self._determine_error_severity(error),
            agent_name="llm_service",
            error=error,
            user_id=user_id,
            session_id=session_id,
            context={
                **(context or {}),
                "mock_llm_enabled": env_config.is_mock_llm_enabled(),
                "error_type": "llm_service_error"
            }
        )
        
        # Log the error with mock mode context
        await self._log_error_event(error_event)
        
        # Check if LLM mock mode is enabled via environment variable
        if env_config.is_mock_llm_enabled():
            logger.info(
                f"🎭 LLM mock mode enabled - error will be handled with mock response",
                extra={
                    "error_message": str(error),
                    "mock_mode_reason": "USE_MOCK_LLM=true in environment"
                }
            )
            
            # Add mock mode information to error event
            error_event.context["mock_fallback_used"] = True
            error_event.context["mock_fallback_reason"] = "Environment variable USE_MOCK_LLM=true"
        else:
            logger.error(
                f"❌ LLM service failed and mock mode disabled - error will propagate",
                extra={
                    "error_message": str(error),
                    "mock_mode_status": "disabled"
                }
            )
            
            # Add propagation information to error event
            error_event.context["mock_fallback_used"] = False
            error_event.context["error_propagation"] = "Mock mode disabled, real LLM service failure propagated"
        
        # Send notifications
        await self._send_error_notifications(error_event)
        
        # Update error tracking
        self._update_error_tracking(error_event)
        
        logger.info(
            f"LLM service error handled in workflow {plan_id} - mock_mode={env_config.is_mock_llm_enabled()}"
        )
        
        return error_event
        """
        Handle system-level errors that affect overall stability.
        
        Args:
            plan_id: Workflow plan identifier
            error: System error exception
            user_id: User identifier
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            ErrorEvent with system error details
        """
        error_event = self._create_error_event(
            plan_id=plan_id,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            agent_name=None,
            error=error,
            user_id=user_id,
            session_id=session_id,
            context=context
        )
        
        await self._log_error_event(error_event)
        await self._send_error_notifications(error_event)
        self._update_error_tracking(error_event)
        
        # System errors are critical - increment system error count
        self.system_error_count += 1
        await self._check_system_stability()
        
        logger.critical(f"System error handled: {plan_id} - {str(error)}")
        
        return error_event
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive error statistics for monitoring.
        
        Returns:
            Dictionary with error statistics
        """
        now = datetime.utcnow()
        
        # Calculate error rates
        recent_errors = [
            e for e in self.error_history
            if (now - e.timestamp).total_seconds() < 3600  # Last hour
        ]
        
        error_by_category = {}
        error_by_severity = {}
        
        for error in recent_errors:
            category = error.category.value
            severity = error.severity.value
            
            error_by_category[category] = error_by_category.get(category, 0) + 1
            error_by_severity[severity] = error_by_severity.get(severity, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors_1h": len(recent_errors),
            "system_error_count": self.system_error_count,
            "error_by_category": error_by_category,
            "error_by_severity": error_by_severity,
            "workflows_with_errors": len(self.error_counts),
            "system_stability": self._get_system_stability_status(),
            "error_rate_per_hour": len(recent_errors),
            "most_common_errors": self._get_most_common_errors()
        }
    
    def get_workflow_error_history(self, plan_id: str) -> List[ErrorEvent]:
        """
        Get error history for a specific workflow.
        
        Args:
            plan_id: Workflow plan identifier
            
        Returns:
            List of error events for the workflow
        """
        return [e for e in self.error_history if e.plan_id == plan_id]
    
    def is_workflow_stable(self, plan_id: str) -> bool:
        """
        Check if a workflow is stable (low error rate).
        
        Args:
            plan_id: Workflow plan identifier
            
        Returns:
            True if workflow is stable, False otherwise
        """
        error_count = self.error_counts.get(plan_id, 0)
        return error_count < 5  # Threshold for stability
    
    def _create_error_event(
        self,
        plan_id: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        error: Exception,
        agent_name: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorEvent:
        """Create structured error event."""
        error_id = f"{plan_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        return ErrorEvent(
            plan_id=plan_id,
            error_id=error_id,
            category=category,
            severity=severity,
            agent_name=agent_name,
            error_message=str(error),
            error_type=type(error).__name__,
            stack_trace=traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            context=context
        )
    
    def _determine_error_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type."""
        if isinstance(error, (SystemError, MemoryError)):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, (OSError, TimeoutError, ConnectionError, RuntimeError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError, AttributeError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    async def _log_error_event(self, error_event: ErrorEvent) -> None:
        """Log error event with appropriate level."""
        log_data = error_event.to_dict()
        
        if error_event.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {error_event.error_message}", extra=log_data)
        elif error_event.severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR: {error_event.error_message}", extra=log_data)
        elif error_event.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR: {error_event.error_message}", extra=log_data)
        else:
            logger.info(f"LOW SEVERITY ERROR: {error_event.error_message}", extra=log_data)
    
    async def _send_error_notifications(self, error_event: ErrorEvent) -> None:
        """Send error notifications via WebSocket and HITL."""
        try:
            # Send WebSocket notification
            await self.websocket_manager.send_message(error_event.plan_id, {
                "type": "error_event",
                "data": {
                    "error_id": error_event.error_id,
                    "category": error_event.category.value,
                    "severity": error_event.severity.value,
                    "agent_name": error_event.agent_name,
                    "error_message": error_event.error_message,
                    "error_type": error_event.error_type,
                    "timestamp": error_event.timestamp.isoformat() + "Z",
                    "requires_attention": error_event.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
                }
            })
            
            # Send HITL notification for medium/high/critical errors
            if error_event.severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                await self.hitl_interface.send_error_notification(
                    plan_id=error_event.plan_id,
                    agent_name=error_event.agent_name or "system",
                    error_message=error_event.error_message,
                    error_type=error_event.error_type,
                    websocket_manager=self.websocket_manager
                )
                
        except Exception as notification_error:
            logger.error(f"Failed to send error notifications: {str(notification_error)}")
    
    def _update_error_tracking(self, error_event: ErrorEvent) -> None:
        """Update internal error tracking."""
        # Add to history
        self.error_history.append(error_event)
        
        # Maintain history size limit
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history:]
        
        # Update error counts
        plan_id = error_event.plan_id
        self.error_counts[plan_id] = self.error_counts.get(plan_id, 0) + 1
        self.last_errors[plan_id] = error_event
    
    async def _check_system_stability(self) -> None:
        """Check overall system stability and take action if needed."""
        now = datetime.utcnow()
        
        # Reset error window if needed (hourly)
        if (now - self.system_error_window_start).total_seconds() > 3600:
            self.system_error_count = 0
            self.system_error_window_start = now
        
        # Check if system error threshold exceeded
        if self.system_error_count > self.system_error_threshold:
            logger.critical(
                f"System stability threshold exceeded: {self.system_error_count} errors in the last hour"
            )
            
            # Could implement additional stability measures here
            # For now, just log the critical condition
    
    def _get_system_stability_status(self) -> str:
        """Get current system stability status."""
        if self.system_error_count > self.system_error_threshold:
            return "unstable"
        elif self.system_error_count > self.system_error_threshold * 0.7:
            return "degraded"
        else:
            return "stable"
    
    def _get_most_common_errors(self) -> List[Dict[str, Any]]:
        """Get most common error types."""
        error_types = {}
        
        for error in self.error_history[-100:]:  # Last 100 errors
            error_type = error.error_type
            if error_type not in error_types:
                error_types[error_type] = {
                    "error_type": error_type,
                    "count": 0,
                    "last_occurrence": error.timestamp
                }
            error_types[error_type]["count"] += 1
            if error.timestamp > error_types[error_type]["last_occurrence"]:
                error_types[error_type]["last_occurrence"] = error.timestamp
        
        # Sort by count and return top 5
        sorted_errors = sorted(error_types.values(), key=lambda x: x["count"], reverse=True)
        return sorted_errors[:5]


# Global error handler instance
_error_handler: Optional[WorkflowErrorHandler] = None


def get_error_handler() -> Optional[WorkflowErrorHandler]:
    """
    Get the global error handler instance.
    
    Returns:
        WorkflowErrorHandler instance or None if not initialized
    """
    return _error_handler


def initialize_error_handler(
    websocket_manager: WebSocketManager,
    hitl_interface: HITLInterface
) -> WorkflowErrorHandler:
    """
    Initialize the global error handler instance.
    
    Args:
        websocket_manager: WebSocket manager for notifications
        hitl_interface: HITL interface for error notifications
        
    Returns:
        Initialized WorkflowErrorHandler instance
    """
    global _error_handler
    _error_handler = WorkflowErrorHandler(websocket_manager, hitl_interface)
    return _error_handler


def reset_error_handler() -> None:
    """Reset the global error handler (useful for testing)."""
    global _error_handler
    _error_handler = None