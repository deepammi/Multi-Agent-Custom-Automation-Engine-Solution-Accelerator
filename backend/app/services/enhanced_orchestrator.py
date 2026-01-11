"""
Enhanced Multi-Agent Orchestrator for Invoice Analysis Workflow

This module provides improved multi-agent coordination with:
- Enhanced agent sequencing logic based on task analysis
- Improved data passing between agents with validation
- Agent execution order validation with dependency checking
- Better error handling and recovery mechanisms
"""
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timezone

from app.agents.state import AgentState
from app.services.websocket_service import WebSocketManager

logger = logging.getLogger(__name__)


class AgentDependency(Enum):
    """Agent dependency types for execution order validation."""
    NONE = "none"
    EMAIL_DATA = "email_data"
    VENDOR_INFO = "vendor_info"
    INVOICE_DATA = "invoice_data"
    AP_DATA = "ap_data"
    CRM_DATA = "crm_data"
    ALL_DATA = "all_data"


@dataclass
class AgentMetadata:
    """Metadata for agent execution and dependencies."""
    name: str
    category: str
    dependencies: List[AgentDependency]
    provides: List[str]
    execution_priority: int
    estimated_duration: float
    required_for_analysis: bool


@dataclass
class DataFlowValidation:
    """Validation result for data flow between agents."""
    is_valid: bool
    missing_dependencies: List[str]
    available_data: List[str]
    recommendations: List[str]


