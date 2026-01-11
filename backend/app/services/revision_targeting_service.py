"""
Revision Targeting Service for intelligent revision parsing and agent-specific routing.

This service provides advanced revision logic that can:
- Parse user feedback to identify which specific agents need revision
- Determine whether to re-run specific agents vs full replan
- Handle complex revision instructions with context preservation
"""
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class RevisionType(Enum):
    """Types of revision requests."""
    FULL_REPLAN = "full_replan"
    SPECIFIC_AGENTS = "specific_agents"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    DATA_CORRECTION = "data_correction"
    APPROVAL = "approval"
    REJECTION = "rejection"


class RevisionScope(Enum):
    """Scope of revision impact."""
    SINGLE_AGENT = "single_agent"
    MULTIPLE_AGENTS = "multiple_agents"
    DOWNSTREAM_AGENTS = "downstream_agents"
    FULL_WORKFLOW = "full_workflow"


@dataclass
class RevisionTarget:
    """Represents a specific revision target."""
    agent_name: str
    revision_reason: str
    preserve_context: bool = True
    priority: int = 1  # Higher = more important


@dataclass
class RevisionInstruction:
    """Parsed revision instruction from user feedback."""
    revision_type: RevisionType
    revision_scope: RevisionScope
    targets: List[RevisionTarget]
    feedback_text: str
    confidence_score: float
    preserve_results: Set[str]  # Agent results to preserve
    rerun_agents: Set[str]  # Agents to re-run
    new_parameters: Dict[str, Any]  # Parameter adjustments
    iteration_count: int = 0


