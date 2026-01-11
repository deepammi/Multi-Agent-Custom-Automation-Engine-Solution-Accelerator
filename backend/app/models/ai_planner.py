"""AI Planner data models for task analysis and agent sequence generation."""
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from dataclasses import dataclass


class TaskAnalysis(BaseModel):
    """Task analysis model for AI-driven planning."""
    complexity: Literal["simple", "medium", "complex"]
    required_systems: List[str] = Field(description="Systems needed: email, erp, crm, etc.")
    business_context: str = Field(description="Business context and domain")
    data_sources_needed: List[str] = Field(description="Data sources required")
    estimated_agents: List[str] = Field(description="Estimated agents needed")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in analysis")
    reasoning: str = Field(description="AI reasoning for the analysis")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentSequence(BaseModel):
    """Agent sequence model for linear workflow execution."""
    agents: List[str] = Field(description="Ordered list of agents to execute")
    reasoning: Dict[str, str] = Field(description="Reasoning for each agent inclusion")
    estimated_duration: int = Field(description="Estimated duration in seconds")
    complexity_score: float = Field(ge=0.0, le=1.0, description="Workflow complexity score")
    task_analysis: TaskAnalysis = Field(description="Original task analysis")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_total_steps(self) -> int:
        """Get total number of steps in the sequence."""
        return len(self.agents)
    
    def get_agent_at_step(self, step: int) -> Optional[str]:
        """Get agent name at specific step (0-indexed)."""
        if 0 <= step < len(self.agents):
            return self.agents[step]
        return None
    
    def is_valid_sequence(self) -> bool:
        """Validate that the sequence is valid."""
        # Must have at least one agent
        if not self.agents:
            return False
        
        # All agents must be valid
        valid_agents = {
            "planner", "gmail", "invoice", "salesforce", "zoho", 
            "audit", "analysis"
        }
        
        for agent in self.agents:
            if agent.lower() not in valid_agents:
                return False
        
        # Must have reasoning for each agent
        for agent in self.agents:
            if agent not in self.reasoning:
                return False
        
        return True


class PlanApprovalRequest(BaseModel):
    """Request model for plan approval."""
    plan_id: str
    agent_sequence: AgentSequence
    task_description: str
    estimated_completion_time: str
    requires_approval: bool = True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PlanApprovalResponse(BaseModel):
    """Response model for plan approval."""
    plan_id: str
    approved: bool
    feedback: Optional[str] = None
    modified_sequence: Optional[AgentSequence] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AIPlanningSummary(BaseModel):
    """Summary of AI planning results for logging and monitoring."""
    task_description: str
    analysis_duration: float = Field(description="Time taken for analysis in seconds")
    sequence_generation_duration: float = Field(description="Time taken for sequence generation in seconds")
    total_duration: float = Field(description="Total planning duration in seconds")
    task_analysis: TaskAnalysis
    agent_sequence: AgentSequence
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }