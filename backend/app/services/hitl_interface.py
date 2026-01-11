"""
Human-in-the-Loop (HITL) Interface for plan and result approval workflows.

This module provides the core HITL functionality for the LangGraph orchestrator,
enabling human approval of AI-generated plans and final results with enhanced
presentation formats, plan modification capabilities, comprehensive logging,
and correlation ID tracking.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import uuid

from app.models.ai_planner import (
    AgentSequence, 
    PlanApprovalRequest, 
    PlanApprovalResponse
)
from app.services.workflow_logger import (
    get_workflow_logger, 
    EventType, 
    LogLevel
)

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Status of approval requests."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    MODIFIED = "modified"
    CANCELLED = "cancelled"


class ModificationType(Enum):
    """Types of plan modifications."""
    AGENT_REORDER = "agent_reorder"
    AGENT_ADDITION = "agent_addition"
    AGENT_REMOVAL = "agent_removal"
    PARAMETER_CHANGE = "parameter_change"
    STEP_MODIFICATION = "step_modification"


class PlanModification:
    """Represents a modification to an execution plan."""
    
    def __init__(
        self,
        modification_type: ModificationType,
        description: str,
        original_value: Any = None,
        new_value: Any = None,
        affected_agents: Optional[List[str]] = None,
        justification: Optional[str] = None
    ):
        self.id = str(uuid.uuid4())
        self.modification_type = modification_type
        self.description = description
        self.original_value = original_value
        self.new_value = new_value
        self.affected_agents = affected_agents or []
        self.justification = justification
        self.timestamp = datetime.utcnow()


class EnhancedPlanPresentation:
    """Enhanced presentation format for human reviewers."""
    
    def __init__(
        self,
        plan_id: str,
        task_description: str,
        agent_sequence: AgentSequence,
        risk_assessment: Optional[Dict[str, Any]] = None,
        estimated_costs: Optional[Dict[str, float]] = None
    ):
        self.plan_id = plan_id
        self.task_description = task_description
        self.agent_sequence = agent_sequence
        self.risk_assessment = risk_assessment or {}
        self.estimated_costs = estimated_costs or {}
        self.presentation_timestamp = datetime.utcnow()
    
    def to_human_readable_format(self) -> Dict[str, Any]:
        """Convert plan to human-readable format for approval."""
        return {
            "plan_overview": {
                "plan_id": self.plan_id,
                "task_description": self.task_description,
                "total_agents": len(self.agent_sequence.agents),
                "estimated_duration": f"{self.agent_sequence.estimated_duration} seconds",
                "complexity_score": self.agent_sequence.complexity_score,
                "created_at": self.presentation_timestamp.isoformat()
            },
            "execution_sequence": [
                {
                    "step_number": idx + 1,
                    "agent_name": agent_name,
                    "agent_type": agent_name,  # Use agent name as type for simplicity
                    "description": self.agent_sequence.reasoning.get(agent_name, f"Execute {agent_name} agent"),
                    "estimated_duration": f"{self.agent_sequence.estimated_duration // len(self.agent_sequence.agents)}s",
                    "required_tools": [],  # Simplified for testing
                    "dependencies": [],  # Simplified for testing
                    "risk_level": self._assess_agent_risk(agent_name)
                }
                for idx, agent_name in enumerate(self.agent_sequence.agents)
            ],
            "risk_assessment": {
                "overall_risk": self._calculate_overall_risk(),
                "potential_issues": self._identify_potential_issues(),
                "mitigation_strategies": self._suggest_mitigations()
            },
            "resource_requirements": {
                "estimated_costs": self.estimated_costs,
                "external_services": self._identify_external_services(),
                "data_sources": self._identify_data_sources()
            },
            "modification_options": self._generate_modification_options(),
            "approval_recommendations": self._generate_approval_recommendations()
        }
    
    def _assess_agent_risk(self, agent_name: str) -> str:
        """Assess risk level for individual agent."""
        # Simple risk assessment based on agent name
        high_risk_agents = ['invoice', 'salesforce', 'zoho']
        medium_risk_agents = ['gmail', 'analysis']
        
        if agent_name.lower() in high_risk_agents:
            return "high"
        elif agent_name.lower() in medium_risk_agents:
            return "medium"
        return "low"
    
    def _calculate_overall_risk(self) -> str:
        """Calculate overall risk level for the plan."""
        risk_scores = []
        for agent_name in self.agent_sequence.agents:
            risk = self._assess_agent_risk(agent_name)
            if risk == "high":
                risk_scores.append(3)
            elif risk == "medium":
                risk_scores.append(2)
            else:
                risk_scores.append(1)
        
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 1
        
        if avg_risk >= 2.5:
            return "high"
        elif avg_risk >= 1.5:
            return "medium"
        return "low"
    
    def _identify_potential_issues(self) -> List[str]:
        """Identify potential issues with the plan."""
        issues = []
        
        # Check for long execution chains
        if len(self.agent_sequence.agents) > 5:
            issues.append("Long execution chain may increase failure risk")
        
        # Check for high-risk agents
        high_risk_count = sum(
            1 for agent in self.agent_sequence.agents
            if self._assess_agent_risk(agent) == "high"
        )
        if high_risk_count > 2:
            issues.append("Multiple high-risk agents may compound failure probability")
        
        # Check for estimated duration
        if self.agent_sequence.estimated_duration > 300:  # 5 minutes
            issues.append("Long execution time may lead to timeout issues")
        
        return issues
    
    def _suggest_mitigations(self) -> List[str]:
        """Suggest mitigation strategies."""
        mitigations = []
        
        if len(self.agent_sequence.agents) > 5:
            mitigations.append("Consider breaking into smaller sub-workflows")
        
        if self.agent_sequence.estimated_duration > 300:
            mitigations.append("Add intermediate checkpoints for long-running processes")
        
        mitigations.append("Enable detailed logging for troubleshooting")
        mitigations.append("Set up monitoring alerts for agent failures")
        
        return mitigations
    
    def _identify_external_services(self) -> List[str]:
        """Identify external services that will be used."""
        services = set()
        for agent_name in self.agent_sequence.agents:
            if agent_name == 'gmail':
                services.add("Gmail API")
            elif agent_name == 'invoice':
                services.add("Bill.com API")
            elif agent_name in ['salesforce', 'zoho']:
                services.add("Salesforce API" if agent_name == 'salesforce' else "Zoho API")
        return list(services)
    
    def _identify_data_sources(self) -> List[str]:
        """Identify data sources that will be accessed."""
        sources = set()
        for agent_name in self.agent_sequence.agents:
            if agent_name == 'gmail':
                sources.add("Email communications")
            elif agent_name == 'invoice':
                sources.add("Billing and payment records")
            elif agent_name in ['salesforce', 'zoho']:
                sources.add("Customer relationship data")
        return list(sources)
    
    def _generate_modification_options(self) -> List[Dict[str, Any]]:
        """Generate available modification options."""
        options = []
        
        # Agent reordering options
        if len(self.agent_sequence.agents) > 1:
            options.append({
                "type": "agent_reorder",
                "description": "Reorder agent execution sequence",
                "impact": "Changes execution flow and data dependencies"
            })
        
        # Agent removal options
        if len(self.agent_sequence.agents) > 2:
            options.append({
                "type": "agent_removal",
                "description": "Remove optional agents to reduce complexity",
                "impact": "Faster execution but potentially less comprehensive results"
            })
        
        # Parameter modification
        options.append({
            "type": "parameter_change",
            "description": "Modify agent parameters or search criteria",
            "impact": "Changes scope or focus of data collection"
        })
        
        return options
    
    def _generate_approval_recommendations(self) -> Dict[str, Any]:
        """Generate approval recommendations based on plan analysis."""
        overall_risk = self._calculate_overall_risk()
        
        if overall_risk == "low":
            recommendation = "APPROVE"
            confidence = "high"
            reasoning = "Low risk plan with standard agent sequence"
        elif overall_risk == "medium":
            recommendation = "APPROVE_WITH_MONITORING"
            confidence = "medium"
            reasoning = "Medium risk plan - recommend enhanced monitoring"
        else:
            recommendation = "REVIEW_REQUIRED"
            confidence = "low"
            reasoning = "High risk plan - manual review recommended"
        
        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning,
            "suggested_modifications": self._suggest_plan_improvements()
        }
    
    def _suggest_plan_improvements(self) -> List[str]:
        """Suggest specific plan improvements."""
        suggestions = []
        
        if self.agent_sequence.estimated_duration > 300:
            suggestions.append("Add timeout handling for long-running agents")
        
        if len(self.agent_sequence.agents) > 5:
            suggestions.append("Consider parallel execution for independent agents")
        
        return suggestions


class ApprovalResult:
    """Result of an approval request with enhanced tracking."""
    
    def __init__(
        self,
        plan_id: str,
        status: ApprovalStatus,
        approved: bool = False,
        feedback: Optional[str] = None,
        modified_sequence: Optional[AgentSequence] = None,
        modifications: Optional[List[PlanModification]] = None,
        timeout_seconds: Optional[float] = None,
        reviewer_id: Optional[str] = None,
        approval_confidence: Optional[str] = None
    ):
        self.plan_id = plan_id
        self.status = status
        self.approved = approved
        self.feedback = feedback
        self.modified_sequence = modified_sequence
        self.modifications = modifications or []
        self.timeout_seconds = timeout_seconds
        self.reviewer_id = reviewer_id
        self.approval_confidence = approval_confidence
        self.timestamp = datetime.utcnow()
        self.approval_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "approval_id": self.approval_id,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "approved": self.approved,
            "feedback": self.feedback,
            "modifications": [
                {
                    "id": mod.id,
                    "type": mod.modification_type.value,
                    "description": mod.description,
                    "justification": mod.justification,
                    "timestamp": mod.timestamp.isoformat()
                }
                for mod in self.modifications
            ],
            "timeout_seconds": self.timeout_seconds,
            "reviewer_id": self.reviewer_id,
            "approval_confidence": self.approval_confidence,
            "timestamp": self.timestamp.isoformat()
        }


class HITLInterface:
    """
    Enhanced Human-in-the-Loop interface for approval workflows.
    
    Handles plan approval, result approval, and progress updates via WebSocket.
    Manages approval state with enhanced presentation formats, plan modification
    capabilities, comprehensive approval response handling, and structured logging
    with correlation ID tracking.
    """
    
    def __init__(self, default_timeout: int = 300):  # 5 minutes default
        self.default_timeout = default_timeout
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.approval_history: Dict[str, List[ApprovalResult]] = {}
        self.modification_templates: Dict[str, Dict[str, Any]] = self._load_modification_templates()
        self.workflow_logger = get_workflow_logger()
        
    def _load_modification_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined modification templates."""
        return {
            "reduce_complexity": {
                "description": "Remove optional agents to reduce execution complexity",
                "type": ModificationType.AGENT_REMOVAL,
                "suggested_removals": ["analysis", "secondary_validation"]
            },
            "add_validation": {
                "description": "Add validation steps for high-risk operations",
                "type": ModificationType.AGENT_ADDITION,
                "suggested_additions": ["validation_agent", "audit_agent"]
            },
            "reorder_for_efficiency": {
                "description": "Reorder agents for optimal data flow",
                "type": ModificationType.AGENT_REORDER,
                "optimization_strategy": "dependency_based"
            },
            "add_checkpoints": {
                "description": "Add intermediate checkpoints for long workflows",
                "type": ModificationType.STEP_MODIFICATION,
                "checkpoint_frequency": "every_3_agents"
            }
        }
        
    async def request_plan_approval(
        self,
        plan_id: str,
        agent_sequence: AgentSequence,
        task_description: str,
        websocket_manager: Optional[Any] = None,
        timeout_seconds: Optional[int] = None,
        reviewer_id: Optional[str] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> ApprovalResult:
        """
        Request HITL approval for an AI-generated agent sequence with enhanced presentation.
        
        Args:
            plan_id: Unique identifier for the plan
            agent_sequence: AI-generated sequence of agents
            task_description: Original task description
            websocket_manager: WebSocket manager for real-time communication
            timeout_seconds: Timeout for approval (defaults to class default)
            reviewer_id: Optional identifier for the human reviewer
            risk_assessment: Optional risk assessment data
            correlation_id: Correlation ID for tracking related events
            
        Returns:
            ApprovalResult with approval decision and any modifications
        """
        # Create correlation ID if not provided
        if correlation_id is None:
            correlation_id = self.workflow_logger.create_correlation_id("hitl_approval")
        
        # Log approval request start
        self.workflow_logger.log_event(
            event_type=EventType.HITL_REQUEST,
            message=f"Requesting plan approval for {len(agent_sequence.agents)} agents",
            correlation_id=correlation_id,
            plan_id=plan_id,
            agent_count=len(agent_sequence.agents),
            estimated_duration=agent_sequence.estimated_duration,
            complexity_score=agent_sequence.complexity_score,
            reviewer_id=reviewer_id
        )
        
        logger.info(f"🔍 Requesting enhanced plan approval for plan {plan_id}")
        
        timeout = timeout_seconds or self.default_timeout
        
        # Create enhanced plan presentation
        presentation = EnhancedPlanPresentation(
            plan_id=plan_id,
            task_description=task_description,
            agent_sequence=agent_sequence,
            risk_assessment=risk_assessment
        )
        
        # Log presentation creation
        self.workflow_logger.log_event(
            event_type=EventType.PLAN_APPROVAL,
            message="Created enhanced plan presentation for human review",
            correlation_id=correlation_id,
            plan_id=plan_id,
            presentation_risk_level=presentation._calculate_overall_risk(),
            potential_issues_count=len(presentation._identify_potential_issues())
        )
        
        # Create approval request with enhanced data
        approval_request = PlanApprovalRequest(
            plan_id=plan_id,
            agent_sequence=agent_sequence,
            task_description=task_description,
            estimated_completion_time=f"{agent_sequence.estimated_duration}s"
        )
        
        # Store pending approval with enhanced data
        self.pending_approvals[plan_id] = {
            "type": "plan_approval",
            "request": approval_request,
            "presentation": presentation,
            "reviewer_id": reviewer_id,
            "correlation_id": correlation_id,
            "created_at": datetime.utcnow(),
            "timeout_at": datetime.utcnow() + timedelta(seconds=timeout),
            "websocket_manager": websocket_manager,
            "modification_history": []
        }
        
        # Send enhanced approval request via WebSocket
        if websocket_manager:
            await self._send_enhanced_plan_approval_request(
                websocket_manager, 
                plan_id, 
                presentation,
                correlation_id
            )
            
            # Log WebSocket message sent
            self.workflow_logger.log_event(
                event_type=EventType.WEBSOCKET_MESSAGE,
                message="Sent enhanced plan approval request via WebSocket",
                correlation_id=correlation_id,
                plan_id=plan_id,
                message_type="enhanced_plan_approval_request"
            )
        
        # Wait for approval or timeout
        start_time = datetime.utcnow()
        result = await self._wait_for_approval(plan_id, timeout, correlation_id)
        response_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log approval result
        self.workflow_logger.log_event(
            event_type=EventType.HITL_RESPONSE,
            message=f"Plan approval {result.status.value}: {result.approved}",
            level=LogLevel.INFO if result.approved else LogLevel.WARNING,
            correlation_id=correlation_id,
            plan_id=plan_id,
            execution_time=response_time,
            success=result.approved,
            approval_status=result.status.value,
            modifications_count=len(result.modifications),
            reviewer_id=result.reviewer_id,
            approval_confidence=result.approval_confidence
        )
        
        # Store in history
        if plan_id not in self.approval_history:
            self.approval_history[plan_id] = []
        self.approval_history[plan_id].append(result)
        
        # Clean up pending approval
        self.pending_approvals.pop(plan_id, None)
        
        logger.info(f"📋 Enhanced plan approval result for {plan_id}: {result.status.value}")
        return result
    
    async def request_result_approval(
        self,
        plan_id: str,
        final_results: Dict[str, Any],
        websocket_manager: Optional[Any] = None,
        timeout_seconds: Optional[int] = None
    ) -> ApprovalResult:
        """
        Request HITL approval for final workflow results.
        
        Args:
            plan_id: Unique identifier for the plan
            final_results: Final results from workflow execution
            websocket_manager: WebSocket manager for real-time communication
            timeout_seconds: Timeout for approval
            
        Returns:
            ApprovalResult with approval decision
        """
        logger.info(f"📊 Requesting result approval for plan {plan_id}")
        
        timeout = timeout_seconds or self.default_timeout
        
        # Store pending approval
        self.pending_approvals[plan_id] = {
            "type": "result_approval",
            "results": final_results,
            "created_at": datetime.utcnow(),
            "timeout_at": datetime.utcnow() + timedelta(seconds=timeout),
            "websocket_manager": websocket_manager
        }
        
        # Send result approval request via WebSocket
        if websocket_manager:
            await self._send_result_approval_request(
                websocket_manager,
                plan_id,
                final_results
            )
        
        # Wait for approval or timeout
        result = await self._wait_for_approval(plan_id, timeout)
        
        # Store in history
        if plan_id not in self.approval_history:
            self.approval_history[plan_id] = []
        self.approval_history[plan_id].append(result)
        
        # Clean up pending approval
        self.pending_approvals.pop(plan_id, None)
        
        logger.info(f"✅ Result approval result for {plan_id}: {result.status.value}")
        return result
    
    async def submit_approval_response(
        self,
        plan_id: str,
        approved: bool,
        feedback: Optional[str] = None,
        modified_sequence: Optional[AgentSequence] = None,
        modifications: Optional[List[PlanModification]] = None,
        reviewer_id: Optional[str] = None,
        approval_confidence: Optional[str] = None
    ) -> bool:
        """
        Submit enhanced approval response from HITL with modification support.
        
        Args:
            plan_id: Plan identifier
            approved: Whether the plan/result is approved
            feedback: Optional feedback from HITL
            modified_sequence: Optional modified agent sequence
            modifications: List of specific modifications made
            reviewer_id: Identifier of the human reviewer
            approval_confidence: Confidence level of the approval decision
            
        Returns:
            True if response was accepted, False if no pending approval
        """
        if plan_id not in self.pending_approvals:
            logger.warning(f"⚠️  No pending approval found for plan {plan_id}")
            return False
        
        pending = self.pending_approvals[plan_id]
        correlation_id = pending.get("correlation_id")
        
        # Log approval response received
        self.workflow_logger.log_event(
            event_type=EventType.HITL_RESPONSE,
            message=f"Received approval response: {'approved' if approved else 'rejected'}",
            correlation_id=correlation_id,
            plan_id=plan_id,
            success=approved,
            reviewer_id=reviewer_id,
            approval_confidence=approval_confidence,
            feedback_provided=feedback is not None,
            modifications_provided=modifications is not None and len(modifications) > 0
        )
        
        # Validate modifications if provided
        validated_modifications = []
        if modifications:
            validated_modifications = await self._validate_modifications(
                plan_id, modifications, pending["request"].agent_sequence
            )
            
            # Log modification validation
            self.workflow_logger.log_event(
                event_type=EventType.PLAN_MODIFICATION,
                message=f"Validated {len(validated_modifications)} of {len(modifications)} modifications",
                correlation_id=correlation_id,
                plan_id=plan_id,
                original_modifications=len(modifications),
                validated_modifications=len(validated_modifications)
            )
        
        # Create enhanced response
        response = PlanApprovalResponse(
            plan_id=plan_id,
            approved=approved,
            feedback=feedback,
            modified_sequence=modified_sequence
        )
        
        # Store enhanced response data
        pending["response"] = response
        pending["response_received"] = True
        pending["modifications"] = validated_modifications
        pending["reviewer_id"] = reviewer_id
        pending["approval_confidence"] = approval_confidence
        pending["response_timestamp"] = datetime.utcnow()
        
        # Log modification details
        if validated_modifications:
            logger.info(f"📝 Plan {plan_id} approved with {len(validated_modifications)} modifications")
            for mod in validated_modifications:
                logger.info(f"   - {mod.modification_type.value}: {mod.description}")
                
                # Log each modification
                self.workflow_logger.log_event(
                    event_type=EventType.PLAN_MODIFICATION,
                    message=f"Applied modification: {mod.modification_type.value}",
                    correlation_id=correlation_id,
                    plan_id=plan_id,
                    modification_type=mod.modification_type.value,
                    modification_description=mod.description,
                    modification_justification=mod.justification,
                    affected_agents=mod.affected_agents
                )
        
        logger.info(f"📝 Enhanced approval response received for {plan_id}: {'approved' if approved else 'rejected'}")
        return True
    
    async def request_plan_modification(
        self,
        plan_id: str,
        modification_type: ModificationType,
        modification_details: Dict[str, Any],
        justification: str,
        websocket_manager: Optional[Any] = None
    ) -> bool:
        """
        Request specific plan modifications during approval process.
        
        Args:
            plan_id: Plan identifier
            modification_type: Type of modification requested
            modification_details: Details of the modification
            justification: Justification for the modification
            websocket_manager: WebSocket manager for communication
            
        Returns:
            True if modification request was processed
        """
        if plan_id not in self.pending_approvals:
            logger.warning(f"⚠️  No pending approval found for plan {plan_id}")
            return False
        
        pending = self.pending_approvals[plan_id]
        
        # Create modification object
        modification = PlanModification(
            modification_type=modification_type,
            description=modification_details.get("description", ""),
            original_value=modification_details.get("original_value"),
            new_value=modification_details.get("new_value"),
            affected_agents=modification_details.get("affected_agents", []),
            justification=justification
        )
        
        # Add to modification history
        if "modification_history" not in pending:
            pending["modification_history"] = []
        pending["modification_history"].append(modification)
        
        # Send modification request via WebSocket
        if websocket_manager:
            await self._send_modification_request(
                websocket_manager, plan_id, modification
            )
        
        logger.info(f"🔧 Plan modification requested for {plan_id}: {modification_type.value}")
        return True
    
    async def apply_modification_template(
        self,
        plan_id: str,
        template_name: str,
        websocket_manager: Optional[Any] = None
    ) -> Optional[AgentSequence]:
        """
        Apply a predefined modification template to a plan.
        
        Args:
            plan_id: Plan identifier
            template_name: Name of the modification template
            websocket_manager: WebSocket manager for communication
            
        Returns:
            Modified agent sequence or None if template not found
        """
        if plan_id not in self.pending_approvals:
            logger.warning(f"⚠️  No pending approval found for plan {plan_id}")
            return None
        
        if template_name not in self.modification_templates:
            logger.warning(f"⚠️  Unknown modification template: {template_name}")
            return None
        
        pending = self.pending_approvals[plan_id]
        original_sequence = pending["request"].agent_sequence
        template = self.modification_templates[template_name]
        
        # Apply template modifications
        modified_sequence = await self._apply_template_modifications(
            original_sequence, template
        )
        
        if modified_sequence:
            # Create modification record
            modification = PlanModification(
                modification_type=template["type"],
                description=template["description"],
                original_value=len(original_sequence.agents),
                new_value=len(modified_sequence.agents),
                justification=f"Applied template: {template_name}"
            )
            
            # Store modification
            if "modification_history" not in pending:
                pending["modification_history"] = []
            pending["modification_history"].append(modification)
            
            # Send update via WebSocket
            if websocket_manager:
                await self._send_template_applied_notification(
                    websocket_manager, plan_id, template_name, modification
                )
            
            logger.info(f"🔧 Applied modification template '{template_name}' to plan {plan_id}")
        
        return modified_sequence
    
    async def _validate_modifications(
        self,
        plan_id: str,
        modifications: List[PlanModification],
        original_sequence: AgentSequence
    ) -> List[PlanModification]:
        """Validate that modifications are feasible and safe."""
        validated = []
        
        for mod in modifications:
            # Basic validation - ensure modification makes sense
            if mod.modification_type == ModificationType.AGENT_REMOVAL:
                if len(original_sequence.agents) <= 1:
                    logger.warning(f"⚠️  Cannot remove agent - only one agent remaining")
                    continue
            
            elif mod.modification_type == ModificationType.AGENT_REORDER:
                if not mod.affected_agents:
                    logger.warning(f"⚠️  Agent reorder requires affected_agents list")
                    continue
            
            # Add more validation rules as needed
            validated.append(mod)
        
        return validated
    
    async def _apply_template_modifications(
        self,
        original_sequence: AgentSequence,
        template: Dict[str, Any]
    ) -> Optional[AgentSequence]:
        """Apply template modifications to create a new sequence."""
        # This is a simplified implementation - in practice, this would
        # involve more complex logic to modify the agent sequence
        
        if template["type"] == ModificationType.AGENT_REMOVAL:
            # Remove suggested agents
            suggested_removals = template.get("suggested_removals", [])
            filtered_agents = [
                agent for agent in original_sequence.agents
                if not any(removal in agent.name.lower() for removal in suggested_removals)
            ]
            
            if len(filtered_agents) < len(original_sequence.agents):
                # Create new sequence with filtered agents
                new_sequence = AgentSequence(
                    agents=filtered_agents,
                    reasoning=f"Modified: {template['description']}",
                    estimated_duration=original_sequence.estimated_duration * 0.8,  # Assume 20% reduction
                    complexity_score=max(1, original_sequence.complexity_score - 1)
                )
                return new_sequence
        
        # Add more template application logic as needed
        return None
    
    async def send_progress_update(
        self,
        plan_id: str,
        current_step: int,
        total_steps: int,
        current_agent: str,
        websocket_manager: Optional[Any] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Send real-time progress updates during workflow execution.
        
        Args:
            plan_id: Plan identifier
            current_step: Current step number (1-indexed)
            total_steps: Total number of steps
            current_agent: Currently executing agent
            websocket_manager: WebSocket manager for communication
            correlation_id: Correlation ID for tracking
        """
        if not websocket_manager:
            return
        
        progress_percentage = (current_step / total_steps) * 100
        
        # Log progress update
        if correlation_id:
            self.workflow_logger.log_event(
                event_type=EventType.PERFORMANCE_METRIC,
                message=f"Progress update: {current_step}/{total_steps} ({current_agent})",
                correlation_id=correlation_id,
                plan_id=plan_id,
                current_step=current_step,
                total_steps=total_steps,
                current_agent=current_agent,
                progress_percentage=progress_percentage
            )
        
        await websocket_manager.send_message(plan_id, {
            "type": "progress_update",
            "data": {
                "plan_id": plan_id,
                "current_step": current_step,
                "total_steps": total_steps,
                "current_agent": current_agent,
                "progress_percentage": round(progress_percentage, 1),
                "status": "in_progress",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
        
        logger.debug(f"📈 Progress update sent for {plan_id}: {current_step}/{total_steps} ({current_agent})")
    
    async def send_error_notification(
        self,
        plan_id: str,
        agent_name: str,
        error_message: str,
        error_type: str,
        websocket_manager: Optional[Any] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Send error notification to HITL via WebSocket.
        
        Args:
            plan_id: Plan identifier
            agent_name: Name of the failed agent
            error_message: Error message
            error_type: Type of error
            websocket_manager: WebSocket manager for communication
            correlation_id: Correlation ID for tracking
        """
        # Log error notification
        if correlation_id:
            self.workflow_logger.log_event(
                event_type=EventType.AGENT_ERROR,
                message=f"Agent error notification: {agent_name} - {error_type}",
                level=LogLevel.ERROR,
                correlation_id=correlation_id,
                plan_id=plan_id,
                agent_name=agent_name,
                error_message=error_message,
                error_type=error_type,
                success=False
            )
        
        if not websocket_manager:
            logger.warning(f"No WebSocket manager available for error notification: {plan_id}")
            return
        
        await websocket_manager.send_message(plan_id, {
            "type": "error_notification",
            "data": {
                "plan_id": plan_id,
                "agent_name": agent_name,
                "error_message": error_message,
                "error_type": error_type,
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
        
        logger.info(f"🚨 Error notification sent for {plan_id}: {agent_name} - {error_type}")
    
    def is_plan_approved(self, plan_id: str) -> bool:
        """
        Check if a plan has been approved.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if plan is approved, False otherwise
        """
        if plan_id not in self.approval_history:
            return False
        
        # Get the most recent plan approval
        plan_approvals = [
            result for result in self.approval_history[plan_id]
            if result.status in [ApprovalStatus.APPROVED, ApprovalStatus.MODIFIED]
        ]
        
        return len(plan_approvals) > 0
    
    def get_approved_sequence(self, plan_id: str) -> Optional[AgentSequence]:
        """
        Get the approved agent sequence for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Approved agent sequence or None if not approved
        """
        if plan_id not in self.approval_history:
            return None
        
        # Find the most recent approved plan
        for result in reversed(self.approval_history[plan_id]):
            if result.status == ApprovalStatus.APPROVED:
                # Return original sequence from pending approval
                if plan_id in self.pending_approvals:
                    return self.pending_approvals[plan_id]["request"].agent_sequence
            elif result.status == ApprovalStatus.MODIFIED:
                return result.modified_sequence
        
        return None
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """
        Get statistics about approval requests for monitoring.
        
        Returns:
            Dictionary with approval statistics and comprehensive metrics
        """
        total_requests = sum(len(history) for history in self.approval_history.values())
        pending_count = len(self.pending_approvals)
        
        if total_requests == 0:
            return {
                "total_requests": 0,
                "pending_requests": pending_count,
                "approval_rate": 0.0,
                "average_response_time": 0.0,
                "workflow_logger_stats": self.workflow_logger.get_performance_summary()
            }
        
        approved_count = 0
        rejected_count = 0
        modified_count = 0
        timeout_count = 0
        response_times = []
        
        for history in self.approval_history.values():
            for result in history:
                if result.status == ApprovalStatus.APPROVED:
                    approved_count += 1
                elif result.status == ApprovalStatus.REJECTED:
                    rejected_count += 1
                elif result.status == ApprovalStatus.MODIFIED:
                    modified_count += 1
                elif result.status == ApprovalStatus.TIMEOUT:
                    timeout_count += 1
                
                if result.timeout_seconds:
                    response_times.append(result.timeout_seconds)
        
        approval_rate = (approved_count / total_requests) * 100
        modification_rate = (modified_count / total_requests) * 100
        timeout_rate = (timeout_count / total_requests) * 100
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        return {
            "total_requests": total_requests,
            "pending_requests": pending_count,
            "approved_requests": approved_count,
            "rejected_requests": rejected_count,
            "modified_requests": modified_count,
            "timeout_requests": timeout_count,
            "approval_rate": round(approval_rate, 1),
            "modification_rate": round(modification_rate, 1),
            "timeout_rate": round(timeout_rate, 1),
            "average_response_time": round(avg_response_time, 2),
            "workflow_logger_stats": self.workflow_logger.get_performance_summary()
        }
    
    def get_audit_trail(self, plan_id: str) -> Dict[str, Any]:
        """
        Get comprehensive audit trail for a specific plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Dictionary with complete audit trail
        """
        # Get approval history
        approval_history = self.approval_history.get(plan_id, [])
        
        # Get workflow logs
        workflow_logs = self.workflow_logger.get_logs_by_plan(plan_id)
        
        # Get pending approval if exists
        pending_approval = self.pending_approvals.get(plan_id)
        
        return {
            "plan_id": plan_id,
            "approval_history": [result.to_dict() for result in approval_history],
            "workflow_logs": [log.to_dict() for log in workflow_logs],
            "pending_approval": {
                "exists": pending_approval is not None,
                "created_at": pending_approval["created_at"].isoformat() if pending_approval else None,
                "timeout_at": pending_approval["timeout_at"].isoformat() if pending_approval else None,
                "correlation_id": pending_approval.get("correlation_id") if pending_approval else None
            },
            "summary": {
                "total_approvals": len(approval_history),
                "total_log_entries": len(workflow_logs),
                "last_activity": max(
                    [log.timestamp for log in workflow_logs] + 
                    [result.timestamp.isoformat() for result in approval_history]
                ) if (workflow_logs or approval_history) else None
            }
        }
    
    def export_approval_metrics(self, format_type: str = "json") -> Union[str, Dict[str, Any]]:
        """
        Export comprehensive approval metrics for analysis.
        
        Args:
            format_type: Export format ("json", "dict")
            
        Returns:
            Exported metrics in specified format
        """
        metrics = {
            "approval_statistics": self.get_approval_stats(),
            "workflow_performance": self.workflow_logger.get_performance_summary(),
            "modification_templates": {
                name: {
                    "description": template["description"],
                    "type": template["type"].value
                }
                for name, template in self.modification_templates.items()
            },
            "recent_approvals": [
                {
                    "plan_id": plan_id,
                    "latest_status": history[-1].status.value if history else None,
                    "latest_timestamp": history[-1].timestamp.isoformat() if history else None
                }
                for plan_id, history in self.approval_history.items()
            ][-10:]  # Last 10 approvals
        }
        
        if format_type == "json":
            return json.dumps(metrics, indent=2, default=str)
        else:
            return metrics
    
    async def _send_enhanced_plan_approval_request(
        self,
        websocket_manager: Any,
        plan_id: str,
        presentation: EnhancedPlanPresentation,
        correlation_id: Optional[str] = None
    ) -> None:
        """Send enhanced plan approval request via WebSocket."""
        human_readable = presentation.to_human_readable_format()
        
        await websocket_manager.send_message(plan_id, {
            "type": "enhanced_plan_approval_request",
            "data": {
                "plan_id": plan_id,
                "correlation_id": correlation_id,
                "presentation": human_readable,
                "modification_templates": list(self.modification_templates.keys()),
                "approval_options": {
                    "approve": "Approve plan as-is",
                    "approve_with_modifications": "Approve with modifications",
                    "reject": "Reject plan",
                    "request_changes": "Request specific changes"
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    async def _send_modification_request(
        self,
        websocket_manager: Any,
        plan_id: str,
        modification: PlanModification
    ) -> None:
        """Send plan modification request via WebSocket."""
        await websocket_manager.send_message(plan_id, {
            "type": "plan_modification_request",
            "data": {
                "plan_id": plan_id,
                "modification": {
                    "id": modification.id,
                    "type": modification.modification_type.value,
                    "description": modification.description,
                    "justification": modification.justification,
                    "affected_agents": modification.affected_agents
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    async def _send_template_applied_notification(
        self,
        websocket_manager: Any,
        plan_id: str,
        template_name: str,
        modification: PlanModification
    ) -> None:
        """Send notification that a modification template was applied."""
        await websocket_manager.send_message(plan_id, {
            "type": "modification_template_applied",
            "data": {
                "plan_id": plan_id,
                "template_name": template_name,
                "modification": {
                    "id": modification.id,
                    "type": modification.modification_type.value,
                    "description": modification.description,
                    "justification": modification.justification
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    async def _send_result_approval_request(
        self,
        websocket_manager: Any,
        plan_id: str,
        final_results: Dict[str, Any]
    ) -> None:
        """Send result approval request via WebSocket."""
        await websocket_manager.send_message(plan_id, {
            "type": "result_approval_request",
            "data": {
                "plan_id": plan_id,
                "final_results": final_results,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    async def _wait_for_approval(self, plan_id: str, timeout_seconds: int, correlation_id: Optional[str] = None) -> ApprovalResult:
        """
        Wait for approval response or timeout with enhanced result handling.
        
        Args:
            plan_id: Plan identifier
            timeout_seconds: Timeout in seconds
            
        Returns:
            ApprovalResult with the outcome and any modifications
        """
        start_time = datetime.utcnow()
        
        while True:
            # Check if response received
            if plan_id in self.pending_approvals:
                pending = self.pending_approvals[plan_id]
                
                if pending.get("response_received"):
                    response = pending["response"]
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    
                    status = ApprovalStatus.APPROVED if response.approved else ApprovalStatus.REJECTED
                    if response.modified_sequence:
                        status = ApprovalStatus.MODIFIED
                    
                    return ApprovalResult(
                        plan_id=plan_id,
                        status=status,
                        approved=response.approved,
                        feedback=response.feedback,
                        modified_sequence=response.modified_sequence,
                        modifications=pending.get("modifications", []),
                        timeout_seconds=elapsed,
                        reviewer_id=pending.get("reviewer_id"),
                        approval_confidence=pending.get("approval_confidence")
                    )
            
            # Check for timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= timeout_seconds:
                logger.warning(f"⏰ Approval timeout for plan {plan_id} after {elapsed}s")
                return ApprovalResult(
                    plan_id=plan_id,
                    status=ApprovalStatus.TIMEOUT,
                    approved=False,
                    timeout_seconds=elapsed
                )
            
            # Wait a bit before checking again
            await asyncio.sleep(0.5)


# Global HITL interface instance
_hitl_interface: Optional[HITLInterface] = None


def get_hitl_interface() -> HITLInterface:
    """
    Get or create the global HITL interface instance.
    
    Returns:
        HITLInterface instance
    """
    global _hitl_interface
    if _hitl_interface is None:
        _hitl_interface = HITLInterface()
    return _hitl_interface


def reset_hitl_interface() -> None:
    """Reset the global HITL interface (useful for testing)."""
    global _hitl_interface
    _hitl_interface = None