class RevisionTargetingService:
    """
    Service for parsing user feedback and determining revision targets.
    
    Provides intelligent revision analysis that can:
    - Parse natural language feedback to identify specific issues
    - Map feedback to specific agents and their capabilities
    - Determine optimal revision strategy (partial vs full)
    - Preserve context and results where appropriate
    """
    
    def __init__(self):
        self.agent_capabilities = self._load_agent_capabilities()
        self.revision_patterns = self._load_revision_patterns()
        self.revision_history: Dict[str, List[RevisionInstruction]] = {}
        
    def _load_agent_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Load agent capabilities for revision targeting."""
        return {
            "gmail": {
                "domains": ["email", "communication", "messages", "inbox", "correspondence"],
                "actions": ["search", "read", "analyze", "extract", "filter"],
                "data_types": ["emails", "attachments", "contacts", "threads"]
            },
            "invoice": {
                "domains": ["billing", "payment", "invoice", "accounting", "financial"],
                "actions": ["extract", "validate", "calculate", "verify", "process"],
                "data_types": ["invoices", "amounts", "dates", "vendors", "line_items"]
            },
            "salesforce": {
                "domains": ["crm", "customer", "sales", "opportunity", "account"],
                "actions": ["lookup", "update", "create", "search", "analyze"],
                "data_types": ["accounts", "contacts", "opportunities", "cases", "leads"]
            },
            "zoho": {
                "domains": ["erp", "business", "workflow", "process", "management"],
                "actions": ["retrieve", "update", "process", "validate", "sync"],
                "data_types": ["records", "transactions", "workflows", "reports"]
            },
            "analysis": {
                "domains": ["analysis", "correlation", "summary", "insights", "reporting"],
                "actions": ["analyze", "correlate", "summarize", "compare", "recommend"],
                "data_types": ["results", "patterns", "trends", "metrics", "recommendations"]
            },
            "planner": {
                "domains": ["planning", "strategy", "coordination", "workflow", "routing"],
                "actions": ["plan", "route", "coordinate", "optimize", "sequence"],
                "data_types": ["plans", "sequences", "strategies", "workflows"]
            }
        }
    
    def _load_revision_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns for revision detection."""
        return {
            # Approval patterns - high priority, specific phrases
            "approval": {
                "patterns": [
                    r"\b(perfect|excellent|great|fantastic|wonderful)\b",
                    r"\b(looks?\s+good|sounds?\s+good|that'?s?\s+right|that'?s?\s+correct)\b",
                    r"\b(ok|okay|yes|approve|approved|good|correct|fine|accept)\b",
                    r"\b(proceed|continue|go\s+ahead)\b"
                ],
                "confidence_boost": 0.95
            },
            
            # Strong rejection patterns - full restart needed
            "rejection": {
                "patterns": [
                    r"\b(completely\s+wrong|totally\s+wrong|all\s+wrong)\b",
                    r"\b(start\s+over|start\s+again|redo\s+everything|restart)\b",
                    r"\b(this\s+is\s+wrong|everything\s+is\s+wrong)\b",
                    r"\b(no|reject|rejected|cancel|stop)\b"
                ],
                "confidence_boost": 0.9
            },
            
            # Agent-specific patterns
            "agent_specific": {
                "gmail": [
                    r"\b(email|gmail|message|correspondence|inbox)\b",
                    r"\b(wrong\s+email|missing\s+email|email\s+issue)\b"
                ],
                "invoice": [
                    r"\b(invoice|billing|payment|amount|cost|price)\b",
                    r"\b(wrong\s+amount|incorrect\s+total|billing\s+error)\b"
                ],
                "salesforce": [
                    r"\b(salesforce|crm|customer|account|contact)\b",
                    r"\b(wrong\s+customer|missing\s+account|crm\s+data)\b"
                ],
                "analysis": [
                    r"\b(analysis|summary|report|conclusion|insight)\b",
                    r"\b(wrong\s+analysis|missing\s+data|incomplete)\b"
                ]
            },
            
            # Revision type patterns
            "data_correction": {
                "patterns": [
                    r"\b(wrong|incorrect|fix|correct|update|change)\b",
                    r"\b(data\s+is\s+wrong|need\s+to\s+fix|incorrect\s+information)\b"
                ]
            },
            
            "parameter_adjustment": {
                "patterns": [
                    r"\b(search\s+for|look\s+for|find|include|exclude)\b",
                    r"\b(different\s+criteria|change\s+parameters|adjust\s+search)\b"
                ]
            }
        }
    
    async def parse_revision_feedback(
        self,
        plan_id: str,
        feedback: str,
        current_results: Dict[str, Any],
        agent_sequence: List[str]
    ) -> RevisionInstruction:
        """
        Parse user feedback to determine revision targets and strategy.
        
        Args:
            plan_id: Plan identifier
            feedback: User feedback text
            current_results: Current agent results
            agent_sequence: Current agent execution sequence
            
        Returns:
            RevisionInstruction with parsed targets and strategy
        """
        logger.info(f"🔍 Parsing revision feedback for plan {plan_id}: {feedback[:100]}...")
        
        feedback_lower = feedback.lower().strip()
        
        # Get revision history for context
        iteration_count = len(self.revision_history.get(plan_id, []))
        
        # Detect revision type
        revision_type = self._detect_revision_type(feedback_lower)
        
        # Parse specific targets if not approval/rejection
        targets = []
        preserve_results = set()
        rerun_agents = set()
        new_parameters = {}
        
        if revision_type in [RevisionType.SPECIFIC_AGENTS, RevisionType.DATA_CORRECTION, RevisionType.PARAMETER_ADJUSTMENT]:
            targets = self._identify_revision_targets(feedback_lower, agent_sequence)
            preserve_results, rerun_agents = self._determine_agent_impact(targets, agent_sequence)
            new_parameters = self._extract_parameter_changes(feedback_lower)
        elif revision_type in [RevisionType.FULL_REPLAN, RevisionType.REJECTION]:
            rerun_agents = set(agent_sequence)
        elif revision_type == RevisionType.APPROVAL:
            preserve_results = set(agent_sequence)
        
        # Determine revision scope
        revision_scope = self._determine_revision_scope(targets, rerun_agents, agent_sequence)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(feedback_lower, revision_type, targets)
        
        # Create revision instruction
        instruction = RevisionInstruction(
            revision_type=revision_type,
            revision_scope=revision_scope,
            targets=targets,
            feedback_text=feedback,
            confidence_score=confidence_score,
            preserve_results=preserve_results,
            rerun_agents=rerun_agents,
            new_parameters=new_parameters,
            iteration_count=iteration_count
        )
        
        # Store in history
        if plan_id not in self.revision_history:
            self.revision_history[plan_id] = []
        self.revision_history[plan_id].append(instruction)
        
        logger.info(f"📋 Parsed revision: {revision_type.value}, scope: {revision_scope.value}, targets: {len(targets)}")
        return instruction
    
    def _detect_revision_type(self, feedback: str) -> RevisionType:
        """Detect the type of revision from feedback."""
        # Check for approval patterns first (highest priority)
        approval_score = 0
        for pattern in self.revision_patterns["approval"]["patterns"]:
            if re.search(pattern, feedback, re.IGNORECASE):
                approval_score += 1
        
        # Strong approval indicators
        if approval_score >= 1 and len(feedback.split()) <= 5:  # Short positive feedback
            return RevisionType.APPROVAL
        elif approval_score >= 2:  # Multiple approval indicators
            return RevisionType.APPROVAL
        
        # Check for strong rejection patterns (before agent-specific)
        rejection_score = 0
        for pattern in self.revision_patterns["rejection"]["patterns"]:
            if re.search(pattern, feedback, re.IGNORECASE):
                rejection_score += 1
        
        # Strong rejection indicators
        if rejection_score >= 2:  # Multiple rejection indicators
            return RevisionType.REJECTION
        elif re.search(r"\b(completely|totally|everything)\s+(wrong|incorrect)\b", feedback, re.IGNORECASE):
            return RevisionType.REJECTION
        
        # Check for agent-specific mentions (before general patterns)
        agent_mentions = 0
        mentioned_agents = []
        for agent, patterns in self.revision_patterns["agent_specific"].items():
            for pattern in patterns:
                if re.search(pattern, feedback, re.IGNORECASE):
                    agent_mentions += 1
                    mentioned_agents.append(agent)
        
        # If specific agents mentioned, it's likely targeted revision
        if agent_mentions > 0:
            return RevisionType.SPECIFIC_AGENTS
        
        # Check for data correction patterns
        for pattern in self.revision_patterns["data_correction"]["patterns"]:
            if re.search(pattern, feedback, re.IGNORECASE):
                return RevisionType.DATA_CORRECTION
        
        # Check for parameter adjustment patterns
        for pattern in self.revision_patterns["parameter_adjustment"]["patterns"]:
            if re.search(pattern, feedback, re.IGNORECASE):
                return RevisionType.PARAMETER_ADJUSTMENT
        
        # Check for weak rejection patterns (after other checks)
        if rejection_score >= 1:
            return RevisionType.REJECTION
        
        # Default to full replan for unclear feedback
        return RevisionType.FULL_REPLAN
    
    def _identify_revision_targets(self, feedback: str, agent_sequence: List[str]) -> List[RevisionTarget]:
        """Identify specific agents that need revision."""
        targets = []
        
        for agent in agent_sequence:
            if agent not in self.agent_capabilities:
                continue
                
            capabilities = self.agent_capabilities[agent]
            agent_score = 0
            reasons = []
            
            # Check domain mentions
            for domain in capabilities["domains"]:
                if domain in feedback:
                    agent_score += 2
                    reasons.append(f"{domain} mentioned")
            
            # Check action mentions
            for action in capabilities["actions"]:
                if action in feedback:
                    agent_score += 1
                    reasons.append(f"{action} action needed")
            
            # Check data type mentions
            for data_type in capabilities["data_types"]:
                if data_type in feedback:
                    agent_score += 1
                    reasons.append(f"{data_type} data involved")
            
            # Check agent-specific patterns
            if agent in self.revision_patterns["agent_specific"]:
                for pattern in self.revision_patterns["agent_specific"][agent]:
                    if re.search(pattern, feedback, re.IGNORECASE):
                        agent_score += 3
                        reasons.append("direct agent reference")
            
            # Create target if score is high enough
            if agent_score >= 2:
                target = RevisionTarget(
                    agent_name=agent,
                    revision_reason="; ".join(reasons),
                    preserve_context=agent_score < 4,  # Preserve context for minor issues
                    priority=min(agent_score, 5)
                )
                targets.append(target)
        
        # Sort by priority (highest first)
        targets.sort(key=lambda t: t.priority, reverse=True)
        return targets
    
    def _determine_agent_impact(
        self, 
        targets: List[RevisionTarget], 
        agent_sequence: List[str]
    ) -> Tuple[Set[str], Set[str]]:
        """Determine which agents to preserve vs re-run."""
        if not targets and not agent_sequence:
            return set(), set()
        
        rerun_agents = set()
        preserve_results = set()
        
        # If no specific targets, it's a full restart
        if not targets:
            rerun_agents = set(agent_sequence)
            return preserve_results, rerun_agents
        
        # Add direct targets
        for target in targets:
            rerun_agents.add(target.agent_name)
        
        # Determine downstream impact
        agent_positions = {agent: i for i, agent in enumerate(agent_sequence)}
        
        for target in targets:
            if target.agent_name in agent_positions:
                target_pos = agent_positions[target.agent_name]
                
                # If not preserving context, re-run downstream agents
                if not target.preserve_context:
                    for i in range(target_pos + 1, len(agent_sequence)):
                        downstream_agent = agent_sequence[i]
                        if downstream_agent == "analysis":  # Analysis always re-runs if data changes
                            rerun_agents.add(downstream_agent)
        
        # Preserve agents not marked for re-run
        for agent in agent_sequence:
            if agent not in rerun_agents:
                preserve_results.add(agent)
        
        return preserve_results, rerun_agents
    
    def _extract_parameter_changes(self, feedback: str) -> Dict[str, Any]:
        """Extract parameter changes from feedback."""
        parameters = {}
        
        # Look for search criteria changes
        search_patterns = [
            r"search\s+for\s+([^.!?]+)",
            r"look\s+for\s+([^.!?]+)",
            r"find\s+([^.!?]+)",
            r"include\s+([^.!?]+)",
            r"exclude\s+([^.!?]+)"
        ]
        
        for pattern in search_patterns:
            matches = re.findall(pattern, feedback, re.IGNORECASE)
            if matches:
                parameters["search_criteria"] = matches[0].strip()
        
        # Look for date ranges
        date_patterns = [
            r"from\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"after\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"before\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, feedback, re.IGNORECASE)
            if matches:
                parameters["date_filter"] = matches[0]
        
        return parameters
    
    def _determine_revision_scope(
        self, 
        targets: List[RevisionTarget], 
        rerun_agents: Set[str], 
        agent_sequence: List[str]
    ) -> RevisionScope:
        """Determine the scope of the revision."""
        if not targets and not rerun_agents:
            return RevisionScope.FULL_WORKFLOW
        
        if len(rerun_agents) == len(agent_sequence):
            return RevisionScope.FULL_WORKFLOW
        elif len(rerun_agents) > 1:
            return RevisionScope.MULTIPLE_AGENTS
        elif len(rerun_agents) == 1:
            # Check if downstream agents are affected
            agent_positions = {agent: i for i, agent in enumerate(agent_sequence)}
            rerun_agent = next(iter(rerun_agents))
            
            if rerun_agent in agent_positions:
                pos = agent_positions[rerun_agent]
                if pos < len(agent_sequence) - 1:  # Not the last agent
                    return RevisionScope.DOWNSTREAM_AGENTS
            
            return RevisionScope.SINGLE_AGENT
        
        return RevisionScope.FULL_WORKFLOW
    
    def _calculate_confidence_score(
        self, 
        feedback: str, 
        revision_type: RevisionType, 
        targets: List[RevisionTarget]
    ) -> float:
        """Calculate confidence score for the revision parsing."""
        base_score = 0.5
        
        # Boost for clear approval/rejection
        if revision_type == RevisionType.APPROVAL:
            for pattern in self.revision_patterns["approval"]["patterns"]:
                if re.search(pattern, feedback, re.IGNORECASE):
                    base_score = max(base_score, 0.9)
        elif revision_type == RevisionType.REJECTION:
            for pattern in self.revision_patterns["rejection"]["patterns"]:
                if re.search(pattern, feedback, re.IGNORECASE):
                    base_score = max(base_score, 0.8)
        
        # Boost for specific targets
        if targets:
            target_score = sum(t.priority for t in targets) / (len(targets) * 5)
            base_score += target_score * 0.3
        
        # Penalty for very short feedback
        if len(feedback.split()) < 3:
            base_score *= 0.8
        
        # Boost for longer, detailed feedback
        elif len(feedback.split()) > 10:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def get_revision_history(self, plan_id: str) -> List[RevisionInstruction]:
        """Get revision history for a plan."""
        return self.revision_history.get(plan_id, [])
    
    def should_limit_revisions(self, plan_id: str, max_iterations: int = 5) -> bool:
        """Check if revision iterations should be limited."""
        history = self.revision_history.get(plan_id, [])
        return len(history) >= max_iterations
    
    def get_revision_stats(self) -> Dict[str, Any]:
        """Get revision statistics for monitoring."""
        total_revisions = sum(len(history) for history in self.revision_history.values())
        
        if total_revisions == 0:
            return {
                "total_revisions": 0,
                "plans_with_revisions": 0,
                "average_iterations": 0.0,
                "revision_types": {},
                "confidence_distribution": {}
            }
        
        # Count revision types
        revision_types = {}
        confidence_scores = []
        
        for history in self.revision_history.values():
            for instruction in history:
                rev_type = instruction.revision_type.value
                revision_types[rev_type] = revision_types.get(rev_type, 0) + 1
                confidence_scores.append(instruction.confidence_score)
        
        # Calculate confidence distribution
        confidence_distribution = {
            "high (>0.8)": len([s for s in confidence_scores if s > 0.8]),
            "medium (0.5-0.8)": len([s for s in confidence_scores if 0.5 <= s <= 0.8]),
            "low (<0.5)": len([s for s in confidence_scores if s < 0.5])
        }
        
        return {
            "total_revisions": total_revisions,
            "plans_with_revisions": len(self.revision_history),
            "average_iterations": total_revisions / len(self.revision_history),
            "revision_types": revision_types,
            "confidence_distribution": confidence_distribution,
            "average_confidence": sum(confidence_scores) / len(confidence_scores)
        }


# Global service instance
_revision_targeting_service: Optional[RevisionTargetingService] = None


def get_revision_targeting_service() -> RevisionTargetingService:
    """Get or create the global revision targeting service instance."""
    global _revision_targeting_service
    if _revision_targeting_service is None:
        _revision_targeting_service = RevisionTargetingService()
    return _revision_targeting_service


def reset_revision_targeting_service() -> None:
    """Reset the global service (useful for testing)."""
    global _revision_targeting_service
    _revision_targeting_service = None