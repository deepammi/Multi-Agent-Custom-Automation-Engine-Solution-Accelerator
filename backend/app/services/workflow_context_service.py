"""
Simple Workflow Context Service for basic execution tracking.

This service provides simple workflow state tracking without complex revision logic.
Focus on basic execution history, approval status, and restart workflow capabilities.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Simple workflow status states."""
    CREATED = "created"
    PLANNING = "planning"
    AWAITING_PLAN_APPROVAL = "awaiting_plan_approval"
    PLAN_APPROVED = "plan_approved"
    PLAN_REJECTED = "plan_rejected"
    EXECUTING = "executing"
    AWAITING_FINAL_APPROVAL = "awaiting_final_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTARTED = "restarted"


@dataclass
class WorkflowEvent:
    """Simple workflow event for tracking."""
    timestamp: str
    event_type: str
    agent_name: Optional[str] = None
    message: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WorkflowContext:
    """Simple workflow context for a plan."""
    plan_id: str
    session_id: str
    task_description: str
    status: WorkflowStatus
    created_at: str
    updated_at: str
    agent_sequence: List[str]
    current_step: int
    total_steps: int
    events: List[WorkflowEvent]
    plan_approved: Optional[bool] = None
    final_approved: Optional[bool] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "plan_id": self.plan_id,
            "session_id": self.session_id,
            "task_description": self.task_description,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "agent_sequence": self.agent_sequence,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_percentage": (self.current_step / self.total_steps * 100) if self.total_steps > 0 else 0,
            "plan_approved": self.plan_approved,
            "final_approved": self.final_approved,
            "error_message": self.error_message,
            "events": [asdict(event) for event in self.events],
            "event_count": len(self.events)
        }


