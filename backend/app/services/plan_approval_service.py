"""
Plan Approval Service for managing plan approval workflows.

This service handles plan approval requests, modifications, rejections, and state management
for the multi-agent HITL (Human-in-the-Loop) workflow system.

Requirements covered:
- 2.1: Plan approval request formatting and management
- 2.2: Plan display with agent sequence and duration
- 2.3: Plan approval/rejection handling
- 2.4: Plan modification support
- 2.5: Plan approval state management
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

from app.models.ai_planner import AgentSequence, PlanApprovalRequest, PlanApprovalResponse
from app.services.approval_state_manager import get_approval_state_manager, WorkflowState
from app.services.websocket_service import get_websocket_manager, MessageType
from app.db.repositories import PlanRepository

logger = logging.getLogger(__name__)


class PlanApprovalStatus(Enum):
    """Plan approval status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    EXPIRED = "expired"


class PlanApprovalService:
    """
    Service for managing plan approval workflows in multi-agent HITL systems.
    
    This service provides comprehensive plan approval management including:
    - Plan approval request formatting and validation
    - Plan modification and rejection handling
    - State management across approval workflows
    - WebSocket communication for real-time updates
    """
    
    def __init__(self):
        self.approval_state_manager = get_approval_state_manager()
        self.websocket_manager = get_websocket_manager()
        self.approval_timeout_minutes = 30  # Default timeout for plan approvals
        
    async def create_plan_approval_request(
        self,
        plan_id: str,
        agent_sequence: AgentSequence,
        task_description: str,
        estimated_completion_time: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create and format a plan approval request.
        
        Args:
            plan_id: Unique plan identifier
            agent_sequence: Sequence of agents to be executed
            task_description: Original task description
            estimated_completion_time: Optional estimated completion time
            additional_metadata: Optional additional metadata
            
        Returns:
            Formatted plan approval request data
            
        Validates: Requirements 2.1, 2.2
        """
        try:
            logger.info(f"Creating plan approval request for plan {plan_id}")
            
            # Validate agent sequence
            if not agent_sequence.is_valid_sequence():
                raise ValueError("Invalid agent sequence provided")
            
            # Calculate estimated completion if not provided
            if not estimated_completion_time:
                estimated_seconds = agent_sequence.estimated_duration
                estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_seconds)
                estimated_completion_time = estimated_completion.isoformat() + "Z"
            
            # Set workflow state to awaiting plan approval
            self.approval_state_manager.set_workflow_state(
                plan_id, 
                WorkflowState.AWAITING_PLAN_APPROVAL,
                metadata={
                    "agent_sequence": agent_sequence.agents,
                    "task_description": task_description,
                    "estimated_completion": estimated_completion_time,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Format plan approval request
            plan_approval_data = {
                "plan_id": plan_id,
                "plan": {
                    "description": task_description,
                    "agent_sequence": agent_sequence.agents,
                    "estimated_duration": agent_sequence.estimated_duration,
                    "estimated_completion_time": estimated_completion_time,
                    "data_sources": self._extract_data_sources(agent_sequence),
                    "complexity": agent_sequence.task_analysis.complexity if hasattr(agent_sequence, 'task_analysis') else "medium",
                    "reasoning": agent_sequence.reasoning,
                    "total_steps": agent_sequence.get_total_steps()
                },
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "timeout": (datetime.utcnow() + timedelta(minutes=self.approval_timeout_minutes)).isoformat() + "Z"
            }
            
            # Add additional metadata if provided
            if additional_metadata:
                plan_approval_data["plan"].update(additional_metadata)
            
            logger.info(f"Plan approval request created for {plan_id}: {len(agent_sequence.agents)} agents, ~{agent_sequence.estimated_duration}s")
            
            return plan_approval_data
            
        except Exception as e:
            logger.error(f"Failed to create plan approval request for {plan_id}: {e}")
            # Set workflow state to failed
            self.approval_state_manager.set_workflow_state(
                plan_id, 
                WorkflowState.FAILED,
                metadata={"error": str(e)}
            )
            raise
    
    async def send_plan_approval_request(
        self,
        plan_id: str,
        agent_sequence: AgentSequence,
        task_description: str,
        estimated_completion_time: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send plan approval request via WebSocket.
        
        Args:
            plan_id: Unique plan identifier
            agent_sequence: Sequence of agents to be executed
            task_description: Original task description
            estimated_completion_time: Optional estimated completion time
            additional_metadata: Optional additional metadata
            
        Returns:
            True if request was sent successfully, False otherwise
            
        Validates: Requirements 2.1, 2.2
        """
        try:
            # Create plan approval request data
            approval_data = await self.create_plan_approval_request(
                plan_id=plan_id,
                agent_sequence=agent_sequence,
                task_description=task_description,
                estimated_completion_time=estimated_completion_time,
                additional_metadata=additional_metadata
            )
            
            # Send via WebSocket
            await self.websocket_manager.send_message(
                plan_id,
                {
                    "type": MessageType.PLAN_APPROVAL_REQUEST.value,
                    "data": approval_data
                },
                MessageType.PLAN_APPROVAL_REQUEST.value,
                priority=2  # High priority for approval requests
            )
            
            logger.info(f"Plan approval request sent for {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send plan approval request for {plan_id}: {e}")
            return False
    
    async def handle_plan_approval_response(
        self,
        plan_id: str,
        approved: bool,
        feedback: Optional[str] = None,
        modified_sequence: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Handle plan approval response from user.
        
        Args:
            plan_id: Unique plan identifier
            approved: Whether the plan was approved
            feedback: Optional user feedback
            modified_sequence: Optional modified agent sequence
            
        Returns:
            Response data with next steps
            
        Validates: Requirements 2.3, 2.4, 2.5
        """
        try:
            logger.info(f"Handling plan approval response for {plan_id}: approved={approved}")
            
            # Validate current state
            current_state = self.approval_state_manager.get_workflow_state(plan_id)
            if current_state != WorkflowState.AWAITING_PLAN_APPROVAL:
                raise ValueError(f"Invalid state for approval: {current_state}")
            
            if approved:
                return await self._handle_plan_approval(plan_id, feedback, modified_sequence)
            else:
                return await self._handle_plan_rejection(plan_id, feedback)
                
        except Exception as e:
            logger.error(f"Failed to handle plan approval response for {plan_id}: {e}")
            
            # Set workflow state to failed
            self.approval_state_manager.set_workflow_state(
                plan_id, 
                WorkflowState.FAILED,
                metadata={"error": str(e), "stage": "approval_response"}
            )
            
            return {
                "status": "error",
                "plan_id": plan_id,
                "error": str(e),
                "next_action": "retry_approval"
            }
    
    async def _handle_plan_approval(
        self,
        plan_id: str,
        feedback: Optional[str] = None,
        modified_sequence: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Handle plan approval (internal method).
        
        Args:
            plan_id: Unique plan identifier
            feedback: Optional user feedback
            modified_sequence: Optional modified agent sequence
            
        Returns:
            Response data for approved plan
        """
        try:
            # Get original agent sequence from approval state
            approval_history = self.approval_state_manager.get_approval_history(plan_id)
            if not approval_history:
                raise ValueError("No approval history found for plan")
            
            original_metadata = approval_history.get("metadata", {})
            original_agents = original_metadata.get("agent_sequence", [])
            
            # Use modified sequence if provided, otherwise use original
            final_sequence = modified_sequence if modified_sequence else original_agents
            
            # Create AgentSequence object for the approved sequence
            # Note: In a real implementation, you'd reconstruct the full AgentSequence
            # For now, we'll create a simplified version
            approved_sequence_data = {
                "agents": final_sequence,
                "reasoning": {agent: f"Approved for execution: {agent}" for agent in final_sequence},
                "estimated_duration": len(final_sequence) * 60,  # Simplified estimation
                "complexity_score": 0.5
            }
            
            # Store plan approval
            self.approval_state_manager.store_plan_approval(
                plan_id=plan_id,
                approved=True,
                agent_sequence=type('AgentSequence', (), {'agents': original_agents})(),  # Mock object
                feedback=feedback,
                modified_sequence=type('AgentSequence', (), {'agents': final_sequence})() if modified_sequence else None
            )
            
            # Update plan status in database
            await PlanRepository.update_status(plan_id, "approved")
            
            # Send approval confirmation via WebSocket
            await self.websocket_manager.send_message(
                plan_id,
                {
                    "type": MessageType.PLAN_APPROVAL_RESPONSE.value,
                    "data": {
                        "plan_id": plan_id,
                        "status": "approved",
                        "approved_sequence": final_sequence,
                        "sequence_modified": modified_sequence is not None,
                        "feedback": feedback,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "next_action": "execute_agents"
                    }
                },
                MessageType.PLAN_APPROVAL_RESPONSE.value,
                priority=2
            )
            
            logger.info(f"Plan {plan_id} approved with sequence: {' → '.join(final_sequence)}")
            
            return {
                "status": "approved",
                "plan_id": plan_id,
                "approved_sequence": final_sequence,
                "sequence_modified": modified_sequence is not None,
                "feedback": feedback,
                "next_action": "execute_agents"
            }
            
        except Exception as e:
            logger.error(f"Failed to handle plan approval for {plan_id}: {e}")
            raise
    
    async def _handle_plan_rejection(
        self,
        plan_id: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle plan rejection (internal method).
        
        Args:
            plan_id: Unique plan identifier
            feedback: Optional user feedback
            
        Returns:
            Response data for rejected plan
        """
        try:
            # Store plan rejection
            self.approval_state_manager.store_plan_approval(
                plan_id=plan_id,
                approved=False,
                agent_sequence=type('AgentSequence', (), {'agents': []})(),  # Mock empty sequence
                feedback=feedback
            )
            
            # Update plan status in database
            await PlanRepository.update_status(plan_id, "rejected")
            
            # Send rejection notification via WebSocket
            await self.websocket_manager.send_message(
                plan_id,
                {
                    "type": MessageType.PLAN_APPROVAL_RESPONSE.value,
                    "data": {
                        "plan_id": plan_id,
                        "status": "rejected",
                        "feedback": feedback,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "next_action": "modify_plan_or_cancel"
                    }
                },
                MessageType.PLAN_APPROVAL_RESPONSE.value,
                priority=2
            )
            
            logger.info(f"Plan {plan_id} rejected. Feedback: {feedback}")
            
            return {
                "status": "rejected",
                "plan_id": plan_id,
                "feedback": feedback,
                "next_action": "modify_plan_or_cancel"
            }
            
        except Exception as e:
            logger.error(f"Failed to handle plan rejection for {plan_id}: {e}")
            raise
    
    async def modify_plan(
        self,
        plan_id: str,
        new_task_description: Optional[str] = None,
        new_agent_sequence: Optional[List[str]] = None,
        modification_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Modify an existing plan and request re-approval.
        
        Args:
            plan_id: Unique plan identifier
            new_task_description: Optional new task description
            new_agent_sequence: Optional new agent sequence
            modification_reason: Optional reason for modification
            
        Returns:
            Response data for modified plan
            
        Validates: Requirements 2.4, 2.5
        """
        try:
            logger.info(f"Modifying plan {plan_id}")
            
            # Get current approval history
            approval_history = self.approval_state_manager.get_approval_history(plan_id)
            if not approval_history:
                raise ValueError("No approval history found for plan")
            
            current_metadata = approval_history.get("metadata", {})
            
            # Use new values or fall back to current ones
            task_description = new_task_description or current_metadata.get("task_description", "")
            agent_sequence = new_agent_sequence or current_metadata.get("agent_sequence", [])
            
            if not task_description or not agent_sequence:
                raise ValueError("Task description and agent sequence are required for modification")
            
            # Create modified AgentSequence
            # Note: In a real implementation, you'd use the AI Planner to regenerate
            modified_sequence = type('AgentSequence', (), {
                'agents': agent_sequence,
                'reasoning': {agent: f"Modified plan: {agent}" for agent in agent_sequence},
                'estimated_duration': len(agent_sequence) * 60,
                'get_total_steps': lambda: len(agent_sequence),
                'is_valid_sequence': lambda: len(agent_sequence) > 0
            })()
            
            # Reset workflow state to planning
            self.approval_state_manager.set_workflow_state(
                plan_id, 
                WorkflowState.PLANNING,
                metadata={
                    "modification_reason": modification_reason,
                    "modified_at": datetime.utcnow().isoformat(),
                    "original_sequence": current_metadata.get("agent_sequence", []),
                    "new_sequence": agent_sequence
                }
            )
            
            # Send new approval request
            success = await self.send_plan_approval_request(
                plan_id=plan_id,
                agent_sequence=modified_sequence,
                task_description=task_description,
                additional_metadata={
                    "modification_reason": modification_reason,
                    "modified_at": datetime.utcnow().isoformat()
                }
            )
            
            if success:
                logger.info(f"Plan {plan_id} modified and re-submitted for approval")
                return {
                    "status": "modified",
                    "plan_id": plan_id,
                    "new_sequence": agent_sequence,
                    "modification_reason": modification_reason,
                    "next_action": "awaiting_approval"
                }
            else:
                raise Exception("Failed to send modified plan approval request")
                
        except Exception as e:
            logger.error(f"Failed to modify plan {plan_id}: {e}")
            
            # Set workflow state to failed
            self.approval_state_manager.set_workflow_state(
                plan_id, 
                WorkflowState.FAILED,
                metadata={"error": str(e), "stage": "plan_modification"}
            )
            
            return {
                "status": "error",
                "plan_id": plan_id,
                "error": str(e),
                "next_action": "retry_modification"
            }
    
    def get_plan_approval_status(self, plan_id: str) -> Dict[str, Any]:
        """
        Get current plan approval status.
        
        Args:
            plan_id: Unique plan identifier
            
        Returns:
            Current approval status and metadata
            
        Validates: Requirements 2.5
        """
        try:
            # Get workflow state
            workflow_state = self.approval_state_manager.get_workflow_state(plan_id)
            
            # Get approval history
            approval_history = self.approval_state_manager.get_approval_history(plan_id)
            
            # Determine approval status
            if workflow_state == WorkflowState.AWAITING_PLAN_APPROVAL:
                status = PlanApprovalStatus.PENDING
            elif workflow_state == WorkflowState.PLAN_APPROVED:
                status = PlanApprovalStatus.APPROVED
            elif workflow_state == WorkflowState.PLAN_REJECTED:
                status = PlanApprovalStatus.REJECTED
            elif workflow_state == WorkflowState.PLANNING:
                status = PlanApprovalStatus.MODIFIED
            else:
                status = PlanApprovalStatus.PENDING
            
            return {
                "plan_id": plan_id,
                "status": status.value,
                "workflow_state": workflow_state.value if workflow_state else None,
                "approval_history": approval_history,
                "is_approved": self.approval_state_manager.is_plan_approved(plan_id),
                "execution_allowed": self.approval_state_manager.is_execution_allowed(plan_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get plan approval status for {plan_id}: {e}")
            return {
                "plan_id": plan_id,
                "status": "error",
                "error": str(e)
            }
    
    def is_plan_approved(self, plan_id: str) -> bool:
        """
        Check if a plan is approved for execution.
        
        Args:
            plan_id: Unique plan identifier
            
        Returns:
            True if plan is approved, False otherwise
            
        Validates: Requirements 2.5
        """
        return self.approval_state_manager.is_plan_approved(plan_id)
    
    def is_execution_allowed(self, plan_id: str) -> bool:
        """
        Check if execution is allowed for a plan.
        
        Args:
            plan_id: Unique plan identifier
            
        Returns:
            True if execution is allowed, False otherwise
            
        Validates: Requirements 2.5
        """
        return self.approval_state_manager.is_execution_allowed(plan_id)
    
    async def cleanup_expired_approvals(self) -> int:
        """
        Clean up expired plan approvals.
        
        Returns:
            Number of expired approvals cleaned up
            
        Validates: Requirements 2.5
        """
        try:
            logger.info("Cleaning up expired plan approvals")
            
            # Get all approval histories
            expired_count = 0
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.approval_timeout_minutes)
            
            # This would need to be implemented with proper storage
            # For now, we'll use the approval state manager's cleanup
            cleaned_workflows = self.approval_state_manager.cleanup_completed_workflows(
                max_age_hours=self.approval_timeout_minutes / 60
            )
            
            logger.info(f"Cleaned up {cleaned_workflows} expired workflows")
            return cleaned_workflows
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired approvals: {e}")
            return 0
    
    def _extract_data_sources(self, agent_sequence: AgentSequence) -> List[str]:
        """
        Extract data sources from agent sequence.
        
        Args:
            agent_sequence: Agent sequence to analyze
            
        Returns:
            List of data sources required
        """
        data_sources = []
        agent_to_source = {
            "gmail": "email",
            "invoice": "bill_com",
            "salesforce": "salesforce",
            "zoho": "zoho",
            "audit": "audit_logs",
            "analysis": "aggregated_data"
        }
        
        for agent in agent_sequence.agents:
            source = agent_to_source.get(agent.lower())
            if source and source not in data_sources:
                data_sources.append(source)
        
        return data_sources
    
    def get_approval_statistics(self) -> Dict[str, Any]:
        """
        Get approval statistics for monitoring.
        
        Returns:
            Dictionary with approval statistics
        """
        try:
            # Get state statistics from approval state manager
            state_stats = self.approval_state_manager.get_state_statistics()
            
            # Calculate approval-specific metrics
            total_workflows = state_stats["total_workflows"]
            awaiting_approval = state_stats["state_counts"].get("awaiting_plan_approval", 0)
            approved = state_stats["state_counts"].get("plan_approved", 0)
            rejected = state_stats["state_counts"].get("plan_rejected", 0)
            
            approval_rate = (approved / max(approved + rejected, 1)) * 100
            
            return {
                "total_workflows": total_workflows,
                "awaiting_approval": awaiting_approval,
                "approved": approved,
                "rejected": rejected,
                "approval_rate_percent": round(approval_rate, 2),
                "active_executions": state_stats["active_executions"],
                "state_distribution": state_stats["state_counts"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get approval statistics: {e}")
            return {
                "error": str(e),
                "total_workflows": 0,
                "awaiting_approval": 0,
                "approved": 0,
                "rejected": 0
            }


# Global plan approval service instance
_plan_approval_service: Optional[PlanApprovalService] = None


def get_plan_approval_service() -> PlanApprovalService:
    """
    Get or create the global plan approval service instance.
    
    Returns:
        PlanApprovalService instance
    """
    global _plan_approval_service
    if _plan_approval_service is None:
        _plan_approval_service = PlanApprovalService()
    return _plan_approval_service


def reset_plan_approval_service() -> None:
    """Reset the global plan approval service (useful for testing)."""
    global _plan_approval_service
    _plan_approval_service = None