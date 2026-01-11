"""LangGraph checkpointer configuration for persistent state management."""
import logging
import os
from typing import Optional
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


class CheckpointerService:
    """Service for managing LangGraph checkpointer."""
    
    _checkpointer: Optional[MemorySaver] = None
    
    @classmethod
    def get_checkpointer(cls) -> MemorySaver:
        """
        Get or create Memory checkpointer for state management.
        
        The checkpointer stores:
        - Graph execution state
        - Agent conversation history
        - HITL approval states
        - Execution checkpoints for resume
        
        Note: Using MemorySaver for Phase 1. Will upgrade to persistent
        storage (MongoDB/SQLite) in later phases for production.
        
        Returns:
            MemorySaver: Configured checkpointer instance
        """
        if cls._checkpointer is None:
            try:
                cls._checkpointer = MemorySaver()
                logger.info("MemorySaver checkpointer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize checkpointer: {e}")
                raise
        
        return cls._checkpointer
    
    @classmethod
    def clear_checkpoints(cls) -> bool:
        """
        Clear all checkpoints (reset memory).
        
        Returns:
            bool: True if successful
        """
        try:
            cls._checkpointer = None
            logger.info("Cleared all checkpoints (reset memory)")
            return True
        except Exception as e:
            logger.error(f"Failed to clear checkpoints: {e}")
            return False


def get_checkpointer() -> MemorySaver:
    """
    Convenience function to get checkpointer.
    
    Returns:
        MemorySaver: Configured checkpointer instance
    """
    return CheckpointerService.get_checkpointer()
