"""
Category-Based AccountsPayable Agent for Multi-Service AP Operations.

This agent replaces brand-specific AP agents (ZohoAgent) with a unified
category-based approach that accepts service parameters to route operations
to appropriate accounts payable service backends.

**Feature: mcp-client-standardization, Property 4: Base Client Inheritance**
**Validates: Requirements 2.1, 2.5**
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.mcp_client_service import get_mcp_manager, MCPError

logger = logging.getLogger(__name__)


class AccountsPayableAgent:
    """
    Category-based agent for accounts payable operations across multiple services.
    
    This agent provides a unified interface for AP operations while supporting
    multiple AP service providers through service parameters. It uses proper
    MCP protocol for all external service communications.
    
    Supported Services:
    - bill_com: Bill.com via MCP (primary AP service)
    - quickbooks: QuickBooks via MCP (future)
    - xero: Xero via MCP (future)
    
    Note: Zoho is NOT included as it's an accounts receivable system (for customer invoices),
    not an accounts payable system (for vendor bills).
    """
    
    def __init__(self, mcp_manager=None):
        """
        Initialize AccountsPayable Agent with MCP client manager.
        
        Args:
            mcp_manager: MCP client manager instance (optional, will use global if None)
        """
        self.mcp_manager = mcp_manager or get_mcp_manager()
        self.supported_services = {
            'bill_com': {
                'name': 'Bill.com',
                'tools': {
                    'list_bills': 'get_bill_com_invoices',
                    'get_bill': 'get_bill_com_invoice',
                    'list_vendors': 'get_bill_com_vendors',
                    'get_vendor': 'get_bill_com_vendor',
                    'search_bills': 'search_bill_com_invoices',
                    'get_audit_trail': 'get_audit_trail',
                    'detect_audit_exceptions': 'detect_audit_exceptions',
                    'generate_audit_report': 'generate_audit_report'
                }
            },
            # Future service support
            'quickbooks': {
                'name': 'QuickBooks AP',
                'tools': {
                    'list_bills': 'quickbooks_list_bills',
                    'get_bill': 'quickbooks_get_bill',
                    'list_vendors': 'quickbooks_list_vendors',
                    'get_vendor': 'quickbooks_get_vendor',
                    'search_bills': 'quickbooks_search_bills'
                }
            },
            'xero': {
                'name': 'Xero AP',
                'tools': {
                    'list_bills': 'xero_list_bills',
                    'get_bill': 'xero_get_bill',
                    'list_contacts': 'xero_list_contacts',
                    'get_contact': 'xero_get_contact',
                    'search_bills': 'xero_search_bills'
                }
            }
        }
        
        logger.info(
            "AccountsPayable Agent initialized",
            extra={
                "supported_services": list(self.supported_services.keys()),
                "default_service": "bill_com"
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
                f"Unsupported accounts payable service: '{service}'. "
                f"Supported services: {supported}"
            )
    
    def _get_tool_name(self, service: str, operation: str) -> str:
        """
        Get the MCP tool name for a service operation.
        
        Args:
            service: Service name (e.g., 'zoho', 'bill_com')
            operation: Operation name (e.g., 'list_invoices')
            
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
    
    async def get_bills(
        self, 
        service: str = 'bill_com',
        status: Optional[str] = None,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        vendor_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get bills from specified accounts payable service.
        
        Args:
            service: AP service to use ('bill_com', 'quickbooks', etc.)
            status: Filter by bill status (paid, unpaid, overdue, etc.)
            limit: Maximum number of bills to return
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)
            vendor_name: Filter by vendor name
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing bill list and metadata
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported
        """
        try:
            tool_name = self._get_tool_name(service, 'list_bills')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'limit': limit,
                **kwargs
            }
            
            # Add optional filters if provided
            if status:
                arguments['status'] = status
            if start_date:
                arguments['start_date'] = start_date
            if end_date:
                arguments['end_date'] = end_date
            if vendor_name:
                arguments['vendor_name'] = vendor_name
            
            logger.info(
                f"Getting bills via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "status": status,
                    "limit": limit,
                    "vendor_name": vendor_name
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully retrieved bills from {service}",
                extra={
                    "service": service,
                    "bill_count": len(result.get('invoices', [])),  # Bill.com uses 'invoices' for bills
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to get bills from {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPError(f"Bill retrieval failed: {e}", service, "GET_BILLS_FAILED")
    
    async def get_bill(
        self,
        bill_id: str,
        service: str = 'bill_com',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get a specific bill from specified accounts payable service.
        
        Args:
            bill_id: Unique bill identifier
            service: AP service to use ('bill_com', 'quickbooks', etc.)
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing bill details
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported or bill_id missing
        """
        if not bill_id:
            raise ValueError("bill_id is required for getting bill details")
        
        try:
            tool_name = self._get_tool_name(service, 'get_bill')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'invoice_id': bill_id,  # Bill.com uses 'invoice_id' for bills
                **kwargs
            }
            
            logger.info(
                f"Getting bill via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "bill_id": bill_id
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully retrieved bill from {service}",
                extra={
                    "service": service,
                    "bill_id": bill_id,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to get bill from {service}: {e}",
                extra={
                    "service": service,
                    "bill_id": bill_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPError(f"Bill retrieval failed: {e}", service, "GET_BILL_FAILED")
    
    async def get_vendors(
        self, 
        service: str = 'bill_com',
        limit: int = 15,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get vendors from specified accounts payable service.
        
        Args:
            service: AP service to use ('bill_com', 'quickbooks', etc.)
            limit: Maximum number of vendors to return
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing vendor list and metadata
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported
        """
        try:
            # All AP services use 'list_vendors' terminology
            tool_name = self._get_tool_name(service, 'list_vendors')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'limit': limit,
                **kwargs
            }
            
            logger.info(
                f"Getting vendors via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "limit": limit
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully retrieved vendors from {service}",
                extra={
                    "service": service,
                    "vendor_count": len(result.get('vendors', [])),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to get vendors from {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPError(f"Vendor retrieval failed: {e}", service, "GET_VENDORS_FAILED")
    
    async def search_bills(
        self,
        search_term: str,
        service: str = 'bill_com',
        search_type: str = "invoice_number",
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search bills in specified accounts payable service.
        
        Args:
            search_term: Search term/query
            service: AP service to use ('bill_com', 'quickbooks', etc.)
            search_type: Type of search (invoice_number, vendor_name, etc.)
            limit: Maximum number of results to return
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing search results
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported or search_term missing
        """
        if not search_term:
            raise ValueError("search_term is required for searching bills")
        
        try:
            tool_name = self._get_tool_name(service, 'search_bills')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'search_term': search_term,
                'search_type': search_type,
                'limit': limit,
                **kwargs
            }
            
            logger.info(
                f"Searching bills via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "search_term": search_term,
                    "search_type": search_type,
                    "limit": limit
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully searched bills in {service}",
                extra={
                    "service": service,
                    "search_term": search_term,
                    "result_count": len(result.get('invoices', [])),  # Bill.com uses 'invoices' for bills
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to search bills in {service}: {e}",
                extra={
                    "service": service,
                    "search_term": search_term,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPError(f"Bill search failed: {e}", service, "SEARCH_BILLS_FAILED")
    
    async def get_audit_trail(
        self,
        entity_id: str,
        service: str = 'bill_com',
        entity_type: str = "invoice",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get audit trail for an entity (primarily for Bill.com).
        
        Args:
            entity_id: ID of the entity to get audit trail for
            service: AP service to use (primarily 'bill_com')
            entity_type: Type of entity (invoice, vendor, etc.)
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)
            limit: Maximum number of audit entries to return
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing audit trail data
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported or entity_id missing
        """
        if not entity_id:
            raise ValueError("entity_id is required for getting audit trail")
        
        try:
            tool_name = self._get_tool_name(service, 'get_audit_trail')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'entity_id': entity_id,
                'entity_type': entity_type,
                **kwargs
            }
            
            # Add optional filters if provided
            if start_date:
                arguments['start_date'] = start_date
            if end_date:
                arguments['end_date'] = end_date
            if limit:
                arguments['limit'] = limit
            
            logger.info(
                f"Getting audit trail via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "entity_id": entity_id,
                    "entity_type": entity_type
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully retrieved audit trail from {service}",
                extra={
                    "service": service,
                    "entity_id": entity_id,
                    "audit_entries": len(result.get('audit_entries', [])),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to get audit trail from {service}: {e}",
                extra={
                    "service": service,
                    "entity_id": entity_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPError(f"Audit trail retrieval failed: {e}", service, "GET_AUDIT_TRAIL_FAILED")
    
    async def get_bill_summary(
        self,
        service: str = 'bill_com',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get bill summary statistics from specified accounts payable service.
        
        Args:
            service: AP service to use ('bill_com', 'quickbooks', etc.)
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing summary statistics
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported
        """
        try:
            # Note: This may not be available for all services
            # For now, we'll try to get a summary by listing bills
            result = await self.get_bills(service=service, limit=100, **kwargs)
            
            # Generate summary from bill list
            bills = result.get('invoices', [])  # Bill.com uses 'invoices' for bills
            
            total_amount = sum(bill.get('total', 0) for bill in bills)
            total_balance = sum(bill.get('balance', 0) for bill in bills)
            
            summary = {
                'total_bills': len(bills),
                'total_amount': total_amount,
                'total_outstanding': total_balance,
                'service': service,
                'success': True
            }
            
            logger.info(
                f"Successfully generated bill summary from {service}",
                extra={
                    "service": service,
                    "total_bills": len(bills),
                    "success": True
                }
            )
            
            return summary
            
        except Exception as e:
            logger.error(
                f"Failed to get bill summary from {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPError(f"Bill summary retrieval failed: {e}", service, "GET_SUMMARY_FAILED")
    
    def get_supported_services(self) -> List[str]:
        """
        Get list of supported accounts payable services.
        
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
        Check health status of a specific accounts payable service.
        
        Args:
            service: Service name to check
            
        Returns:
            Dictionary containing health status
        """
        try:
            self._validate_service(service)
            
            # Get health status from MCP manager
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
        Check health status of all supported accounts payable services.
        
        Returns:
            Dictionary mapping service names to their health status
        """
        health_results = {}
        
        for service in self.supported_services.keys():
            health_results[service] = await self.check_service_health(service)
        
        return health_results


# Global instance for backward compatibility and easy access
_accounts_payable_agent: Optional[AccountsPayableAgent] = None


def get_accounts_payable_agent() -> AccountsPayableAgent:
    """
    Get or create global AccountsPayable Agent instance.
    
    Returns:
        AccountsPayableAgent instance
    """
    global _accounts_payable_agent
    
    if _accounts_payable_agent is None:
        _accounts_payable_agent = AccountsPayableAgent()
    
    return _accounts_payable_agent