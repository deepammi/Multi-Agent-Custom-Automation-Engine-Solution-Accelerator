# Design Document

## Overview

This design document outlines the integration of Bill.com API as a backend tool for the Multi-Agent Custom Automation Engine (MACAE). The integration follows Phase 1 approach with hardcoded query functions, similar to existing Salesforce and Zoho integrations, while maintaining a structure that can evolve toward AI-generated queries in future phases.

The solution adds Bill.com API wrapper functions to the existing MCP server, handles authentication and session management, and provides invoice data access tools for Invoice, Closing, and Audit agents.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   LangGraph     │
│   Agents        │
│ (Invoice/Audit/ │
│   Closing)      │
└────────┬────────┘
         │ MCP Tool Calls
         ▼
┌─────────────────┐
│   MCP Server    │
│ (Existing)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Bill.com API    │
│   Wrapper       │
│   Service       │
└────────┬────────┘
         │ HTTPS/REST
         ▼
┌─────────────────┐
│   Bill.com      │
│   API Gateway   │
│ (gateway.stage. │
│  bill.com)      │
└─────────────────┘
```

### Component Interaction Flow

1. **Agent requests invoice data** → Calls MCP tool (e.g., "get_bill_com_invoices")
2. **MCP Server receives call** → Routes to Bill.com API wrapper
3. **Authentication check** → Validates/refreshes Bill.com session
4. **API call execution** → Makes authenticated request to Bill.com API
5. **Response processing** → Formats data into standardized structure
6. **Result return** → Sends formatted data back to agent
7. **Agent processing** → Uses invoice data for analysis/workflow

## Components and Interfaces

### 1. Bill.com API Service (`src/mcp_server/services/bill_com_service.py`)

**Purpose**: Core service for Bill.com API authentication and data operations.

```python
import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BillComConfig:
    """Bill.com API configuration."""
    base_url: str
    username: str
    password: str
    organization_id: str
    dev_key: str
    environment: str = "stage"  # stage or production
    
    @classmethod
    def from_env(cls) -> 'BillComConfig':
        """Load configuration from environment variables."""
        return cls(
            base_url=os.getenv("BILL_COM_BASE_URL", "https://gateway.stage.bill.com"),
            username=os.getenv("BILL_COM_USERNAME"),
            password=os.getenv("BILL_COM_PASSWORD"),
            organization_id=os.getenv("BILL_COM_ORG_ID"),
            dev_key=os.getenv("BILL_COM_DEV_KEY"),
            environment=os.getenv("BILL_COM_ENVIRONMENT", "stage")
        )
    
    def validate(self) -> bool:
        """Validate that all required fields are present."""
        required_fields = [self.username, self.password, self.organization_id, self.dev_key]
        return all(field is not None for field in required_fields)


@dataclass
class BillComSession:
    """Bill.com API session information."""
    session_id: str
    organization_id: str
    user_id: str
    expires_at: datetime
    
    def is_expired(self) -> bool:
        """Check if session is expired (with 5 minute buffer)."""
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=5))


