"""Plan data models."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Step(BaseModel):
    """Plan step model."""
    id: str
    description: str
    agent: str
    status: str = "pending"
    result: Optional[str] = None


class AgentProgress(BaseModel):
    """Agent progress tracking."""
    agent_name: str
    status: str  # e.g., "planning completed", "waiting for input", "processing", "completed"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Plan(BaseModel):
    """Plan model."""
    id: str = Field(alias="plan_id")
    session_id: str
    user_id: str = "default_user"
    description: str
    status: str = "pending"
    steps: List[Step] = []
    agent_progress: List[AgentProgress] = []  # Track progress of each agent
    extraction_data: Optional[dict] = None  # Store extraction result if available
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PlanResponse(BaseModel):
    """Plan response model - frontend compatible."""
    id: str
    plan_id: str
    session_id: str
    user_id: str
    description: str
    initial_goal: str
    status: str
    overall_status: str
    steps: List[Step]
    agent_progress: List[AgentProgress] = []  # Latest status from each agent
    extraction_data: Optional[dict] = None  # Extraction result if available
    created_at: str
    updated_at: str
    timestamp: str
    data_type: str = "plan"
    
    @classmethod
    def from_plan(cls, plan: Plan) -> "PlanResponse":
        """Create frontend-compatible response from Plan model."""
        created_at_str = plan.created_at.isoformat() if isinstance(plan.created_at, datetime) else str(plan.created_at)
        updated_at_str = plan.updated_at.isoformat() if isinstance(plan.updated_at, datetime) else str(plan.updated_at)
        
        return cls(
            id=plan.id,
            plan_id=plan.id,
            session_id=plan.session_id,
            user_id=plan.user_id,
            description=plan.description,
            initial_goal=plan.description,
            status=plan.status,
            overall_status=plan.status,
            steps=plan.steps,
            agent_progress=plan.agent_progress,
            extraction_data=plan.extraction_data,
            created_at=created_at_str,
            updated_at=updated_at_str,
            timestamp=created_at_str,
            data_type="plan"
        )


class ProcessRequestInput(BaseModel):
    """Input for process_request endpoint."""
    description: str
    session_id: Optional[str] = None
    team_id: Optional[str] = None


class ProcessRequestResponse(BaseModel):
    """Response from process_request endpoint."""
    plan_id: str
    status: str
    session_id: str
