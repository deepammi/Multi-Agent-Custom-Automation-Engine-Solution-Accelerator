"""
Fixed Bill.com API service with correct authentication and request patterns.

Key Fixes:
1. sessionId and devKey in request BODY, not headers
2. Correct POST request structure for Bill.com API
3. Proper data filtering and response parsing
4. Better error messages showing actual API responses
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import httpx
from dataclasses import dataclass
import time
import uuid

logger = logging.getLogger(__name__)

@dataclass
class BillComConfig:
    """Bill.com API configuration."""
    base_url: str
    username: str
    password: str
    organization_id: str
    dev_key: str
    environment: str = "stage"
    ssl_verify: bool = True
    
    @classmethod
    def from_env(cls) -> 'BillComConfig':
        """Load configuration from environment variables."""
        return cls(
            base_url=os.getenv("BILL_COM_BASE_URL", "https://gateway.stage.bill.com"),
            username=os.getenv("BILL_COM_USERNAME"),
            password=os.getenv("BILL_COM_PASSWORD"),
            organization_id=os.getenv("BILL_COM_ORG_ID"),
            dev_key=os.getenv("BILL_COM_DEV_KEY"),
            environment=os.getenv("BILL_COM_ENVIRONMENT", "stage"),
            ssl_verify=os.getenv("BILL_COM_SSL_VERIFY", "true").lower() != "false"
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
        return datetime.now(timezone.utc) >= (self.expires_at - timedelta(minutes=5))


class BillComAPIService:
    """Fixed Bill.com API service with correct request patterns."""
    
    def __init__(self, plan_id: Optional[str] = None, agent: Optional[str] = None):
        self.config = BillComConfig.from_env()
        self.session: Optional[BillComSession] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self.plan_id = plan_id or str(uuid.uuid4())
        self.agent = agent or "unknown"
    
    async def __aenter__(self):
        """Async context manager entry."""
        ssl_verify = self.config.ssl_verify
        if not ssl_verify:
            logger.warning("⚠️  SSL verification disabled for Bill.com API")
        
        self._http_client = httpx.AsyncClient(
            verify=ssl_verify,
            timeout=httpx.Timeout(30.0)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
    
    async def authenticate(self) -> bool:
        """Authenticate with Bill.com API.
        
        Bill.com Authentication:
        - POST to /v3/login
        - Credentials in REQUEST BODY (not headers)
        - Returns sessionId for subsequent requests
        """
        if not self.config.validate():
            logger.error("❌ Bill.com configuration validation failed")
            return False
        
        login_url = f"{self.config.base_url}/connect/v3/login"
        
        # ✅ CORRECT: Credentials in request body with correct field names
        login_data = {
            "username": self.config.username,           # Note: username, not userName
            "password": self.config.password,
            "organizationId": self.config.organization_id,  # Note: organizationId, not orgId
            "devKey": self.config.dev_key
        }
        
        try:
            logger.info(f"🔐 Authenticating with Bill.com ({self.config.environment})...")
            logger.debug(f"   URL: {login_url}")
            logger.debug(f"   Org ID: {self.config.organization_id}")
            logger.debug(f"   Username: {self.config.username}")
            logger.debug(f"   Request body: {json.dumps(login_data, indent=2)}")
            
            response = await self._http_client.post(
                login_url,
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            # Log response for debugging
            logger.debug(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # ✅ FIXED: Bill.com v3 login API returns data directly (not wrapped in response_data)
                if "sessionId" in data and "organizationId" in data and "userId" in data:
                    self.session = BillComSession(
                        session_id=data["sessionId"],
                        organization_id=data["organizationId"],  # Note: organizationId, not orgId
                        user_id=data["userId"],
                        expires_at=datetime.now(timezone.utc) + timedelta(hours=2)
                    )
                    
                    logger.info(f"✅ Bill.com authentication successful")
                    logger.info(f"   Session ID: {self.session.session_id[:8]}...")
                    logger.info(f"   User ID: {self.session.user_id}")
                    logger.info(f"   Org ID: {self.session.organization_id}")
                    return True
                else:
                    logger.error(f"❌ Unexpected response format: {json.dumps(data, indent=2)}")
                    return False
            else:
                error_text = response.text
                logger.error(f"❌ Authentication failed (Status {response.status_code})")
                logger.error(f"   Response: {error_text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def ensure_authenticated(self) -> bool:
        """Ensure we have a valid authenticated session."""
        if not self.session or self.session.is_expired():
            return await self.authenticate()
        return True
    
    async def make_api_call(
        self,
        endpoint: str,
        method: str = "POST",  # Bill.com v2 API uses POST for most operations
        data: Optional[Dict] = None,
        filters: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """Make authenticated API call to Bill.com with CORRECT request structure.
        
        Bill.com v2 API Pattern (for data operations):
        - Use https://api-stage.bill.com/api/v2/ for data operations
        - POST with form-encoded data
        - sessionId, devKey, and data as form parameters
        """
        if not await self.ensure_authenticated():
            logger.error("❌ Cannot make API call - authentication failed")
            return None
        
        # ✅ FIXED: Use different base URL for data API calls
        if endpoint.startswith("/v2/"):
            # Data API calls use api-stage.bill.com
            url = f"https://api-stage.bill.com/api{endpoint}"
        else:
            # Other calls use gateway (like authentication)
            url = f"{self.config.base_url}{endpoint}"
        
        # ✅ FIXED: Build form data for v2 API calls
        if endpoint.startswith("/v2/"):
            # v2 API uses form-encoded data
            form_data = {
                "sessionId": self.session.session_id,
                "devKey": self.config.dev_key
            }
            
            # Add filters/data if provided
            if filters:
                form_data["data"] = json.dumps(filters)
            elif data:
                form_data["data"] = json.dumps(data)
            else:
                form_data["data"] = "{}"
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            logger.debug(f"🔧 API Call (v2): {method} {endpoint}")
            logger.debug(f"   Form data keys: {list(form_data.keys())}")
            
        else:
            # v3 API uses JSON
            request_body = {
                "sessionId": self.session.session_id,
                "devKey": self.config.dev_key
            }
            
            # Add filters/data if provided
            if filters:
                request_body["filters"] = filters
            if data:
                request_body["data"] = data
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            logger.debug(f"🔧 API Call (v3): {method} {endpoint}")
            logger.debug(f"   Request body keys: {list(request_body.keys())}")
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = 2 ** (attempt - 1)
                    logger.info(f"   Retry {attempt}/{max_retries} after {delay}s...")
                    await asyncio.sleep(delay)
                
                if endpoint.startswith("/v2/"):
                    # Form-encoded request for v2 API
                    response = await self._http_client.request(
                        method=method,
                        url=url,
                        data=form_data,
                        headers=headers,
                        timeout=30.0
                    )
                else:
                    # JSON request for v3 API
                    response = await self._http_client.request(
                        method=method,
                        url=url,
                        json=request_body,
                        headers=headers,
                        timeout=30.0
                    )
                
                logger.debug(f"   Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    # Log response structure for debugging
                    logger.debug(f"   Response keys: {list(response_data.keys())}")
                    return response_data
                elif response.status_code == 401:
                    logger.warning(f"   Session expired, re-authenticating...")
                    if await self.authenticate():
                        if endpoint.startswith("/v2/"):
                            form_data["sessionId"] = self.session.session_id
                        else:
                            request_body["sessionId"] = self.session.session_id
                        continue
                    else:
                        return None
                else:
                    error_text = response.text
                    logger.error(f"❌ API call failed (Status {response.status_code})")
                    logger.error(f"   URL: {url}")
                    logger.error(f"   Response: {error_text[:500]}")
                    if attempt < max_retries:
                        continue
                    return {"error": True, "status_code": response.status_code, "message": error_text}
                    
            except Exception as e:
                logger.error(f"❌ API call exception: {e}")
                if attempt < max_retries:
                    continue
                return {"error": True, "message": str(e)}
        
        return None
    
    # ✅ FIXED: Bill.com API methods with correct v2 patterns
    
    async def get_bills(
        self,
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        vendor_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """Get bills using Bill.com v2 API with correct POST structure."""
        # ✅ CORRECT: Use POST /v2/List/Bill.json with filters in form data
        filters = {
            "start": 0,  # Required: pagination start index
            "max": limit  # Required: maximum number of records
        }
        
        if start_date:
            filters["startDate"] = start_date
        if end_date:
            filters["endDate"] = end_date
        if vendor_id:
            filters["vendorId"] = vendor_id
        if status:
            filters["status"] = status
        
        response = await self.make_api_call(
            endpoint="/v2/List/Bill.json",
            method="POST",
            filters=filters
        )
        
        if response and response.get("error"):
            logger.error(f"Failed to get bills: {response.get('message', 'Unknown error')}")
            return []
        
        # Check for API error in response
        if response and "error_code" in response:
            logger.error(f"Bill.com API error: {response.get('error_code')} - {response.get('error_message')}")
            return []
        
        # Bill.com v2 API returns data in 'response_data' field
        if response and "response_data" in response:
            data = response["response_data"]
            # response_data should be a list of bills
            if isinstance(data, list):
                return data
            else:
                logger.warning(f"Expected list but got {type(data)}: {data}")
                return []
        
        return []
    
    async def get_bill_by_id(self, bill_id: str) -> Optional[Dict]:
        """Get detailed bill information by ID using Bill.com v2 API."""
        # ✅ CORRECT: Use POST /v2/Crud/Read/Bill.json with bill ID in data
        response = await self.make_api_call(
            endpoint="/v2/Crud/Read/Bill.json",
            method="POST",
            data={"id": bill_id}
        )
        
        if response and response.get("error"):
            logger.error(f"Failed to get bill {bill_id}: {response.get('message', 'Unknown error')}")
            return None
        
        # Bill.com v2 API returns data in 'response_data' field
        if response and "response_data" in response:
            return response["response_data"]
        
        return None
    
    async def get_complete_bill_details(self, bill_id: str) -> Optional[Dict]:
        """
        Get complete bill details including basic info and payments.
        
        Args:
            bill_id: Bill.com bill ID
            
        Returns:
            Complete bill details or None if not found
        """
        try:
            # Get basic bill details
            bill_data = await self.get_bill_by_id(bill_id)
            
            if not bill_data:
                logger.error(f"Bill {bill_id} not found")
                return None
            
            # Get payment history
            payments = await self.get_bill_payments(bill_id)
            
            # Calculate financial details
            total_amount = float(bill_data.get("amount", 0))
            total_payments = sum(float(payment.get("amount", 0)) for payment in payments)
            remaining_balance = total_amount - total_payments
            
            # Build complete details
            complete_details = {
                # Basic bill information
                "id": bill_data.get("id"),
                "bill_number": bill_data.get("billNumber"),
                "vendor_name": bill_data.get("vendorName"),
                "vendor_id": bill_data.get("vendorId"),
                "bill_date": bill_data.get("billDate"),
                "due_date": bill_data.get("dueDate"),
                "total_amount": total_amount,
                "currency": bill_data.get("currency", "USD"),
                "status": bill_data.get("status"),
                "description": bill_data.get("description", ""),
                
                # Financial details
                "remaining_balance": remaining_balance,
                "total_payments": total_payments,
                "is_fully_paid": remaining_balance <= 0.01,
                
                # Payment history
                "payment_history": payments,
                "payment_count": len(payments),
                
                # Timestamps
                "created_time": bill_data.get("createdTime"),
                "updated_time": bill_data.get("updatedTime"),
                
                # Metadata
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "data_completeness_score": 1.0 if bill_data else 0.0
            }
            
            logger.info(f"Successfully retrieved complete bill details for {bill_id}")
            return complete_details
            
        except Exception as e:
            logger.error(f"Error retrieving complete bill details for {bill_id}: {e}")
            return None

    
    async def search_bills_by_number(self, bill_number: str) -> List[Dict]:
        """Search bills by bill number using Bill.com v2 API."""
        # ✅ CORRECT: Use POST /v2/List/Bill.json with billNumber filter
        filters = {
            "start": 0,  # Required: pagination start index
            "max": 100,  # Maximum number of records to search
            "billNumber": bill_number
        }
        
        response = await self.make_api_call(
            endpoint="/v2/List/Bill.json",
            method="POST",
            filters=filters
        )
        
        if response and response.get("error"):
            logger.error(f"Failed to search bills by number {bill_number}: {response.get('message', 'Unknown error')}")
            return []
        
        # Check for API error in response
        if response and "error_code" in response:
            logger.error(f"Bill.com API error: {response.get('error_code')} - {response.get('error_message')}")
            return []
        
        if response and "response_data" in response:
            data = response["response_data"]
            # response_data should be a list of bills
            if isinstance(data, list):
                return data
            else:
                logger.warning(f"Expected list but got {type(data)}: {data}")
                return []
        
        return []
    
    async def get_vendors(self, limit: int = 100) -> List[Dict]:
        """Get list of vendors using Bill.com v2 API."""
        # ✅ CORRECT: Use POST /v2/List/Vendor.json with max limit
        filters = {
            "start": 0,  # Required: pagination start index
            "max": limit  # Required: maximum number of records
        }
        
        response = await self.make_api_call(
            endpoint="/v2/List/Vendor.json",
            method="POST",
            filters=filters
        )
        
        if response and response.get("error"):
            logger.error(f"Failed to get vendors: {response.get('message', 'Unknown error')}")
            return []
        
        # Check for API error in response
        if response and "error_code" in response:
            logger.error(f"Bill.com API error: {response.get('error_code')} - {response.get('error_message')}")
            return []
        
        if response and "response_data" in response:
            data = response["response_data"]
            # response_data should be a list of vendors
            if isinstance(data, list):
                return data
            else:
                logger.warning(f"Expected list but got {type(data)}: {data}")
                return []
        
        return []
    
    async def get_bill_payments(self, bill_id: str) -> List[Dict]:
        """Get payment history for a bill using Bill.com v2 API."""
        # ✅ CORRECT: Use POST /v2/List/BillPayment.json with billId filter
        filters = {
            "start": 0,  # Required: pagination start index
            "max": 100,  # Maximum number of records
            "billId": bill_id
        }
        
        response = await self.make_api_call(
            endpoint="/v2/List/BillPayment.json",
            method="POST",
            filters=filters
        )
        
        if response and response.get("error"):
            logger.error(f"Failed to get payments for bill {bill_id}: {response.get('message', 'Unknown error')}")
            return []
        
        # Check for API error in response
        if response and "error_code" in response:
            logger.error(f"Bill.com API error: {response.get('error_code')} - {response.get('error_message')}")
            return []
        
        if response and "response_data" in response:
            data = response["response_data"]
            # response_data should be a list of payments
            if isinstance(data, list):
                return data
            else:
                logger.warning(f"Expected list but got {type(data)}: {data}")
                return []
        
        return []


# Global service instance
_bill_com_service: Optional[BillComAPIService] = None


async def get_bill_com_service(plan_id: Optional[str] = None, agent: Optional[str] = None) -> BillComAPIService:
    """
    Get or create Bill.com service instance with optional context.
    
    Args:
        plan_id: Optional plan ID for logging context
        agent: Optional agent name for logging context
        
    Returns:
        BillComAPIService instance
    """
    global _bill_com_service
    
    if _bill_com_service is None:
        _bill_com_service = BillComAPIService(plan_id=plan_id, agent=agent)
        await _bill_com_service.__aenter__()
    else:
        # Update context if provided
        if plan_id:
            _bill_com_service.plan_id = plan_id
        if agent:
            _bill_com_service.agent = agent
    
    return _bill_com_service 
   
