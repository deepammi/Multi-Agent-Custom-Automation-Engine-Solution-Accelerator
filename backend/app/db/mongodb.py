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
