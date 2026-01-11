"""
Category-Based CRM Agent for Multi-Service CRM Operations.

This agent replaces brand-specific CRM agents (SalesforceAgent) with a unified
category-based approach that accepts service parameters to route operations
to appropriate CRM service backends.

**Feature: mcp-client-standardization, Property 4: Base Client Inheritance**
**Validates: Requirements 2.1, 2.5**
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.mcp_http_client import get_mcp_http_manager, MCPHTTPError

logger = logging.getLogger(__name__)


class CRMAgent:
    """
    Category-based agent for CRM operations across multiple services.
    
    This agent provides a unified interface for CRM operations while supporting
    multiple CRM service providers through service parameters. It uses proper
    MCP protocol for all external service communications.
    
    Supported Services:
    - salesforce: Salesforce via MCP
    - hubspot: HubSpot via MCP (future)
    - pipedrive: Pipedrive via MCP (future)
    - zoho_crm: Zoho CRM via MCP (future)
    """
    
    def __init__(self, mcp_manager=None):
        """
        Initialize CRM Agent with MCP client manager.
        
        Args:
            mcp_manager: MCP client manager instance (optional, will use global if None)
        """
        self.mcp_manager = mcp_manager or get_mcp_http_manager()
        self.supported_services = {
            'salesforce': {
                'name': 'Salesforce',
                'tools': {
                    'get_accounts': 'salesforce_get_accounts',
                    'search_accounts': 'salesforce_get_accounts',  # Alias for search functionality
                    'get_opportunities': 'salesforce_get_opportunities',
                    'get_contacts': 'salesforce_get_contacts',
                    'search_records': 'salesforce_search_records',
                    'run_soql_query': 'salesforce_soql_query',
                    'list_orgs': 'salesforce_list_orgs'
                }
            },
            # Future service support
            'hubspot': {
                'name': 'HubSpot',
                'tools': {
                    'get_accounts': 'hubspot_get_companies',
                    'get_opportunities': 'hubspot_get_deals',
                    'get_contacts': 'hubspot_get_contacts',
                    'search_records': 'hubspot_search_records'
                }
            },
            'pipedrive': {
                'name': 'Pipedrive',
                'tools': {
                    'get_accounts': 'pipedrive_get_organizations',
                    'get_opportunities': 'pipedrive_get_deals',
                    'get_contacts': 'pipedrive_get_persons',
                    'search_records': 'pipedrive_search_records'
                }
            },
            'zoho_crm': {
                'name': 'Zoho CRM',
                'tools': {
                    'get_accounts': 'zoho_crm_get_accounts',
                    'get_opportunities': 'zoho_crm_get_deals',
                    'get_contacts': 'zoho_crm_get_contacts',
                    'search_records': 'zoho_crm_search_records'
                }
            }
        }
        
        logger.info(
            "CRM Agent initialized",
            extra={
                "supported_services": list(self.supported_services.keys()),
                "default_service": "salesforce"
            }
        )
    
    def _validate_service(self, service: str) -> None:
        """
        Validate that the requested service is supported.
        
        Args:
            service: Service name to validate
            
        Raises:
            ValueError: If service is not supported
        """
        if service not in self.supported_services:
            supported = list(self.supported_services.keys())
            raise ValueError(
                f"Unsupported CRM service: '{service}'. "
                f"Supported services: {supported}"
            )
    
    def _get_tool_name(self, service: str, operation: str) -> str:
        """
        Get the MCP tool name for a service operation.
        
        Args:
            service: Service name (e.g., 'salesforce')
            operation: Operation name (e.g., 'get_accounts')
            
        Returns:
            MCP tool name
            
        Raises:
            ValueError: If service or operation not supported
        """
        self._validate_service(service)
        
        service_config = self.supported_services[service]
        if operation not in service_config['tools']:
            available_ops = list(service_config['tools'].keys())
            raise ValueError(
                f"Unsupported operation '{operation}' for service '{service}'. "
                f"Available operations: {available_ops}"
            )
        
        return service_config['tools'][operation]
    
    async def get_accounts(
        self, 
        service: str = 'salesforce',
        account_name: Optional[str] = None,
        limit: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get accounts from specified CRM service.
        
        Args:
            service: CRM service to use ('salesforce', 'hubspot', etc.)
            account_name: Optional account name filter
            limit: Maximum number of accounts to return
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing account list and metadata
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported
        """
        try:
            tool_name = self._get_tool_name(service, 'get_accounts')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'limit': limit,
                **kwargs
            }
            
            # Add optional filters if provided
            if account_name:
                arguments['account_name'] = account_name
            
            # Add service-specific parameters
            if service == 'salesforce':
                arguments['org_alias'] = kwargs.get('org_alias', 'DEFAULT_TARGET_ORG')
            
            logger.info(
                f"Getting accounts via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "account_name": account_name,
                    "limit": limit
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully retrieved accounts from {service}",
                extra={
                    "service": service,
                    "account_count": result.get('totalSize', len(result.get('records', []))),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to get accounts from {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Account retrieval failed: {e}", service, "GET_ACCOUNTS_FAILED")
    
    async def get_opportunities(
        self, 
        service: str = 'salesforce',
        limit: int = 5,
        stage: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get opportunities from specified CRM service.
        
        Args:
            service: CRM service to use ('salesforce', 'hubspot', etc.)
            limit: Maximum number of opportunities to return
            stage: Optional stage filter
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing opportunity list and metadata
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported
        """
        try:
            tool_name = self._get_tool_name(service, 'get_opportunities')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'limit': limit,
                **kwargs
            }
            
            # Add optional filters if provided
            if stage:
                arguments['stage'] = stage
            
            # Add service-specific parameters
            if service == 'salesforce':
                arguments['org_alias'] = kwargs.get('org_alias', 'DEFAULT_TARGET_ORG')
            
            logger.info(
                f"Getting opportunities via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "stage": stage,
                    "limit": limit
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully retrieved opportunities from {service}",
                extra={
                    "service": service,
                    "opportunity_count": result.get('totalSize', len(result.get('records', []))),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to get opportunities from {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Opportunity retrieval failed: {e}", service, "GET_OPPORTUNITIES_FAILED")
    
    async def get_contacts(
        self, 
        service: str = 'salesforce',
        limit: int = 5,
        account_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get contacts from specified CRM service.
        
        Args:
            service: CRM service to use ('salesforce', 'hubspot', etc.)
            limit: Maximum number of contacts to return
            account_name: Optional account name filter
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing contact list and metadata
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported
        """
        try:
            tool_name = self._get_tool_name(service, 'get_contacts')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'limit': limit,
                **kwargs
            }
            
            # Add optional filters if provided
            if account_name:
                arguments['account_name'] = account_name
            
            # Add service-specific parameters
            if service == 'salesforce':
                arguments['org_alias'] = kwargs.get('org_alias', 'DEFAULT_TARGET_ORG')
            
            logger.info(
                f"Getting contacts via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "account_name": account_name,
                    "limit": limit
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully retrieved contacts from {service}",
                extra={
                    "service": service,
                    "contact_count": result.get('totalSize', len(result.get('records', []))),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to get contacts from {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Contact retrieval failed: {e}", service, "GET_CONTACTS_FAILED")
    
    async def search_records(
        self,
        search_term: str,
        service: str = 'salesforce',
        objects: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search records across multiple objects in specified CRM service.
        
        Args:
            search_term: Search term/query
            service: CRM service to use ('salesforce', 'hubspot', etc.)
            objects: List of object types to search (Account, Contact, etc.)
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing search results
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported or search_term missing
        """
        if not search_term:
            raise ValueError("search_term is required for searching CRM records")
        
        try:
            tool_name = self._get_tool_name(service, 'search_records')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'search_term': search_term,
                **kwargs
            }
            
            # Add optional object list if provided
            if objects:
                arguments['objects'] = objects
            elif service == 'salesforce':
                # Default Salesforce objects
                arguments['objects'] = ['Account', 'Contact', 'Opportunity']
            
            # Add service-specific parameters
            if service == 'salesforce':
                arguments['org_alias'] = kwargs.get('org_alias', 'DEFAULT_TARGET_ORG')
            
            logger.info(
                f"Searching records via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "search_term": search_term,
                    "objects": objects
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully searched records in {service}",
                extra={
                    "service": service,
                    "search_term": search_term,
                    "result_count": len(result.get('results', [])),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to search records in {service}: {e}",
                extra={
                    "service": service,
                    "search_term": search_term,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Record search failed: {e}", service, "SEARCH_RECORDS_FAILED")
    
    async def run_soql_query(
        self,
        query: str,
        service: str = 'salesforce',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a SOQL query (Salesforce-specific operation).
        
        Args:
            query: SOQL query string
            service: CRM service to use (must be 'salesforce')
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing query results
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported or query missing
        """
        if not query:
            raise ValueError("query is required for running SOQL query")
        
        if service != 'salesforce':
            raise ValueError("SOQL queries are only supported for Salesforce")
        
        try:
            tool_name = self._get_tool_name(service, 'run_soql_query')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'query': query,
                'org_alias': kwargs.get('org_alias', 'DEFAULT_TARGET_ORG'),
                **kwargs
            }
            
            logger.info(
                f"Running SOQL query via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "query_length": len(query)
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully executed SOQL query in {service}",
                extra={
                    "service": service,
                    "record_count": result.get('totalSize', 0),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to run SOQL query in {service}: {e}",
                extra={
                    "service": service,
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"SOQL query failed: {e}", service, "SOQL_QUERY_FAILED")
    
    async def list_orgs(
        self,
        service: str = 'salesforce',
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        List connected organizations (Salesforce-specific operation).
        
        Args:
            service: CRM service to use (must be 'salesforce')
            **kwargs: Additional service-specific parameters
            
        Returns:
            List of organization information
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported
        """
        if service != 'salesforce':
            raise ValueError("Organization listing is only supported for Salesforce")
        
        try:
            tool_name = self._get_tool_name(service, 'list_orgs')
            
            # Prepare arguments for MCP tool call
            arguments = kwargs
            
            logger.info(
                f"Listing orgs via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            # Extract orgs list from result
            orgs = result.get('orgs', [])
            
            logger.info(
                f"Successfully listed orgs from {service}",
                extra={
                    "service": service,
                    "org_count": len(orgs),
                    "success": True
                }
            )
            
            return orgs
            
        except Exception as e:
            logger.error(
                f"Failed to list orgs from {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Organization listing failed: {e}", service, "LIST_ORGS_FAILED")
    
    def get_supported_services(self) -> List[str]:
        """
        Get list of supported CRM services.
        
        Returns:
            List of supported service names
        """
        return list(self.supported_services.keys())
    
    def get_service_info(self, service: str) -> Dict[str, Any]:
        """
        Get information about a specific service.
        
        Args:
            service: Service name
            
        Returns:
            Dictionary containing service information
            
        Raises:
            ValueError: If service not supported
        """
        self._validate_service(service)
        
        service_config = self.supported_services[service]
        return {
            'name': service_config['name'],
            'operations': list(service_config['tools'].keys()),
            'service_id': service
        }
    
    def get_all_services_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all supported services.
        
        Returns:
            Dictionary mapping service names to their information
        """
        return {
            service: self.get_service_info(service)
            for service in self.supported_services.keys()
        }
    
    async def check_service_health(self, service: str) -> Dict[str, Any]:
        """
        Check health status of a specific CRM service.
        
        Args:
            service: Service name to check
            
        Returns:
            Dictionary containing health status
        """
        try:
            self._validate_service(service)
            
            # Get health status from HTTP MCP manager
            health_status = await self.mcp_manager.get_service_health(service)
            
            return {
                'service': service,
                'is_healthy': health_status.is_healthy,
                'last_check': health_status.last_check.isoformat(),
                'response_time_ms': health_status.response_time_ms,
                'available_tools': health_status.available_tools,
                'error_message': health_status.error_message,
                'connection_status': health_status.connection_status
            }
            
        except Exception as e:
            logger.error(
                f"Failed to check health for {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e)
                }
            )
            
            return {
                'service': service,
                'is_healthy': False,
                'last_check': datetime.now().isoformat(),
                'response_time_ms': 0,
                'available_tools': 0,
                'error_message': str(e),
                'connection_status': 'failed'
            }
    
    async def check_all_services_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health status of all supported CRM services.
        
        Returns:
            Dictionary mapping service names to their health status
        """
        health_results = {}
        
        for service in self.supported_services.keys():
            health_results[service] = await self.check_service_health(service)
        
        return health_results


# Global instance for backward compatibility and easy access
_crm_agent: Optional[CRMAgent] = None


def get_crm_agent() -> CRMAgent:
    """
    Get or create global CRM Agent instance.
    
    Returns:
        CRMAgent instance
    """
    global _crm_agent
    
    if _crm_agent is None:
        _crm_agent = CRMAgent()
    
    return _crm_agent


# Backward compatibility wrapper for existing Salesforce-specific code
class SalesforceAgentLegacy:
    """
    Legacy wrapper that maintains Salesforce-specific interface while using
    the new category-based CRM Agent internally.
    
    This allows existing code to work without changes while benefiting
    from proper MCP protocol implementation.
    """
    
    def __init__(self):
        self._crm_agent = get_crm_agent()
        self.service = 'salesforce'  # Fixed to Salesforce for backward compatibility
        
        logger.warning(
            "Using legacy SalesforceAgentLegacy wrapper. "
            "Consider migrating to CRMAgent for multi-service support."
        )
    
    async def get_account_info(
        self, 
        account_name: Optional[str] = None, 
        limit: int = 5
    ) -> Dict[str, Any]:
        """Legacy interface for getting Salesforce account info."""
        return await self._crm_agent.get_accounts(
            service=self.service,
            account_name=account_name,
            limit=limit
        )
    
    async def get_opportunity_info(self, limit: int = 5) -> Dict[str, Any]:
        """Legacy interface for getting Salesforce opportunity info."""
        return await self._crm_agent.get_opportunities(
            service=self.service,
            limit=limit
        )
    
    async def get_contact_info(self, limit: int = 5) -> Dict[str, Any]:
        """Legacy interface for getting Salesforce contact info."""
        return await self._crm_agent.get_contacts(
            service=self.service,
            limit=limit
        )
    
    async def search_records(
        self, 
        search_term: str, 
        objects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Legacy interface for searching Salesforce records."""
        return await self._crm_agent.search_records(
            search_term=search_term,
            service=self.service,
            objects=objects
        )
    
    async def run_soql_query(self, query: str) -> Dict[str, Any]:
        """Legacy interface for running SOQL queries."""
        return await self._crm_agent.run_soql_query(
            query=query,
            service=self.service
        )
    
    async def list_orgs(self) -> List[Dict[str, Any]]:
        """Legacy interface for listing Salesforce orgs."""
        return await self._crm_agent.list_orgs(service=self.service)


def get_salesforce_agent() -> SalesforceAgentLegacy:
    """
    Get Salesforce agent instance for backward compatibility.
    
    Returns:
        SalesforceAgentLegacy instance that wraps CRMAgent
    """
    return SalesforceAgentLegacy()