class BillComAPIService:
    """Service for Bill.com API operations."""
    
    def __init__(self):
        self.config = BillComConfig.from_env()
        self.session: Optional[BillComSession] = None
        self._http_session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._http_session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_session:
            await self._http_session.close()
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Bill.com API and establish session.
        
        Returns:
            bool: True if authentication successful
        """
        if not self.config.validate():
            logger.error("Bill.com configuration is incomplete")
            return False
        
        login_url = f"{self.config.base_url}/connect/v3/login"
        login_data = {
            "username": self.config.username,
            "password": self.config.password,
            "organizationId": self.config.organization_id,
            "devKey": self.config.dev_key
        }
        
        try:
            logger.info(f"Authenticating with Bill.com API [org={self.config.organization_id}]")
            
            async with self._http_session.post(
                login_url,
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Create session object
                    self.session = BillComSession(
                        session_id=data["sessionId"],
                        organization_id=data["organizationId"],
                        user_id=data["userId"],
                        expires_at=datetime.utcnow() + timedelta(hours=2)  # Assume 2 hour session
                    )
                    
                    logger.info(f"✅ Bill.com authentication successful [session={self.session.session_id[:8]}...]")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Bill.com authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Bill.com authentication error: {e}")
            return False
    
    async def ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid authenticated session.
        
        Returns:
            bool: True if session is valid/established
        """
        if not self.session or self.session.is_expired():
            return await self.authenticate()
        return True
    
    async def make_api_call(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make authenticated API call to Bill.com.
        
        Args:
            endpoint: API endpoint (e.g., "/v3/invoices")
            method: HTTP method
            data: Request body data
            params: Query parameters
            
        Returns:
            API response data or None if failed
        """
        if not await self.ensure_authenticated():
            logger.error("Cannot make API call - authentication failed")
            return None
        
        url = f"{self.config.base_url}{endpoint}"
        
        # Add session ID to request
        if params is None:
            params = {}
        params["sessionId"] = self.session.session_id
        
        headers = {"Content-Type": "application/json"}
        
        try:
            logger.debug(f"Bill.com API call: {method} {endpoint}")
            
            async with self._http_session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    # Session expired, try to re-authenticate
                    logger.warning("Bill.com session expired, re-authenticating...")
                    if await self.authenticate():
                        # Retry with new session
                        params["sessionId"] = self.session.session_id
                        async with self._http_session.request(
                            method=method,
                            url=url,
                            json=data,
                            params=params,
                            headers=headers
                        ) as retry_response:
                            if retry_response.status == 200:
                                return await retry_response.json()
                    
                    logger.error("Bill.com re-authentication failed")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Bill.com API error: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Bill.com API call failed: {e}")
            return None
    
    # Hardcoded query functions for Phase 1
    
    async def get_invoices(
        self,
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        vendor_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get invoices with optional filtering.
        
        Args:
            limit: Maximum number of invoices to return
            start_date: Filter by invoice date (YYYY-MM-DD)
            end_date: Filter by invoice date (YYYY-MM-DD)
            vendor_id: Filter by vendor ID
            status: Filter by status (draft, sent, viewed, approved, paid)
            
        Returns:
            List of invoice data
        """
        params = {"max": limit}
        
        # Add filters if provided
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if vendor_id:
            params["vendorId"] = vendor_id
        if status:
            params["status"] = status
        
        response = await self.make_api_call("/v3/invoices", params=params)
        
        if response and "response_data" in response:
            return response["response_data"]
        return []
    
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Dict]:
        """
        Get detailed invoice information by ID.
        
        Args:
            invoice_id: Bill.com invoice ID
            
        Returns:
            Invoice details or None if not found
        """
        response = await self.make_api_call(f"/v3/invoices/{invoice_id}")
        
        if response and "response_data" in response:
            return response["response_data"]
        return None
    
    async def search_invoices_by_number(self, invoice_number: str) -> List[Dict]:
        """
        Search invoices by invoice number.
        
        Args:
            invoice_number: Invoice number to search for
            
        Returns:
            List of matching invoices
        """
        params = {"invoiceNumber": invoice_number}
        response = await self.make_api_call("/v3/invoices/search", params=params)
        
        if response and "response_data" in response:
            return response["response_data"]
        return []
    
    async def get_vendors(self, limit: int = 100) -> List[Dict]:
        """
        Get list of vendors.
        
        Args:
            limit: Maximum number of vendors to return
            
        Returns:
            List of vendor data
        """
        params = {"max": limit}
        response = await self.make_api_call("/v3/vendors", params=params)
        
        if response and "response_data" in response:
            return response["response_data"]
        return []
    
    async def get_invoice_payments(self, invoice_id: str) -> List[Dict]:
        """
        Get payment history for an invoice.
        
        Args:
            invoice_id: Bill.com invoice ID
            
        Returns:
            List of payment records
        """
        response = await self.make_api_call(f"/v3/invoices/{invoice_id}/payments")
        
        if response and "response_data" in response:
            return response["response_data"]
        return []


# Global service instance
_bill_com_service: Optional[BillComAPIService] = None


