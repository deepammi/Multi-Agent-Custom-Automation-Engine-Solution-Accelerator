"""Team configuration models."""
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Agent configuration."""
    name: str
    role: str
    instructions: str


class TeamConfiguration(BaseModel):
    """Team configuration model."""
    team_id: str
    name: str
    description: str
    agents: List[Agent] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    """Session model."""
    session_id: str
    user_id: str
    team_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
