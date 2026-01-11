"""
Email Agent Node for LangGraph workflows - Multi-Provider Support.
Provides email functionality using the category-based Email Agent with proper MCP protocol.

This file supports multiple email providers (Gmail, Outlook, etc.) while maintaining
backward compatibility with existing Gmail-specific code.
"""

from typing import Dict, Any, List, Optional
import logging
import json
import re
from .email_agent import get_email_agent

logger = logging.getLogger(__name__)

class EmailAgentNode:
    """
    Email agent node for LangGraph workflows - Multi-Provider Support.
    
    This class uses the category-based Email Agent internally and supports
    multiple email providers (Gmail, Outlook, etc.) while maintaining
    backward compatibility with existing code.
    """
    
    def __init__(self, service: str = 'gmail'):
        """
        Initialize EmailAgentNode with specified email service.
        
        Args:
            service: Email service to use ('gmail', 'outlook', etc.)
                    Defaults to 'gmail' for backward compatibility
        """
        self.email_agent = get_email_agent()
        self.service = service
        self.name = f"{service}_agent"
        
        # Validate service is supported
        supported_services = self.email_agent.get_supported_services()
        if service not in supported_services:
            logger.warning(
                f"Service '{service}' not in supported services {supported_services}, "
                f"defaulting to 'gmail'"
            )
            self.service = 'gmail'
            self.name = "gmail_agent"
        
        logger.info(
            "EmailAgentNode initialized with category-based Email Agent",
            extra={
                "service": self.service,
                "agent_type": "category_based",
                "supported_services": supported_services
            }
        )
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process email-related tasks for the configured service."""
        try:
            task = state.get("task", "")
            user_request = state.get("user_request", "")
            
            # Determine the email action based on the task or user request
            action_result = await self._determine_and_execute_action(task, user_request, state)
            
            # Use service-specific result key for backward compatibility
            result_key = f"{self.service}_result"
            
            return {
                **state,
                result_key: action_result,
                "last_agent": self.name,
                "messages": state.get("messages", []) + [{
                    "role": "assistant",
                    "content": f"{self.service.title()} Agent: {action_result}",
                    "agent": self.name
                }]
            }
            
        except Exception as e:
            logger.error(f"{self.service.title()} agent error: {e}")
            error_message = f"{self.service.title()} agent encountered an error: {str(e)}"
            result_key = f"{self.service}_result"
            
            return {
                **state,
                result_key: error_message,
                "last_agent": self.name,
                "messages": state.get("messages", []) + [{
                    "role": "assistant",
                    "content": error_message,
                    "agent": self.name
                }]
            }
    
    async def _determine_and_execute_action(self, task: str, user_request: str, state: Dict[str, Any]) -> str:
        """Use LLM to determine email action and execute it intelligently."""
        combined_text = f"{task} {user_request}".strip()
        
        # Import LLM service and prompt builder
        from app.services.llm_service import LLMService
        from app.agents.prompts import build_gmail_prompt
        
        # Check if mock mode is enabled
        if LLMService.is_mock_mode():
            logger.info(f"🎭 Using mock mode for {self.service.title()} Agent")
            return LLMService.get_mock_response(self.service.title(), combined_text)
        
        try:
            # Step 1: Use LLM to parse the user query and determine the action
            action_analysis = await self._analyze_user_intent(combined_text, state)
            
            # Log the LLM-generated action analysis
            logger.info(
                f"📧 LLM Action Analysis Generated for {self.service}",
                extra={
                    "user_request": combined_text,
                    "action_analysis": action_analysis,
                    "action_type": action_analysis.get("action", "unknown"),
                    "query": action_analysis.get("query", ""),
                    "service": self.service,
                    "agent": self.service.title()
                }
            )
            print(f"🔍 LLM ACTION ANALYSIS ({self.service}): {json.dumps(action_analysis, indent=2)}")
            
            # Step 2: Execute the determined action using MCP tools
            if action_analysis["action"] == "search":
                email_data = await self._search_emails_with_llm_query(action_analysis["query"])
            elif action_analysis["action"] == "get":
                email_data = await self._get_specific_email(action_analysis["message_id"], state)
            elif action_analysis["action"] == "send":
                email_data = await self._send_email_with_llm_extraction(combined_text, state)
            elif action_analysis["action"] == "list":
                email_data = await self._read_recent_emails_with_llm_params(action_analysis.get("max_results", 10))
            else:
                return f"I couldn't determine what {self.service} action you want me to perform. Please be more specific."
            
            # Log the email data returned from the search/action
            logger.info(
                f"📬 Email Data Retrieved from {self.service}",
                extra={
                    "action_type": action_analysis["action"],
                    "email_count": len(email_data.get("messages", [])) if isinstance(email_data, dict) else 0,
                    "has_error": "error" in email_data if isinstance(email_data, dict) else False,
                    "email_data_keys": list(email_data.keys()) if isinstance(email_data, dict) else [],
                    "service": self.service,
                    "agent": self.service.title()
                }
            )
            print(f"📬 EMAIL DATA RETRIEVED ({self.service}): {json.dumps(email_data, indent=2, default=str)}")
            
            print(f"MANUAL DEBUG {self.service.upper()} AGENT RESULT\n")
            print("action_analysis", action_analysis["action"])
            print("action_analysis query", action_analysis["query"])
            print("email_data", email_data)

            # Step 3: Use LLM to analyze the results and format response
            return await self._analyze_email_results_with_llm(combined_text, email_data, state)
            
        except Exception as e:
            logger.error(f"{self.service.title()} agent LLM processing failed: {e}")
            return f"I encountered an error while processing your {self.service} request: {str(e)}"
    
    async def _analyze_user_intent(self, user_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze user intent and determine email action.
        Uses LLM to assess action required from Email, and returns LLM response as JSON"""

        intent_prompt = f"""
        You are a Gmail AI Planner that helps users manage their email. Your job is to understand user requests and select the appropriate Gmail tools.

        Request: "{user_request}"

        🚨 CRITICAL KEYWORD DETECTION 🚨
        If the user request contains ANY of these patterns, you MUST use "search" action:
        - Company names (TBI Corp, Acme Inc, etc.)
        - Invoice/Bill numbers (TBI-001, INV-123, etc.)
        - Keywords like "check", "find", "show", "get", "analyze"
        - Specific terms like "invoice", "bill", "payment", "contract"
        - ANY search criteria whatsoever

        TOOL SELECTION GUIDELINES:

        1. **search** - Use for finding emails based on ANY criteria (THIS IS YOUR DEFAULT CHOICE!)
        - Examples: "find emails from John", "emails about TBI Corp", "check emails with TBI-001", "show invoices"
        - Supports Gmail search operators: from:, to:, subject:, has:attachment, is:unread, after:, before:, etc.
        - Best when: user wants to find specific emails (99% of requests!)
        - ALWAYS use this when user mentions company names, numbers, or any search terms

        2. **list** - Use ONLY for generic recent emails with NO search criteria
        - Examples: "show my recent emails", "latest messages", "inbox"
        - Returns messages in reverse chronological order
        - Best when: user wants a general overview with absolutely no filtering
        - RARELY used - only for truly generic requests

        3. **get** - Use when you have a specific message ID
        - Examples: "show me message 12345", "get details for that email"
        - Returns complete email content
        - Best when: you already have a message ID

        4. **send** - Use for sending new emails
        - Examples: "send email to john@example.com", "compose message"
        - Requires: recipient(s), subject, and body content

        🔥 DECISION LOGIC 🔥
        1. Does request mention ANY company name, number, or keyword? → "search" (NOT "list"!)
        2. Does request say "check", "find", "show", "get", "analyze"? → "search" (NOT "list"!)
        3. Does request mention specific criteria? → "search" (NOT "list"!)
        4. Only if request is purely "recent emails" with no criteria → "list"

        🎯 KEYWORD EXAMPLES THAT REQUIRE "search" ACTION:
        - "TBI Corp" → search with query "TBI Corp"
        - "TBI-001" → search with query "TBI-001"
        - "check emails" → search with appropriate query
        - "show invoices" → search with query "invoice"
        - "find bills" → search with query "bill"
        - "analyze emails about X" → search with query "X"

        SEARCH QUERY CONSTRUCTION:
        - Include ALL keywords from user request
        - Use OR for multiple terms: "TBI Corp OR TBI-001"
        - Add Gmail operators when relevant: from:, subject:, has:attachment
        - Preserve exact company names and numbers

        RESPOND WITH RAW JSON ONLY (no markdown formatting):
        {{
            "action": "search|get|send|list",
            "query": "comprehensive Gmail search query including ALL terms and operators",
            "message_id": "message_id (for get action)",
            "recipient": "email@example.com (for send action)",
            "subject": "subject (for send action)",
            "body": "body text (for send action)",
            "max_results": 15
        }}

        🚨 FINAL CHECK 🚨
        Before responding, ask yourself:
        - Does the user request contain ANY specific terms, names, or numbers? → Use "search"!
        - Is this a truly generic "recent emails" request with zero criteria? → Use "list"
        - Default to "search" when in doubt - it's safer and more useful!
        """
        
        try:
            # Import LLM service here to avoid circular imports
            from app.services.llm_service import LLMService
            
            # Get WebSocket manager from global service instead of state
            from app.services.websocket_service import get_websocket_manager
            websocket_manager = get_websocket_manager()
            plan_id = state.get("plan_id", "unknown")
            
            # Check if WebSocket is available for this plan
            websocket_available = (
                state.get("websocket_available", False) and 
                websocket_manager.get_connection_count(plan_id) > 0
            )
            
            if websocket_available:
                response = await LLMService.call_llm_streaming(
                    prompt=intent_prompt,
                    plan_id=plan_id,
                    websocket_manager=websocket_manager,
                    agent_name=self.service.title()
                )
            else:
                # Call LLM without streaming
                response = await LLMService.call_llm_non_streaming(
                    prompt=intent_prompt,
                    agent_name=self.service.title()
                )
            
            # Log the raw LLM response before parsing
            logger.info(
                f"🤖 LLM Intent Analysis Response for {self.service}",
                extra={
                    "user_request": user_request,
                    "llm_response": response,
                    "response_length": len(response),
                    "service": self.service,
                    "agent": self.service.title()
                }
            )
            print(f"🤖 RAW LLM RESPONSE for {self.service} intent analysis: {response}")
            
            # Try to parse JSON response
            import json
            import re
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
                    f"✅ Successfully parsed and validated LLM intent analysis for {self.service}",
                    extra={
                        "parsed_action": validated_result.get("action"),
                        "parsed_query": validated_result.get("query"),
                        "validation_applied": True,
                        "service": self.service,
                        "agent": self.service.title()
                    }
                )
                return validated_result
            except json.JSONDecodeError:
                logger.warning(
                    f"⚠️ LLM response was not valid JSON for {self.service}, using fallback",
                    extra={
                        "llm_response": response,
                        "cleaned_response": cleaned_response,
                        "service": self.service,
                        "agent": self.service.title()
                    }
                )
                # Fallback to simple pattern matching if LLM doesn't return valid JSON
                fallback_result = self._fallback_intent_analysis(user_request)
                # Still validate the fallback result
                return self._validate_and_sanitize_action_analysis(fallback_result, user_request)
                
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            fallback_result = self._fallback_intent_analysis(user_request)
            # Still validate the fallback result
            return self._validate_and_sanitize_action_analysis(fallback_result, user_request)
    
    def _validate_and_sanitize_action_analysis(self, action_analysis: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """
        Validate and sanitize LLM-generated action analysis to ensure MCP-compatible structured JSON.
        
        This method implements robust validation for the 3 main Gmail action types:
        1. search - requires valid query
        2. get - requires message_id  
        3. send - requires recipient, subject, body
        4. list - requires max_results
        
        Args:
            action_analysis: Raw LLM response parsed as dict
            user_request: Original user request for fallback parameter generation
            
        Returns:
            Validated and sanitized action analysis with guaranteed required fields
        """
        
        logger.info(
            "🔍 Validating LLM action analysis for MCP compatibility",
            extra={
                "raw_action": action_analysis.get("action", "unknown"),
                "has_query": bool(action_analysis.get("query")),
                "has_message_id": bool(action_analysis.get("message_id")),
                "has_recipient": bool(action_analysis.get("recipient")),
                "agent": "Gmail"
            }
        )
        
        # Ensure action field exists and is valid
        valid_actions = ["search", "get", "send", "list"]
        action = action_analysis.get("action", "").lower().strip()
        
        # Handle LLM variations of action names
        action_mappings = {
            "search_messages": "search",
            "list_messages": "list", 
            "get_message": "get",
            "send_message": "send"
        }
        
        if action in action_mappings:
            action = action_mappings[action]
        
        if action not in valid_actions:
            logger.warning(
                f"⚠️ Invalid action '{action}', defaulting to 'search'",
                extra={"original_action": action, "user_request": user_request, "agent": "Gmail"}
            )
            action = "search"  # Default to search as safest option
        
        # Create validated result with guaranteed structure
        validated_result = {
            "action": action,
            "query": "",
            "message_id": "",
            "recipient": "",
            "subject": "",
            "body": "",
            "max_results": 10
        }
        
        # Action-specific validation and fallback parameter generation
        if action == "search":
            # SEARCH: Requires valid query
            query = action_analysis.get("query", "").strip()
            if not query:
                # Generate fallback query from user request
                query = self._generate_fallback_search_query(user_request)
                logger.warning(
                    f"⚠️ Missing search query, generated fallback: '{query}'",
                    extra={"user_request": user_request, "agent": "Gmail"}
                )
            
            validated_result.update({
                "query": query,
                "max_results": max(1, min(50, action_analysis.get("max_results", 15)))  # Clamp between 1-50
            })
            
        elif action == "get":
            # GET: Requires message_id
            message_id = action_analysis.get("message_id", "").strip()
            if not message_id:
                # Try to extract from user request
                message_id = self._extract_message_id(user_request)
                if not message_id:
                    logger.error(
                        "❌ GET action requires message_id but none found",
                        extra={"user_request": user_request, "agent": "Gmail"}
                    )
                    # Fallback to search instead
                    action = "search"
                    validated_result["action"] = "search"
                    validated_result["query"] = self._generate_fallback_search_query(user_request)
                else:
                    validated_result["message_id"] = message_id
            else:
                validated_result["message_id"] = message_id
                
        elif action == "send":
            # SEND: Requires recipient, subject, body
            recipient = action_analysis.get("recipient", "").strip()
            subject = action_analysis.get("subject", "").strip()
            body = action_analysis.get("body", "").strip()
            
            # Validate recipient (must be valid email)
            if not recipient or "@" not in recipient:
                recipient = self._extract_email_recipient(user_request, {})
                if not recipient or "@" not in recipient:
                    logger.error(
                        "❌ SEND action requires valid recipient email",
                        extra={"user_request": user_request, "extracted_recipient": recipient, "agent": "Gmail"}
                    )
                    # Cannot send without recipient, fallback to search
                    action = "search"
                    validated_result["action"] = "search"
                    validated_result["query"] = self._generate_fallback_search_query(user_request)
                else:
                    validated_result["recipient"] = recipient
            else:
                validated_result["recipient"] = recipient
            
            # Generate fallback subject if missing
            if not subject and action == "send":
                subject = self._extract_email_subject(user_request, {})
                if not subject:
                    subject = "Email from MACAE Gmail Agent"
                logger.warning(
                    f"⚠️ Missing email subject, using fallback: '{subject}'",
                    extra={"user_request": user_request, "agent": "Gmail"}
                )
            
            # Generate fallback body if missing
            if not body and action == "send":
                body = self._extract_email_body(user_request, {})
                if not body:
                    body = f"This email was sent via MACAE Gmail Agent in response to: {user_request}"
                logger.warning(
                    f"⚠️ Missing email body, using fallback: '{body[:50]}...'",
                    extra={"user_request": user_request, "agent": "Gmail"}
                )
            
            if action == "send":  # Only update if still send action
                validated_result.update({
                    "subject": subject,
                    "body": body
                })
                
        elif action == "list":
            # LIST: Requires max_results
            max_results = action_analysis.get("max_results", 10)
            try:
                max_results = int(max_results)
                max_results = max(1, min(50, max_results))  # Clamp between 1-50
            except (ValueError, TypeError):
                max_results = 10
                logger.warning(
                    f"⚠️ Invalid max_results, using default: {max_results}",
                    extra={"original_max_results": action_analysis.get("max_results"), "agent": "Gmail"}
                )
            
            validated_result["max_results"] = max_results
        
        # Final validation check
        validation_passed = self._final_validation_check(validated_result)
        
        logger.info(
            "✅ Action analysis validation completed",
            extra={
                "final_action": validated_result["action"],
                "validation_passed": validation_passed,
                "has_required_fields": self._check_required_fields(validated_result),
                "agent": "Gmail"
            }
        )
        
        if not validation_passed:
            logger.error(
                "❌ Final validation failed, using safe fallback",
                extra={"validated_result": validated_result, "agent": "Gmail"}
            )
            # Ultimate fallback - safe search
            return {
                "action": "search",
                "query": "inbox",
                "message_id": "",
                "recipient": "",
                "subject": "",
                "body": "",
                "max_results": 10
            }
        
        return validated_result
    
    def _generate_fallback_search_query(self, user_request: str) -> str:
        """Generate a fallback search query when LLM fails to provide one."""
        request_lower = user_request.lower()
        
        # Extract key terms for search
        search_terms = []
        
        # Look for specific identifiers
        import re
        
        # Invoice numbers (INV-XXXX, Invoice #XXXX, etc.)
        invoice_patterns = [
            r'inv-\d+',
            r'invoice\s*#?\s*\d+',
            r'bill\s*#?\s*\d+',
            r'\b\d{4,}\b'  # 4+ digit numbers
        ]
        
        for pattern in invoice_patterns:
            matches = re.findall(pattern, request_lower)
            search_terms.extend(matches)
        
        # Common email keywords
        email_keywords = ["invoice", "bill", "payment", "receipt", "order", "purchase"]
        for keyword in email_keywords:
            if keyword in request_lower:
                search_terms.append(keyword)
        
        # Time constraints
        if any(term in request_lower for term in ["last month", "1 month", "30 days"]):
            search_terms.append("newer_than:1m")
        elif any(term in request_lower for term in ["last week", "7 days"]):
            search_terms.append("newer_than:7d")
        elif any(term in request_lower for term in ["2 months", "60 days"]):
            search_terms.append("newer_than:2m")
        
        # Sender constraints
        sender_match = re.search(r'from\s+([a-zA-Z0-9@.\-]+)', request_lower)
        if sender_match:
            sender = sender_match.group(1)
            if "@" in sender:
                search_terms.append(f"from:{sender}")
            else:
                search_terms.append(f"from:{sender}")
        
        # Build final query
        if search_terms:
            # Combine terms intelligently
            query_parts = []
            time_constraints = [term for term in search_terms if "newer_than:" in term or "older_than:" in term]
            from_constraints = [term for term in search_terms if "from:" in term]
            content_terms = [term for term in search_terms if not any(x in term for x in ["newer_than:", "older_than:", "from:"])]
            
            # Add content terms
            if content_terms:
                if len(content_terms) == 1:
                    query_parts.append(content_terms[0])
                else:
                    # Use OR for multiple content terms
                    query_parts.append(f"({' OR '.join(content_terms)})")
            
            # Add constraints
            query_parts.extend(from_constraints)
            query_parts.extend(time_constraints)
            
            return " ".join(query_parts)
        else:
            # Ultimate fallback - search for common business terms
            return "invoice OR bill OR payment"
    
    def _final_validation_check(self, validated_result: Dict[str, Any]) -> bool:
        """Perform final validation to ensure MCP compatibility."""
        action = validated_result.get("action")
        
        if action == "search":
            return bool(validated_result.get("query", "").strip())
        elif action == "get":
            return bool(validated_result.get("message_id", "").strip())
        elif action == "send":
            recipient = validated_result.get("recipient", "").strip()
            return bool(recipient and "@" in recipient)
        elif action == "list":
            max_results = validated_result.get("max_results", 0)
            return isinstance(max_results, int) and max_results > 0
        
        return False
    
    def _check_required_fields(self, validated_result: Dict[str, Any]) -> bool:
        """Check if all required fields are present for the action type."""
        action = validated_result.get("action")
        
        required_fields = {
            "search": ["query"],
            "get": ["message_id"],
            "send": ["recipient", "subject", "body"],
            "list": ["max_results"]
        }
        
        if action not in required_fields:
            return False
        
        for field in required_fields[action]:
            if not validated_result.get(field):
                return False
        
        return True
    
    def _fallback_intent_analysis(self, user_request: str) -> Dict[str, Any]:
        """Fallback intent analysis using simple pattern matching.
        This is used when LLM based intent analysis does not work - so should be rare"""
        
        request_lower = user_request.lower()
        
        print("WARNING! LLM did not return valid JSON so falling back to manual pattern matching for email query intent")

        # Enhanced search keywords - if ANY of these are present, use search
        search_keywords = [
            # Explicit search terms
            "search", "find", "look for", "show me", "get me", "check",
            # Content-based searches
            "invoice", "bill", "payment", "receipt", "order", "purchase", "contract",
            # Sender-based searches  
            "from", "sent by", "emails from",
            # Subject-based searches
            "about", "regarding", "subject", "titled",
            # Status-based searches
            "unread", "starred", "important", "urgent",
            # Time-based searches
            "last week", "last month", "yesterday", "today", "recent",
            # Attachment searches
            "attachment", "attached", "with file",
            # Keywords/content searches
            "containing", "with keywords", "keywords", "mentions",
            # Company/entity names (common patterns)
            "corp", "inc", "llc", "ltd", "company", "organization"
        ]
        
        # Check if this is clearly a search request
        is_search_request = any(keyword in request_lower for keyword in search_keywords)
        
        # Also check for specific patterns that indicate search
        search_patterns = [
            r'\b(emails?|messages?)\s+(about|containing|with|from|regarding)',
            r'\b(check|show|find|get)\s+(all\s+)?(emails?|messages?)',
            r'\bwith\s+keywords?\b',
            r'\bkeywords?\s+\w+',
            r'\b(tbi|corp|inc|llc)\b',  # Company identifiers
            r'\b\w+-\d+\b',  # Pattern like TBI-001, INV-123, etc.
        ]
        
        import re
        has_search_pattern = any(re.search(pattern, request_lower) for pattern in search_patterns)
        
        if is_search_request or has_search_pattern:
            return {
                "action": "search",
                "query": self._build_intelligent_search_query(user_request),
                "max_results": 15
            }
        elif any(keyword in request_lower for keyword in ["send", "compose", "email to"]):
            return {
                "action": "send",
                "recipient": self._extract_email_recipient(user_request, {}),
                "subject": self._extract_email_subject(user_request, {}),
                "body": self._extract_email_body(user_request, {})
            }
        elif any(keyword in request_lower for keyword in ["get email", "show email"]):
            return {
                "action": "get",
                "message_id": self._extract_message_id(user_request)
            }
        else:
            # Only use list for truly generic requests like "recent emails", "latest messages"
            generic_list_patterns = [
                r'^(show|list|get)\s+(my\s+)?(recent|latest|new)\s+(emails?|messages?)$',
                r'^(recent|latest|new)\s+(emails?|messages?)$',
                r'^(my\s+)?(inbox|emails?|messages?)$'
            ]
            
            is_generic_list = any(re.match(pattern, request_lower.strip()) for pattern in generic_list_patterns)
            
            if is_generic_list:
                return {
                    "action": "list",
                    "max_results": 10
                }
            else:
                # Default to search for anything else - it's safer than list
                return {
                    "action": "search", 
                    "query": self._build_intelligent_search_query(user_request),
                    "max_results": 15
                }
    
    async def _search_emails_with_llm_query(self, search_query: str) -> Dict[str, Any]:
        """Search emails using the LLM-generated query."""
        try:
            logger.info(f"Searching emails with LLM query: {search_query}")
            
            # Use category-based Email Agent with proper MCP protocol
            messages_data = await self.email_agent.search_messages(
                query=search_query,
                service=self.service,
                max_results=15
            )
            
            # Log the detailed email data returned from the search
            logger.info(
                "🔍 Email Search Results Retrieved",
                extra={
                    "search_query": search_query,
                    "messages_count": len(messages_data.get("messages", [])),
                    "has_error": "error" in messages_data,
                    "service": self.service,
                    "agent": "Gmail"
                }
            )
            print(f"🔍 EMAIL SEARCH RESULTS for query '{search_query}':")
            print(f"   - Found {len(messages_data.get('messages', []))} messages")
            print(f"   - Data structure keys: {list(messages_data.keys())}")
            if messages_data.get("messages"):
                print(f"   - First message preview: {messages_data['messages'][0].get('snippet', 'No snippet')[:100]}...")
            
            return messages_data
            
        except Exception as e:
            logger.error(f"Failed to search emails with LLM query: {e}")
            return {"messages": [], "error": str(e)}
    
    async def _read_recent_emails_with_llm_params(self, max_results: int) -> Dict[str, Any]:
        """Read recent emails with LLM-determined parameters."""
        try:
            logger.info(f"Reading {max_results} recent emails")
            
            # Use category-based Email Agent with proper MCP protocol
            messages_data = await self.email_agent.list_messages(
                service=self.service,
                max_results=max_results
            )
            
            return messages_data
            
        except Exception as e:
            logger.error(f"Failed to read recent emails: {e}")
            return {"messages": [], "error": str(e)}
    
    async def _send_email_with_llm_extraction(self, user_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using LLM-extracted parameters."""
        try:
            # Extract email details using existing methods
            to = self._extract_email_recipient(user_request, state)
            subject = self._extract_email_subject(user_request, state)
            body = self._extract_email_body(user_request, state)
            
            if not to:
                return {"error": "Cannot send email: recipient address not specified"}
            
            logger.info(f"Sending email to {to} with subject '{subject}'")
            
            # Use category-based Email Agent with proper MCP protocol
            result_data = await self.email_agent.send_message(
                to=to,
                subject=subject,
                body=body,
                service=self.service
            )
            
            return {"success": True, "message": f"Email sent successfully to {to}"}
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {"error": str(e)}
    
    async def _analyze_email_results_with_llm(self, original_request: str, email_data: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Use LLM to analyze email results and format response."""
        try:
            # Import LLM service here to avoid circular imports
            from app.services.llm_service import LLMService
            
            # Check if there was an error
            if "error" in email_data:
                return f"I encountered an error: {email_data['error']}"
            
            # Check if this was a send operation
            if "success" in email_data:
                return email_data.get("message", "Email operation completed successfully")
            
            # For search/list operations, analyze the messages
            messages = email_data.get("messages", [])
            
            if not messages:
                return "No emails found matching your criteria."
            
            # Build analysis prompt
            analysis_prompt = f"""
            Original user request: "{original_request}"
            
            I found {len(messages)} email(s). Here are the details:
            
            {self._format_emails_for_llm_analysis(messages)}
            
            Please provide a comprehensive analysis of these emails in relation to the user's request. Include:
            1. Summary of what was found
            2. Key information from the emails
            3. Any patterns or insights
            4. Direct answers to the user's questions
            
            Be specific and reference actual email content, not hypothetical information.
            """
            
            # Get WebSocket manager from global service instead of state
            from app.services.websocket_service import get_websocket_manager
            websocket_manager = get_websocket_manager()
            plan_id = state.get("plan_id", "unknown")
            
            # Check if WebSocket is available for this plan
            websocket_available = (
                state.get("websocket_available", False) and 
                websocket_manager.get_connection_count(plan_id) > 0
            )
            
            if websocket_available:
                response = await LLMService.call_llm_streaming(
                    prompt=analysis_prompt,
                    plan_id=plan_id,
                    websocket_manager=websocket_manager,
                    agent_name="Gmail"
                )
                return response
            else:
                # Fallback to formatted results
                return self._format_detailed_email_results(email_data, "Email Analysis Results", original_request)
                
        except Exception as e:
            logger.error(f"Failed to analyze email results with LLM: {e}")
            return f"Found {len(email_data.get('messages', []))} emails but failed to analyze them: {str(e)}"
    
    def _format_emails_for_llm_analysis(self, messages: List[Dict[str, Any]]) -> str:
        """Format emails for LLM analysis."""
        formatted_emails = []
        
        for i, msg in enumerate(messages[:10], 1):  # Limit to 10 for LLM context
            # Extract basic info
            subject = "No subject"
            sender = "Unknown sender"
            date = "Unknown date"
            snippet = msg.get("snippet", "No preview available")
            
            # Extract headers if available
            if "payload" in msg and "headers" in msg["payload"]:
                headers = msg["payload"]["headers"]
                for header in headers:
                    header_name = header.get("name", "").lower()
                    header_value = header.get("value", "")
                    
                    if header_name == "subject":
                        subject = header_value
                    elif header_name == "from":
                        sender = header_value
                    elif header_name == "date":
                        date = header_value
            
            formatted_emails.append(f"""
            Email {i}:
            From: {sender}
            Subject: {subject}
            Date: {date}
            Content: {snippet}
            """)
        
        return "\n".join(formatted_emails)
    async def _execute_email_actions_if_needed(self, combined_text: str, state: Dict[str, Any]) -> str:
        """Legacy method - now redirects to LLM-based processing."""
        return await self._determine_and_execute_action("", combined_text, state)
    
    async def _read_recent_emails(self, request_text: str) -> str:
        """Read recent emails using category-based Email Agent."""
        try:
            # Extract number of emails if specified
            max_results = 10  # default
            import re
            number_match = re.search(r'(\d+)', request_text)
            if number_match:
                max_results = min(int(number_match.group(1)), 50)  # cap at 50
            
            return await self._read_recent_emails_with_llm_params(max_results)
            
        except Exception as e:
            logger.error(f"Failed to read recent emails: {e}")
            return f"Failed to read emails: {str(e)}"
    
    async def _send_email(self, request_text: str, state: Dict[str, Any]) -> str:
        """Send an email using category-based Email Agent."""
        return await self._send_email_with_llm_extraction(request_text, state)
    
    async def _search_emails_intelligent(self, request_text: str) -> str:
        """Intelligently search Gmail messages using LLM-generated query."""
        try:
            # Use LLM to generate search query
            action_analysis = await self._analyze_user_intent(request_text, {})
            search_query = action_analysis.get("query", request_text)
            
            # Execute search
            messages_data = await self._search_emails_with_llm_query(search_query)
            
            # Format results
            messages = messages_data.get("messages", [])
            if not messages:
                return f"Nothing found. No emails matching search criteria: {search_query}"
            
            return self._format_detailed_email_results(
                messages_data, 
                f"Email search results for: {search_query}",
                request_text
            )
            
        except Exception as e:
            logger.error(f"Failed to search emails intelligently: {e}")
            return f"Failed to search emails: {str(e)}"
    
    def _build_intelligent_search_query(self, request_text: str) -> str:
        """Build intelligent search query - simplified version for fallback."""
        request_lower = request_text.lower()
        
        # Simple extraction of key terms
        search_terms = []
        
        # Look for invoice terms
        if "invoice" in request_lower:
            search_terms.append("invoice")
        
        # Look for company names
        if "acme" in request_lower:
            search_terms.append("from:acme")
        
        # Look for time constraints
        if "2 months" in request_lower:
            search_terms.append("newer_than:2m")
        elif "1 month" in request_lower or "last month" in request_lower:
            search_terms.append("newer_than:1m")
        elif "last week" in request_lower:
            search_terms.append("newer_than:7d")
        
        # Build query
        if search_terms:
            return ' '.join(search_terms)
        else:
            # Extract important words as fallback
            words = request_text.split()
            important_words = [word for word in words if len(word) > 3 and word.lower() not in 
                             ['what', 'the', 'status', 'from', 'with', 'and', 'all', 'emails']]
            return ' '.join(important_words[:3]) if important_words else "invoice"
    
    async def _get_specific_email(self, request_text: str, state: Dict[str, Any]) -> str:
        """Get a specific email by ID using category-based Email Agent."""
        try:
            # Try to extract message ID from request or state
            message_id = state.get("email_id") or self._extract_message_id(request_text)
            
            if not message_id:
                return "Please specify the email ID to retrieve."
            
            logger.info(
                f"Getting email via Email Agent",
                extra={
                    "service": self.service,
                    "message_id": message_id
                }
            )
            
            # Use category-based Email Agent with proper MCP protocol
            message_data = await self.email_agent.get_message(
                message_id=message_id,
                service=self.service
            )
            
            return self._format_email_details_from_agent_result(message_data)
            
        except Exception as e:
            logger.error(f"Failed to get specific email: {e}")
            return f"Failed to get email: {str(e)}"
    
    def _format_detailed_email_results(self, data: Dict[str, Any], title: str, original_request: str) -> str:
        """Format detailed email results showing full content of each email.
        This is used when LLM based result analysis does not work - so should be rare"""
        
        print("WARNING EMAIL RESULT FORMATTING: LLM formatting did not work so manually attempting.")
        try:
            messages = data.get("messages", [])
            
            if not messages:
                return f"{title}\n\nNo emails found matching the search criteria."
            
            formatted_output = [f"{title}"]
            formatted_output.append(f"Original Request: {original_request}")
            formatted_output.append(f"Found {len(messages)} email(s)")
            formatted_output.append("=" * 80)
            
            for i, msg in enumerate(messages, 1):
                formatted_output.append(f"\n📧 EMAIL {i} OF {len(messages)}")
                formatted_output.append("-" * 50)
                
                # Extract basic info
                message_id = msg.get("id", "Unknown ID")
                thread_id = msg.get("threadId", "Unknown Thread")
                snippet = msg.get("snippet", "No preview available")
                
                formatted_output.append(f"Message ID: {message_id}")
                formatted_output.append(f"Thread ID: {thread_id}")
                
                # Extract headers if available
                subject = "No subject"
                sender = "Unknown sender"
                date = "Unknown date"
                to = "Unknown recipient"
                
                if "payload" in msg and "headers" in msg["payload"]:
                    headers = msg["payload"]["headers"]
                    for header in headers:
                        header_name = header.get("name", "").lower()
                        header_value = header.get("value", "")
                        
                        if header_name == "subject":
                            subject = header_value
                        elif header_name == "from":
                            sender = header_value
                        elif header_name == "date":
                            date = header_value
                        elif header_name == "to":
                            to = header_value
                
                formatted_output.append(f"From: {sender}")
                formatted_output.append(f"To: {to}")
                formatted_output.append(f"Subject: {subject}")
                formatted_output.append(f"Date: {date}")
                formatted_output.append(f"Snippet: {snippet}")
                
                # Try to extract body content
                body_text = self._extract_email_body_content(msg)
                if body_text:
                    formatted_output.append(f"\nFull Email Content:")
                    formatted_output.append("-" * 30)
                    formatted_output.append(body_text)
                else:
                    formatted_output.append(f"\nEmail Body: {snippet}")
                
                formatted_output.append("\n" + "=" * 80)
            
            # Add summary
            formatted_output.append(f"\n📊 SEARCH SUMMARY:")
            formatted_output.append(f"Total emails found: {len(messages)}")
            formatted_output.append(f"Search completed successfully")
            
            return "\n".join(formatted_output)
            
        except Exception as e:
            logger.error(f"Failed to format detailed email results: {e}")
            return f"Retrieved {len(data.get('messages', []))} emails but failed to format them: {str(e)}"
    
    def _extract_email_body_content(self, message: Dict[str, Any]) -> str:
        """Extract the full body content from an email message.
        This is used when LLM based result analysis does not work - so should be rare"""

        try:
            payload = message.get("payload", {})
            
            # Try to get body from parts
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        body_data = part.get("body", {}).get("data", "")
                        if body_data:
                            # Decode base64 if needed
                            import base64
                            try:
                                decoded = base64.urlsafe_b64decode(body_data + "===").decode('utf-8')
                                return decoded
                            except:
                                return body_data
            
            # Try to get body directly
            body_data = payload.get("body", {}).get("data", "")
            if body_data:
                import base64
                try:
                    decoded = base64.urlsafe_b64decode(body_data + "===").decode('utf-8')
                    return decoded
                except:
                    return body_data
            
            # Fallback to snippet
            return message.get("snippet", "No body content available")
            
        except Exception as e:
            logger.error(f"Failed to extract email body: {e}")
            return "Failed to extract email body content"
    
    def _format_email_list_from_agent_result(self, data: Dict[str, Any], title: str = "Recent emails:") -> str:
        """Format email list from Email Agent result for display."""
        try:
            messages = data.get("messages", [])
            
            if not messages:
                return "No emails found."
            
            formatted_emails = [title]
            for i, msg in enumerate(messages[:10], 1):  # Limit to 10 for readability
                subject = "No subject"
                sender = "Unknown sender"
                snippet = "No preview available"
                
                # Extract headers if available
                if "payload" in msg and "headers" in msg["payload"]:
                    headers = msg["payload"]["headers"]
                    for header in headers:
                        if header.get("name") == "Subject":
                            subject = header.get("value", "No subject")
                        elif header.get("name") == "From":
                            sender = header.get("value", "Unknown sender")
                
                if "snippet" in msg:
                    snippet = msg["snippet"]
                
                formatted_emails.append(f"{i}. From: {sender}")
                formatted_emails.append(f"   Subject: {subject}")
                formatted_emails.append(f"   Preview: {snippet[:100]}...")
                formatted_emails.append("")
            
            return "\\n".join(formatted_emails)
            
        except Exception as e:
            logger.error(f"Failed to format email list: {e}")
            return f"Retrieved emails but failed to format them: {str(e)}"
    
    def _format_email_list(self, data: Dict[str, Any], title: str = "Recent emails:") -> str:
        """Legacy format method for backward compatibility."""
        try:
            if "result" in data and "content" in data["result"]:
                content = data["result"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    content_text = content[0].get("text", "")
                    if content_text:
                        parsed_content = json.loads(content_text)
                        return self._format_email_list_from_agent_result(parsed_content, title)
            
            return "No emails found or unexpected response format."
            
        except Exception as e:
            logger.error(f"Failed to format email list: {e}")
            return f"Retrieved emails but failed to format them: {str(e)}"
    
    def _format_email_details_from_agent_result(self, data: Dict[str, Any]) -> str:
        """Format detailed email information from Email Agent result."""
        try:
            # Extract email details
            subject = "No subject"
            sender = "Unknown sender"
            date = "Unknown date"
            body = "No body content"
            
            if "payload" in data and "headers" in data["payload"]:
                headers = data["payload"]["headers"]
                for header in headers:
                    if header.get("name") == "Subject":
                        subject = header.get("value", "No subject")
                    elif header.get("name") == "From":
                        sender = header.get("value", "Unknown sender")
                    elif header.get("name") == "Date":
                        date = header.get("value", "Unknown date")
            
            # Try to extract body
            if "snippet" in data:
                body = data["snippet"]
            
            return f"""Email Details:
                From: {sender}
                Subject: {subject}
                Date: {date}
                Body: {body}"""
                            
        except Exception as e:
            logger.error(f"Failed to format email details: {e}")
            return f"Retrieved email but failed to format details: {str(e)}"
    
    def _format_email_details(self, data: Dict[str, Any]) -> str:
        """Legacy format method for backward compatibility."""
        try:
            if "result" in data and "content" in data["result"]:
                content = data["result"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    content_text = content[0].get("text", "")
                    if content_text:
                        parsed_content = json.loads(content_text)
                        return self._format_email_details_from_agent_result(parsed_content)
            
            return "Email retrieved but could not parse details."
            
        except Exception as e:
            logger.error(f"Failed to format email details: {e}")
            return f"Retrieved email but failed to format details: {str(e)}"
    
    def _extract_email_recipient(self, text: str, state: Dict[str, Any]) -> str:
        """Extract email recipient from text or state."""
        # Check state first
        if "email_to" in state:
            return state["email_to"]
        
        # Look for email patterns in text
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""
    
    def _extract_email_subject(self, text: str, state: Dict[str, Any]) -> str:
        """Extract email subject from text or state."""
        # Check state first
        if "email_subject" in state:
            return state["email_subject"]
        
        # Look for subject patterns
        subject_patterns = [
            r'subject[:\\s]+([^\\n]+)',
            r'with subject[:\\s]+([^\\n]+)',
            r'titled[:\\s]+([^\\n]+)'
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().strip('"').strip("'")
        
        return "Automated Email from MACAE"
    
    def _extract_email_body(self, text: str, state: Dict[str, Any]) -> str:
        """Extract email body from text or state."""
        # Check state first
        if "email_body" in state:
            return state["email_body"]
        
        # Look for body patterns
        body_patterns = [
            r'body[:\\s]+([^\\n]+)',
            r'message[:\\s]+([^\\n]+)',
            r'saying[:\\s]+([^\\n]+)'
        ]
        
        for pattern in body_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().strip('"').strip("'")
        
        return "This is an automated email sent from the Multi-Agent Custom Automation Engine (MACAE)."
    
    def _extract_search_query(self, text: str) -> str:
        """Extract search query from text."""
        # Look for search patterns
        search_patterns = [
            r'search for[:\\s]+([^\\n]+)',
            r'find emails[:\\s]+([^\\n]+)',
            r'look for[:\\s]+([^\\n]+)',
            r'containing[:\\s]+([^\\n]+)'
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().strip('"').strip("'")
        
        return ""
    
    def _extract_message_id(self, text: str) -> str:
        """Extract message ID from text."""
        # Look for message ID patterns
        id_patterns = [
            r'id[:\\s]+([a-zA-Z0-9]+)',
            r'message[:\\s]+([a-zA-Z0-9]+)',
            r'email[:\\s]+([a-zA-Z0-9]+)'
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _get_help_message(self) -> str:
        """Get help message for email agent capabilities."""
        return """Email Agent is ready to help with email tasks. I can:

        • Read recent emails: "read my recent emails" or "check my inbox"
        • Send emails: "send email to user@example.com with subject 'Hello' and message 'Hi there'"
        • Search emails: "search for emails containing 'invoice'"
        • Get specific emails: "get email with ID [message_id]"

        Please specify what you'd like me to do with your emails."""


# Backward compatibility class for existing Gmail-specific code
class GmailAgentNode(EmailAgentNode):
    """
    Backward compatibility wrapper for GmailAgentNode.
    
    This class maintains the exact same interface as the original GmailAgentNode
    while using the new multi-provider EmailAgentNode internally.
    """
    
    def __init__(self):
        """Initialize GmailAgentNode with Gmail service for backward compatibility."""
        super().__init__(service='gmail')
        
        logger.info(
            "GmailAgentNode initialized (backward compatibility wrapper)",
            extra={
                "service": self.service,
                "wrapper_type": "backward_compatibility"
            }
        )


# Create a function to be used in LangGraph
async def gmail_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced Gmail agent node function for LangGraph multi-step workflows."""
    agent = GmailAgentNode()  # Uses backward compatibility wrapper
    result = await agent.process(state)
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
    plan_id = state.get("plan_id", "")
    gmail_result = result.get("gmail_result", "")
    
    # Save Gmail agent result to database
    if plan_id and gmail_result:
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="Gmail",
            content=gmail_result,
            agent_type="agent",
            metadata={"status": "completed", "email_service": "gmail"}
        )
    
    # Update state with simplified structure
    from app.agents.state import AgentStateManager
    
    # Add agent result to state
    agent_result = {
        "status": "completed",
        "data": {"gmail_response": gmail_result},
        "message": gmail_result
    }
    
    AgentStateManager.add_agent_result(state, "Gmail", agent_result)
    
    # Send progress update if websocket available
    websocket_manager = state.get("websocket_manager")
    if websocket_manager:
        from datetime import datetime
        progress = AgentStateManager.get_progress_info(state)
        await websocket_manager.send_message(state["plan_id"], {
            "type": "step_progress",
            "data": {
                "step": progress["current_step"],
                "total": progress["total_steps"],
                "agent": "Gmail",
                "progress_percentage": progress["progress_percentage"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    # Update result with simplified state
    result.update({
        "collected_data": state["collected_data"],  # Use updated state
        "execution_results": state["execution_results"]  # Use updated state
    })
    
    return result


# Multi-provider email agent node function for LangGraph
async def email_agent_node(state: Dict[str, Any], service: str = 'gmail') -> Dict[str, Any]:
    """
    Enhanced email agent node function for LangGraph multi-step workflows.
    
    Args:
        state: LangGraph state dictionary
        service: Email service to use ('gmail', 'outlook', etc.)
    
    Returns:
        Updated state dictionary
    """
    agent = EmailAgentNode(service=service)
    result = await agent.process(state)
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
    plan_id = state.get("plan_id", "")
    service_result = result.get(f"{service}_result", "")
    
    # Save email agent result to database
    if plan_id and service_result:
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name=service.title(),
            content=service_result,
            agent_type="agent",
            metadata={"status": "completed", "email_service": service}
        )
    
    # Update state with simplified structure
    from app.agents.state import AgentStateManager
    
    # Add agent result to state
    result_key = f"{service}_response"
    agent_result = {
        "status": "completed",
        "data": {result_key: service_result},
        "message": service_result
    }
    
    AgentStateManager.add_agent_result(state, service.title(), agent_result)
    
    # Send progress update if websocket available
    websocket_manager = state.get("websocket_manager")
    if websocket_manager:
        from datetime import datetime
        progress = AgentStateManager.get_progress_info(state)
        await websocket_manager.send_message(state["plan_id"], {
            "type": "step_progress",
            "data": {
                "step": progress["current_step"],
                "total": progress["total_steps"],
                "agent": service.title(),
                "progress_percentage": progress["progress_percentage"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        })
    
    # Update result with simplified state
    result.update({
        "collected_data": state["collected_data"],  # Use updated state
        "execution_results": state["execution_results"]  # Use updated state
    })
    
    return result