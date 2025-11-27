"""Plan approval models."""
from pydantic import BaseModel
from typing import Optional


class PlanApprovalRequest(BaseModel):
    """Request for plan approval."""
    m_plan_id: str
    approved: bool
    feedback: Optional[str] = None


class PlanApprovalResponse(BaseModel):
    """Response from plan approval."""
    status: str
    message: Optional[str] = None
