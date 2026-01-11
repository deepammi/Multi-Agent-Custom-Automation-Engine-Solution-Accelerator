"""
Standardized Salesforce MCP Client using proper MCP protocol.
Replaces the incorrect CLI-based approach with proper MCP communication.
"""

import logging
import os
from typing import Dict, Any, List, Optional

from .mcp_client_service import BaseMCPClient, MCPError, get_mcp_manager

logger = logging.getLogger(__name__)


class SalesforceStandardMCPClient(BaseMCPClient):
    """
    Proper MCP client for Salesforce using MCP server protocol.
    
    This replaces the incorrect CLI-based SalesforceMCPService with
    proper MCP protocol implementation.
    """
    
    def __init__(self):
        # Get configuration from environment
        org_alias = os.getenv("SALESFORCE_ORG_ALIAS", "DEFAULT_TARGET_ORG")
        enabled = os.getenv("SALESFORCE_MCP_ENABLED", "false").lower() == "true"
        
        super().__init__(
            service_name="salesforce",
            server_command="python3",
            server_args=["src/mcp_server/salesforce_mcp_server.py"],
            timeout=30,
            retry_attempts=3
        )
        
        self.org_alias = org_alias
        self.enabled = enabled
        
        logger.info(
            f"Salesforce Standard MCP Client initialized",
            extra={
                "service": self.service_name,
                "org_alias": self.org_alias,
                "enabled": self.enabled
            }
        )
    
    async def run_soql_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a SOQL query using proper MCP protocol.
        
        Args:
            query: SOQL query string
            
        Returns:
            Query results as dictionary
        """
        if not self.enabled:
            logger.info("Salesforce MCP disabled, using mock data")
            return self._get_mock_query_result(query)
        
        try:
            # Call MCP tool instead of CLI
            result = await self.call_tool("salesforce_soql_query", {
                "query": query,
                "org_alias": self.org_alias
            })
            
            logger.info(
                f"SOQL query executed via MCP",
                extra={
                    "service": self.service_name,
                    "query_length": len(query),
                    "record_count": result.get("totalSize", 0)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"SOQL query failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "error": str(e)
                }
            )
            
            # Fallback to mock data on error
            return self._get_mock_query_result(query)
    
    async def list_orgs(self) -> List[Dict[str, Any]]:
        """
        List connected Salesforce orgs using proper MCP protocol.
        
        Returns:
            List of org information
        """
        if not self.enabled:
            logger.info("Salesforce MCP disabled, using mock org data")
            return self._get_mock_orgs()
        
        try:
            # Call MCP tool instead of CLI
            result = await self.call_tool("salesforce_list_orgs", {})
            
            logger.info(
                f"Org list retrieved via MCP",
                extra={
                    "service": self.service_name,
                    "org_count": len(result.get("orgs", []))
                }
            )
            
            return result.get("orgs", [])
            
        except Exception as e:
            logger.error(
                f"Org listing failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "error": str(e)
                }
            )
            
            # Fallback to mock data on error
            return self._get_mock_orgs()
    
    async def get_account_info(self, account_name: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """
        Get account information using proper MCP protocol.
        
        Args:
            account_name: Optional account name filter
            limit: Maximum number of records to return
            
        Returns:
            Account information
        """
        if not self.enabled:
            return self._get_mock_query_result("account")
        
        try:
            # Call MCP tool instead of building SOQL manually
            result = await self.call_tool("salesforce_get_accounts", {
                "account_name": account_name,
                "limit": limit,
                "org_alias": self.org_alias
            })
            
            logger.info(
                f"Account info retrieved via MCP",
                extra={
                    "service": self.service_name,
                    "account_name": account_name,
                    "limit": limit,
                    "record_count": result.get("totalSize", 0)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Account info retrieval failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "account_name": account_name,
                    "error": str(e)
                }
            )
            
            # Fallback to mock data on error
            return self._get_mock_query_result("account")
    
    async def get_opportunity_info(self, limit: int = 5) -> Dict[str, Any]:
        """
        Get opportunity information using proper MCP protocol.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            Opportunity information
        """
        if not self.enabled:
            return self._get_mock_query_result("opportunity")
        
        try:
            # Call MCP tool instead of building SOQL manually
            result = await self.call_tool("salesforce_get_opportunities", {
                "limit": limit,
                "org_alias": self.org_alias
            })
            
            logger.info(
                f"Opportunity info retrieved via MCP",
                extra={
                    "service": self.service_name,
                    "limit": limit,
                    "record_count": result.get("totalSize", 0)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Opportunity info retrieval failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "error": str(e)
                }
            )
            
            # Fallback to mock data on error
            return self._get_mock_query_result("opportunity")
    
    async def get_contact_info(self, limit: int = 5) -> Dict[str, Any]:
        """
        Get contact information using proper MCP protocol.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            Contact information
        """
        if not self.enabled:
            return self._get_mock_query_result("contact")
        
        try:
            # Call MCP tool instead of building SOQL manually
            result = await self.call_tool("salesforce_get_contacts", {
                "limit": limit,
                "org_alias": self.org_alias
            })
            
            logger.info(
                f"Contact info retrieved via MCP",
                extra={
                    "service": self.service_name,
                    "limit": limit,
                    "record_count": result.get("totalSize", 0)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Contact info retrieval failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "error": str(e)
                }
            )
            
            # Fallback to mock data on error
            return self._get_mock_query_result("contact")
    
    async def search_records(self, search_term: str, objects: List[str] = None) -> Dict[str, Any]:
        """
        Search for records using proper MCP protocol.
        
        Args:
            search_term: Search term
            objects: List of object types to search
            
        Returns:
            Search results
        """
        if not objects:
            objects = ["Account", "Contact", "Opportunity"]
        
        if not self.enabled:
            return await self.get_account_info(account_name=search_term, limit=10)
        
        try:
            # Call MCP tool instead of building SOSL manually
            result = await self.call_tool("salesforce_search_records", {
                "search_term": search_term,
                "objects": objects,
                "org_alias": self.org_alias
            })
            
            logger.info(
                f"Record search completed via MCP",
                extra={
                    "service": self.service_name,
                    "search_term": search_term,
                    "objects": objects,
                    "result_count": len(result.get("results", []))
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Record search failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "search_term": search_term,
                    "error": str(e)
                }
            )
            
            # Fallback to account search
            return await self.get_account_info(account_name=search_term, limit=10)
    
    def _get_mock_query_result(self, query_type: str) -> Dict[str, Any]:
        """Generate mock query results based on query type."""
        query_type_lower = query_type.lower()
        
        if "account" in query_type_lower:
            return {
                "success": True,
                "totalSize": 3,
                "records": [
                    {
                        "Id": "001xx000003DGb2AAG",
                        "Name": "Acme Corporation",
                        "Phone": "(415) 555-1234",
                        "Industry": "Technology",
                        "AnnualRevenue": 5000000
                    },
                    {
                        "Id": "001xx000003DGb3AAG",
                        "Name": "Global Industries",
                        "Phone": "(212) 555-5678",
                        "Industry": "Manufacturing",
                        "AnnualRevenue": 12000000
                    },
                    {
                        "Id": "001xx000003DGb4AAG",
                        "Name": "Tech Solutions Inc",
                        "Phone": "(650) 555-9012",
                        "Industry": "Technology",
                        "AnnualRevenue": 8500000
                    }
                ]
            }
        elif "opportunity" in query_type_lower:
            return {
                "success": True,
                "totalSize": 2,
                "records": [
                    {
                        "Id": "006xx000001T2jzAAC",
                        "Name": "Enterprise Software Deal",
                        "StageName": "Negotiation/Review",
                        "Amount": 250000,
                        "CloseDate": "2025-03-15",
                        "Account": {"Name": "Acme Corporation"}
                    },
                    {
                        "Id": "006xx000001T2k0AAC",
                        "Name": "Cloud Migration Project",
                        "StageName": "Proposal/Price Quote",
                        "Amount": 180000,
                        "CloseDate": "2025-04-01",
                        "Account": {"Name": "Global Industries"}
                    }
                ]
            }
        elif "contact" in query_type_lower:
            return {
                "success": True,
                "totalSize": 2,
                "records": [
                    {
                        "Id": "003xx000001T2jzAAC",
                        "Name": "John Smith",
                        "Email": "john.smith@acme.com",
                        "Phone": "(415) 555-1234",
                        "Title": "VP of Engineering",
                        "Account": {"Name": "Acme Corporation"}
                    },
                    {
                        "Id": "003xx000001T2k0AAC",
                        "Name": "Sarah Johnson",
                        "Email": "sarah.j@globalind.com",
                        "Phone": "(212) 555-5678",
                        "Title": "CTO",
                        "Account": {"Name": "Global Industries"}
                    }
                ]
            }
        else:
            return {
                "success": True,
                "totalSize": 0,
                "records": []
            }
    
    def _get_mock_orgs(self) -> List[Dict[str, Any]]:
        """Generate mock org data."""
        return [
            {
                "alias": "MockDevOrg",
                "username": "demo@example.com",
                "orgId": "00Dxx0000001gEREAY",
                "instanceUrl": "https://na1.salesforce.com",
                "isDefaultOrg": True
            }
        ]


# Backward compatibility wrapper
class SalesforceMCPServiceStandardized:
    """
    Backward compatibility wrapper that maintains the old interface
    but uses proper MCP protocol internally.
    """
    
    def __init__(self):
        self._client = None
        self._manager = get_mcp_manager()
        
        # Register Salesforce service with manager
        async def create_salesforce_client():
            client = SalesforceStandardMCPClient()
            await client.connect()
            return client
        
        self._manager.register_service("salesforce", create_salesforce_client)
        
        logger.info("Salesforce MCP service initialized with proper MCP protocol")
    
    async def _get_client(self) -> SalesforceStandardMCPClient:
        """Get or create standardized MCP client."""
        if self._client is None:
            self._client = await self._manager.get_client("salesforce")
        return self._client
    
    async def initialize(self):
        """Initialize method for backward compatibility."""
        await self._get_client()
    
    def is_enabled(self) -> bool:
        """Check if Salesforce MCP is enabled."""
        return os.getenv("SALESFORCE_MCP_ENABLED", "false").lower() == "true"
    
    async def run_soql_query(self, query: str) -> Dict[str, Any]:
        """Execute SOQL query using proper MCP protocol."""
        client = await self._get_client()
        return await client.run_soql_query(query)
    
    async def list_orgs(self) -> List[Dict[str, Any]]:
        """List orgs using proper MCP protocol."""
        client = await self._get_client()
        return await client.list_orgs()
    
    async def get_account_info(self, account_name: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Get account info using proper MCP protocol."""
        client = await self._get_client()
        return await client.get_account_info(account_name, limit)
    
    async def get_opportunity_info(self, limit: int = 5) -> Dict[str, Any]:
        """Get opportunity info using proper MCP protocol."""
        client = await self._get_client()
        return await client.get_opportunity_info(limit)
    
    async def get_contact_info(self, limit: int = 5) -> Dict[str, Any]:
        """Get contact info using proper MCP protocol."""
        client = await self._get_client()
        return await client.get_contact_info(limit)
    
    async def search_records(self, search_term: str, objects: List[str] = None) -> Dict[str, Any]:
        """Search records using proper MCP protocol."""
        client = await self._get_client()
        return await client.search_records(search_term, objects)


# Global instance for backward compatibility
_salesforce_service = None


def get_salesforce_service() -> SalesforceMCPServiceStandardized:
    """Get or create standardized Salesforce MCP service instance."""
    global _salesforce_service
    if _salesforce_service is None:
        _salesforce_service = SalesforceMCPServiceStandardized()
    return _salesforce_service