async def get_bill_com_service() -> BillComAPIService:
    """Get or create Bill.com service instance."""
    global _bill_com_service
    
    if _bill_com_service is None:
        _bill_com_service = BillComAPIService()
        await _bill_com_service.__aenter__()
    
    return _bill_com_service
```

### 2. MCP Tool Definitions (`src/mcp_server/core/bill_com_tools.py`)

**Purpose**: Define MCP tools that wrap Bill.com API operations for agent use.

```python
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime, timedelta

from ..services.bill_com_service import get_bill_com_service

logger = logging.getLogger(__name__)


async def get_bill_com_invoices(
    limit: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    vendor_name: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get invoices from Bill.com with optional filtering.
    
    Args:
        limit: Maximum number of invoices (default 20, max 100)
        start_date: Start date filter (YYYY-MM-DD format)
        end_date: End date filter (YYYY-MM-DD format)  
        vendor_name: Filter by vendor name (partial match)
        status: Filter by status (draft, sent, viewed, approved, paid)
    
    Returns:
        Dict with invoices list and metadata
    """
    try:
        service = await get_bill_com_service()
        
        # Validate limit
        limit = min(max(1, limit), 100)
        
        # Get invoices from Bill.com
        invoices = await service.get_invoices(
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        # Filter by vendor name if provided (client-side filtering)
        if vendor_name and invoices:
            vendor_name_lower = vendor_name.lower()
            invoices = [
                inv for inv in invoices 
                if vendor_name_lower in inv.get("vendorName", "").lower()
            ]
        
        # Format response
        formatted_invoices = []
        for invoice in invoices:
            formatted_invoices.append({
                "id": invoice.get("id"),
                "invoice_number": invoice.get("invoiceNumber"),
                "vendor_name": invoice.get("vendorName"),
                "invoice_date": invoice.get("invoiceDate"),
                "due_date": invoice.get("dueDate"),
                "total_amount": invoice.get("amount"),
                "status": invoice.get("status"),
                "currency": invoice.get("currency", "USD"),
                "description": invoice.get("description", "")
            })
        
        return {
            "success": True,
            "invoices": formatted_invoices,
            "count": len(formatted_invoices),
            "filters_applied": {
                "limit": limit,
                "start_date": start_date,
                "end_date": end_date,
                "vendor_name": vendor_name,
                "status": status
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Bill.com invoices: {e}")
        return {
            "success": False,
            "error": str(e),
            "invoices": [],
            "count": 0
        }


async def get_bill_com_invoice_details(invoice_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific Bill.com invoice.
    
    Args:
        invoice_id: Bill.com invoice ID
    
    Returns:
        Dict with detailed invoice information
    """
    try:
        service = await get_bill_com_service()
        
        # Get invoice details
        invoice = await service.get_invoice_by_id(invoice_id)
        
        if not invoice:
            return {
                "success": False,
                "error": f"Invoice {invoice_id} not found",
                "invoice": None
            }
        
        # Get payment history
        payments = await service.get_invoice_payments(invoice_id)
        
        # Format detailed response
        formatted_invoice = {
            "id": invoice.get("id"),
            "invoice_number": invoice.get("invoiceNumber"),
            "vendor_name": invoice.get("vendorName"),
            "vendor_id": invoice.get("vendorId"),
            "invoice_date": invoice.get("invoiceDate"),
            "due_date": invoice.get("dueDate"),
            "total_amount": invoice.get("amount"),
            "status": invoice.get("status"),
            "currency": invoice.get("currency", "USD"),
            "description": invoice.get("description", ""),
            "line_items": invoice.get("lineItems", []),
            "approval_status": invoice.get("approvalStatus"),
            "created_time": invoice.get("createdTime"),
            "updated_time": invoice.get("updatedTime"),
            "payment_history": payments,
            "remaining_balance": invoice.get("remainingBalance", invoice.get("amount"))
        }
        
        return {
            "success": True,
            "invoice": formatted_invoice,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Bill.com invoice details for {invoice_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "invoice": None
        }


async def search_bill_com_invoices(
    query: str,
    search_type: str = "invoice_number"
) -> Dict[str, Any]:
    """
    Search Bill.com invoices by various criteria.
    
    Args:
        query: Search query string
        search_type: Type of search (invoice_number, vendor_name, amount_range)
    
    Returns:
        Dict with search results
    """
    try:
        service = await get_bill_com_service()
        
        if search_type == "invoice_number":
            # Search by invoice number
            invoices = await service.search_invoices_by_number(query)
            
        elif search_type == "vendor_name":
            # Search by vendor name (get all invoices and filter)
            all_invoices = await service.get_invoices(limit=100)
            query_lower = query.lower()
            invoices = [
                inv for inv in all_invoices
                if query_lower in inv.get("vendorName", "").lower()
            ]
            
        elif search_type == "amount_range":
            # Parse amount range (e.g., "100-500" or ">1000")
            try:
                if "-" in query:
                    min_amount, max_amount = map(float, query.split("-"))
                    all_invoices = await service.get_invoices(limit=100)
                    invoices = [
                        inv for inv in all_invoices
                        if min_amount <= float(inv.get("amount", 0)) <= max_amount
                    ]
                elif query.startswith(">"):
                    min_amount = float(query[1:])
                    all_invoices = await service.get_invoices(limit=100)
                    invoices = [
                        inv for inv in all_invoices
                        if float(inv.get("amount", 0)) > min_amount
                    ]
                elif query.startswith("<"):
                    max_amount = float(query[1:])
                    all_invoices = await service.get_invoices(limit=100)
                    invoices = [
                        inv for inv in all_invoices
                        if float(inv.get("amount", 0)) < max_amount
                    ]
                else:
                    exact_amount = float(query)
                    all_invoices = await service.get_invoices(limit=100)
                    invoices = [
                        inv for inv in all_invoices
                        if abs(float(inv.get("amount", 0)) - exact_amount) < 0.01
                    ]
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid amount range format: {query}",
                    "invoices": [],
                    "count": 0
                }
        else:
            return {
                "success": False,
                "error": f"Unsupported search type: {search_type}",
                "invoices": [],
                "count": 0
            }
        
        # Format results
        formatted_invoices = []
        for invoice in invoices:
            formatted_invoices.append({
                "id": invoice.get("id"),
                "invoice_number": invoice.get("invoiceNumber"),
                "vendor_name": invoice.get("vendorName"),
                "invoice_date": invoice.get("invoiceDate"),
                "due_date": invoice.get("dueDate"),
                "total_amount": invoice.get("amount"),
                "status": invoice.get("status"),
                "currency": invoice.get("currency", "USD")
            })
        
        return {
            "success": True,
            "invoices": formatted_invoices,
            "count": len(formatted_invoices),
            "search_query": query,
            "search_type": search_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to search Bill.com invoices: {e}")
        return {
            "success": False,
            "error": str(e),
            "invoices": [],
            "count": 0
        }


async def get_bill_com_vendors() -> Dict[str, Any]:
    """
    Get list of vendors from Bill.com.
    
    Returns:
        Dict with vendors list
    """
    try:
        service = await get_bill_com_service()
        
        vendors = await service.get_vendors(limit=100)
        
        # Format vendors
        formatted_vendors = []
        for vendor in vendors:
            formatted_vendors.append({
                "id": vendor.get("id"),
                "name": vendor.get("name"),
                "email": vendor.get("email"),
                "phone": vendor.get("phone"),
                "address": vendor.get("address"),
                "status": vendor.get("isActive", True),
                "created_time": vendor.get("createdTime")
            })
        
        return {
            "success": True,
            "vendors": formatted_vendors,
            "count": len(formatted_vendors),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Bill.com vendors: {e}")
        return {
            "success": False,
            "error": str(e),
            "vendors": [],
            "count": 0
        }


# Tool registry for MCP server
BILL_COM_TOOLS = {
    "get_bill_com_invoices": {
        "function": get_bill_com_invoices,
        "description": "Get invoices from Bill.com with optional filtering by date, vendor, and status",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of invoices to return (1-100)",
                    "default": 20
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date filter in YYYY-MM-DD format",
                    "pattern": r"^\d{4}-\d{2}-\d{2}$"
                },
                "end_date": {
                    "type": "string", 
                    "description": "End date filter in YYYY-MM-DD format",
                    "pattern": r"^\d{4}-\d{2}-\d{2}$"
                },
                "vendor_name": {
                    "type": "string",
                    "description": "Filter by vendor name (partial match supported)"
                },
                "status": {
                    "type": "string",
                    "description": "Filter by invoice status",
                    "enum": ["draft", "sent", "viewed", "approved", "paid"]
                }
            }
        }
    },
    
    "get_bill_com_invoice_details": {
        "function": get_bill_com_invoice_details,
        "description": "Get detailed information for a specific Bill.com invoice including line items and payment history",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_id": {
                    "type": "string",
                    "description": "Bill.com invoice ID"
                }
            },
            "required": ["invoice_id"]
        }
    },
    
    "search_bill_com_invoices": {
        "function": search_bill_com_invoices,
        "description": "Search Bill.com invoices by invoice number, vendor name, or amount range",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (invoice number, vendor name, or amount range like '100-500' or '>1000')"
                },
                "search_type": {
                    "type": "string",
                    "description": "Type of search to perform",
                    "enum": ["invoice_number", "vendor_name", "amount_range"],
                    "default": "invoice_number"
                }
            },
            "required": ["query"]
        }
    },
    
    "get_bill_com_vendors": {
        "function": get_bill_com_vendors,
        "description": "Get list of vendors from Bill.com",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}
