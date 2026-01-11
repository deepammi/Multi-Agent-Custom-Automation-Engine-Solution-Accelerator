"""
Gmail MCP Service - UPDATED to use proper MCP protocol.
This file now imports the standardized implementation while maintaining backward compatibility.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import the standardized implementation
from .gmail_standard_mcp_client import (
    GmailMCPServiceStandardized,
    get_gmail_service as get_standardized_service
)

logger = logging.getLogger(__name__)

class GmailMCPService:
    """
    LEGACY WRAPPER - Gmail service using proper MCP protocol.
    
    This class now delegates to the standardized MCP implementation
    while maintaining backward compatibility with existing code.
    """
    
    def __init__(self):
        # Delegate to standardized implementation
        self._standardized_service = GmailMCPServiceStandardized()
        
        # Maintain legacy interface properties
        self.domain = "gmail"
        self.service = None
        self._initialized = False
        
        logger.warning(
            "Using legacy GmailMCPService wrapper. "
            "Consider migrating to GmailMCPServiceStandardized for better performance."
        )
    

    
    async def list_messages(self, max_results: int = 10, query: str = "") -> str:
        """List Gmail messages using proper MCP protocol."""
        return await self._standardized_service.list_messages(max_results, query)
    
    async def send_message(self, to: str, subject: str, body: str, cc: Optional[str] = None) -> str:
        """Send Gmail message using proper MCP protocol."""
        return await self._standardized_service.send_message(to, subject, body, cc)
    
    async def get_message(self, message_id: str, include_body_html: bool = False) -> str:
        """Get Gmail message using proper MCP protocol."""
        return await self._standardized_service.get_message(message_id, include_body_html)
    
    async def search_messages(self, query: str, max_results: int = 10) -> str:
        """Search Gmail messages using proper MCP protocol."""
        return await self._standardized_service.search_messages(query, max_results)
    
    async def get_profile(self) -> str:
        """Get Gmail profile using proper MCP protocol."""
        return await self._standardized_service.get_profile()

# Global service instance - now uses standardized implementation
_gmail_service: Optional[GmailMCPService] = None

def get_gmail_service() -> GmailMCPService:
    """
    Get or create Gmail MCP service instance.
    
    Note: This returns the legacy wrapper for backward compatibility.
    For new code, consider using get_standardized_service() directly.
    """
    global _gmail_service
    
    if _gmail_service is None:
        _gmail_service = GmailMCPService()
    
    return _gmail_service