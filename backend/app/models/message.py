"""Message data models."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """Agent message model."""
    plan_id: str
    agent_name: str
    agent_type: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}
