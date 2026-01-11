"""
Zoho Invoice MCP client service for interacting with Zoho Invoice data.

This service now uses standardized MCP protocol while maintaining backward compatibility.
The original HTTP-based implementation is preserved as a fallback.

**Feature: mcp-client-standardization, Property 1: MCP Protocol Compliance**
**Validates: Requirements 1.1, 1.3, 1.5**
"""
import logging
import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Flag to control whether to use standardized MCP client or legacy HTTP client
USE_STANDARDIZED_MCP = os.getenv("ZOHO_USE_STANDARDIZED_MCP", "true").lower() == "true"

if USE_STANDARDIZED_MCP:
    try:
        from app.services.zoho_standard_mcp_client import ZohoStandardMCPClient
        STANDARDIZED_CLIENT_AVAILABLE = True
        logger.info("Using standardized Zoho MCP client")
    except ImportError as e:
        STANDARDIZED_CLIENT_AVAILABLE = False
        logger.warning(f"Standardized MCP client not available, falling back to legacy: {e}")
else:
    STANDARDIZED_CLIENT_AVAILABLE = False
    logger.info("Using legacy Zoho HTTP client (standardized MCP disabled)")


class ZohoMCPService:
    """Service for interacting with Zoho Invoice via MCP (with OAuth support)."""
    
    def __init__(self):
        self.mcp_client = None
        self._initialized = False
        self.enabled = os.getenv("ZOHO_MCP_ENABLED", "false").lower() == "true"
        self.use_mock = os.getenv("ZOHO_USE_MOCK", "true").lower() == "true"
        
        # Initialize standardized client if available
        self._standardized_client = None
        if USE_STANDARDIZED_MCP and STANDARDIZED_CLIENT_AVAILABLE:
            self._use_standardized = True
            logger.info("Zoho service will use standardized MCP client")
        else:
            self._use_standardized = False
            logger.info("Zoho service will use legacy HTTP client")
        
        # OAuth configuration
        self.client_id = os.getenv("ZOHO_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("ZOHO_CLIENT_SECRET", "").strip()
        self.refresh_token = os.getenv("ZOHO_REFRESH_TOKEN", "").strip()
        self.organization_id = os.getenv("ZOHO_ORGANIZATION_ID", "").strip()
        self.data_center = os.getenv("ZOHO_DATA_CENTER", "com").strip()
        
        # Access token (will be refreshed as needed)
        self._access_token = None
        self._token_expires_at = None
        
        # API URLs
        self.dc_urls = {
            'com': {
                'accounts': 'https://accounts.zoho.com',
                'api': 'https://invoice.zoho.com/api/v3'
            },
            'eu': {
                'accounts': 'https://accounts.zoho.eu',
                'api': 'https://invoice.zoho.eu/api/v3'
            },
            'in': {
                'accounts': 'https://accounts.zoho.in',
                'api': 'https://invoice.zoho.in/api/v3'
            }
        }
        self.urls = self.dc_urls.get(self.data_center, self.dc_urls['com'])
    
    async def initialize(self):
        """Initialize Zoho MCP service."""
        if self._initialized:
            return
        
        if self._use_standardized:
            # Initialize standardized MCP client
            try:
                self._standardized_client = ZohoStandardMCPClient()
                await self._standardized_client.initialize()
                logger.info("Zoho MCP service initialized with standardized MCP client")
            except Exception as e:
                logger.error(f"Failed to initialize standardized MCP client: {e}")
                self._use_standardized = False
                logger.info("Falling back to legacy HTTP client")
        
        if not self._use_standardized:
            # Use legacy initialization
            if self.use_mock:
                logger.info("Zoho MCP service initialized in MOCK mode")
            elif self.enabled and self.refresh_token:
                logger.info("Zoho MCP service initialized with OAuth")
            else:
                logger.warning("Zoho MCP service initialized but OAuth not configured")
        
        self._initialized = True
    
    def is_enabled(self) -> bool:
        """Check if Zoho MCP is enabled."""
        return self.enabled
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self.use_mock
    
    async def _get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary."""
        # Check if we have a valid token
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        # Need to refresh token
        if not self.refresh_token:
            logger.error("No refresh token available")
            return None
        
        try:
            token_url = f"{self.urls['accounts']}/oauth/v2/token"
            payload = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token
            }
            
            response = requests.post(token_url, data=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self._access_token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("Access token refreshed successfully")
            return self._access_token
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return None
    
    async def _make_api_request(self, endpoint: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated API request to Zoho Invoice."""
        access_token = await self._get_access_token()
        if not access_token:
            return {"success": False, "error": "No valid access token"}
        
        url = f"{self.urls['api']}/{endpoint}"
        headers = {
            'Authorization': f'Zoho-oauthtoken {access_token}',
            'X-com-zoho-invoice-organizationid': self.organization_id
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                return {"success": True, **result}
            else:
                return {"success": False, "error": result.get('message', 'Unknown error')}
                
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_mock_invoices(self) -> List[Dict[str, Any]]:
        """Generate mock invoice data."""
        return [
            {
                "invoice_id": "90300000079426",
                "invoice_number": "INV-00001",
                "customer_name": "Acme Corporation",
                "customer_id": "90300000079001",
                "status": "sent",
                "date": "2025-01-15",
                "due_date": "2025-02-14",
                "currency_code": "USD",
                "currency_symbol": "$",
                "total": 1500.00,
                "balance": 1500.00,
                "created_time": "2025-01-15T10:30:00-0800"
            },
            {
                "invoice_id": "90300000079427",
                "invoice_number": "INV-00002",
                "customer_name": "Tech Solutions Inc",
                "customer_id": "90300000079002",
                "status": "paid",
                "date": "2025-01-20",
                "due_date": "2025-02-19",
                "currency_code": "USD",
                "currency_symbol": "$",
                "total": 2750.00,
                "balance": 0.00,
                "created_time": "2025-01-20T14:15:00-0800"
            },
            {
                "invoice_id": "90300000079428",
                "invoice_number": "INV-00003",
                "customer_name": "Global Industries",
                "customer_id": "90300000079003",
                "status": "overdue",
                "date": "2024-12-10",
                "due_date": "2025-01-09",
                "currency_code": "USD",
                "currency_symbol": "$",
                "total": 5200.00,
                "balance": 5200.00,
                "created_time": "2024-12-10T09:45:00-0800"
            }
        ]
    
    def _get_mock_customers(self) -> List[Dict[str, Any]]:
        """Generate mock customer data."""
        return [
            {
                "contact_id": "90300000079001",
                "contact_name": "Acme Corporation",
                "company_name": "Acme Corporation",
                "email": "billing@acme.com",
                "phone": "(415) 555-1234",
                "status": "active"
            },
            {
                "contact_id": "90300000079002",
                "contact_name": "Tech Solutions Inc",
                "company_name": "Tech Solutions Inc",
                "email": "accounts@techsolutions.com",
                "phone": "(650) 555-5678",
                "status": "active"
            },
            {
                "contact_id": "90300000079003",
                "contact_name": "Global Industries",
                "company_name": "Global Industries",
                "email": "finance@globalind.com",
                "phone": "(212) 555-9012",
                "status": "active"
            }
        ]
    
    async def list_invoices(self, status: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        List invoices from Zoho Invoice.
        
        Args:
            status: Filter by status (sent, paid, overdue, draft, etc.)
            limit: Maximum number of invoices to return
            
        Returns:
            Dictionary with success status and invoice list
        """
        if not self._initialized:
            await self.initialize()
        
        # Use standardized MCP client if available
        if self._use_standardized and self._standardized_client:
            try:
                return await self._standardized_client.list_invoices(status=status, limit=limit)
            except Exception as e:
                logger.error(f"Standardized MCP client failed, falling back to legacy: {e}")
                self._use_standardized = False
        
        # Use legacy implementation
        # Use mock data if enabled
        if self.use_mock:
            logger.info("Using mock invoice data")
            invoices = self._get_mock_invoices()
            
            # Apply status filter if provided
            if status:
                invoices = [inv for inv in invoices if inv['status'].lower() == status.lower()]
            
            # Apply limit
            invoices = invoices[:limit]
            
            return {
                "success": True,
                "invoices": invoices,
                "total": len(invoices)
            }
        
        # Use real API
        params = {'per_page': limit}
        if status:
            params['status'] = status
        
        result = await self._make_api_request('invoices', params=params)
        
        if result.get('success'):
            return {
                "success": True,
                "invoices": result.get('invoices', []),
                "total": result.get('page_context', {}).get('total', 0)
            }
        else:
            return result
    
    async def get_invoice(self, invoice_identifier: str) -> Dict[str, Any]:
        """
        Get details of a specific invoice.
        
        Args:
            invoice_identifier: Zoho invoice ID or invoice number (e.g., "INV-000001")
            
        Returns:
            Dictionary with success status and invoice details
        """
        if not self._initialized:
            await self.initialize()
        
        # Use standardized MCP client if available
        if self._use_standardized and self._standardized_client:
            try:
                return await self._standardized_client.get_invoice(invoice_identifier)
            except Exception as e:
                logger.error(f"Standardized MCP client failed, falling back to legacy: {e}")
                self._use_standardized = False
        
        # Use legacy implementation
        # Use mock data if enabled
        if self.use_mock:
            logger.info(f"Using mock data for invoice {invoice_identifier}")
            invoices = self._get_mock_invoices()
            invoice = next((inv for inv in invoices if inv['invoice_id'] == invoice_identifier or inv['invoice_number'] == invoice_identifier), None)
            
            if invoice:
                return {"success": True, "invoice": invoice}
            else:
                return {"success": False, "error": "Invoice not found"}
        
        # Check if this is an invoice number (starts with letters) or ID (all digits)
        if invoice_identifier.replace('-', '').replace('_', '').isalpha() or '-' in invoice_identifier:
            # This looks like an invoice number, need to search for it
            logger.info(f"Searching for invoice by number: {invoice_identifier}")
            result = await self.list_invoices(limit=100)
            
            if result.get('success'):
                invoices = result.get('invoices', [])
                invoice = next((inv for inv in invoices if inv.get('invoice_number') == invoice_identifier), None)
                
                if invoice:
                    # Now get full details using the invoice_id
                    invoice_id = invoice.get('invoice_id')
                    return await self._get_invoice_by_id(invoice_id)
                else:
                    return {"success": False, "error": f"Invoice {invoice_identifier} not found"}
            else:
                return result
        else:
            # This is an invoice ID
            return await self._get_invoice_by_id(invoice_identifier)
    
    async def _get_invoice_by_id(self, invoice_id: str) -> Dict[str, Any]:
        """Get invoice by numeric ID."""
        result = await self._make_api_request(f'invoices/{invoice_id}')
        
        if result.get('success'):
            return {
                "success": True,
                "invoice": result.get('invoice', {})
            }
        else:
            return result
    
    async def list_customers(self, limit: int = 10) -> Dict[str, Any]:
        """
        List customers from Zoho Invoice.
        
        Args:
            limit: Maximum number of customers to return
            
        Returns:
            Dictionary with success status and customer list
        """
        if not self._initialized:
            await self.initialize()
        
        # Use standardized MCP client if available
        if self._use_standardized and self._standardized_client:
            try:
                return await self._standardized_client.list_customers(limit=limit)
            except Exception as e:
                logger.error(f"Standardized MCP client failed, falling back to legacy: {e}")
                self._use_standardized = False
        
        # Use legacy implementation
        # Use mock data if enabled
        if self.use_mock:
            logger.info("Using mock customer data")
            customers = self._get_mock_customers()[:limit]
            
            return {
                "success": True,
                "contacts": customers,
                "total": len(customers)
            }
        
        # Use real API
        params = {'per_page': limit}
        result = await self._make_api_request('contacts', params=params)
        
        if result.get('success'):
            return {
                "success": True,
                "contacts": result.get('contacts', []),
                "total": result.get('page_context', {}).get('total', 0)
            }
        else:
            return result
    
    async def get_invoice_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for invoices.
        
        Returns:
            Dictionary with invoice statistics
        """
        if not self._initialized:
            await self.initialize()
        
        # Use standardized MCP client if available
        if self._use_standardized and self._standardized_client:
            try:
                return await self._standardized_client.get_invoice_summary()
            except Exception as e:
                logger.error(f"Standardized MCP client failed, falling back to legacy: {e}")
                self._use_standardized = False
        
        # Use legacy implementation
        # Get all invoices
        result = await self.list_invoices(limit=100)
        
        if not result.get('success'):
            return result
        
        invoices = result.get('invoices', [])
        
        # Calculate statistics
        total_invoices = len(invoices)
        total_amount = sum(inv.get('total', 0) for inv in invoices)
        total_outstanding = sum(inv.get('balance', 0) for inv in invoices)
        
        status_counts = {}
        for inv in invoices:
            status = inv.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "success": True,
            "summary": {
                "total_invoices": total_invoices,
                "total_amount": total_amount,
                "total_outstanding": total_outstanding,
                "status_breakdown": status_counts
            }
        }


# Singleton instance
_zoho_service = None


def get_zoho_service() -> ZohoMCPService:
    """Get or create Zoho MCP service instance."""
    global _zoho_service
    if _zoho_service is None:
        _zoho_service = ZohoMCPService()
    return _zoho_service
