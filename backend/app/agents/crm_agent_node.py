"""
CRM Agent Node for LangGraph using Category-Based Architecture with LLM Integration.

This node uses the category-based CRMAgent that can work with multiple CRM service providers.
Now includes robust LLM-based intent analysis and validation similar to Gmail agent.

**Feature: mcp-client-standardization, Property 4: Base Client Inheritance**
**Validates: Requirements 2.1, 2.5**
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional

from app.agents.state import AgentState
from app.agents.crm_agent import get_crm_agent

logger = logging.getLogger(__name__)


class CRMAgentNode:
    """
    CRM agent node for LangGraph workflows with LLM integration.
    
    This class uses LLM-based intent analysis to understand user requests
    and convert them into proper MCP queries with robust validation.
    """
    
    def __init__(self):
        self.crm_agent = get_crm_agent()
        self.name = "crm_agent"
        
        logger.info(
            "CRMAgentNode initialized with LLM integration",
            extra={
                "agent_type": "category_based_with_llm",
                "supported_services": self.crm_agent.get_supported_services()
            }
        )
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process CRM-related tasks using LLM-based intent analysis."""
        try:
            task = state.get("task_description", "")
            plan_id = state.get("plan_id", "unknown")
            
            # Get WebSocket manager from global service instead of state
            from app.services.websocket_service import get_websocket_manager
            websocket_manager = get_websocket_manager()
            
            # Check if WebSocket is available for this plan
            websocket_available = (
                state.get("websocket_available", False) and 
                websocket_manager.get_connection_count(plan_id) > 0
            )
            
            # Send initial processing message
            if websocket_available:
                try:
                    from datetime import datetime
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": "CRM",
                            "content": "🏢 Analyzing CRM request...",
                            "status": "in_progress",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to send WebSocket message: {e}")
            
            # Use LLM to determine CRM action and execute it intelligently
            crm_result = await self._determine_and_execute_crm_action(task, state)
            
            # Send completion message
            if websocket_manager:
                try:
                    from datetime import datetime
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message",
                        "data": {
                            "agent_name": "CRM",
                            "content": "✅ CRM analysis complete",
                            "status": "completed",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to send WebSocket message: {e}")
            
            return {
                **state,
                "crm_result": crm_result,
                "last_agent": self.name,
                "messages": state.get("messages", []) + [{
                    "role": "assistant",
                    "content": f"CRM Agent: {crm_result}",
                    "agent": self.name
                }]
            }
            
        except Exception as e:
            logger.error(f"CRM agent error: {e}")
            error_message = f"CRM agent encountered an error: {str(e)}"
            return {
                **state,
                "crm_result": error_message,
                "last_agent": self.name,
                "messages": state.get("messages", []) + [{
                    "role": "assistant",
                    "content": error_message,
                    "agent": self.name
                }]
            }
    
    async def _determine_and_execute_crm_action(self, task: str, state: Dict[str, Any]) -> str:
        """Use LLM to determine CRM action and execute it intelligently."""
        
        # Import LLM service
        from app.services.llm_service import LLMService
        
        # Check if mock mode is enabled
        if LLMService.is_mock_mode():
            logger.info("🎭 Using mock mode for CRM Agent")
            return LLMService.get_mock_response("CRM", task)
        
        try:
            # Step 1: Use LLM to parse the user query and determine the action
            action_analysis = await self._analyze_user_intent(task, state)
            
            # Log the LLM-generated action analysis
            logger.info(
                "🏢 LLM Action Analysis Generated",
                extra={
                    "user_request": task,
                    "action_analysis": action_analysis,
                    "action_type": action_analysis.get("action", "unknown"),
                    "service": action_analysis.get("service", "salesforce"),
                    "agent": "CRM"
                }
            )
            print(f"🔍 CRM LLM ACTION ANALYSIS: {json.dumps(action_analysis, indent=2)}")
            
            # Step 2: Execute the determined action using MCP tools
            if action_analysis["action"] == "get_accounts":
                crm_data = await self._get_accounts_with_llm_params(action_analysis)
            elif action_analysis["action"] == "get_opportunities":
                crm_data = await self._get_opportunities_with_llm_params(action_analysis)
            elif action_analysis["action"] == "get_contacts":
                crm_data = await self._get_contacts_with_llm_params(action_analysis)
            elif action_analysis["action"] == "search_records":
                crm_data = await self._search_records_with_llm_params(action_analysis)
            elif action_analysis["action"] == "run_soql_query":
                crm_data = await self._run_soql_query_with_llm_params(action_analysis)
            else:
                return "I couldn't determine what CRM action you want me to perform. Please be more specific."
            
            # Log the CRM data returned from the action
            logger.info(
                "🏢 CRM Data Retrieved",
                extra={
                    "action_type": action_analysis["action"],
                    "service": action_analysis.get("service", "salesforce"),
                    "data_count": len(crm_data.get("records", [])) if isinstance(crm_data, dict) else 0,
                    "has_error": "error" in crm_data if isinstance(crm_data, dict) else False,
                    "agent": "CRM"
                }
            )
            print(f"🏢 CRM DATA RETRIEVED: {json.dumps(crm_data, indent=2, default=str)}")
            
            # Step 3: Use LLM to analyze the results and format response
            return await self._analyze_crm_results_with_llm(task, crm_data, action_analysis, state)
            
        except Exception as e:
            logger.error(f"CRM agent LLM processing failed: {e}")
            return f"I encountered an error while processing your CRM request: {str(e)}"
    
    async def _analyze_user_intent(self, user_request: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze user intent and determine CRM action."""
        
        intent_prompt = f"""
        You are a Salesforce AI Planner that helps users interact with their Salesforce data. Your job is to understand user requests and select the appropriate Salesforce tools.

        Request: "{user_request}"

        TOOL SELECTION GUIDELINES:

        1. **search_records** - Use for broad, text-based searches across multiple fields or objects
        - Examples: "find contacts named John", "search for accounts in California", "look for opportunities mentioning 'enterprise'"
        - Uses SOSL for full-text search
        - Best when: user uses words like "find", "search", "look for" without specifying exact field matching

        2. **query_records** - Use for precise, structured queries with specific field criteria
        - Examples: "get all open opportunities over $100k", "show contacts where email contains '@acme.com'", "list cases created this month"
        - Uses SOQL for precise filtering, sorting, and field selection
        - Best when: user specifies exact conditions, filters, date ranges, or needs sorted/limited results

        3. **get_record** - Use when user references a specific record by ID or when you already have an ID
        - Examples: "show me opportunity 006...", "get details for that account"
        - Fastest way to retrieve a single known record

        4. **describe_object** - Use when you need to understand object structure before querying
        - Examples: "what fields does Account have?", when user asks about data you're unfamiliar with
        - Call this FIRST if you're unsure about available fields or object structure

        DECISION TREE:
        - Does user have a specific RECORD ID? → get_record
        - Does user want to SEARCH with keywords across fields? → search_records
        - Does user want to QUERY with specific conditions/filters? → query_records
        - Are you UNSURE about object structure? → describe_object first

        BEST PRACTICES:
        - If user's request is ambiguous between search_records and query_records, prefer search_records for simpler queries and query_records for complex filtering
        - Always call describe_object if you're uncertain about field names or data types
        - If a query might return many records, consider limiting results
        - Chain tools when needed: describe_object → query_records → update_record

        Remember: Choose the most efficient tool for the task. Don't overcomplicate simple requests.

        RESPOND WITH RAW JSON ONLY (no markdown formatting):
        {{
            "action": "search_records|get_accounts|get_opportunities|get_contacts|run_soql_query",
            "service": "salesforce",
            "account_name": "specific account name filter",
            "search_term": "search keywords for search_records",
            "stage": "opportunity stage filter",
            "objects": ["Account", "Contact", "Opportunity"],
            "soql_query": "SELECT Id, Name FROM Account LIMIT 5",
            "limit": 15
        }}

        CRITICAL RULES:
        - ALWAYS use search_records instead of get_accounts/get_opportunities/get_contacts when user provides ANY search criteria (company names, keywords, topics)
        - For "find accounts with X" or "search for companies Y" → ALWAYS search_records, NEVER get_accounts
        - get_accounts/get_opportunities/get_contacts are ONLY for "show recent accounts" with zero filtering
        - When user says "TBI Corp" or any company name, use search_records with that as search_term

        EXAMPLE MAPPINGS:
        "Find accounts for TBI Corp" → search_records with search_term "TBI Corp" (NOT get_accounts!)
        "Search for companies in California" → search_records with search_term "California"
        "Show recent accounts" → get_accounts with limit (acceptable)
        "Look for opportunities mentioning enterprise" → search_records with search_term "enterprise"
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
                    agent_name="CRM"
                )
            else:
                # Fallback to non-streaming LLM call when websocket not available
                response = await LLMService.call_llm_non_streaming(
                    prompt=intent_prompt,
                    agent_name="CRM"
                )
            
            # Log the raw LLM response before parsing
            logger.info(
                "🤖 LLM Intent Analysis Response",
                extra={
                    "user_request": user_request,
                    "llm_response": response,
                    "response_length": len(response),
                    "agent": "CRM"
                }
            )
            print(f"🤖 RAW LLM RESPONSE for CRM intent analysis: {response}")
            
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
                
                # CRITICAL: Apply action mapping to handle LLM variations
                validated_result = self._apply_action_mapping(validated_result, user_request)
                
                logger.info(
                    "✅ Successfully parsed and validated LLM intent analysis",
                    extra={
                        "parsed_action": validated_result.get("action"),
                        "parsed_service": validated_result.get("service"),
                        "validation_applied": True,
                        "action_mapping_applied": True,
                        "agent": "CRM"
                    }
                )
                return validated_result
            except json.JSONDecodeError:
                logger.warning(
                    "⚠️ LLM response was not valid JSON, using fallback",
                    extra={
                        "llm_response": response,
                        "cleaned_response": cleaned_response,
                        "agent": "CRM"
                    }
                )
                # Fallback to simple pattern matching if LLM doesn't return valid JSON
                fallback_result = self._fallback_intent_analysis(user_request)
                # Still validate the fallback result
                return self._validate_and_sanitize_action_analysis(fallback_result, user_request)
                
        except Exception as e:
            logger.error(f"CRM intent analysis failed: {e}")
            fallback_result = self._fallback_intent_analysis(user_request)
            # Still validate the fallback result
            return self._validate_and_sanitize_action_analysis(fallback_result, user_request)
    
    def _validate_and_sanitize_action_analysis(self, action_analysis: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """
        Validate and sanitize LLM-generated action analysis to ensure MCP-compatible structured JSON.
        
        This method implements robust validation for the main CRM action types:
        1. get_accounts - requires limit
        2. get_opportunities - requires limit
        3. get_contacts - requires limit
        4. search_records - requires search_term
        5. run_soql_query - requires soql_query (Salesforce only)
        
        Args:
            action_analysis: Raw LLM response parsed as dict
            user_request: Original user request for fallback parameter generation
            
        Returns:
            Validated and sanitized action analysis with guaranteed required fields
        """
        
        logger.info(
            "🔍 Validating CRM LLM action analysis for MCP compatibility",
            extra={
                "raw_action": action_analysis.get("action", "unknown"),
                "has_search_term": bool(action_analysis.get("search_term")),
                "has_account_name": bool(action_analysis.get("account_name")),
                "has_soql_query": bool(action_analysis.get("soql_query")),
                "agent": "CRM"
            }
        )
        
        # Ensure action field exists and is valid
        valid_actions = ["get_accounts", "get_opportunities", "get_contacts", "search_records", "run_soql_query"]
        action = action_analysis.get("action", "").lower().strip()
        
        if action not in valid_actions:
            logger.warning(
                f"⚠️ Invalid CRM action '{action}', defaulting to 'get_accounts'",
                extra={"original_action": action, "user_request": user_request, "agent": "CRM"}
            )
            action = "get_accounts"  # Default to get_accounts as safest option
        
        # Ensure service field exists and is valid
        valid_services = ["salesforce", "hubspot", "pipedrive", "zoho_crm"]
        service = action_analysis.get("service", "salesforce").lower().strip()
        
        if service not in valid_services:
            logger.warning(
                f"⚠️ Invalid CRM service '{service}', defaulting to 'salesforce'",
                extra={"original_service": service, "agent": "CRM"}
            )
            service = "salesforce"
        
        # Create validated result with guaranteed structure
        validated_result = {
            "action": action,
            "service": service,
            "account_name": "",
            "search_term": "",
            "stage": "",
            "objects": ["Account", "Contact", "Opportunity"],
            "soql_query": "",
            "limit": 5
        }
        
        # Action-specific validation and fallback parameter generation
        if action in ["get_accounts", "get_opportunities", "get_contacts"]:
            # These actions require limit
            limit = action_analysis.get("limit", 5)
            try:
                limit = int(limit)
                limit = max(1, min(20, limit))  # Clamp between 1-20 for CRM data
            except (ValueError, TypeError):
                limit = 5
                logger.warning(
                    f"⚠️ Invalid limit for {action}, using default: {limit}",
                    extra={"original_limit": action_analysis.get("limit"), "agent": "CRM"}
                )
            
            validated_result.update({
                "limit": limit,
                "account_name": action_analysis.get("account_name", "").strip(),
                "stage": action_analysis.get("stage", "").strip()
            })
            
        elif action == "search_records":
            # SEARCH_RECORDS: Requires search_term
            search_term = action_analysis.get("search_term", "").strip()
            
            if not search_term:
                # Generate fallback search term from user request
                search_term = self._generate_fallback_search_term(user_request)
                logger.warning(
                    f"⚠️ Missing search term, generated fallback: '{search_term}'",
                    extra={"user_request": user_request, "agent": "CRM"}
                )
            
            # Validate objects list
            objects = action_analysis.get("objects", ["Account", "Contact", "Opportunity"])
            if not isinstance(objects, list) or not objects:
                objects = ["Account", "Contact", "Opportunity"]
            
            validated_result.update({
                "search_term": search_term,
                "objects": objects
            })
            
        elif action == "run_soql_query":
            # RUN_SOQL_QUERY: Requires soql_query and must be Salesforce
            if service != "salesforce":
                logger.warning(
                    f"⚠️ SOQL queries only supported on Salesforce, changing service from '{service}' to 'salesforce'",
                    extra={"original_service": service, "agent": "CRM"}
                )
                service = "salesforce"
                validated_result["service"] = service
            
            soql_query = action_analysis.get("soql_query", "").strip()
            
            if not soql_query:
                # Generate fallback SOQL query
                soql_query = self._generate_fallback_soql_query(user_request)
                logger.warning(
                    f"⚠️ Missing SOQL query, generated fallback: '{soql_query}'",
                    extra={"user_request": user_request, "agent": "CRM"}
                )
            
            validated_result["soql_query"] = soql_query
        
        # Final validation check
        validation_passed = self._final_validation_check(validated_result)
        
        logger.info(
            "✅ CRM action analysis validation completed",
            extra={
                "final_action": validated_result["action"],
                "final_service": validated_result["service"],
                "validation_passed": validation_passed,
                "has_required_fields": self._check_required_fields(validated_result),
                "agent": "CRM"
            }
        )
        
        if not validation_passed:
            logger.error(
                "❌ Final CRM validation failed, using safe fallback",
                extra={"validated_result": validated_result, "agent": "CRM"}
            )
            # Ultimate fallback - safe get_accounts
            return {
                "action": "get_accounts",
                "service": "salesforce",
                "account_name": "",
                "search_term": "",
                "stage": "",
                "objects": ["Account", "Contact", "Opportunity"],
                "soql_query": "",
                "limit": 5
            }
        
        return validated_result
    
    def _apply_action_mapping(self, action_analysis: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """
        Apply action mapping to handle LLM variations and ensure correct tool selection.
        
        This method implements intelligent fallback logic to prefer search_records over get_accounts
        when the user provides keywords or company names, even if the LLM chooses the wrong action.
        """
        
        action = action_analysis.get("action", "")
        search_term = action_analysis.get("search_term", "").strip()
        account_name = action_analysis.get("account_name", "").strip()
        
        # Check if user request contains keywords that should trigger search
        request_lower = user_request.lower()
        has_company_keywords = any(keyword in request_lower for keyword in [
            "corp", "inc", "llc", "ltd", "company", "corporation", "tbi"
        ])
        has_search_keywords = any(keyword in request_lower for keyword in [
            "find", "search", "look for", "with", "from", "containing"
        ])
        
        # Check if this is a "recent" or "list all" query that should NOT be converted to search
        is_recent_query = any(keyword in request_lower for keyword in [
            "recent", "latest", "last", "show all", "list all"
        ])
        
        # Extract potential company names from request
        import re
        company_patterns = [
            r'([A-Z][a-zA-Z0-9\s&.-]*(?:Corp|Inc|LLC|Ltd|Company))',
            r'(TBI[- ]?\w*)',  # Specific pattern for TBI
            r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',  # Capitalized words
        ]
        
        extracted_terms = []
        for pattern in company_patterns:
            matches = re.findall(pattern, user_request, re.IGNORECASE)
            extracted_terms.extend(matches)
        
        # CRITICAL MAPPING LOGIC: Only convert to search_records if NOT a recent query
        should_convert_to_search = (
            (has_company_keywords or has_search_keywords or extracted_terms) 
            and not is_recent_query
        )
        
        # If LLM chose get_accounts but user has search criteria (and it's not a recent query), switch to search_records
        if action == "get_accounts" and should_convert_to_search:
            logger.warning(
                "🔄 CRM Action Mapping: LLM chose 'get_accounts' but user has search criteria, switching to 'search_records'",
                extra={
                    "original_action": action,
                    "user_request": user_request,
                    "has_company_keywords": has_company_keywords,
                    "has_search_keywords": has_search_keywords,
                    "extracted_terms": extracted_terms,
                    "agent": "CRM"
                }
            )
            
            action_analysis["action"] = "search_records"
            
            # Generate search term if not provided
            if not search_term:
                if extracted_terms:
                    action_analysis["search_term"] = extracted_terms[0]
                    logger.info(f"🔍 Generated search term from extraction: '{extracted_terms[0]}'")
                elif account_name:
                    action_analysis["search_term"] = account_name
                    logger.info(f"🔍 Using account_name as search term: '{account_name}'")
                else:
                    # Extract from user request
                    action_analysis["search_term"] = self._generate_fallback_search_term(user_request)
                    logger.info(f"🔍 Generated fallback search term: '{action_analysis['search_term']}'")
        
        # Similar logic for get_opportunities and get_contacts
        if action in ["get_opportunities", "get_contacts"] and should_convert_to_search:
            logger.warning(
                f"🔄 CRM Action Mapping: LLM chose '{action}' but user has search criteria, switching to 'search_records'",
                extra={
                    "original_action": action,
                    "user_request": user_request,
                    "has_company_keywords": has_company_keywords,
                    "has_search_keywords": has_search_keywords,
                    "extracted_terms": extracted_terms,
                    "agent": "CRM"
                }
            )
            
            action_analysis["action"] = "search_records"
            
            # Generate search term if not provided
            if not search_term:
                if extracted_terms:
                    action_analysis["search_term"] = extracted_terms[0]
                elif account_name:
                    action_analysis["search_term"] = account_name
                else:
                    action_analysis["search_term"] = self._generate_fallback_search_term(user_request)
        
        # Handle variations in action names (LLM might return slightly different names)
        action_mappings = {
            "search_record": "search_records",
            "find_records": "search_records",
            "query_records": "search_records",  # Map query to search for simplicity
            "get_account": "get_accounts",
            "list_accounts": "get_accounts",
            "get_opportunity": "get_opportunities",
            "list_opportunities": "get_opportunities",
            "get_contact": "get_contacts",
            "list_contacts": "get_contacts",
            "run_query": "run_soql_query",
            "soql_query": "run_soql_query"
        }
        
        original_action = action_analysis.get("action", "")
        if original_action in action_mappings:
            mapped_action = action_mappings[original_action]
            logger.info(
                f"🔄 CRM Action Mapping: '{original_action}' → '{mapped_action}'",
                extra={
                    "original_action": original_action,
                    "mapped_action": mapped_action,
                    "agent": "CRM"
                }
            )
            action_analysis["action"] = mapped_action
        
        return action_analysis
    
    def _generate_fallback_search_term(self, user_request: str) -> str:
        """Generate fallback search term when LLM fails to provide one."""
        request_lower = user_request.lower()
        
        # Look for company names or specific terms
        company_patterns = [
            r'([A-Z][a-zA-Z0-9\s&.-]*(?:Corp|Inc|LLC|Ltd|Company))',
            r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',  # Capitalized words
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, user_request)
            if match:
                return match.group(1).strip()
        
        # Look for common CRM terms
        crm_keywords = ["account", "opportunity", "contact", "lead", "deal"]
        for keyword in crm_keywords:
            if keyword in request_lower:
                return keyword
        
        # Default fallback
        return "account"
    
    def _generate_fallback_soql_query(self, user_request: str) -> str:
        """Generate fallback SOQL query when LLM fails to provide one."""
        request_lower = user_request.lower()
        
        # Determine what type of data to query based on request
        if "opportunity" in request_lower or "deal" in request_lower:
            return "SELECT Id, Name, StageName, Amount, CloseDate FROM Opportunity LIMIT 5"
        elif "contact" in request_lower:
            return "SELECT Id, Name, Email, Account.Name FROM Contact LIMIT 5"
        else:
            # Default to accounts
            return "SELECT Id, Name, Type, Industry FROM Account LIMIT 5"
    
    def _final_validation_check(self, validated_result: Dict[str, Any]) -> bool:
        """Perform final validation to ensure MCP compatibility."""
        action = validated_result.get("action")
        
        if action in ["get_accounts", "get_opportunities", "get_contacts"]:
            limit = validated_result.get("limit", 0)
            return isinstance(limit, int) and limit > 0
        elif action == "search_records":
            return bool(validated_result.get("search_term", "").strip())
        elif action == "run_soql_query":
            return bool(validated_result.get("soql_query", "").strip())
        
        return False
    
    def _check_required_fields(self, validated_result: Dict[str, Any]) -> bool:
        """Check if all required fields are present for the action type."""
        action = validated_result.get("action")
        
        required_fields = {
            "get_accounts": ["limit"],
            "get_opportunities": ["limit"],
            "get_contacts": ["limit"],
            "search_records": ["search_term"],
            "run_soql_query": ["soql_query"]
        }
        
        if action not in required_fields:
            return False
        
        for field in required_fields[action]:
            if not validated_result.get(field):
                return False
        
        return True
    
    def _fallback_intent_analysis(self, user_request: str) -> Dict[str, Any]:
        """Fallback intent analysis using simple pattern matching."""
        
        request_lower = user_request.lower()
        
        print("WARNING! LLM did not return valid JSON so falling back to manual pattern matching for CRM query intent")
        
        # Check for SOQL query requests
        if "soql" in request_lower or "query" in request_lower:
            return {
                "action": "run_soql_query",
                "service": "salesforce",
                "soql_query": self._generate_fallback_soql_query(user_request)
            }
        
        # Check for opportunity requests
        elif any(keyword in request_lower for keyword in ["opportunity", "opportunities", "deal", "deals"]):
            return {
                "action": "get_opportunities",
                "service": "salesforce",
                "limit": 5
            }
        
        # Check for contact requests
        elif any(keyword in request_lower for keyword in ["contact", "contacts"]):
            return {
                "action": "get_contacts",
                "service": "salesforce",
                "limit": 5
            }
        
        # Check for search requests
        elif any(keyword in request_lower for keyword in ["search", "find", "look for"]):
            return {
                "action": "search_records",
                "service": "salesforce",
                "search_term": self._generate_fallback_search_term(user_request)
            }
        
        # Default to get_accounts
        else:
            return {
                "action": "get_accounts",
                "service": "salesforce",
                "limit": 5
            }
    
    async def _get_accounts_with_llm_params(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get accounts using LLM-determined parameters."""
        try:
            service = action_analysis.get("service", "salesforce")
            account_name = action_analysis.get("account_name", "")
            limit = action_analysis.get("limit", 5)
            
            logger.info(f"Getting accounts with LLM params: account_name='{account_name}', limit={limit}")
            
            result = await self.crm_agent.get_accounts(
                service=service,
                account_name=account_name if account_name else None,
                limit=limit
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get accounts with LLM params: {e}")
            return {"records": [], "error": str(e)}
    
    async def _get_opportunities_with_llm_params(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get opportunities using LLM-determined parameters."""
        try:
            service = action_analysis.get("service", "salesforce")
            stage = action_analysis.get("stage", "")
            limit = action_analysis.get("limit", 5)
            
            logger.info(f"Getting opportunities with LLM params: stage='{stage}', limit={limit}")
            
            result = await self.crm_agent.get_opportunities(
                service=service,
                stage=stage if stage else None,
                limit=limit
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get opportunities with LLM params: {e}")
            return {"records": [], "error": str(e)}
    
    async def _get_contacts_with_llm_params(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get contacts using LLM-determined parameters."""
        try:
            service = action_analysis.get("service", "salesforce")
            account_name = action_analysis.get("account_name", "")
            limit = action_analysis.get("limit", 5)
            
            logger.info(f"Getting contacts with LLM params: account_name='{account_name}', limit={limit}")
            
            result = await self.crm_agent.get_contacts(
                service=service,
                account_name=account_name if account_name else None,
                limit=limit
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get contacts with LLM params: {e}")
            return {"records": [], "error": str(e)}
    
    async def _search_records_with_llm_params(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Search records using LLM-determined parameters."""
        try:
            service = action_analysis.get("service", "salesforce")
            search_term = action_analysis.get("search_term", "")
            objects = action_analysis.get("objects", ["Account", "Contact", "Opportunity"])
            
            logger.info(f"Searching records with LLM params: search_term='{search_term}', objects={objects}")
            
            result = await self.crm_agent.search_records(
                search_term=search_term,
                service=service,
                objects=objects
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search records with LLM params: {e}")
            return {"results": [], "error": str(e)}
    
    async def _run_soql_query_with_llm_params(self, action_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Run SOQL query using LLM-determined parameters."""
        try:
            service = action_analysis.get("service", "salesforce")
            soql_query = action_analysis.get("soql_query", "")
            
            logger.info(f"Running SOQL query with LLM params: query='{soql_query}'")
            
            result = await self.crm_agent.run_soql_query(
                query=soql_query,
                service=service
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to run SOQL query with LLM params: {e}")
            return {"records": [], "error": str(e)}
    
    async def _analyze_crm_results_with_llm(self, original_request: str, crm_data: Dict[str, Any], 
                                         action_analysis: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Use LLM to analyze CRM results and format response."""
        try:
            # Import LLM service here to avoid circular imports
            from app.services.llm_service import LLMService
            
            # Check if there was an error
            if "error" in crm_data:
                return f"I encountered an error: {crm_data['error']}"
            
            # Determine data type and count
            records = crm_data.get("records", [])
            results = crm_data.get("results", [])
            
            if records:
                # Standard CRM records (accounts, opportunities, contacts)
                data_summary = f"Found {len(records)} record(s)"
                data_content = f"Records: {json.dumps(records, indent=2, default=str)}"
            elif results:
                # Search results
                data_summary = f"Found {len(results)} search result(s)"
                data_content = f"Results: {json.dumps(results, indent=2, default=str)}"
            else:
                return "No data found matching your criteria."
            
            # Build analysis prompt
            analysis_prompt = f"""
            Original user request: "{original_request}"
            Action taken: {action_analysis.get('action', 'unknown')}
            Service used: {action_analysis.get('service', 'salesforce')}
            
            {data_summary}. Here are the details:
            
            {data_content}
            
            Please provide a comprehensive analysis of this CRM data in relation to the user's request. Include:
            1. Summary of what was found
            2. Key business information (names, amounts, stages, dates)
            3. Any patterns or insights relevant to customer relationship management
            4. Direct answers to the user's questions
            5. Format monetary amounts clearly with $ symbols where applicable
            
            Be specific and reference actual data from the results, not hypothetical information.
            Use clear formatting with bullet points and sections where appropriate.
            Focus on business-relevant insights for sales and customer management.
            """
            
            websocket_manager = state.get("websocket_manager")
            plan_id = state.get("plan_id", "unknown")
            
            if websocket_manager:
                response = await LLMService.call_llm_streaming(
                    prompt=analysis_prompt,
                    plan_id=plan_id,
                    websocket_manager=websocket_manager,
                    agent_name="CRM"
                )
                return response
            else:
                # Fallback to formatted results
                return self._format_detailed_crm_results(crm_data, action_analysis, original_request)
                
        except Exception as e:
            logger.error(f"Failed to analyze CRM results with LLM: {e}")
            return f"Found data but failed to analyze it: {str(e)}"
    
    def _format_detailed_crm_results(self, crm_data: Dict[str, Any], action_analysis: Dict[str, Any], 
                                   original_request: str) -> str:
        """Format detailed CRM results when LLM analysis fails."""
        
        print("WARNING CRM RESULT FORMATTING: LLM formatting did not work so manually attempting.")
        
        try:
            action = action_analysis.get("action", "unknown")
            service = action_analysis.get("service", "salesforce")
            
            # Handle different data types
            if "records" in crm_data:
                records = crm_data["records"]
                if not records:
                    return f"No records found matching your criteria.\n\n**Original Request:** {original_request}"
                
                result = [f"🏢 **CRM Records Found: {len(records)}**\n"]
                
                for i, record in enumerate(records[:10], 1):  # Limit to 10 for readability
                    name = record.get('Name', 'N/A')
                    record_type = record.get('attributes', {}).get('type', 'Record')
                    
                    result.append(f"{i}. **{name}** ({record_type})")
                    
                    # Add type-specific fields
                    if record_type == 'Account':
                        industry = record.get('Industry', 'N/A')
                        account_type = record.get('Type', 'N/A')
                        if industry != 'N/A':
                            result.append(f"   - Industry: {industry}")
                        if account_type != 'N/A':
                            result.append(f"   - Type: {account_type}")
                    
                    elif record_type == 'Opportunity':
                        stage = record.get('StageName', 'N/A')
                        amount = record.get('Amount', 0)
                        close_date = record.get('CloseDate', 'N/A')
                        result.append(f"   - Stage: {stage}")
                        if amount > 0:
                            result.append(f"   - Amount: ${amount:,.2f}")
                        if close_date != 'N/A':
                            result.append(f"   - Close Date: {close_date}")
                    
                    elif record_type == 'Contact':
                        email = record.get('Email', 'N/A')
                        account_name = record.get('Account', {}).get('Name', 'N/A')
                        if email != 'N/A':
                            result.append(f"   - Email: {email}")
                        if account_name != 'N/A':
                            result.append(f"   - Account: {account_name}")
                    
                    # Add ID for reference
                    record_id = record.get('Id', 'N/A')
                    result.append(f"   - ID: {record_id}")
                    result.append("")
                
                result.append(f"**Original Request:** {original_request}")
                result.append(f"**Service Used:** {service.title()}")
                
                return "\n".join(result)
            
            elif "results" in crm_data:
                results = crm_data["results"]
                if not results:
                    return f"No search results found.\n\n**Original Request:** {original_request}"
                
                result = [f"🔍 **Search Results Found: {len(results)}**\n"]
                
                for i, search_result in enumerate(results[:10], 1):
                    result.append(f"{i}. {search_result}")
                    result.append("")
                
                result.append(f"**Original Request:** {original_request}")
                result.append(f"**Service Used:** {service.title()}")
                
                return "\n".join(result)
            
            else:
                return f"Retrieved data but couldn't format it properly.\n\n**Original Request:** {original_request}"
                
        except Exception as e:
            logger.error(f"Failed to format detailed CRM results: {e}")
            return f"Retrieved data but failed to format it: {str(e)}"


# Create the async function for the node
async def crm_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    CRM agent node - handles CRM operations with LLM integration.
    
    This agent uses LLM-based intent analysis to understand user requests
    and convert them into proper MCP queries with robust validation.
    """
    
    # Create the CRM agent node instance
    crm_node = CRMAgentNode()
    
    # Process the request
    result = await crm_node.process(state)
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
    plan_id = state.get("plan_id", "")
    crm_result = result.get("crm_result", "")
    
    # Save CRM agent result to database
    if plan_id and crm_result:
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="CRM",
            content=crm_result,
            agent_type="agent",
            metadata={"status": "completed", "agent_type": "crm"}
        )
    
    # Update state with simplified structure
    from app.agents.state import AgentStateManager
    
    # Add agent result to state
    agent_result = {
        "status": "completed",
        "data": {"crm_response": crm_result},
        "message": crm_result
    }
    
    AgentStateManager.add_agent_result(state, "CRM", agent_result)
    
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
                    "agent": "CRM",
                    "progress_percentage": progress["progress_percentage"],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")
    
    return {
        "messages": [result.get("crm_result", "")],
        "current_agent": "CRM",
        "crm_result": result.get("crm_result", ""),
        "collected_data": state.get("collected_data", {}),
        "execution_results": state.get("execution_results", [])
    }