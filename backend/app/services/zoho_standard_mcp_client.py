"""
Standardized Zoho MCP Client using proper MCP protocol.

This client replaces the direct HTTP-based ZohoMCPService with proper
MCP protocol implementation while maintaining backward compatibility.

**Feature: mcp-client-standardization, Property 1: MCP Protocol Compliance**
**Validates: Requirements 1.1, 1.3, 1.5**
"""

import logging
from typing import Dict, Any, Optional, List

from app.services.mcp_client_service import BaseMCPClient, MCPError

logger = logging.getLogger(__name__)


class ZohoStandardMCPClient:
    """
    Standardized Zoho MCP client using proper MCP protocol.
    
    This client provides the same interface as the legacy ZohoMCPService
    but uses proper MCP protocol for all communications with Zoho Invoice.
    """
    
    def __init__(self):
        """Initialize Zoho MCP client with proper protocol."""
        self.mcp_client = BaseMCPClient(
            service_name="zoho",
            server_command="python3",
            server_args=["../src/mcp_server/zoho_mcp_server.py"],
            timeout=25,
            retry_attempts=3
        )
        self._initialized = False
        
        logger.info("Zoho Standard MCP Client initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def initialize(self) -> None:
        """Initialize MCP connection to Zoho server."""
        if self._initialized:
            return
        
        try:
            await self.mcp_client.connect()
            self._initialized = True
            
            logger.info(
                "Zoho MCP client initialized successfully",
                extra={
                    "service": "zoho",
                    "available_tools": await self.mcp_client.list_available_tools()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Zoho MCP client: {e}")
            raise MCPError(f"Zoho initialization failed: {e}", "zoho", "INIT_FAILED")
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self._initialized:
            try:
                await self.mcp_client.disconnect()
                self._initialized = False
                logger.info("Zoho MCP client disconnected")
            except Exception as e:
                logger.warning(f"Error during Zoho MCP disconnect: {e}")
    
    def is_enabled(self) -> bool:
        """Check if Zoho MCP is enabled (always true for MCP client)."""
        return self._initialized
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode (determined by server)."""
        # This will be determined by the MCP server based on configuration
        return False  # MCP client doesn't know server's mock status
    
    async def list_invoices(
        self, 
        status: Optional[str] = None, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        List invoices from Zoho Invoice using MCP protocol.
        
        Args:
            status: Filter by status (sent, paid, overdue, draft, etc.)
            limit: Maximum number of invoices to return
            
        Returns:
            Dictionary with success status and invoice list
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            arguments = {"limit": limit}
            if status:
                arguments["status"] = status
            
            logger.info(
                f"Listing Zoho invoices via MCP",
                extra={
                    "status": status,
                    "limit": limit
                }
            )
            
            result = await self.mcp_client.call_tool("zoho_list_invoices", arguments)
            
            logger.info(
                f"Successfully listed Zoho invoices",
                extra={
                    "invoice_count": len(result.get("invoices", [])),
                    "success": result.get("success", False)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list Zoho invoices: {e}")
            return {
                "success": False,
                "error": str(e),
                "invoices": []
            }
    
    async def get_invoice(self, invoice_identifier: str) -> Dict[str, Any]:
        """
        Get details of a specific invoice using MCP protocol.
        
        Args:
            invoice_identifier: Zoho invoice ID or invoice number
            
        Returns:
            Dictionary with success status and invoice details
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            arguments = {"invoice_id": invoice_identifier}
            
            logger.info(
                f"Getting Zoho invoice via MCP",
                extra={
                    "invoice_id": invoice_identifier
                }
            )
            
            result = await self.mcp_client.call_tool("zoho_get_invoice", arguments)
            
            logger.info(
                f"Successfully retrieved Zoho invoice",
                extra={
                    "invoice_id": invoice_identifier,
                    "success": result.get("success", False)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get Zoho invoice: {e}")
            return {
                "success": False,
                "error": str(e),
                "invoice": {}
            }
    
    async def list_customers(self, limit: int = 10) -> Dict[str, Any]:
        """
        List customers from Zoho Invoice using MCP protocol.
        
        Args:
            limit: Maximum number of customers to return
            
        Returns:
            Dictionary with success status and customer list
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            arguments = {"limit": limit}
            
            logger.info(
                f"Listing Zoho customers via MCP",
                extra={
                    "limit": limit
                }
            )
            
            result = await self.mcp_client.call_tool("zoho_list_customers", arguments)
            
            logger.info(
                f"Successfully listed Zoho customers",
                extra={
                    "customer_count": len(result.get("contacts", [])),
                    "success": result.get("success", False)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list Zoho customers: {e}")
            return {
                "success": False,
                "error": str(e),
                "contacts": []
            }
    
    async def search_invoices(
        self,
        search_term: str,
        search_type: str = "all",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search invoices in Zoho Invoice using MCP protocol.
        
        Args:
            search_term: Search term or query
            search_type: Type of search (invoice_number, customer_name, amount, all)
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with success status and search results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            arguments = {
                "search_term": search_term,
                "search_type": search_type,
                "limit": limit
            }
            
            logger.info(
                f"Searching Zoho invoices via MCP",
                extra={
                    "search_term": search_term,
                    "search_type": search_type,
                    "limit": limit
                }
            )
            
            result = await self.mcp_client.call_tool("zoho_search_invoices", arguments)
            
            logger.info(
                f"Successfully searched Zoho invoices",
                extra={
                    "search_term": search_term,
                    "result_count": len(result.get("invoices", [])),
                    "success": result.get("success", False)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search Zoho invoices: {e}")
            return {
                "success": False,
                "error": str(e),
                "invoices": []
            }
    
    async def get_invoice_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for invoices using MCP protocol.
        
        Returns:
            Dictionary with invoice statistics
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            arguments = {"include_breakdown": True}
            
            logger.info("Getting Zoho invoice summary via MCP")
            
            result = await self.mcp_client.call_tool("zoho_get_invoice_summary", arguments)
            
            logger.info(
                f"Successfully retrieved Zoho invoice summary",
                extra={
                    "success": result.get("success", False)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get Zoho invoice summary: {e}")
            return {
                "success": False,
                "error": str(e),
                "summary": {}
            }
    
    async def list_payments(
        self,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List payments from Zoho Invoice using MCP protocol.
        
        Args:
            limit: Maximum number of payments to return
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)
            
        Returns:
            Dictionary with success status and payment list
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            arguments = {"limit": limit}
            if start_date:
                arguments["start_date"] = start_date
            if end_date:
                arguments["end_date"] = end_date
            
            logger.info(
                f"Listing Zoho payments via MCP",
                extra={
                    "limit": limit,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            result = await self.mcp_client.call_tool("zoho_list_payments", arguments)
            
            logger.info(
                f"Successfully listed Zoho payments",
                extra={
                    "payment_count": len(result.get("payments", [])),
                    "success": result.get("success", False)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list Zoho payments: {e}")
            return {
                "success": False,
                "error": str(e),
                "payments": []
            }
    
    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Get details of a specific payment using MCP protocol.
        
        Args:
            payment_id: Zoho payment ID
            
        Returns:
            Dictionary with success status and payment details
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            arguments = {"payment_id": payment_id}
            
            logger.info(
                f"Getting Zoho payment via MCP",
                extra={
                    "payment_id": payment_id
                }
            )
            
            result = await self.mcp_client.call_tool("zoho_get_payment", arguments)
            
            logger.info(
                f"Successfully retrieved Zoho payment",
                extra={
                    "payment_id": payment_id,
                    "success": result.get("success", False)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get Zoho payment: {e}")
            return {
                "success": False,
                "error": str(e),
                "payment": {}
            }
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check health of Zoho MCP connection.
        
        Returns:
            Dictionary with health status
        """
        try:
            if not self._initialized:
                return {
                    "is_healthy": False,
                    "error": "Not initialized",
                    "service": "zoho"
                }
            
            health_status = await self.mcp_client.check_health()
            
            return {
                "is_healthy": health_status.is_healthy,
                "last_check": health_status.last_check.isoformat(),
                "response_time_ms": health_status.response_time_ms,
                "available_tools": health_status.available_tools,
                "error_message": health_status.error_message,
                "connection_status": health_status.connection_status,
                "service": "zoho"
            }
            
        except Exception as e:
            logger.error(f"Failed to check Zoho health: {e}")
            return {
                "is_healthy": False,
                "error": str(e),
                "service": "zoho"
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the Zoho MCP client."""
        if not self._initialized:
            return {
                "service": "zoho",
                "error": "Not initialized"
            }
        
        return self.mcp_client.get_performance_metrics()


# Global instance for backward compatibility
_zoho_standard_client: Optional[ZohoStandardMCPClient] = None


async def get_zoho_standard_service() -> ZohoStandardMCPClient:
    """
    Get Zoho standard MCP client instance.
    
    This function provides the new standardized MCP client while maintaining
    the same interface as the legacy get_zoho_service function.
    """
    global _zoho_standard_client
    
    if _zoho_standard_client is None:
        _zoho_standard_client = ZohoStandardMCPClient()
    
    return _zoho_standard_client


# Backward compatibility wrapper
class ZohoMCPServiceStandardized:
    """
    Backward compatibility wrapper that maintains the old ZohoMCPService interface
    but uses the new standardized MCP client internally.
    
    This allows existing code to work without changes while using proper MCP protocol.
    """
    
    def __init__(self):
        self._client = None
        self._initialized = False
    
    async def _get_client(self) -> ZohoStandardMCPClient:
        """Get or create standardized MCP client."""
        if self._client is None:
            self._client = await get_zoho_standard_service()
        return self._client
    
    async def initialize(self):
        """Initialize the service (backward compatibility)."""
        if not self._initialized:
            client = await self._get_client()
            await client.initialize()
            self._initialized = True
    
    def is_enabled(self) -> bool:
        """Check if service is enabled (backward compatibility)."""
        return self._initialized
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode (backward compatibility)."""
        # The standardized client doesn't expose mock mode status
        return False
    
    async def list_invoices(self, **kwargs) -> Dict[str, Any]:
        """Legacy interface for list_invoices."""
        client = await self._get_client()
        return await client.list_invoices(**kwargs)
    
    async def get_invoice(self, invoice_identifier: str) -> Dict[str, Any]:
        """Legacy interface for get_invoice."""
        client = await self._get_client()
        return await client.get_invoice(invoice_identifier)
    
    async def list_customers(self, **kwargs) -> Dict[str, Any]:
        """Legacy interface for list_customers."""
        client = await self._get_client()
        return await client.list_customers(**kwargs)
    
    async def get_invoice_summary(self) -> Dict[str, Any]:
        """Legacy interface for get_invoice_summary."""
        client = await self._get_client()
        return await client.get_invoice_summary()


def get_zoho_service_legacy() -> ZohoMCPServiceStandardized:
    """
    Get Zoho service instance for backward compatibility.
    
    This function maintains the same name and interface as the original
    get_zoho_service function but uses standardized MCP protocol internally.
    """
    return ZohoMCPServiceStandardized()