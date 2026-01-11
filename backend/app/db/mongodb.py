"""
MongoDB connection and database management.
"""
import logging
import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    def connect(cls):
        """Connect to MongoDB."""
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("MONGODB_DATABASE", "macae_db")
        
        try:
            cls.client = AsyncIOMotorClient(mongodb_url)
            cls.database = cls.client[database_name]
            logger.info(f"Connected to MongoDB: {database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    def close(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.database is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return cls.database
    
    @classmethod
    async def test_connection(cls) -> bool:
        """Test database connection."""
        try:
            db = cls.get_database()
            await db.command("ping")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    @classmethod
    async def initialize_indexes(cls) -> bool:
        """
        Initialize database indexes for optimal performance.
        
        Returns:
            True if indexes were created successfully, False otherwise
        """
        try:
            db = cls.get_database()
            
            # Create indexes for messages collection
            messages_collection = db["messages"]
            
            # Index for chronological ordering by plan_id and timestamp
            await messages_collection.create_index([
                ("plan_id", 1),
                ("timestamp", 1)
            ], name="plan_id_timestamp_idx")
            
            # Index for efficient plan_id queries
            await messages_collection.create_index("plan_id", name="plan_id_idx")
            
            # Index for agent-based queries
            await messages_collection.create_index([
                ("plan_id", 1),
                ("agent_name", 1),
                ("timestamp", 1)
            ], name="plan_agent_timestamp_idx")
            
            # Create indexes for plans collection
            plans_collection = db["plans"]
            
            # Index for plan retrieval by session
            await plans_collection.create_index([
                ("session_id", 1),
                ("created_at", -1)
            ], name="session_created_idx")
            
            # Index for plan_id queries
            await plans_collection.create_index("plan_id", name="plan_id_idx", unique=True)
            
            logger.info("✅ Database indexes initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database indexes: {e}")
            return False