class WorkflowContextService:
    """
    Simple service for workflow context tracking.
    
    Provides basic execution history, status tracking, and restart capabilities
    without complex revision logic.
    """
    
    def __init__(self):
        self.contexts: Dict[str, WorkflowContext] = {}
        
    def create_workflow_context(
        self,
        plan_id: str,
        session_id: str,
        task_description: str,
        agent_sequence: List[str]
    ) -> WorkflowContext:
        """Create a new workflow context."""
        now = datetime.utcnow().isoformat() + "Z"
        
        context = WorkflowContext(
            plan_id=plan_id,
            session_id=session_id,
            task_description=task_description,
            status=WorkflowStatus.CREATED,
            created_at=now,
            updated_at=now,
            agent_sequence=agent_sequence,
            current_step=0,
            total_steps=len(agent_sequence),
            events=[]
        )
        
        # Store context first so add_event can find it
        self.contexts[plan_id] = context
        
        # Add creation event
        self.add_event(
            plan_id,
            "workflow_created",
            message=f"Workflow created with {len(agent_sequence)} agents"
        )
        
        logger.info(f"📝 Created workflow context for plan {plan_id}")
        return context
    
    def get_workflow_context(self, plan_id: str) -> Optional[WorkflowContext]:
        """Get workflow context by plan ID."""
        return self.contexts.get(plan_id)
    
    def update_workflow_status(
        self,
        plan_id: str,
        status: WorkflowStatus,
        message: str = ""
    ) -> bool:
        """Update workflow status."""
        context = self.contexts.get(plan_id)
        if not context:
            logger.warning(f"No context found for plan {plan_id}")
            return False
        
        old_status = context.status
        context.status = status
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # Add status change event
        self.add_event(
            plan_id,
            "status_changed",
            message=f"Status changed from {old_status.value} to {status.value}. {message}".strip()
        )
        
        logger.info(f"📊 Updated workflow {plan_id} status: {old_status.value} → {status.value}")
        return True
    
    def update_progress(
        self,
        plan_id: str,
        current_step: int,
        current_agent: str = ""
    ) -> bool:
        """Update workflow progress."""
        context = self.contexts.get(plan_id)
        if not context:
            return False
        
        context.current_step = current_step
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # Add progress event
        progress_pct = (current_step / context.total_steps * 100) if context.total_steps > 0 else 0
        self.add_event(
            plan_id,
            "progress_updated",
            agent_name=current_agent,
            message=f"Progress: {current_step}/{context.total_steps} ({progress_pct:.1f}%)"
        )
        
        return True
    
    def add_event(
        self,
        plan_id: str,
        event_type: str,
        agent_name: Optional[str] = None,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add an event to workflow context."""
        context = self.contexts.get(plan_id)
        if not context:
            return False
        
        event = WorkflowEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=event_type,
            agent_name=agent_name,
            message=message,
            metadata=metadata or {}
        )
        
        context.events.append(event)
        context.updated_at = event.timestamp
        
        return True
    
    def set_plan_approval(
        self,
        plan_id: str,
        approved: bool,
        feedback: str = ""
    ) -> bool:
        """Set plan approval status."""
        context = self.contexts.get(plan_id)
        if not context:
            return False
        
        context.plan_approved = approved
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        if approved:
            context.status = WorkflowStatus.PLAN_APPROVED
            self.add_event(
                plan_id,
                "plan_approved",
                message=f"Plan approved by user. {feedback}".strip()
            )
        else:
            context.status = WorkflowStatus.PLAN_REJECTED
            self.add_event(
                plan_id,
                "plan_rejected",
                message=f"Plan rejected by user. {feedback}".strip()
            )
        
        return True
    
    def set_final_approval(
        self,
        plan_id: str,
        approved: bool,
        feedback: str = ""
    ) -> bool:
        """Set final results approval status."""
        context = self.contexts.get(plan_id)
        if not context:
            return False
        
        context.final_approved = approved
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        if approved:
            context.status = WorkflowStatus.COMPLETED
            self.add_event(
                plan_id,
                "final_approved",
                message=f"Final results approved by user. {feedback}".strip()
            )
        else:
            # User wants to restart - mark as restarted
            context.status = WorkflowStatus.RESTARTED
            self.add_event(
                plan_id,
                "restart_requested",
                message=f"User requested workflow restart. {feedback}".strip()
            )
        
        return True
    
    def set_error(
        self,
        plan_id: str,
        error_message: str,
        agent_name: Optional[str] = None
    ) -> bool:
        """Set workflow error status."""
        context = self.contexts.get(plan_id)
        if not context:
            return False
        
        context.status = WorkflowStatus.FAILED
        context.error_message = error_message
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        self.add_event(
            plan_id,
            "error_occurred",
            agent_name=agent_name,
            message=f"Workflow failed: {error_message}"
        )
        
        return True
    
    def get_workflow_summary(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of workflow execution."""
        context = self.contexts.get(plan_id)
        if not context:
            return None
        
        # Count events by type
        event_counts = {}
        agent_events = {}
        
        for event in context.events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
            
            if event.agent_name:
                if event.agent_name not in agent_events:
                    agent_events[event.agent_name] = []
                agent_events[event.agent_name].append({
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "message": event.message
                })
        
        # Calculate duration
        duration_seconds = 0
        if context.events:
            start_time = datetime.fromisoformat(context.created_at.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(context.updated_at.replace('Z', '+00:00'))
            duration_seconds = (end_time - start_time).total_seconds()
        
        return {
            "plan_id": plan_id,
            "status": context.status.value,
            "task_description": context.task_description,
            "duration_seconds": duration_seconds,
            "progress": {
                "current_step": context.current_step,
                "total_steps": context.total_steps,
                "percentage": (context.current_step / context.total_steps * 100) if context.total_steps > 0 else 0
            },
            "approvals": {
                "plan_approved": context.plan_approved,
                "final_approved": context.final_approved
            },
            "agent_sequence": context.agent_sequence,
            "event_counts": event_counts,
            "agent_events": agent_events,
            "total_events": len(context.events),
            "error_message": context.error_message,
            "created_at": context.created_at,
            "updated_at": context.updated_at
        }
    
    def get_recent_events(
        self,
        plan_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent events for a workflow."""
        context = self.contexts.get(plan_id)
        if not context:
            return []
        
        # Get most recent events
        recent_events = context.events[-limit:] if len(context.events) > limit else context.events
        return [asdict(event) for event in recent_events]
    
    def get_workflows_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all workflows for a session."""
        workflows = []
        
        for context in self.contexts.values():
            if context.session_id == session_id:
                workflows.append(context.to_dict())
        
        # Sort by creation time (most recent first)
        workflows.sort(key=lambda w: w["created_at"], reverse=True)
        return workflows
    
    def cleanup_old_contexts(self, max_age_hours: int = 24) -> int:
        """Clean up old workflow contexts."""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        removed_count = 0
        
        to_remove = []
        for plan_id, context in self.contexts.items():
            created_time = datetime.fromisoformat(context.created_at.replace('Z', '+00:00')).timestamp()
            if created_time < cutoff_time:
                to_remove.append(plan_id)
        
        for plan_id in to_remove:
            del self.contexts[plan_id]
            removed_count += 1
        
        if removed_count > 0:
            logger.info(f"🧹 Cleaned up {removed_count} old workflow contexts")
        
        return removed_count
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        if not self.contexts:
            return {
                "total_workflows": 0,
                "status_distribution": {},
                "average_events_per_workflow": 0,
                "total_events": 0
            }
        
        status_counts = {}
        total_events = 0
        
        for context in self.contexts.values():
            status = context.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            total_events += len(context.events)
        
        return {
            "total_workflows": len(self.contexts),
            "status_distribution": status_counts,
            "average_events_per_workflow": total_events / len(self.contexts),
            "total_events": total_events
        }


# Global service instance
_workflow_context_service: Optional[WorkflowContextService] = None


def get_workflow_context_service() -> WorkflowContextService:
    """Get or create the global workflow context service instance."""
    global _workflow_context_service
    if _workflow_context_service is None:
        _workflow_context_service = WorkflowContextService()
    return _workflow_context_service


def reset_workflow_context_service() -> None:
    """Reset the global service (useful for testing)."""
    global _workflow_context_service
    _workflow_context_service = None