class EnhancedOrchestrator:
    """
    Enhanced orchestrator for multi-agent coordination with improved:
    - Agent sequencing logic based on task analysis and dependencies
    - Data passing validation and structured flow management
    - Execution order validation with dependency checking
    - Error recovery and graceful degradation
    """
    
    def __init__(self):
        """Initialize the enhanced orchestrator."""
        self.agent_registry = self._initialize_agent_registry()
        self.execution_history: List[Dict[str, Any]] = []
        self.data_flow_cache: Dict[str, Any] = {}
        
    def _initialize_agent_registry(self) -> Dict[str, AgentMetadata]:
        """Initialize agent registry with metadata and dependencies."""
        return {
            "planner": AgentMetadata(
                name="planner",
                category="planning",
                dependencies=[AgentDependency.NONE],
                provides=["execution_plan", "task_analysis"],
                execution_priority=1,
                estimated_duration=30.0,
                required_for_analysis=True
            ),
            "gmail": AgentMetadata(
                name="gmail",
                category="email",
                dependencies=[AgentDependency.VENDOR_INFO],
                provides=["email_data", "invoice_numbers", "communication_history"],
                execution_priority=2,
                estimated_duration=45.0,
                required_for_analysis=True
            ),
            "email": AgentMetadata(
                name="email",
                category="email",
                dependencies=[AgentDependency.VENDOR_INFO],
                provides=["email_data", "invoice_numbers", "communication_history"],
                execution_priority=2,
                estimated_duration=45.0,
                required_for_analysis=True
            ),
            "invoice": AgentMetadata(
                name="invoice",
                category="accounts_payable",
                dependencies=[AgentDependency.VENDOR_INFO, AgentDependency.EMAIL_DATA],
                provides=["ap_data", "bill_status", "payment_info"],
                execution_priority=3,
                estimated_duration=60.0,
                required_for_analysis=True
            ),
            "accounts_payable": AgentMetadata(
                name="accounts_payable",
                category="accounts_payable",
                dependencies=[AgentDependency.VENDOR_INFO, AgentDependency.EMAIL_DATA],
                provides=["ap_data", "bill_status", "payment_info"],
                execution_priority=3,
                estimated_duration=60.0,
                required_for_analysis=True
            ),
            "salesforce": AgentMetadata(
                name="salesforce",
                category="crm",
                dependencies=[AgentDependency.VENDOR_INFO],
                provides=["crm_data", "account_info", "opportunities"],
                execution_priority=4,
                estimated_duration=50.0,
                required_for_analysis=True
            ),
            "crm": AgentMetadata(
                name="crm",
                category="crm",
                dependencies=[AgentDependency.VENDOR_INFO],
                provides=["crm_data", "account_info", "opportunities"],
                execution_priority=4,
                estimated_duration=50.0,
                required_for_analysis=True
            ),
            "analysis": AgentMetadata(
                name="analysis",
                category="analysis",
                dependencies=[AgentDependency.ALL_DATA],
                provides=["final_analysis", "recommendations", "insights", "correlations", "discrepancies", "payment_issues"],
                execution_priority=5,
                estimated_duration=90.0,
                required_for_analysis=True
            )
        }
    
    def analyze_task_requirements(self, task_description: str) -> Dict[str, Any]:
        """
        Analyze task description to determine required agents and optimal sequence.
        
        Args:
            task_description: Natural language task description
            
        Returns:
            Dictionary with task analysis and agent requirements
        """
        task_lower = task_description.lower()
        
        # Analyze task type and complexity
        task_analysis = {
            "task_type": "invoice_analysis",
            "complexity_score": 0.5,
            "required_agents": set(),
            "optional_agents": set(),
            "data_requirements": set(),
            "estimated_duration": 0.0
        }
        
        # Determine required agents based on task content
        if any(word in task_lower for word in ["email", "communication", "correspondence", "received"]):
            task_analysis["required_agents"].add("gmail")
            task_analysis["data_requirements"].add("email_data")
            task_analysis["complexity_score"] += 0.2
        
        if any(word in task_lower for word in ["invoice", "bill", "payment", "accounts payable", "ap"]):
            task_analysis["required_agents"].add("invoice")
            task_analysis["data_requirements"].add("ap_data")
            task_analysis["complexity_score"] += 0.2
        
        if any(word in task_lower for word in ["customer", "crm", "salesforce", "account", "relationship"]):
            task_analysis["required_agents"].add("salesforce")
            task_analysis["data_requirements"].add("crm_data")
            task_analysis["complexity_score"] += 0.2
        
        if any(word in task_lower for word in ["analyze", "analysis", "cross-reference", "correlate"]):
            task_analysis["required_agents"].add("analysis")
            task_analysis["complexity_score"] += 0.3
        
        # Always include planner for coordination
        task_analysis["required_agents"].add("planner")
        
        # If no specific agents identified, use default comprehensive set
        if len(task_analysis["required_agents"]) <= 1:  # Only planner
            task_analysis["required_agents"].update(["gmail", "invoice", "salesforce", "analysis"])
            task_analysis["complexity_score"] = 0.8
        
        # Calculate estimated duration
        for agent_name in task_analysis["required_agents"]:
            if agent_name in self.agent_registry:
                task_analysis["estimated_duration"] += self.agent_registry[agent_name].estimated_duration
        
        logger.info(
            f"Task analysis completed",
            extra={
                "task_type": task_analysis["task_type"],
                "complexity_score": task_analysis["complexity_score"],
                "required_agents": list(task_analysis["required_agents"]),
                "estimated_duration": task_analysis["estimated_duration"]
            }
        )
        
        return task_analysis
    
    def generate_optimal_sequence(self, required_agents: Set[str], task_analysis: Dict[str, Any]) -> List[str]:
        """
        Generate optimal agent execution sequence based on dependencies and task requirements.
        
        Args:
            required_agents: Set of required agent names
            task_analysis: Task analysis results
            
        Returns:
            Ordered list of agent names for execution
        """
        # Filter to valid agents
        valid_agents = {agent for agent in required_agents if agent in self.agent_registry}
        
        if not valid_agents:
            logger.warning("No valid agents found, using default sequence")
            return ["planner", "gmail", "invoice", "salesforce", "analysis"]
        
        # Build dependency graph
        dependency_graph = {}
        for agent_name in valid_agents:
            agent_meta = self.agent_registry[agent_name]
            dependency_graph[agent_name] = {
                "dependencies": agent_meta.dependencies,
                "priority": agent_meta.execution_priority,
                "provides": agent_meta.provides
            }
        
        # Topological sort with priority consideration
        sequence = []
        remaining_agents = valid_agents.copy()
        available_data = set()
        
        # Always start with planner if present
        if "planner" in remaining_agents:
            sequence.append("planner")
            remaining_agents.remove("planner")
            available_data.update(self.agent_registry["planner"].provides)
        
        # Process remaining agents based on dependencies and priority
        while remaining_agents:
            # Find agents whose dependencies are satisfied
            ready_agents = []
            
            for agent_name in remaining_agents:
                agent_meta = self.agent_registry[agent_name]
                dependencies_met = True
                
                for dep in agent_meta.dependencies:
                    if dep == AgentDependency.NONE:
                        continue
                    elif dep == AgentDependency.VENDOR_INFO and "execution_plan" not in available_data:
                        # Allow if planner has already run or is in sequence before this agent
                        if "planner" not in sequence[:sequence.index(agent_name) + 1] if agent_name in sequence else True:
                            dependencies_met = False
                            break
                    elif dep == AgentDependency.EMAIL_DATA and "email_data" not in available_data:
                        # Allow if email agent will run before this agent
                        dependencies_met = False
                        break
                    elif dep == AgentDependency.AP_DATA and "ap_data" not in available_data:
                        dependencies_met = False
                        break
                    elif dep == AgentDependency.CRM_DATA and "crm_data" not in available_data:
                        dependencies_met = False
                        break
                    elif dep == AgentDependency.ALL_DATA:
                        # For analysis agent, be more flexible - allow if most data agents are present
                        if agent_name == "analysis":
                            # Analysis can run if at least 2 data sources are available or will be available
                            data_agents_in_sequence = [a for a in remaining_agents if a in ["gmail", "email", "invoice", "accounts_payable", "salesforce", "crm"]]
                            if len(data_agents_in_sequence) < 2:
                                dependencies_met = False
                                break
                        else:
                            required_data = {"email_data", "ap_data", "crm_data"}
                            if not required_data.issubset(available_data):
                                dependencies_met = False
                                break
                
                if dependencies_met:
                    ready_agents.append(agent_name)
            
            if not ready_agents:
                # Break dependency deadlock by adding highest priority agent
                logger.warning("Dependency deadlock detected, adding highest priority agent")
                ready_agents = [min(remaining_agents, key=lambda x: self.agent_registry[x].execution_priority)]
            
            # Sort ready agents by priority and add the highest priority one
            ready_agents.sort(key=lambda x: self.agent_registry[x].execution_priority)
            next_agent = ready_agents[0]
            
            sequence.append(next_agent)
            remaining_agents.remove(next_agent)
            available_data.update(self.agent_registry[next_agent].provides)
        
        logger.info(
            f"Generated optimal sequence: {' → '.join(sequence)}",
            extra={
                "sequence": sequence,
                "total_agents": len(sequence),
                "estimated_duration": sum(self.agent_registry[agent].estimated_duration for agent in sequence)
            }
        )
        
        return sequence
    
    def validate_execution_order(self, agent_sequence: List[str]) -> DataFlowValidation:
        """
        Validate that agent execution order satisfies all dependencies.
        
        Args:
            agent_sequence: Proposed agent execution sequence
            
        Returns:
            DataFlowValidation with validation results and recommendations
        """
        available_data = set()
        missing_dependencies = []
        recommendations = []
        
        for i, agent_name in enumerate(agent_sequence):
            if agent_name not in self.agent_registry:
                missing_dependencies.append(f"Unknown agent: {agent_name}")
                continue
            
            agent_meta = self.agent_registry[agent_name]
            
            # Check if dependencies are satisfied
            for dep in agent_meta.dependencies:
                if dep == AgentDependency.NONE:
                    continue
                elif dep == AgentDependency.VENDOR_INFO and "execution_plan" not in available_data:
                    missing_dependencies.append(f"{agent_name} requires vendor info (from planner)")
                elif dep == AgentDependency.EMAIL_DATA and "email_data" not in available_data:
                    missing_dependencies.append(f"{agent_name} requires email data")
                elif dep == AgentDependency.AP_DATA and "ap_data" not in available_data:
                    missing_dependencies.append(f"{agent_name} requires AP data")
                elif dep == AgentDependency.CRM_DATA and "crm_data" not in available_data:
                    missing_dependencies.append(f"{agent_name} requires CRM data")
                elif dep == AgentDependency.ALL_DATA:
                    required_data = {"email_data", "ap_data", "crm_data"}
                    missing_data = required_data - available_data
                    if missing_data:
                        missing_dependencies.append(f"{agent_name} requires all data, missing: {missing_data}")
            
            # Add data provided by this agent
            available_data.update(agent_meta.provides)
        
        # Generate recommendations
        if missing_dependencies:
            recommendations.append("Reorder agents to satisfy dependencies")
            recommendations.append("Ensure planner runs first to provide vendor info")
            
            if "analysis" in agent_sequence and agent_sequence.index("analysis") < len(agent_sequence) - 1:
                recommendations.append("Move analysis agent to end of sequence")
        
        if "planner" not in agent_sequence:
            recommendations.append("Add planner agent at the beginning")
        
        is_valid = len(missing_dependencies) == 0
        
        validation_result = DataFlowValidation(
            is_valid=is_valid,
            missing_dependencies=missing_dependencies,
            available_data=list(available_data),
            recommendations=recommendations
        )
        
        logger.info(
            f"Execution order validation: {'VALID' if is_valid else 'INVALID'}",
            extra={
                "sequence": agent_sequence,
                "is_valid": is_valid,
                "missing_dependencies": missing_dependencies,
                "recommendations": recommendations
            }
        )
        
        return validation_result
    
    def enhance_data_passing(self, state: AgentState, agent_name: str, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance data passing between agents with validation and structured flow.
        
        Args:
            state: Current agent state
            agent_name: Name of the agent that produced the result
            agent_result: Result data from the agent
            
        Returns:
            Enhanced state with improved data structure and validation
        """
        # Extract and validate data from agent result
        enhanced_data = {
            "agent_name": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": agent_result.get("status", "unknown"),
            "data": agent_result.get("data", {}),
            "message": agent_result.get("message", ""),
            "execution_time": agent_result.get("execution_time", 0.0)
        }
        
        # Add agent-specific data enhancements
        if agent_name in ["gmail", "email"]:
            enhanced_data["data_type"] = "email_data"
            enhanced_data["provides"] = ["email_data", "invoice_numbers", "communication_history"]
            
            # Validate email data structure
            if "data" in agent_result and isinstance(agent_result["data"], dict):
                email_data = agent_result["data"]
                enhanced_data["validation"] = {
                    "has_emails": "emails_found" in email_data,
                    "has_invoice_numbers": "invoice_numbers" in email_data,
                    "email_count": email_data.get("emails_found", 0)
                }
        
        elif agent_name in ["invoice", "accounts_payable"]:
            enhanced_data["data_type"] = "ap_data"
            enhanced_data["provides"] = ["ap_data", "bill_status", "payment_info"]
            
            # Validate AP data structure
            if "data" in agent_result and isinstance(agent_result["data"], dict):
                ap_data = agent_result["data"]
                enhanced_data["validation"] = {
                    "has_bills": "bills_found" in ap_data,
                    "has_payment_status": "payment_status" in ap_data,
                    "bill_count": ap_data.get("bills_found", 0)
                }
        
        elif agent_name in ["salesforce", "crm"]:
            enhanced_data["data_type"] = "crm_data"
            enhanced_data["provides"] = ["crm_data", "account_info", "opportunities"]
            
            # Validate CRM data structure
            if "data" in agent_result and isinstance(agent_result["data"], dict):
                crm_data = agent_result["data"]
                enhanced_data["validation"] = {
                    "has_accounts": "accounts_found" in crm_data,
                    "has_opportunities": "opportunities" in crm_data,
                    "account_count": crm_data.get("accounts_found", 0)
                }
        
        elif agent_name == "analysis":
            enhanced_data["data_type"] = "analysis_result"
            enhanced_data["provides"] = ["final_analysis", "recommendations", "insights"]
            
            # Validate analysis data
            enhanced_data["validation"] = {
                "has_analysis": bool(agent_result.get("message")),
                "analysis_length": len(agent_result.get("message", ""))
            }
        
        # Update collected data with enhanced structure
        collected_data = state.get("collected_data", {})
        collected_data[agent_name] = enhanced_data
        
        # Update data flow cache for cross-agent access
        self.data_flow_cache[f"{state.get('plan_id', 'unknown')}_{agent_name}"] = enhanced_data
        
        # Add cross-references for data correlation
        enhanced_state_updates = {
            "collected_data": collected_data,
            f"{agent_name}_enhanced_data": enhanced_data,
            "data_flow_metadata": {
                "last_updated_by": agent_name,
                "last_update_time": enhanced_data["timestamp"],
                "available_data_types": list(set(
                    data.get("data_type", "unknown") 
                    for data in collected_data.values()
                ))
            }
        }
        
        logger.info(
            f"Enhanced data passing for {agent_name}",
            extra={
                "agent_name": agent_name,
                "data_type": enhanced_data.get("data_type"),
                "provides": enhanced_data.get("provides", []),
                "validation": enhanced_data.get("validation", {})
            }
        )
        
        return enhanced_state_updates
    
    async def coordinate_agent_execution(
        self,
        agent_sequence: List[str],
        state: AgentState,
        websocket_manager: Optional[WebSocketManager] = None
    ) -> Dict[str, Any]:
        """
        Coordinate multi-agent execution with enhanced orchestration.
        
        Args:
            agent_sequence: Ordered list of agents to execute
            state: Initial agent state
            websocket_manager: Optional WebSocket manager for progress updates
            
        Returns:
            Coordination results with execution summary
        """
        plan_id = state.get("plan_id", "unknown")
        
        # Validate execution order
        validation = self.validate_execution_order(agent_sequence)
        if not validation.is_valid:
            logger.warning(
                f"Execution order validation failed for plan {plan_id}",
                extra={
                    "missing_dependencies": validation.missing_dependencies,
                    "recommendations": validation.recommendations
                }
            )
        
        # Track execution progress
        execution_summary = {
            "plan_id": plan_id,
            "agent_sequence": agent_sequence,
            "validation_result": validation,
            "execution_start": datetime.now(timezone.utc).isoformat(),
            "agents_completed": [],
            "agents_failed": [],
            "total_execution_time": 0.0,
            "data_flow_summary": {}
        }
        
        # Send coordination messages via WebSocket
        if websocket_manager:
            if validation.is_valid:
                await websocket_manager.send_message(plan_id, {
                    "type": "system_message",
                    "data": {
                        "message": f"🎯 Enhanced orchestration coordinating {len(agent_sequence)} agents: {' → '.join(agent_sequence)}",
                        "level": "info",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
            else:
                # Send validation warning first, then coordination message
                await websocket_manager.send_message(plan_id, {
                    "type": "system_message",
                    "data": {
                        "message": f"⚠️ Execution order validation warnings: {'; '.join(validation.recommendations)}",
                        "level": "warning",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
                await websocket_manager.send_message(plan_id, {
                    "type": "system_message", 
                    "data": {
                        "message": f"🎯 Enhanced orchestration coordinating {len(agent_sequence)} agents: {' → '.join(agent_sequence)}",
                        "level": "info",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
        
        # Store execution summary for monitoring
        self.execution_history.append(execution_summary)
        
        logger.info(
            f"Enhanced orchestration coordination started for plan {plan_id}",
            extra={
                "plan_id": plan_id,
                "agent_sequence": agent_sequence,
                "validation_valid": validation.is_valid,
                "estimated_duration": sum(
                    self.agent_registry.get(agent, AgentMetadata("", "", [], [], 0, 0.0, False)).estimated_duration
                    for agent in agent_sequence
                )
            }
        )
        
        return execution_summary
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """
        Get orchestration performance metrics.
        
        Returns:
            Dictionary with orchestration metrics and statistics
        """
        if not self.execution_history:
            return {
                "total_executions": 0,
                "average_agents_per_execution": 0.0,
                "success_rate": 0.0,
                "most_common_sequences": []
            }
        
        total_executions = len(self.execution_history)
        total_agents = sum(len(exec_summary["agent_sequence"]) for exec_summary in self.execution_history)
        successful_executions = sum(
            1 for exec_summary in self.execution_history 
            if len(exec_summary["agents_failed"]) == 0
        )
        
        # Find most common sequences
        sequence_counts = {}
        for exec_summary in self.execution_history:
            sequence_key = " → ".join(exec_summary["agent_sequence"])
            sequence_counts[sequence_key] = sequence_counts.get(sequence_key, 0) + 1
        
        most_common_sequences = sorted(
            sequence_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            "total_executions": total_executions,
            "average_agents_per_execution": total_agents / total_executions,
            "success_rate": successful_executions / total_executions,
            "most_common_sequences": most_common_sequences,
            "agent_registry_size": len(self.agent_registry),
            "cache_size": len(self.data_flow_cache)
        }


# Singleton instance
_enhanced_orchestrator: Optional[EnhancedOrchestrator] = None


def get_enhanced_orchestrator() -> EnhancedOrchestrator:
    """Get or create the enhanced orchestrator singleton."""
    global _enhanced_orchestrator
    if _enhanced_orchestrator is None:
        _enhanced_orchestrator = EnhancedOrchestrator()
        logger.info("Enhanced orchestrator initialized")
    return _enhanced_orchestrator