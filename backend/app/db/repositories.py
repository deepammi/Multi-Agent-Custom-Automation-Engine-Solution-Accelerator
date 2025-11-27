"""Database repositories for data access."""
import logging
from typing import List, Optional
from datetime import datetime

from app.db.mongodb import MongoDB
from app.models.plan import Plan
from app.models.message import AgentMessage

logger = logging.getLogger(__name__)


class PlanRepository:
    """Repository for plan operations."""
    
    @staticmethod
    async def create(plan: Plan) -> str:
        """Create a new plan."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        plan_dict = plan.model_dump(by_alias=True)
        plan_dict["plan_id"] = plan.id
        
        result = await collection.insert_one(plan_dict)
        logger.info(f"Created plan: {plan.id}")
        return plan.id
    
    @staticmethod
    async def get_by_id(plan_id: str) -> Optional[Plan]:
        """Get plan by ID."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        plan_dict = await collection.find_one({"plan_id": plan_id})
        if plan_dict:
            plan_dict["id"] = plan_dict["plan_id"]
            return Plan(**plan_dict)
        return None
    
    @staticmethod
    async def get_all(session_id: Optional[str] = None) -> List[Plan]:
        """Get all plans, optionally filtered by session_id."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        query = {"session_id": session_id} if session_id else {}
        cursor = collection.find(query)
        
        plans = []
        async for plan_dict in cursor:
            plan_dict["id"] = plan_dict["plan_id"]
            plans.append(Plan(**plan_dict))
        
        return plans
    
    @staticmethod
    async def update_status(plan_id: str, status: str) -> bool:
        """Update plan status."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        result = await collection.update_one(
            {"plan_id": plan_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0


class MessageRepository:
    """Repository for message operations."""
    
    @staticmethod
    async def create(message: AgentMessage) -> str:
        """Create a new message."""
        db = MongoDB.get_database()
        collection = db["messages"]
        
        message_dict = message.model_dump()
        result = await collection.insert_one(message_dict)
        logger.info(f"Created message for plan: {message.plan_id}")
        return str(result.inserted_id)
    
    @staticmethod
    async def get_by_plan_id(plan_id: str) -> List[AgentMessage]:
        """Get all messages for a plan."""
        db = MongoDB.get_database()
        collection = db["messages"]
        
        cursor = collection.find({"plan_id": plan_id}).sort("timestamp", 1)
        
        messages = []
        async for message_dict in cursor:
            messages.append(AgentMessage(**message_dict))
        
        return messages
