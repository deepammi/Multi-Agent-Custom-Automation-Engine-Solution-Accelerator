"""
Approval State Manager for preventing execution without HITL approval.

This module manages the approval state of workflows to ensure that
no agents execute without explicit human approval of the generated plan.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from enum import Enum

from app.models.ai_planner import AgentSequence

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """States of workflow execution."""
    PLANNING = "planning"
    AWAITING_PLAN_APPROVAL = "awaiting_plan_approval"
    PLAN_APPROVED = "plan_approved"
    PLAN_REJECTED = "plan_rejected"
    EXECUTING = "executing"
    AWAITING_RESULT_APPROVAL = "awaiting_result_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ApprovalStateManager:
    """
    Manages approval state to prevent execution without explicit HITL approval.
    
    Ensures that workflows cannot proceed to execution without proper approval
    and maintains audit trail of all approval decisions.
    """
    
    def __init__(self):
        self.workflow_states: Dict[str, WorkflowState] = {}
        self.approval_data: Dict[str, Dict[str, Any]] = {}
        self.execution_locks: Set[str] = set()
        
    def set_workflow_state(
        self,
        plan_id: str,
        state: WorkflowState,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Set the workflow state for a plan.
        
        Args:
            plan_id: Plan identifier
            state: New workflow state
            metadata: Optional metadata to store with state
        """
        old_state = self.workflow_states.get(plan_id)
        self.workflow_states[plan_id] = state
        
        # Store metadata
        if plan_id not in self.approval_data:
            self.approval_data[plan_id] = {}
        
        self.approval_data[plan_id].update({
            "current_state": state.value,
            "previous_state": old_state.value if old_state else None,
            "state_changed_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        })
        
        logger.info(f"🔄 Workflow state changed for {plan_id}: {old_state} → {state}")
    
    def get_workflow_state(self, plan_id: str) -> Optional[WorkflowState]:
        """
        Get the current workflow state for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Current workflow state or None if not found
        """
        return self.workflow_states.get(plan_id)
    
    def is_execution_allowed(self, plan_id: str) -> bool:
        """
        Check if execution is allowed for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if execution is allowed, False otherwise
        """
        state = self.get_workflow_state(plan_id)
        
        # Only allow execution if plan is approved
        if state != WorkflowState.PLAN_APPROVED:
            logger.warning(f"⚠️  Execution not allowed for {plan_id}: state is {state}")
            return False
        
        # Check if already executing (prevent concurrent execution)
        if plan_id in self.execution_locks:
            logger.warning(f"⚠️  Execution not allowed for {plan_id}: already executing")
            return False
        
        return True
    
    def acquire_execution_lock(self, plan_id: str) -> bool:
        """
        Acquire execution lock for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if lock acquired, False if already locked
        """
        if plan_id in self.execution_locks:
            return False
        
        self.execution_locks.add(plan_id)
        self.set_workflow_state(plan_id, WorkflowState.EXECUTING)
        
        logger.info(f"🔒 Execution lock acquired for {plan_id}")
        return True
    
    def release_execution_lock(self, plan_id: str) -> None:
        """
        Release execution lock for a plan.
        
        Args:
            plan_id: Plan identifier
        """
        self.execution_locks.discard(plan_id)
        # Reset state back to approved so it can be executed again if needed
        if self.get_workflow_state(plan_id) == WorkflowState.EXECUTING:
            self.set_workflow_state(plan_id, WorkflowState.PLAN_APPROVED)
        logger.info(f"🔓 Execution lock released for {plan_id}")
    
    def store_plan_approval(
        self,
        plan_id: str,
        approved: bool,
        agent_sequence: AgentSequence,
        feedback: Optional[str] = None,
        modified_sequence: Optional[AgentSequence] = None
    ) -> None:
        """
        Store plan approval decision.
        
        Args:
            plan_id: Plan identifier
            approved: Whether plan was approved
            agent_sequence: Original agent sequence
            feedback: Optional feedback from HITL
            modified_sequence: Optional modified sequence
        """
        if plan_id not in self.approval_data:
            self.approval_data[plan_id] = {}
        
        approval_data = {
            "plan_approved": approved,
            "original_sequence": agent_sequence.agents,
            "approved_sequence": modified_sequence.agents if modified_sequence else agent_sequence.agents,
            "feedback": feedback,
            "approved_at": datetime.utcnow().isoformat(),
            "sequence_modified": modified_sequence is not None
        }
        
        self.approval_data[plan_id]["plan_approval"] = approval_data
        
        # Update workflow state
        if approved:
            self.set_workflow_state(plan_id, WorkflowState.PLAN_APPROVED)
        else:
            self.set_workflow_state(plan_id, WorkflowState.PLAN_REJECTED)
        
        logger.info(f"📋 Plan approval stored for {plan_id}: {'approved' if approved else 'rejected'}")
    
    def store_result_approval(
        self,
        plan_id: str,
        approved: bool,
        final_results: Dict[str, Any],
        feedback: Optional[str] = None
    ) -> None:
        """
        Store result approval decision.
        
        Args:
            plan_id: Plan identifier
            approved: Whether results were approved
            final_results: Final workflow results
            feedback: Optional feedback from HITL
        """
        if plan_id not in self.approval_data:
            self.approval_data[plan_id] = {}
        
        approval_data = {
            "results_approved": approved,
            "final_results": final_results,
            "feedback": feedback,
            "approved_at": datetime.utcnow().isoformat()
        }
        
        self.approval_data[plan_id]["result_approval"] = approval_data
        
        # Update workflow state
        if approved:
            self.set_workflow_state(plan_id, WorkflowState.COMPLETED)
        else:
            # Results rejected - workflow needs revision
            self.set_workflow_state(plan_id, WorkflowState.AWAITING_RESULT_APPROVAL)
        
        logger.info(f"✅ Result approval stored for {plan_id}: {'approved' if approved else 'rejected'}")
    
    def get_approved_sequence(self, plan_id: str) -> Optional[AgentSequence]:
        """
        Get the approved agent sequence for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Approved agent sequence or None if not approved
        """
        if plan_id not in self.approval_data:
            return None
        
        plan_approval = self.approval_data[plan_id].get("plan_approval")
        if not plan_approval or not plan_approval.get("plan_approved"):
            return None
        
        # Return the approved sequence (could be modified)
        approved_agents = plan_approval.get("approved_sequence")
        if not approved_agents:
            return None
        
        # Create a basic AgentSequence (would need more complete data in real implementation)
        # This is a simplified version for the approval state manager
        return approved_agents
    
    def is_plan_approved(self, plan_id: str) -> bool:
        """
        Check if a plan has been approved.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if plan is approved, False otherwise
        """
        if plan_id not in self.approval_data:
            return False
        
        plan_approval = self.approval_data[plan_id].get("plan_approval")
        return plan_approval and plan_approval.get("plan_approved", False)
    
    def is_result_approved(self, plan_id: str) -> bool:
        """
        Check if results have been approved.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if results are approved, False otherwise
        """
        if plan_id not in self.approval_data:
            return False
        
        result_approval = self.approval_data[plan_id].get("result_approval")
        return result_approval and result_approval.get("results_approved", False)
    
    def get_approval_history(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete approval history for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Approval history or None if not found
        """
        return self.approval_data.get(plan_id)
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """
        Clean up completed workflows older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for completed workflows
            
        Returns:
            Number of workflows cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        plans_to_remove = []
        for plan_id, data in self.approval_data.items():
            state = self.workflow_states.get(plan_id)
            
            # Only clean up completed, failed, or timeout workflows
            if state in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.TIMEOUT]:
                state_changed_at = data.get("state_changed_at")
                if state_changed_at:
                    try:
                        changed_time = datetime.fromisoformat(state_changed_at.replace("Z", "+00:00"))
                        if changed_time < cutoff_time:
                            plans_to_remove.append(plan_id)
                    except ValueError:
                        # Invalid timestamp, remove it
                        plans_to_remove.append(plan_id)
        
        # Remove old workflows
        for plan_id in plans_to_remove:
            self.workflow_states.pop(plan_id, None)
            self.approval_data.pop(plan_id, None)
            self.execution_locks.discard(plan_id)
            cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} completed workflows")
        
        return cleaned_count
    
    def get_state_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about workflow states for monitoring.
        
        Returns:
            Dictionary with state statistics
        """
        state_counts = {}
        for state in WorkflowState:
            state_counts[state.value] = 0
        
        for state in self.workflow_states.values():
            state_counts[state.value] += 1
        
        return {
            "total_workflows": len(self.workflow_states),
            "active_executions": len(self.execution_locks),
            "state_counts": state_counts,
            "approval_data_count": len(self.approval_data)
        }


# Global approval state manager instance
_approval_state_manager: Optional[ApprovalStateManager] = None


def get_approval_state_manager() -> ApprovalStateManager:
    """
    Get or create the global approval state manager instance.
    
    Returns:
        ApprovalStateManager instance
    """
    global _approval_state_manager
    if _approval_state_manager is None:
        _approval_state_manager = ApprovalStateManager()
    return _approval_state_manager


def reset_approval_state_manager() -> None:
    """Reset the global approval state manager (useful for testing)."""
    global _approval_state_manager
    _approval_state_manager = None