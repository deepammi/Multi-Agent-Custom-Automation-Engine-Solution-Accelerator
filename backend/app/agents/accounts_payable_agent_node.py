"""
AccountsPayable Agent Node for LangGraph using Category-Based Architecture with LLM Integration.

This node replaces the brand-specific ZohoAgent with a category-based
AccountsPayableAgent that can work with multiple AP service providers.
Now includes robust LLM-based intent analysis and validation similar to Gmail agent.

**Feature: mcp-client-standardization, Property 4: Base Client Inheritance**
**Validates: Requirements 2.1, 2.5**
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional

from app.agents.state import AgentState
from app.agents.accounts_payable_agent import get_accounts_payable_agent

logger = logging.getLogger(__name__)


class AccountsPayableAgentNode:
    """
    AccountsPayable agent node for LangGraph workflows with LLM integration.
    
    This class uses LLM-based intent analysis to understand user requests
    and convert them into proper MCP queries with robust validation.
    """
    
    def __init__(self):
        self.ap_agent = get_accounts_payable_agent()
        self.name = "accounts_payable_agent"
        
        logger.info(
            "AccountsPayableAgentNode initialized with LLM integration",
            extra={
                "agent_type": "category_based_with_llm",
                "supported_services": self.ap_agent.get_supported_services()
            }
        )
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process AP-related tasks using LLM-based intent analysis."""
        try:
            task = state.get("task_description", "")
            plan_id = state.get("plan_id", "unknown")
            websocket_manager = state.get("websocket_manager")
            
            # Send initial processing message
            if websocket_manager:
                try:
                    from datetime import datetime
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": "AccountsPayable",
                            "content": "📋 Analyzing accounts payable request...",
                            "status": "in_progress",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to send WebSocket message: {e}")
            
            # Use LLM to determine AP action and execute it intelligently
            ap_result = await self._determine_and_execute_ap_action(task, state)
            
            # Send completion message
            if websocket_manager:
                try:
                    from datetime import datetime
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": "AccountsPayable",
                            "content": "✅ Accounts payable analysis complete",
                            "status": "completed",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to send WebSocket message: {e}")
            
            return {
                **state,
                "ap_result": ap_result,
                "last_agent": self.name,
                "messages": state.get("messages", []) + [{
                    "role": "assistant",
                    "content": f"AccountsPayable Agent: {ap_result}",
                    "agent": self.name
                }]
            }
            
        except Exception as e:
            logger.error(f"AccountsPayable agent error: {e}")
            error_message = f"AccountsPayable agent encountered an error: {str(e)}"
            return {
                **state,
                "ap_result": error_message,
                "last_agent": self.name,
                "messages": state.get("messages", []) + [{
                    "role": "assistant",
                    "content": error_message,
                    "agent": self.name
                }]
            }
    
    async def _determine_and_execute_ap_action(self, task: str, state: Dict[str, Any]) -> str:
        """Use LLM to determine AP action and execute it intelligently."""
        
        # Import LLM service
        from app.services.llm_service import LLMService
        
        # Check if mock mode is enabled
        if LLMService.is_mock_mode():
            logger.info("🎭 Using mock mode for AccountsPayable Agent")
            return LLMService.get_mock_response("AccountsPayable", task)
        
        try:
            # Step 1: Use LLM to parse the user query and determine the action
            action_analysis = await self._analyze_user_intent(task, state)
            
            # Log the LLM-generated action analysis
            logger.info(
                "📋 LLM Action Analysis Generated",
                extra={
                    "user_request": task,
                    "action_analysis": action_analysis,
                    "action_type": action_analysis.get("action", "unknown"),
                    "service": action_analysis.get("service", "bill_com"),
                    "agent": "AccountsPayable"
                }
            )
            print(f"🔍 AP LLM ACTION ANALYSIS: {json.dumps(action_analysis, indent=2)}")
            
            # Step 2: Execute the determined action using MCP tools
            if action_analysis["action"] == "search_bills":
                ap_data = await self._search_bills_with_llm_params(action_analysis)
            elif action_analysis["action"] == "get_bill":
                ap_data = await self._get_specific_bill(action_analysis)
            elif action_analysis["action"] == "list_bills":
                ap_data = await self._list_bills_with_llm_params(action_analysis)
            elif action_analysis["action"] == "list_vendors":
                ap_data = await self._list_vendors_with_llm_params(action_analysis)
            elif action_analysis["action"] == "get_vendor":
                ap_data = await self._get_specific_vendor(action_analysis)
            else:
                return "I couldn't determine what accounts payable action you want me to perform. Please be more specific."
            
            # Log the AP data returned from the action
            logger.info(
                "📊 AP Data Retrieved",
                extra={
                    "action_type": action_analysis["action"],
                    "service": action_analysis.get("service", "bill_com"),
                    "data_count": len(ap_data.get("invoices", ap_data.get("vendors", []))) if isinstance(ap_data, dict) else 0,
                    "has_error": "error" in ap_data if isinstance(ap_data, dict) else False,
                    "agent": "AccountsPayable"
                }
            )
            print(f"📊 AP DATA RETRIEVED: {json.dumps(ap_data, indent=2, default=str)}")
            
            # Step 3: Use LLM to analyze the results and format response
            return await self._analyze_ap_results_with_llm(task, ap_data, action_analysis, state)
            
        except Exception as e:
            logger.error(f"AccountsPayable agent LLM processing failed: {e}")
            return f"I encountered an error while processing your accounts payable request: {str(e)}"
    
    async def _analyze_user_intent(self, user_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze user intent and determine AP action."""
        
        intent_prompt = f"""
        Analyze this Accounts Payable request and determine the action to take:
        
        Request: "{user_request}"
        
        CRITICAL INSTRUCTIONS:
        1. Action type: "search_bills", "get_bill", "list_bills", "list_vendors", or "get_vendor"
        2. Service: "bill_com" (default), "quickbooks", or "xero"
        3. For search_bills: Create search terms for vendor names, invoice numbers, keywords, or dates
        4. For get_bill: Extract specific bill/invoice ID or number
        5. For list_bills: Determine status filter (paid, unpaid, overdue, draft) and limit
        6. For list_vendors: Determine limit and any name filters
        7. For get_vendor: Extract specific vendor name or ID
        
        Key AP use cases:
        - Search bills with specific keywords or dates: "search_bills"
        - Search bills for a specific vendor name: "search_bills" with vendor_name
        - Get latest bills from specific vendor: "list_bills" with vendor_name filter
        - Get specific bill by ID/number: "get_bill"
        - List all vendors: "list_vendors"
        
        RESPOND WITH RAW JSON ONLY (no markdown formatting):
        {{
            "action": "search_bills|get_bill|list_bills|list_vendors|get_vendor",
            "service": "bill_com|quickbooks|xero",
            "search_term": "search keywords for bills",
            "vendor_name": "specific vendor name",
            "bill_id": "specific bill/invoice ID",
            "status": "paid|unpaid|overdue|draft",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "limit": 10
        }}
        
        Examples:
        - "Find bills from Acme Corp" → search_bills with vendor_name: "Acme Corp"
        - "Show unpaid invoices" → list_bills with status: "unpaid"
        - "Get invoice INV-1001" → get_bill with bill_id: "INV-1001"
        - "List all vendors" → list_vendors
        - "Bills from last month" → list_bills with date filters
        """
        
        try:
            # Import LLM service here to avoid circular imports
            from app.services.llm_service import LLMService
            
            websocket_manager = state.get("websocket_manager")
            plan_id = state.get("plan_id", "unknown")
            
            if websocket_manager:
                response = await LLMService.call_llm_streaming(
                    prompt=intent_prompt,
                    plan_id=plan_id,
                    websocket_manager=websocket_manager,
                    agent_name="AccountsPayable"
                )
            else:
                # Fallback to mock mode
                response = LLMService.get_mock_response("AccountsPayable", user_request)
            
            # Log the raw LLM response before parsing
            logger.info(
                "🤖 LLM Intent Analysis Response",
                extra={
                    "user_request": user_request,
                    "llm_response": response,
                    "response_length": len(response),
                    "agent": "AccountsPayable"
                }
            )
            print(f"🤖 RAW LLM RESPONSE for AP intent analysis: {response}")
            
            # Try to parse JSON response
            try:
                # Clean the response to handle markdown code blocks
                cleaned_response = response.strip()
                # Remove markdown code blocks if present
                cleaned_response = re.sub(r'```json\s*', '', cleaned_response)
                cleaned_response = re.sub(r'```\s*$', '', cleaned_response)
                cleaned_response = cleaned_response.strip()
                
                parsed_result = json.loads(cleaned_response)
                
                # CRITICAL: Validate and sanitize the LLM response before using it
                validated_result = self._validate_and_sanitize_action_analysis(parsed_result, user_request)
                
                logger.info(
                    "✅ Successfully parsed and validated LLM intent analysis",
                    extra={
                        "parsed_action": validated_result.get("action"),
                        "parsed_service": validated_result.get("service"),
                        "validation_applied": True,
                        "agent": "AccountsPayable"
                    }
                )
                return validated_result
            except json.JSONDecodeError:
                logger.warning(
                    "⚠️ LLM response was not valid JSON, using fallback",
                    extra={
                        "llm_response": response,
                        "cleaned_response": cleaned_response,
                        "agent": "AccountsPayable"
                    }
                )
                # Fallback to simple pattern matching if LLM doesn't return valid JSON
                fallback_result = self._fallback_intent_analysis(user_request)
                # Still validate the fallback result
                return self._validate_and_sanitize_action_analysis(fallback_result, user_request)
                
        except Exception as e:
            logger.error(f"AP intent analysis failed: {e}")
            fallback_result = self._fallback_intent_analysis(user_request)
            # Still validate the fallback result
            return self._validate_and_sanitize_action_analysis(fallback_result, user_request)
    
    def _validate_and_sanitize_action_analysis(self, action_analysis: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """
        Validate and sanitize LLM-generated action analysis to ensure MCP-compatible structured JSON.
        
        This method implements robust validation for the main AP action types:
        1. search_bills - requires search_term or vendor_name
        2. get_bill - requires bill_id
        3. list_bills - requires limit, optional status/vendor filters
        4. list_vendors - requires limit
        5. get_vendor - requires vendor_name or vendor_id
        
        Args:
            action_analysis: Raw LLM response parsed as dict
            user_request: Original user request for fallback parameter generation
            
        Returns:
            Validated and sanitized action analysis with guaranteed required fields
        """
        
        logger.info(
            "🔍 Validating AP LLM action analysis for MCP compatibility",
            extra={
                "raw_action": action_analysis.get("action", "unknown"),
                "has_search_term": bool(action_analysis.get("search_term")),
                "has_vendor_name": bool(action_analysis.get("vendor_name")),
                "has_bill_id": bool(action_analysis.get("bill_id")),
                "agent": "AccountsPayable"
            }
        )
        
        # Ensure action field exists and is valid
        valid_actions = ["search_bills", "get_bill", "list_bills", "list_vendors", "get_vendor"]
        action = action_analysis.get("action", "").lower().strip()
        
        if action not in valid_actions:
            logger.warning(
                f"⚠️ Invalid AP action '{action}', defaulting to 'list_bills'",
                extra={"original_action": action, "user_request": user_request, "agent": "AccountsPayable"}
            )
            action = "list_bills"  # Default to list_bills as safest option
        
        # Ensure service field exists and is valid
        valid_services = ["bill_com", "quickbooks", "xero"]
        service = action_analysis.get("service", "bill_com").lower().strip()
        
        if service not in valid_services:
            logger.warning(
                f"⚠️ Invalid AP service '{service}', defaulting to 'bill_com'",
                extra={"original_service": service, "agent": "AccountsPayable"}
            )
            service = "bill_com"
        
        # Create validated result with guaranteed structure
        validated_result = {
            "action": action,
            "service": service,
            "search_term": "",
            "vendor_name": "",
            "bill_id": "",
            "status": "",
            "start_date": "",
            "end_date": "",
            "limit": 10
        }
        
        # Action-specific validation and fallback parameter generation
        if action == "search_bills":
            # SEARCH_BILLS: Requires search_term or vendor_name
            search_term = action_analysis.get("search_term", "").strip()
            vendor_name = action_analysis.get("vendor_name", "").strip()
            
            if not search_term and not vendor_name:
                # Generate fallback search parameters from user request
                search_term, vendor_name = self._generate_fallback_search_params(user_request)
                logger.warning(
                    f"⚠️ Missing search parameters, generated fallbacks: search_term='{search_term}', vendor_name='{vendor_name}'",
                    extra={"user_request": user_request, "agent": "AccountsPayable"}
                )
            
            validated_result.update({
                "search_term": search_term,
                "vendor_name": vendor_name,
                "status": action_analysis.get("status", "").strip(),
                "start_date": action_analysis.get("start_date", "").strip(),
                "end_date": action_analysis.get("end_date", "").strip(),
                "limit": max(1, min(50, action_analysis.get("limit", 15)))  # Clamp between 1-50
            })
            
        elif action == "get_bill":
            # GET_BILL: Requires bill_id
            bill_id = action_analysis.get("bill_id", "").strip()
            if not bill_id:
                # Try to extract from user request
                bill_id = self._extract_bill_id(user_request)
                if not bill_id:
                    logger.error(
                        "❌ GET_BILL action requires bill_id but none found",
                        extra={"user_request": user_request, "agent": "AccountsPayable"}
                    )
                    # Fallback to list_bills instead
                    action = "list_bills"
                    validated_result["action"] = "list_bills"
                    validated_result["limit"] = 10
                else:
                    validated_result["bill_id"] = bill_id
            else:
                validated_result["bill_id"] = bill_id
                
        elif action == "list_bills":
            # LIST_BILLS: Requires limit, optional filters
            limit = action_analysis.get("limit", 10)
            try:
                limit = int(limit)
                limit = max(1, min(50, limit))  # Clamp between 1-50
            except (ValueError, TypeError):
                limit = 10
                logger.warning(
                    f"⚠️ Invalid limit for list_bills, using default: {limit}",
                    extra={"original_limit": action_analysis.get("limit"), "agent": "AccountsPayable"}
                )
            
            validated_result.update({
                "limit": limit,
                "status": action_analysis.get("status", "").strip(),
                "vendor_name": action_analysis.get("vendor_name", "").strip(),
                "start_date": action_analysis.get("start_date", "").strip(),
                "end_date": action_analysis.get("end_date", "").strip()
            })
            
        elif action == "list_vendors":
            # LIST_VENDORS: Requires limit
            limit = action_analysis.get("limit", 15)
            try:
                limit = int(limit)
                limit = max(1, min(50, limit))  # Clamp between 1-50
            except (ValueError, TypeError):
                limit = 15
                logger.warning(
                    f"⚠️ Invalid limit for list_vendors, using default: {limit}",
                    extra={"original_limit": action_analysis.get("limit"), "agent": "AccountsPayable"}
                )
            
            validated_result.update({
                "limit": limit,
                "vendor_name": action_analysis.get("vendor_name", "").strip()  # Optional filter
            })
            
        elif action == "get_vendor":
            # GET_VENDOR: Requires vendor_name
            vendor_name = action_analysis.get("vendor_name", "").strip()
            if not vendor_name:
                # Try to extract from user request
                vendor_name = self._extract_vendor_name(user_request)
                if not vendor_name:
                    logger.error(
                        "❌ GET_VENDOR action requires vendor_name but none found",
                        extra={"user_request": user_request, "agent": "AccountsPayable"}
                    )
                    # Fallback to list_vendors instead
                    action = "list_vendors"
                    validated_result["action"] = "list_vendors"
                    validated_result["limit"] = 15
                else:
                    validated_result["vendor_name"] = vendor_name
            else:
                validated_result["vendor_name"] = vendor_name
        
        # Final validation check
        validation_passed = self._final_validation_check(validated_result)
        
        logger.info(
            "✅ AP action analysis validation completed",
            extra={
                "final_action": validated_result["action"],
                "final_service": validated_result["service"],
                "validation_passed": validation_passed,
                "has_required_fields": self._check_required_fields(validated_result),
                "agent": "AccountsPayable"
            }
        )
        
        if not validation_passed:
            logger.error(
                "❌ Final AP validation failed, using safe fallback",
                extra={"validated_result": validated_result, "agent": "AccountsPayable"}
            )
            # Ultimate fallback - safe list_bills
            return {
                "action": "list_bills",
                "service": "bill_com",
                "search_term": "",
                "vendor_name": "",
                "bill_id": "",
                "status": "",
                "start_date": "",
                "end_date": "",
                "limit": 10
            }
        
        return validated_result
    
    def _generate_fallback_search_params(self, user_request: str) -> tuple[str, str]:
        """Generate fallback search parameters when LLM fails to provide them."""
        request_lower = user_request.lower()
        
        search_term = ""
        vendor_name = ""
        
        # Look for vendor names (common patterns)
        vendor_patterns = [
            r'from\s+([a-zA-Z0-9\s&.-]+?)(?:\s|$)',
            r'vendor\s+([a-zA-Z0-9\s&.-]+?)(?:\s|$)',
            r'company\s+([a-zA-Z0-9\s&.-]+?)(?:\s|$)',
            r'([A-Z][a-zA-Z0-9\s&.-]*(?:Corp|Inc|LLC|Ltd|Company))',
        ]
        
        for pattern in vendor_patterns:
            match = re.search(pattern, user_request, re.IGNORECASE)
            if match:
                vendor_name = match.group(1).strip()
                break
        
        # Look for search terms
        search_keywords = ["invoice", "bill", "payment", "receipt", "purchase"]
        for keyword in search_keywords:
            if keyword in request_lower:
                search_term = keyword
                break
        
        # Look for invoice numbers
        invoice_patterns = [
            r'inv-\d+',
            r'invoice\s*#?\s*\d+',
            r'bill\s*#?\s*\d+',
            r'\b\d{4,}\b'  # 4+ digit numbers
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, request_lower)
            if match:
                search_term = match.group(0)
                break
        
        # If no specific terms found, use general business terms
        if not search_term and not vendor_name:
            search_term = "invoice"
        
        return search_term, vendor_name
    
    def _extract_bill_id(self, user_request: str) -> str:
        """Extract bill/invoice ID from user request."""
        # Look for various ID patterns
        id_patterns = [
            r'inv-\d+',
            r'invoice\s*#?\s*([a-zA-Z0-9-]+)',
            r'bill\s*#?\s*([a-zA-Z0-9-]+)',
            r'id\s*:?\s*([a-zA-Z0-9-]+)',
            r'\b([A-Z]{2,}-\d+)\b'  # Pattern like INV-1001
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, user_request, re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        
        return ""
    
    def _extract_vendor_name(self, user_request: str) -> str:
        """Extract vendor name from user request."""
        # Look for vendor name patterns
        vendor_patterns = [
            r'vendor\s+([a-zA-Z0-9\s&.-]+?)(?:\s|$)',
            r'from\s+([a-zA-Z0-9\s&.-]+?)(?:\s|$)',
            r'company\s+([a-zA-Z0-9\s&.-]+?)(?:\s|$)',
            r'([A-Z][a-zA-Z0-9\s&.-]*(?:Corp|Inc|LLC|Ltd|Company))',
        ]
        
        for pattern in vendor_patterns:
            match = re.search(pattern, user_request, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _final_validation_check(self, validated_result: Dict[str, Any]) -> bool:
        """Perform final validation to ensure MCP compatibility."""
        action = validated_result.get("action")
        
        if action == "search_bills":
            return bool(validated_result.get("search_term", "").strip() or validated_result.get("vendor_name", "").strip())
        elif action == "get_bill":
            return bool(validated_result.get("bill_id", "").strip())
        elif action == "list_bills":
            limit = validated_result.get("limit", 0)
            return isinstance(limit, int) and limit > 0
        elif action == "list_vendors":
            limit = validated_result.get("limit", 0)
            return isinstance(limit, int) and limit > 0
        elif action == "get_vendor":
            return bool(validated_result.get("vendor_name", "").strip())
        
        return False
    
    def _check_required_fields(self, validated_result: Dict[str, Any]) -> bool:
        """Check if all required fields are present for the action type."""
        action = validated_result.get("action")
        
        required_fields = {
            "search_bills": ["search_term", "vendor_name"],  # At least one required
            "get_bill": ["bill_id"],
            "list_bills": ["limit"],
            "list_vendors": ["limit"],
            "get_vendor": ["vendor_name"]
        }
        
        if action not in required_fields:
            return False
        
        if action == "search_bills":
            # Special case: at least one of search_term or vendor_name required
            return bool(validated_result.get("search_term") or validated_result.get("vendor_name"))
        
        for field in required_fields[action]:
            if not validated_result.get(field):
                return False
        
        return True
    
    def _fallback_intent_analysis(self, user_request: str) -> Dict[str, Any]:
        """Fallback intent analysis using simple pattern matching."""
        
        request_lower = user_request.lower()
        
        print("WARNING! LLM did not return valid JSON so falling back to manual pattern matching for AP query intent")
        
        # Check for specific bill ID
        if re.search(r'inv-\d+|invoice\s*#?\s*\d+|bill\s*#?\s*\d+', request_lower):
            return {
                "action": "get_bill",
                "service": "bill_com",
                "bill_id": self._extract_bill_id(user_request)
            }
        
        # Check for vendor-specific requests
        elif any(keyword in request_lower for keyword in ["vendor", "from", "company"]):
            if any(keyword in request_lower for keyword in ["list", "show", "all"]):
                return {
                    "action": "list_vendors",
                    "service": "bill_com",
                    "limit": 15
                }
            else:
                return {
                    "action": "search_bills",
                    "service": "bill_com",
                    "vendor_name": self._extract_vendor_name(user_request)
                }
        
        # Check for status-specific requests
        elif any(keyword in request_lower for keyword in ["unpaid", "overdue", "paid", "draft"]):
            status = ""
            if "unpaid" in request_lower:
                status = "unpaid"
            elif "overdue" in request_lower:
                status = "overdue"
            elif "paid" in request_lower:
                status = "paid"
            elif "draft" in request_lower:
                status = "draft"
            
            return {
                "action": "list_bills",
                "service": "bill_com",
                "status": status,
                "limit": 10
            }
        
        # Check for search requests
        elif any(keyword in request_lower for keyword in ["search", "find", "look for"]):
            return {
                "action": "search_bills",
                "service": "bill_com",
                "search_term": "invoice"
            }
        
        # Default to list_bills
        else:
            return {
                "action": "list_bills",
                "service": "bill_com",
                "limit": 10
            }


    async def _search_bills_with_llm_params(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Search bills using LLM-generated parameters."""
        try:
            service = action_analysis.get("service", "bill_com")
            search_term = action_analysis.get("search_term", "")
            vendor_name = action_analysis.get("vendor_name", "")
            
            logger.info(f"Searching bills with LLM params: search_term='{search_term}', vendor_name='{vendor_name}'")
            
            # Use the search_bills method if we have a search term
            if search_term:
                result = await self.ap_agent.search_bills(
                    search_term=search_term,
                    service=service,
                    limit=action_analysis.get("limit", 15)
                )
            else:
                # Use get_bills with vendor filter
                result = await self.ap_agent.get_bills(
                    service=service,
                    vendor_name=vendor_name,
                    status=action_analysis.get("status", ""),
                    limit=action_analysis.get("limit", 15),
                    start_date=action_analysis.get("start_date", ""),
                    end_date=action_analysis.get("end_date", "")
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search bills with LLM params: {e}")
            return {"invoices": [], "error": str(e)}
    
    async def _get_specific_bill(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific bill using LLM-extracted ID."""
        try:
            service = action_analysis.get("service", "bill_com")
            bill_id = action_analysis.get("bill_id", "")
            
            logger.info(f"Getting specific bill: {bill_id}")
            
            result = await self.ap_agent.get_bill(
                bill_id=bill_id,
                service=service
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get specific bill: {e}")
            return {"invoice": {}, "error": str(e)}
    
    async def _list_bills_with_llm_params(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """List bills using LLM-determined parameters."""
        try:
            service = action_analysis.get("service", "bill_com")
            
            logger.info(f"Listing bills with LLM params")
            
            result = await self.ap_agent.get_bills(
                service=service,
                status=action_analysis.get("status", ""),
                vendor_name=action_analysis.get("vendor_name", ""),
                limit=action_analysis.get("limit", 10),
                start_date=action_analysis.get("start_date", ""),
                end_date=action_analysis.get("end_date", "")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list bills with LLM params: {e}")
            return {"invoices": [], "error": str(e)}
    
    async def _list_vendors_with_llm_params(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """List vendors using LLM-determined parameters."""
        try:
            service = action_analysis.get("service", "bill_com")
            
            logger.info(f"Listing vendors with LLM params")
            
            result = await self.ap_agent.get_vendors(
                service=service,
                limit=action_analysis.get("limit", 15)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list vendors with LLM params: {e}")
            return {"vendors": [], "error": str(e)}
    
    async def _get_specific_vendor(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific vendor (implemented as filtered vendor list)."""
        try:
            service = action_analysis.get("service", "bill_com")
            vendor_name = action_analysis.get("vendor_name", "")
            
            logger.info(f"Getting specific vendor: {vendor_name}")
            
            # Since most AP services don't have get_vendor by name, we'll search
            result = await self.ap_agent.get_vendors(
                service=service,
                limit=50  # Get more to find the specific vendor
            )
            
            # Filter for the specific vendor
            if result.get("success") and vendor_name:
                vendors = result.get("vendors", [])
                filtered_vendors = [
                    vendor for vendor in vendors
                    if vendor_name.lower() in vendor.get("name", "").lower()
                ]
                result["vendors"] = filtered_vendors
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get specific vendor: {e}")
            return {"vendors": [], "error": str(e)}
    
    async def _analyze_ap_results_with_llm(self, original_request: str, ap_data: Dict[str, Any], 
                                         action_analysis: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Use LLM to analyze AP results and format response."""
        try:
            # Import LLM service here to avoid circular imports
            from app.services.llm_service import LLMService
            
            # Check if there was an error
            if "error" in ap_data:
                return f"I encountered an error: {ap_data['error']}"
            
            # Determine data type and count
            invoices = ap_data.get("invoices", [])
            vendors = ap_data.get("vendors", [])
            invoice = ap_data.get("invoice", {})
            
            if invoice:
                # Single bill result
                data_summary = f"Retrieved bill details for {invoice.get('invoice_number', 'unknown')}"
                data_content = f"Bill: {json.dumps(invoice, indent=2, default=str)}"
            elif invoices:
                # Multiple bills result
                data_summary = f"Found {len(invoices)} bill(s)"
                data_content = f"Bills: {json.dumps(invoices[:5], indent=2, default=str)}"  # Limit for LLM context
            elif vendors:
                # Vendors result
                data_summary = f"Found {len(vendors)} vendor(s)"
                data_content = f"Vendors: {json.dumps(vendors[:10], indent=2, default=str)}"  # Limit for LLM context
            else:
                return "No data found matching your criteria."
            
            # Build analysis prompt
            analysis_prompt = f"""
            Original user request: "{original_request}"
            Action taken: {action_analysis.get('action', 'unknown')}
            Service used: {action_analysis.get('service', 'bill_com')}
            
            {data_summary}. Here are the details:
            
            {data_content}
            
            Please provide a comprehensive analysis of this accounts payable data in relation to the user's request. Include:
            1. Summary of what was found
            2. Key financial information (amounts, dates, statuses)
            3. Any patterns or insights relevant to accounts payable
            4. Direct answers to the user's questions
            5. Format monetary amounts clearly with $ symbols
            
            Be specific and reference actual data from the results, not hypothetical information.
            Use clear formatting with bullet points and sections where appropriate.
            """
            
            websocket_manager = state.get("websocket_manager")
            plan_id = state.get("plan_id", "unknown")
            
            if websocket_manager:
                response = await LLMService.call_llm_streaming(
                    prompt=analysis_prompt,
                    plan_id=plan_id,
                    websocket_manager=websocket_manager,
                    agent_name="AccountsPayable"
                )
                return response
            else:
                # Fallback to formatted results
                return self._format_detailed_ap_results(ap_data, action_analysis, original_request)
                
        except Exception as e:
            logger.error(f"Failed to analyze AP results with LLM: {e}")
            return f"Found data but failed to analyze it: {str(e)}"
    
    def _format_detailed_ap_results(self, ap_data: Dict[str, Any], action_analysis: Dict[str, Any], 
                                  original_request: str) -> str:
        """Format detailed AP results when LLM analysis fails."""
        
        print("WARNING AP RESULT FORMATTING: LLM formatting did not work so manually attempting.")
        
        try:
            action = action_analysis.get("action", "unknown")
            service = action_analysis.get("service", "bill_com")
            
            # Handle different data types
            if "invoice" in ap_data and ap_data["invoice"]:
                # Single bill
                bill = ap_data["invoice"]
                return f"""📄 **Bill Details**

**Invoice:** {bill.get('invoice_number', 'N/A')}
**Vendor:** {bill.get('vendor_name', 'N/A')}
**Date:** {bill.get('date', 'N/A')}
**Due Date:** {bill.get('due_date', 'N/A')}
**Status:** {bill.get('status', 'N/A')}
**Amount:** ${bill.get('total', 0):,.2f}
**Balance Due:** ${bill.get('balance', 0):,.2f}

**Original Request:** {original_request}
**Service Used:** {service.title()}"""
            
            elif "invoices" in ap_data:
                # Multiple bills
                bills = ap_data["invoices"]
                if not bills:
                    return f"No bills found matching your criteria.\n\n**Original Request:** {original_request}"
                
                result = [f"📋 **Bills Found: {len(bills)}**\n"]
                
                total_amount = 0
                total_balance = 0
                
                for i, bill in enumerate(bills[:10], 1):  # Limit to 10 for readability
                    status = bill.get('status', 'N/A')
                    status_emoji = {
                        'paid': '✅',
                        'sent': '📤',
                        'draft': '📝',
                        'overdue': '⚠️',
                        'void': '❌'
                    }.get(status.lower(), '📄')
                    
                    result.append(f"{i}. {status_emoji} **{bill.get('invoice_number', 'N/A')}**")
                    result.append(f"   - Vendor: {bill.get('vendor_name', 'N/A')}")
                    result.append(f"   - Date: {bill.get('date', 'N/A')}")
                    result.append(f"   - Amount: ${bill.get('total', 0):,.2f}")
                    
                    balance = bill.get('balance', 0)
                    if balance > 0:
                        result.append(f"   - Balance Due: ${balance:,.2f}")
                    
                    result.append("")
                    
                    total_amount += bill.get('total', 0)
                    total_balance += balance
                
                result.append(f"**Summary:**")
                result.append(f"- Total Amount: ${total_amount:,.2f}")
                if total_balance > 0:
                    result.append(f"- Total Outstanding: ${total_balance:,.2f}")
                
                result.append(f"\n**Original Request:** {original_request}")
                result.append(f"**Service Used:** {service.title()}")
                
                return "\n".join(result)
            
            elif "vendors" in ap_data:
                # Vendors
                vendors = ap_data["vendors"]
                if not vendors:
                    return f"No vendors found matching your criteria.\n\n**Original Request:** {original_request}"
                
                result = [f"👥 **Vendors Found: {len(vendors)}**\n"]
                
                for i, vendor in enumerate(vendors[:15], 1):  # Limit to 15 for readability
                    name = vendor.get('name') or vendor.get('company_name', 'N/A')
                    email = vendor.get('email', 'N/A')
                    
                    result.append(f"{i}. **{name}**")
                    if email != 'N/A':
                        result.append(f"   - Email: {email}")
                    
                    # Handle outstanding balance if available
                    balance = vendor.get('balance', 0)
                    if balance > 0:
                        result.append(f"   - Outstanding: ${balance:,.2f}")
                    
                    result.append("")
                
                result.append(f"**Original Request:** {original_request}")
                result.append(f"**Service Used:** {service.title()}")
                
                return "\n".join(result)
            
            else:
                return f"Retrieved data but couldn't format it properly.\n\n**Original Request:** {original_request}"
                
        except Exception as e:
            logger.error(f"Failed to format detailed AP results: {e}")
            return f"Retrieved data but failed to format it: {str(e)}"


# Create the async function for the node
async def accounts_payable_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    AccountsPayable agent node - handles AP operations with LLM integration.
    
    This agent uses LLM-based intent analysis to understand user requests
    and convert them into proper MCP queries with robust validation.
    """
    
    # Create the AP agent node instance
    ap_node = AccountsPayableAgentNode()
    
    # Process the request
    result = await ap_node.process(state)
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
    plan_id = state.get("plan_id", "")
    ap_result = result.get("ap_result", "")
    
    # Save AP agent result to database
    if plan_id and ap_result:
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="AccountsPayable",
            content=ap_result,
            agent_type="agent",
            metadata={"status": "completed", "agent_type": "accounts_payable"}
        )
    
    # Update state with simplified structure
    from app.agents.state import AgentStateManager
    
    # Add agent result to state
    agent_result = {
        "status": "completed",
        "data": {"ap_response": ap_result},
        "message": ap_result
    }
    
    AgentStateManager.add_agent_result(state, "AccountsPayable", agent_result)
    
    # Send progress update if websocket available
    websocket_manager = state.get("websocket_manager")
    if websocket_manager:
        try:
            from datetime import datetime
            progress = AgentStateManager.get_progress_info(state)
            await websocket_manager.send_message(state["plan_id"], {
                "type": "step_progress",
                "data": {
                    "step": progress["current_step"],
                    "total": progress["total_steps"],
                    "agent": "AccountsPayable",
                    "progress_percentage": progress["progress_percentage"],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")
    
    return {
        "messages": [result.get("ap_result", "")],
        "current_agent": "AccountsPayable",
        "ap_result": result.get("ap_result", ""),
        "collected_data": state.get("collected_data", {}),
        "execution_results": state.get("execution_results", [])
    }