```

### 3. MCP Server Integration (`src/mcp_server/mcp_server.py`)

**Purpose**: Register Bill.com tools with the existing MCP server.

```python
# Add to existing imports
from .core.bill_com_tools import BILL_COM_TOOLS

# Add to tool registration section
async def register_tools():
    """Register all available tools."""
    tools = {}
    
    # Existing tools (Salesforce, Zoho, etc.)
    # ... existing tool registrations ...
    
    # Add Bill.com tools
    tools.update(BILL_COM_TOOLS)
    
    logger.info(f"Registered {len(tools)} tools including Bill.com integration")
    return tools
```

### 4. Environment Configuration

**Purpose**: Configuration for Bill.com API credentials and settings.

Add to `backend/.env`:
```bash
# Bill.com API Configuration
BILL_COM_BASE_URL=https://gateway.stage.bill.com
BILL_COM_USERNAME=your_username
BILL_COM_PASSWORD=your_password
BILL_COM_ORG_ID=your_organization_id
BILL_COM_DEV_KEY=your_developer_key
BILL_COM_ENVIRONMENT=stage
```

Add to `src/mcp_server/.env.example`:
```bash
# Bill.com API Configuration
BILL_COM_BASE_URL=https://gateway.stage.bill.com
BILL_COM_USERNAME=
BILL_COM_PASSWORD=
BILL_COM_ORG_ID=
BILL_COM_DEV_KEY=
BILL_COM_ENVIRONMENT=stage
```

## Data Models

### Invoice Data Structure

```python
@dataclass
class BillComInvoice:
    """Standardized Bill.com invoice data structure."""
    id: str
    invoice_number: str
    vendor_name: str
    vendor_id: str
    invoice_date: str
    due_date: Optional[str]
    total_amount: float
    status: str
    currency: str
    description: str
    line_items: List[Dict]
    approval_status: Optional[str]
    payment_history: List[Dict]
    remaining_balance: float
    created_time: str
    updated_time: str
