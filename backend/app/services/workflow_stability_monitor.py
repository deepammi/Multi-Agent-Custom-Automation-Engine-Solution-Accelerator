"""
Workflow Stability Monitor for ensuring system stability.

This module monitors workflow health and takes preventive actions
to maintain system stability when individual workflows fail.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from enum import Enum

from app.services.error_handler import WorkflowErrorHandler, ErrorSeverity

logger = logging.getLogger(__name__)


class StabilityStatus(Enum):
    """System stability status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"
    CRITICAL = "critical"


@dataclass
class WorkflowHealth:
    """Health metrics for a workflow."""
    plan_id: str
    user_id: str
    error_count: int
    last_error_time: Optional[datetime]
    success_count: int
    total_executions: int
    average_duration: float
    status: StabilityStatus
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_executions == 0:
            return 100.0
        return (self.success_count / self.total_executions) * 100.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        return 100.0 - self.success_rate


class WorkflowStabilityMonitor:
    """
    Monitor and maintain workflow stability across the system.
    
    Tracks workflow health metrics, detects stability issues,
    and takes preventive actions to maintain system stability.
    """
    
    def __init__(
        self,
        error_handler: WorkflowErrorHandler,
        stability_check_interval: int = 300,  # 5 minutes
        max_error_rate_threshold: float = 20.0,  # 20% error rate
        critical_error_threshold: int = 10,  # 10 errors per workflow
        user_workflow_limit: int = 10
    ):
        self.error_handler = error_handler
        self.stability_check_interval = stability_check_interval
        self.max_error_rate_threshold = max_error_rate_threshold
        self.critical_error_threshold = critical_error_threshold
        self.user_workflow_limit = user_workflow_limit
        
        # Workflow tracking
        self.workflow_health: Dict[str, WorkflowHealth] = {}
        self.user_workflows: Dict[str, Set[str]] = {}  # user_id -> set of plan_ids
        self.blocked_users: Set[str] = set()
        self.quarantined_workflows: Set[str] = set()
        
        # System metrics
        self.system_start_time = datetime.utcnow()
        self.total_workflows_processed = 0
        self.total_successful_workflows = 0
        self.stability_checks_performed = 0
        
        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
        
        logger.info("WorkflowStabilityMonitor initialized")
    
    async def start_monitoring(self) -> None:
        """Start the stability monitoring background task."""
        if self._is_monitoring:
            logger.warning("Stability monitoring is already running")
            return
        
        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Workflow stability monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop the stability monitoring background task."""
        if not self._is_monitoring:
            return
        
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Workflow stability monitoring stopped")
    
    async def record_workflow_start(
        self,
        plan_id: str,
        user_id: str
    ) -> bool:
        """
        Record workflow start and check if it should be allowed.
        
        Args:
            plan_id: Workflow plan identifier
            user_id: User identifier
            
        Returns:
            True if workflow should be allowed, False if blocked
        """
        # Check if user is blocked
        if user_id in self.blocked_users:
            logger.warning(f"Workflow {plan_id} blocked - user {user_id} is blocked")
            return False
        
        # Check if workflow is quarantined
        if plan_id in self.quarantined_workflows:
            logger.warning(f"Workflow {plan_id} blocked - workflow is quarantined")
            return False
        
        # Check user workflow limits
        user_workflow_count = len(self.user_workflows.get(user_id, set()))
        if user_workflow_count >= self.user_workflow_limit:
            logger.warning(
                f"Workflow {plan_id} blocked - user {user_id} has {user_workflow_count} active workflows"
            )
            return False
        
        # Initialize workflow health if not exists
        if plan_id not in self.workflow_health:
            self.workflow_health[plan_id] = WorkflowHealth(
                plan_id=plan_id,
                user_id=user_id,
                error_count=0,
                last_error_time=None,
                success_count=0,
                total_executions=0,
                average_duration=0.0,
                status=StabilityStatus.HEALTHY
            )
        
        # Track user workflows
        if user_id not in self.user_workflows:
            self.user_workflows[user_id] = set()
        self.user_workflows[user_id].add(plan_id)
        
        # Update metrics
        self.total_workflows_processed += 1
        self.workflow_health[plan_id].total_executions += 1
        
        logger.debug(f"Workflow {plan_id} start recorded for user {user_id}")
        return True
    
    async def record_workflow_success(
        self,
        plan_id: str,
        execution_duration: float
    ) -> None:
        """
        Record successful workflow completion.
        
        Args:
            plan_id: Workflow plan identifier
            execution_duration: Workflow execution duration in seconds
        """
        if plan_id not in self.workflow_health:
            logger.warning(f"Recording success for unknown workflow {plan_id}")
            return
        
        health = self.workflow_health[plan_id]
        health.success_count += 1
        
        # Update average duration
        if health.success_count == 1:
            health.average_duration = execution_duration
        else:
            health.average_duration = (
                (health.average_duration * (health.success_count - 1) + execution_duration) /
                health.success_count
            )
        
        # Update system metrics
        self.total_successful_workflows += 1
        
        # Update workflow status
        await self._update_workflow_status(plan_id)
        
        # Clean up user tracking
        await self._cleanup_completed_workflow(plan_id)
        
        logger.debug(f"Workflow {plan_id} success recorded, duration: {execution_duration:.2f}s")
    
    async def record_workflow_failure(
        self,
        plan_id: str,
        error_severity: ErrorSeverity,
        execution_duration: float
    ) -> None:
        """
        Record workflow failure and update stability metrics.
        
        Args:
            plan_id: Workflow plan identifier
            error_severity: Severity of the error that caused failure
            execution_duration: Workflow execution duration before failure
        """
        if plan_id not in self.workflow_health:
            logger.warning(f"Recording failure for unknown workflow {plan_id}")
            return
        
        health = self.workflow_health[plan_id]
        health.error_count += 1
        health.last_error_time = datetime.utcnow()
        
        # Update workflow status
        await self._update_workflow_status(plan_id)
        
        # Take stability actions based on error severity and frequency
        await self._handle_workflow_failure(plan_id, error_severity)
        
        # Clean up user tracking
        await self._cleanup_completed_workflow(plan_id)
        
        logger.warning(
            f"Workflow {plan_id} failure recorded, error count: {health.error_count}, "
            f"error rate: {health.error_rate:.1f}%"
        )
    
    def get_system_stability_report(self) -> Dict[str, Any]:
        """
        Get comprehensive system stability report.
        
        Returns:
            Dictionary with system stability metrics
        """
        now = datetime.utcnow()
        uptime = (now - self.system_start_time).total_seconds()
        
        # Calculate overall system metrics
        overall_success_rate = (
            (self.total_successful_workflows / self.total_workflows_processed * 100)
            if self.total_workflows_processed > 0 else 100.0
        )
        
        # Workflow status distribution
        status_counts = {status.value: 0 for status in StabilityStatus}
        for health in self.workflow_health.values():
            status_counts[health.status.value] += 1
        
        # User metrics
        active_users = len(self.user_workflows)
        blocked_users_count = len(self.blocked_users)
        quarantined_workflows_count = len(self.quarantined_workflows)
        
        # System stability determination
        system_status = self._determine_system_stability()
        
        return {
            "system_status": system_status.value,
            "uptime_seconds": uptime,
            "total_workflows_processed": self.total_workflows_processed,
            "total_successful_workflows": self.total_successful_workflows,
            "overall_success_rate": round(overall_success_rate, 2),
            "workflow_status_distribution": status_counts,
            "active_users": active_users,
            "blocked_users": blocked_users_count,
            "quarantined_workflows": quarantined_workflows_count,
            "stability_checks_performed": self.stability_checks_performed,
            "error_handler_stats": self.error_handler.get_error_statistics(),
            "recommendations": self._generate_stability_recommendations()
        }
    
    def get_workflow_health_report(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get health report for a specific workflow.
        
        Args:
            plan_id: Workflow plan identifier
            
        Returns:
            Dictionary with workflow health metrics or None if not found
        """
        if plan_id not in self.workflow_health:
            return None
        
        health = self.workflow_health[plan_id]
        error_history = self.error_handler.get_workflow_error_history(plan_id)
        
        return {
            "plan_id": health.plan_id,
            "user_id": health.user_id,
            "status": health.status.value,
            "error_count": health.error_count,
            "success_count": health.success_count,
            "total_executions": health.total_executions,
            "success_rate": round(health.success_rate, 2),
            "error_rate": round(health.error_rate, 2),
            "average_duration": round(health.average_duration, 2),
            "last_error_time": health.last_error_time.isoformat() if health.last_error_time else None,
            "is_quarantined": plan_id in self.quarantined_workflows,
            "error_history_count": len(error_history),
            "recent_errors": [e.to_dict() for e in error_history[-5:]]  # Last 5 errors
        }
    
    def get_user_stability_report(self, user_id: str) -> Dict[str, Any]:
        """
        Get stability report for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with user stability metrics
        """
        user_workflows = self.user_workflows.get(user_id, set())
        user_workflow_health = [
            self.workflow_health[plan_id] for plan_id in user_workflows
            if plan_id in self.workflow_health
        ]
        
        # Calculate user metrics
        total_executions = sum(h.total_executions for h in user_workflow_health)
        total_successes = sum(h.success_count for h in user_workflow_health)
        total_errors = sum(h.error_count for h in user_workflow_health)
        
        user_success_rate = (
            (total_successes / total_executions * 100)
            if total_executions > 0 else 100.0
        )
        
        return {
            "user_id": user_id,
            "is_blocked": user_id in self.blocked_users,
            "active_workflows": len(user_workflows),
            "workflow_limit": self.user_workflow_limit,
            "total_executions": total_executions,
            "total_successes": total_successes,
            "total_errors": total_errors,
            "success_rate": round(user_success_rate, 2),
            "workflow_statuses": {
                h.plan_id: h.status.value for h in user_workflow_health
            }
        }
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._is_monitoring:
            try:
                await self._perform_stability_check()
                await asyncio.sleep(self.stability_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stability monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_stability_check(self) -> None:
        """Perform comprehensive stability check."""
        self.stability_checks_performed += 1
        
        # Check workflow health
        unhealthy_workflows = []
        for plan_id, health in self.workflow_health.items():
            if health.status in [StabilityStatus.UNSTABLE, StabilityStatus.CRITICAL]:
                unhealthy_workflows.append(plan_id)
        
        # Check system stability
        system_status = self._determine_system_stability()
        
        # Take corrective actions if needed
        if system_status in [StabilityStatus.UNSTABLE, StabilityStatus.CRITICAL]:
            await self._take_stability_actions(system_status, unhealthy_workflows)
        
        logger.debug(
            f"Stability check completed: {system_status.value}, "
            f"unhealthy workflows: {len(unhealthy_workflows)}"
        )
    
    async def _update_workflow_status(self, plan_id: str) -> None:
        """Update workflow stability status based on metrics."""
        if plan_id not in self.workflow_health:
            return
        
        health = self.workflow_health[plan_id]
        
        # Determine status based on error rate and count
        if health.error_count >= self.critical_error_threshold:
            health.status = StabilityStatus.CRITICAL
        elif health.error_rate > self.max_error_rate_threshold:
            health.status = StabilityStatus.UNSTABLE
        elif health.error_rate > self.max_error_rate_threshold * 0.5:
            health.status = StabilityStatus.DEGRADED
        else:
            health.status = StabilityStatus.HEALTHY
    
    async def _handle_workflow_failure(
        self,
        plan_id: str,
        error_severity: ErrorSeverity
    ) -> None:
        """Handle workflow failure and take appropriate actions."""
        health = self.workflow_health[plan_id]
        
        # Quarantine workflow if it has too many errors
        if health.error_count >= self.critical_error_threshold:
            self.quarantined_workflows.add(plan_id)
            logger.warning(f"Workflow {plan_id} quarantined due to {health.error_count} errors")
        
        # Block user if they have too many failing workflows
        user_id = health.user_id
        user_workflows = self.user_workflows.get(user_id, set())
        failing_workflows = sum(
            1 for wf_id in user_workflows
            if wf_id in self.workflow_health and
            self.workflow_health[wf_id].status in [StabilityStatus.UNSTABLE, StabilityStatus.CRITICAL]
        )
        
        if failing_workflows >= 3:  # Block user if 3+ workflows are failing
            self.blocked_users.add(user_id)
            logger.warning(f"User {user_id} blocked due to {failing_workflows} failing workflows")
    
    async def _cleanup_completed_workflow(self, plan_id: str) -> None:
        """Clean up tracking for completed workflow."""
        if plan_id not in self.workflow_health:
            return
        
        health = self.workflow_health[plan_id]
        user_id = health.user_id
        
        # Remove from user's active workflows
        if user_id in self.user_workflows:
            self.user_workflows[user_id].discard(plan_id)
            if not self.user_workflows[user_id]:
                del self.user_workflows[user_id]
    
    def _determine_system_stability(self) -> StabilityStatus:
        """Determine overall system stability status."""
        if self.total_workflows_processed == 0:
            return StabilityStatus.HEALTHY
        
        overall_success_rate = (
            self.total_successful_workflows / self.total_workflows_processed * 100
        )
        
        # Count workflows by status
        critical_count = sum(
            1 for h in self.workflow_health.values()
            if h.status == StabilityStatus.CRITICAL
        )
        unstable_count = sum(
            1 for h in self.workflow_health.values()
            if h.status == StabilityStatus.UNSTABLE
        )
        
        # Determine system status
        if critical_count > 5 or overall_success_rate < 50:
            return StabilityStatus.CRITICAL
        elif unstable_count > 10 or overall_success_rate < 80:
            return StabilityStatus.UNSTABLE
        elif unstable_count > 5 or overall_success_rate < 90:
            return StabilityStatus.DEGRADED
        else:
            return StabilityStatus.HEALTHY
    
    async def _take_stability_actions(
        self,
        system_status: StabilityStatus,
        unhealthy_workflows: List[str]
    ) -> None:
        """Take corrective actions based on system stability."""
        if system_status == StabilityStatus.CRITICAL:
            # Critical: Quarantine all unhealthy workflows
            for plan_id in unhealthy_workflows:
                self.quarantined_workflows.add(plan_id)
            logger.critical(f"System critical: quarantined {len(unhealthy_workflows)} workflows")
        
        elif system_status == StabilityStatus.UNSTABLE:
            # Unstable: Quarantine worst workflows
            worst_workflows = sorted(
                unhealthy_workflows,
                key=lambda pid: self.workflow_health[pid].error_rate,
                reverse=True
            )[:5]  # Quarantine top 5 worst workflows
            
            for plan_id in worst_workflows:
                self.quarantined_workflows.add(plan_id)
            logger.warning(f"System unstable: quarantined {len(worst_workflows)} worst workflows")
    
    def _generate_stability_recommendations(self) -> List[str]:
        """Generate recommendations for improving system stability."""
        recommendations = []
        
        system_status = self._determine_system_stability()
        
        if system_status in [StabilityStatus.UNSTABLE, StabilityStatus.CRITICAL]:
            recommendations.append("Review and fix failing workflows")
            recommendations.append("Check system resources and performance")
        
        if len(self.blocked_users) > 0:
            recommendations.append(f"Review {len(self.blocked_users)} blocked users")
        
        if len(self.quarantined_workflows) > 0:
            recommendations.append(f"Investigate {len(self.quarantined_workflows)} quarantined workflows")
        
        error_stats = self.error_handler.get_error_statistics()
        if error_stats["recent_errors_1h"] > 20:
            recommendations.append("High error rate detected - investigate common error patterns")
        
        if not recommendations:
            recommendations.append("System is stable - continue monitoring")
        
        return recommendations


# Global stability monitor instance
_stability_monitor: Optional[WorkflowStabilityMonitor] = None


def get_stability_monitor() -> Optional[WorkflowStabilityMonitor]:
    """
    Get the global stability monitor instance.
    
    Returns:
        WorkflowStabilityMonitor instance or None if not initialized
    """
    return _stability_monitor


def initialize_stability_monitor(
    error_handler: WorkflowErrorHandler
) -> WorkflowStabilityMonitor:
    """
    Initialize the global stability monitor instance.
    
    Args:
        error_handler: Error handler for integration
        
    Returns:
        Initialized WorkflowStabilityMonitor instance
    """
    global _stability_monitor
    _stability_monitor = WorkflowStabilityMonitor(error_handler)
    return _stability_monitor


def reset_stability_monitor() -> None:
    """Reset the global stability monitor (useful for testing)."""
    global _stability_monitor
    _stability_monitor = None