"""
Salesforce MCP client service - UPDATED to use proper MCP protocol.
This file now imports the standardized implementation while maintaining backward compatibility.
"""
import logging
import os
from typing import Dict, Any, List, Optional

# Import the standardized implementation
from .salesforce_standard_mcp_client import (
    SalesforceMCPServiceStandardized,
    get_salesforce_service as get_standardized_service
)

logger = logging.getLogger(__name__)


class SalesforceMCPService:
    """
    LEGACY WRAPPER - Service for interacting with Salesforce via proper MCP protocol.
    
    This class now delegates to the standardized MCP implementation
    while maintaining backward compatibility with existing code.
    """
    
    def __init__(self):
        # Delegate to standardized implementation
        self._standardized_service = SalesforceMCPServiceStandardized()
        
        # Maintain legacy interface properties
        self.mcp_client = None
        self._initialized = False
        self.org_alias = os.getenv("SALESFORCE_ORG_ALIAS", "DEFAULT_TARGET_ORG")
        self.enabled = os.getenv("SALESFORCE_MCP_ENABLED", "false").lower() == "true"
        
        logger.warning(
            "Using legacy SalesforceMCPService wrapper. "
            "Consider migrating to SalesforceMCPServiceStandardized for better performance."
        )
    
    async def initialize(self):
        """Initialize MCP client connection using proper MCP protocol."""
        if self._initialized:
            return
        
        try:
            # Delegate to standardized implementation
            await self._standardized_service.initialize()
            self._initialized = True
            
            logger.info(f"✅ Salesforce MCP client initialized with proper MCP protocol")
            
        except Exception as e:
            logger.error(f"Failed to initialize Salesforce MCP client: {e}")
            raise
    
    def is_enabled(self) -> bool:
        """Check if Salesforce MCP is enabled."""
        return self._standardized_service.is_enabled()
    
    async def run_soql_query(self, query: str) -> Dict[str, Any]:
        """Execute SOQL query using proper MCP protocol."""
        return await self._standardized_service.run_soql_query(query)
    

    
    async def list_orgs(self) -> List[Dict[str, Any]]:
        """List connected Salesforce orgs using proper MCP protocol."""
        return await self._standardized_service.list_orgs()
    
    async def get_account_info(self, account_name: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Get account information using proper MCP protocol."""
        return await self._standardized_service.get_account_info(account_name, limit)
    
    async def get_opportunity_info(self, limit: int = 5) -> Dict[str, Any]:
        """Get opportunity information using proper MCP protocol."""
        return await self._standardized_service.get_opportunity_info(limit)
    
    async def get_contact_info(self, limit: int = 5) -> Dict[str, Any]:
        """Get contact information using proper MCP protocol."""
        return await self._standardized_service.get_contact_info(limit)
    
    async def search_records(self, search_term: str, objects: List[str] = None) -> Dict[str, Any]:
        """Search for records using proper MCP protocol."""
        return await self._standardized_service.search_records(search_term, objects)


# Singleton instance - now uses standardized implementation
_salesforce_service = None


def get_salesforce_service() -> SalesforceMCPService:
    """
    Get or create Salesforce MCP service instance.
    
    Note: This returns the legacy wrapper for backward compatibility.
    For new code, consider using get_standardized_service() directly.
    """
    global _salesforce_service
    if _salesforce_service is None:
        _salesforce_service = SalesforceMCPService()
    return _salesforce_service