```

### API Response Format

All Bill.com tools return responses in this standardized format:

```json
{
  "success": true,
  "data": { ... },
  "count": 10,
  "timestamp": "2024-01-15T10:30:00Z",
  "error": null
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Session Management Consistency
*For any* Bill.com API operation, after successful authentication, the sessionId should be stored and reused for subsequent API calls until expiration
**Validates: Requirements 1.2**

### Property 2: Automatic Re-authentication
*For any* expired or invalid session, the system should automatically re-authenticate using stored credentials and retry the original operation
**Validates: Requirements 1.4, 8.2**

### Property 3: Credential Security
*For any* stored credentials, sensitive information (password, devKey) should never be stored or logged in plain text
**Validates: Requirements 1.5, 9.5**

### Property 4: Authenticated API Calls
*For any* agent request for invoice data, the system should make API calls with valid session credentials
**Validates: Requirements 2.1**

### Property 5: Filter Functionality
*For any* invoice fetch request with filters (date range, vendor, status), all returned invoices should match the specified filter criteria
**Validates: Requirements 2.2, 5.1, 5.2, 5.3**

### Property 6: Data Format Consistency
*For any* invoice data retrieved from Bill.com, the system should parse it into the standardized format with consistent field names and types
**Validates: Requirements 2.3**

### Property 7: Retry Behavior
*For any* API call failure, the system should retry with exponential backoff (1s, 2s, 4s) up to 3 times before giving up
**Validates: Requirements 2.4, 8.1**

### Property 8: Rate Limit Compliance
*For any* rate limit response from Bill.com API, the system should wait for the reset period before making additional requests
**Validates: Requirements 2.5, 8.3**

### Property 9: Transparent Authentication
*For any* agent calling Bill.com tools, authentication and session management should be handled transparently without agent involvement
**Validates: Requirements 3.2**

### Property 10: Session Sharing
*For any* multiple agent requests using Bill.com tools, the system should reuse the same authenticated session efficiently
**Validates: Requirements 3.3**

### Property 11: Structured Error Responses
*For any* error scenario, the system should return structured error responses with consistent format and actionable information
**Validates: Requirements 3.5, 8.5**

### Property 12: Configuration Validation
*For any* Bill.com service initialization, if required configuration fields are missing or invalid, the system should fail with clear validation errors
**Validates: Requirements 4.2**

### Property 13: Connection Testing
*For any* configuration change, the system should test the Bill.com connection before accepting the new configuration
**Validates: Requirements 4.3**

### Property 14: Environment Configuration Loading
*For any* service startup, the system should correctly load Bill.com configuration from environment variables
**Validates: Requirements 4.5**

### Property 15: Search Functionality
*For any* search query (invoice number, vendor name, amount range), the system should return only invoices that match the search criteria
**Validates: Requirements 5.1**

### Property 16: Pagination Handling
*For any* large result set, the system should implement pagination to handle results efficiently
**Validates: Requirements 5.4**

### Property 17: Complete Invoice Details
*For any* invoice detail request, the system should fetch complete information including line items when available
**Validates: Requirements 6.1**

### Property 18: Incomplete Data Handling
*For any* invoice with missing or unavailable fields, the system should clearly indicate which fields are incomplete
**Validates: Requirements 6.5**

### Property 19: Audit Data Completeness
*For any* audit data request, the system should include user information and timestamps for each change when available
**Validates: Requirements 7.2**

### Property 20: Audit Report Formatting
*For any* audit report generation, the system should format data consistently for compliance documentation
**Validates: Requirements 7.5**

### Property 21: Error Classification
*For any* network or API error, the system should correctly distinguish between temporary and permanent failures
**Validates: Requirements 8.4**

### Property 22: API Call Logging
*For any* API call made to Bill.com, the system should log request/response details while excluding sensitive data
**Validates: Requirements 9.1**

### Property 23: Authentication Logging
*For any* authentication attempt, the system should log success/failure status with timestamps
**Validates: Requirements 9.2**

### Property 24: Error Context Logging
*For any* error occurrence, the system should log error details with relevant context (plan_id, agent, operation)
**Validates: Requirements 9.3**

### Property 25: Tool Output Consistency
*For any* agent using Bill.com tools, the results should be formatted consistently with existing tool outputs in the system
**Validates: Requirements 10.4**

### Property 26: Data Integration
*For any* workflow execution, Bill.com data should integrate seamlessly with other data sources without format conflicts
**Validates: Requirements 10.5**

## Error Handling

### Error Categories

1. **Authentication Errors**
   - Invalid credentials
   - Session expiration
   - Organization access denied

2. **API Errors**
   - Rate limiting
   - Network timeouts
   - Invalid parameters
   - Resource not found

3. **Configuration Errors**
   - Missing environment variables
   - Invalid configuration values
   - Environment mismatch

4. **Data Processing Errors**
   - Invalid response format
   - Missing required fields
   - Type conversion failures

### Error Response Format

```json
{
  "success": false,
  "error": "Authentication failed: Invalid credentials",
  "error_code": "AUTH_INVALID_CREDENTIALS",
  "retry_after": null,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Retry Strategy

- **Authentication errors**: Retry once with fresh login
- **Rate limit errors**: Wait for reset period, then retry
- **Network errors**: Exponential backoff (1s, 2s, 4s)
- **Invalid parameters**: No retry, return error immediately

## Testing Strategy

### Unit Tests

- Test Bill.com API service authentication flow
- Test individual tool functions with mock responses
- Test error handling for various failure scenarios
- Test configuration validation and loading

### Integration Tests

- Test actual Bill.com API calls with test credentials
- Test MCP tool registration and invocation
- Test agent integration with Bill.com tools
- Test session management and re-authentication

### Property-Based Tests

Each correctness property will be implemented as a property-based test using the testing framework specified in the project. Tests will generate random inputs and verify that the properties hold across all valid scenarios.

## Performance Considerations

### Caching Strategy

- Cache vendor list for 1 hour (vendors change infrequently)
- Cache invoice details for 5 minutes (may be updated)
- No caching for invoice lists (need fresh status information)

### Connection Management

- Reuse HTTP session across multiple API calls
- Implement connection pooling for concurrent requests
- Set appropriate timeouts (30s for API calls, 10s for auth)

### Rate Limiting

- Implement client-side rate limiting to stay within Bill.com limits
- Use exponential backoff for rate limit responses
- Queue requests during high-traffic periods

## Security Considerations

### Credential Management

- Store credentials in environment variables only
- Never log passwords or API keys
- Use secure HTTP (TLS) for all API communications
- Implement credential rotation support

### Session Security

- Store session tokens in memory only (not persistent)
- Implement session timeout handling
- Clear session data on service shutdown

### Data Privacy

- Log only non-sensitive data (no PII, financial details)
- Implement data masking for debug logs
- Follow least-privilege access principles

## Monitoring and Logging

### Metrics to Track

- API call success/failure rates
- Authentication success/failure rates
- Response times for different operations
- Rate limit encounters
- Session expiration frequency

### Log Levels

- **INFO**: Successful operations, authentication events
- **WARNING**: Rate limits, session expirations, retries
- **ERROR**: API failures, authentication failures, configuration errors
- **DEBUG**: Detailed request/response data (non-sensitive)

### Log Format

```
[2024-01-15 10:30:00] INFO [BillComService] Authentication successful [org=12345, session=abc123...]
[2024-01-15 10:30:05] DEBUG [BillComService] API call: GET /v3/invoices [params={"limit": 20}]
[2024-01-15 10:30:06] WARNING [BillComService] Rate limit encountered, waiting 60s
[2024-01-15 10:30:07] ERROR [BillComService] API call failed: 500 Internal Server Error
```

## Deployment Considerations

### Environment Setup

1. **Development**: Use Bill.com staging environment
2. **Testing**: Use test organization with sample data
3. **Production**: Use production Bill.com environment with real credentials

### Configuration Management

- Use environment-specific configuration files
- Implement configuration validation on startup
- Support configuration hot-reloading for non-sensitive settings

### Health Checks

- Implement health check endpoint that tests Bill.com connectivity
- Monitor authentication status and session validity
- Alert on consecutive API failures

## Future Enhancements (Phase 2+)

### AI Query Generation

- Natural language to Bill.com API parameter translation
- Query optimization based on user intent
- Dynamic filter generation from conversational context

### Advanced Features

- Bulk operations support
- Real-time webhook integration
- Advanced caching with invalidation
- Multi-organization support
- Audit trail integration

### Performance Optimizations

- GraphQL-style field selection
- Parallel API calls for related data
- Intelligent prefetching
- Response compression