"""
HTTP-Based CRM Agent for Multi-Service CRM Operations.

This agent uses HTTP MCP transport like the Email agent, replacing the STDIO-based
MCP client with HTTP transport for better compatibility with HTTP MCP servers.

Enhanced for Task 4.3 with:
- Improved Salesforce MCP server connection handling
- Better error parsing for Salesforce API responses
- Optimized query patterns for better data retrieval
- Enhanced retry logic and timeout handling

**Feature: mcp-http-transport-migration, HTTP Transport**
**Validates: Requirements 2.1, 2.5, NFR1.3, NFR1.4**
"""

import logging
import asyncio
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.mcp_http_client import get_mcp_http_manager, MCPHTTPError, MCPHTTPConnectionError, MCPHTTPTimeoutError

logger = logging.getLogger(__name__)


class SalesforceAPIError(Exception):
    """Specific exception for Salesforce API errors."""
    def __init__(self, error_code: str, error_message: str, response_data: Dict = None):
        self.error_code = error_code
        self.error_message = error_message
        self.response_data = response_data or {}
        super().__init__(f"Salesforce API Error {error_code}: {error_message}")


class CRMAgentHTTP:
    """
    HTTP-based agent for CRM operations across multiple services.
    
    This agent provides a unified interface for CRM operations while supporting
    multiple CRM service providers through HTTP MCP transport. It uses the same
    HTTP client architecture as the Email agent.
    
    Supported Services:
    - salesforce: Salesforce via HTTP MCP (primary and only enabled CRM service)
    
    Note: Other CRM services (HubSpot, Pipedrive, Zoho CRM) are commented out 
    as they are not currently implemented or enabled.
    """
    
    def __init__(self, mcp_manager=None):
        """
        Initialize CRM Agent with enhanced HTTP MCP client manager.
        
        Args:
            mcp_manager: HTTP MCP client manager instance (optional, will use global if None)
        """
        self.mcp_manager = mcp_manager or get_mcp_http_manager()
        
        # Enhanced connection settings for Salesforce
        self.salesforce_settings = {
            'max_retries': 4,  # Increased from default 3
            'timeout': 75,     # Increased timeout for Salesforce API calls
            'connection_pool_size': 3,  # Connection pooling
            'backoff_factor': 1.5,
            'max_backoff': 20.0,
            'query_optimization': True  # Enable query pattern optimization
        }
        
        # Parameter mapping for translating user-friendly parameter names to MCP tool parameter names
        self.parameter_mapping = {
            'soql_query': 'query',  # Translate soql_query -> query for SOQL operations
            'account_name': 'account_name',  # Keep as-is
            'limit': 'limit',  # Keep as-is (but note: not all tools support limit)
            'stage': 'stage',  # Keep as-is
            'search_term': 'search_term',  # Keep as-is
            'objects': 'objects',  # Keep as-is
            'org_alias': 'org_alias'  # Keep as-is
        }
        
        # Tool-specific parameter filters (remove unsupported parameters)
        self.tool_parameter_filters = {
            'salesforce_search_records': ['search_term', 'objects', 'org_alias'],  # No limit support
            'salesforce_soql_query': ['query', 'org_alias'],  # No limit support
            'salesforce_get_accounts': ['limit', 'account_name', 'org_alias'],
            'salesforce_get_opportunities': ['limit', 'stage', 'org_alias'],
            'salesforce_get_contacts': ['limit', 'account_name', 'org_alias'],
            'salesforce_list_orgs': []  # No parameters
        }
        
        # Optimized query patterns for better data retrieval
        self.optimized_queries = {
            'get_accounts_by_name': """
                SELECT Id, Name, Type, Industry, AnnualRevenue, Phone, Website, 
                       BillingCity, BillingState, BillingCountry, CreatedDate, LastModifiedDate
                FROM Account 
                WHERE Name LIKE '%{account_name}%' 
                ORDER BY LastModifiedDate DESC 
                LIMIT {limit}
            """,
            'get_recent_opportunities': """
                SELECT Id, Name, StageName, Amount, CloseDate, Account.Name, 
                       Probability, Type, LeadSource, CreatedDate, LastModifiedDate
                FROM Opportunity 
                WHERE LastModifiedDate >= LAST_N_DAYS:30
                ORDER BY LastModifiedDate DESC 
                LIMIT {limit}
            """,
            'get_contacts_by_account': """
                SELECT Id, Name, Email, Phone, Title, Account.Name, 
                       Department, MailingCity, MailingState, CreatedDate, LastModifiedDate
                FROM Contact 
                WHERE Account.Name LIKE '%{account_name}%'
                ORDER BY LastModifiedDate DESC 
                LIMIT {limit}
            """
        }
        
        self.supported_services = {
            'salesforce': {
                'name': 'Salesforce',
                'tools': {
                    'get_accounts': 'salesforce_get_accounts',
                    'get_opportunities': 'salesforce_get_opportunities',
                    'get_contacts': 'salesforce_get_contacts',
                    'search_records': 'salesforce_search_records',
                    'run_soql_query': 'salesforce_soql_query',
                    'list_orgs': 'salesforce_list_orgs'
                },
                'settings': self.salesforce_settings
            },
            # Future service support (currently disabled - not implemented)
            # 'hubspot': {
            #     'name': 'HubSpot',
            #     'tools': {
            #         'get_accounts': 'hubspot_get_companies',
            #         'get_opportunities': 'hubspot_get_deals',
            #         'get_contacts': 'hubspot_get_contacts',
            #         'search_records': 'hubspot_search_records'
            #     }
            # },
            # 'pipedrive': {
            #     'name': 'Pipedrive',
            #     'tools': {
            #         'get_accounts': 'pipedrive_get_organizations',
            #         'get_opportunities': 'pipedrive_get_deals',
            #         'get_contacts': 'pipedrive_get_persons',
            #         'search_records': 'pipedrive_search_records'
            #     }
            # },
            # 'zoho_crm': {
            #     'name': 'Zoho CRM',
            #     'tools': {
            #         'get_accounts': 'zoho_crm_get_accounts',
            #         'get_opportunities': 'zoho_crm_get_deals',
            #         'get_contacts': 'zoho_crm_get_contacts',
            #         'search_records': 'zoho_crm_search_records'
            #     }
            # }
        }
        
        # Performance tracking
        self._call_count = 0
        self._error_count = 0
        self._last_successful_call = None
        self._query_optimization_count = 0
        
        logger.info(
            "Enhanced HTTP CRM Agent initialized",
            extra={
                "supported_services": list(self.supported_services.keys()),
                "default_service": "salesforce",
                "transport": "http",
                "salesforce_timeout": self.salesforce_settings['timeout'],
                "salesforce_max_retries": self.salesforce_settings['max_retries'],
                "query_optimization": self.salesforce_settings['query_optimization']
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
    
    def _normalize_parameters(self, service: str, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parameter names from user-friendly names to MCP tool parameter names.
        
        This method translates parameter names to match what the MCP tools expect
        and filters out unsupported parameters for specific tools.
        
        Args:
            service: The service being used (e.g., 'salesforce')
            operation: The operation being performed (e.g., 'run_soql_query')
            params: Dictionary of parameters with user-friendly names
            
        Returns:
            Dictionary with normalized parameter names for MCP tools
        """
        normalized = {}
        
        # Get the tool name for filtering
        tool_name = None
        try:
            tool_name = self._get_tool_name(service, operation)
        except (ValueError, AttributeError):
            # If we can't determine tool name, proceed without filtering
            pass
        
        for param_name, param_value in params.items():
            # Skip None values
            if param_value is None:
                continue
                
            # Translate parameter name using mapping, or keep original if not in mapping
            mcp_param_name = self.parameter_mapping.get(param_name, param_name)
            
            # Filter out unsupported parameters for specific tools
            if tool_name and tool_name in self.tool_parameter_filters:
                allowed_params = self.tool_parameter_filters[tool_name]
                if mcp_param_name not in allowed_params:
                    logger.debug(
                        f"Filtering out unsupported parameter '{mcp_param_name}' for tool '{tool_name}'",
                        extra={
                            "tool_name": tool_name,
                            "filtered_param": mcp_param_name,
                            "allowed_params": allowed_params
                        }
                    )
                    continue
            
            normalized[mcp_param_name] = param_value
        
        logger.debug(
            f"Parameter normalization for {operation}",
            extra={
                "operation": operation,
                "service": service,
                "tool_name": tool_name,
                "original_params": params,
                "normalized_params": normalized
            }
        )
        
        return normalized
    
    def _process_mcp_result(self, result: Any, service: str = None) -> Dict[str, Any]:
        """
        Process MCP CallToolResult into a standard dictionary format with enhanced error parsing.
        
        This method handles FastMCP CallToolResult format following the same
        pattern as the Bill.com agent for consistent result processing.
        
        Args:
            result: Raw result from MCP tool call
            service: Service name for service-specific error parsing
            
        Returns:
            Processed result dictionary
            
        Raises:
            SalesforceAPIError: If Salesforce API returns an error
        """
        # Handle FastMCP HTTP response format
        if isinstance(result, dict) and 'result' in result:
            # The HTTP MCP client returns a dict with 'result' key containing CallToolResult string
            result_str = result['result']
            
            # Try to extract JSON from the text content within the CallToolResult
            if 'text=' in result_str:
                # Look for the JSON content in the text field
                # Pattern: text='{"success":true,"totalSize":...}'
                pattern = r"text='({.*?})'"
                match = re.search(pattern, result_str, re.DOTALL)
                if match:
                    try:
                        json_str = match.group(1)
                        # Replace null with None for Python compatibility
                        json_str = json_str.replace('null', 'None').replace('true', 'True').replace('false', 'False')
                        structured_data = eval(json_str)  # Use eval since it's already Python-like format
                        
                        # Enhanced error parsing for Salesforce
                        if service == 'salesforce':
                            self._validate_salesforce_response(structured_data)
                        
                        return structured_data
                    except (SyntaxError, ValueError) as e:
                        logger.warning(f"Failed to parse JSON from text content: {e}")
                        # Try with standard JSON parsing
                        try:
                            json_str = match.group(1)
                            structured_data = json.loads(json_str)
                            
                            # Enhanced error parsing for Salesforce
                            if service == 'salesforce':
                                self._validate_salesforce_response(structured_data)
                            
                            return structured_data
                        except json.JSONDecodeError:
                            pass
            
            # If we can't extract structured data, return the raw result
            processed_result = {"result": result_str}
        
        # Handle direct CallToolResult objects (fallback for other transports)
        elif hasattr(result, 'structured_content') and result.structured_content:
            processed_result = result.structured_content
        elif hasattr(result, 'data') and result.data:
            processed_result = result.data
        elif isinstance(result, dict):
            processed_result = result
        elif isinstance(result, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(result)
                processed_result = parsed if isinstance(parsed, dict) else {"result": result}
            except json.JSONDecodeError:
                processed_result = {"result": result}
        else:
            processed_result = {"result": str(result)}
        
        # Enhanced error parsing for Salesforce
        if service == 'salesforce':
            self._validate_salesforce_response(processed_result)
        
        return processed_result
    
    def _validate_salesforce_response(self, response: Dict[str, Any]) -> None:
        """
        Validate Salesforce API response and raise appropriate errors.
        
        Args:
            response: Processed response dictionary
            
        Raises:
            SalesforceAPIError: If response contains Salesforce API errors
        """
        # Check for various Salesforce error patterns
        error_patterns = [
            # Standard Salesforce API error format
            ('errorCode', 'message'),
            # Alternative error formats
            ('error', 'error_description'),
            ('error_code', 'error_message'),
            # SOQL query errors
            ('errors', None),  # Array of error objects
            # Authentication errors
            ('error', 'error_description')
        ]
        
        for error_key, message_key in error_patterns:
            if error_key in response and response[error_key]:
                error_value = response[error_key]
                
                # Handle array of errors (SOQL errors)
                if isinstance(error_value, list) and error_value:
                    error_obj = error_value[0]  # Take first error
                    error_code = error_obj.get('errorCode', 'UNKNOWN_ERROR')
                    error_message = error_obj.get('message', 'Unknown Salesforce error')
                elif isinstance(error_value, str):
                    error_code = error_value
                    error_message = response.get(message_key, 'Unknown Salesforce error') if message_key else error_value
                else:
                    error_code = str(error_value)
                    error_message = response.get(message_key, 'Unknown Salesforce error') if message_key else str(error_value)
                
                logger.error(
                    f"Salesforce API error detected: {error_code} - {error_message}",
                    extra={
                        "error_code": error_code,
                        "error_message": error_message,
                        "full_response": response
                    }
                )
                
                raise SalesforceAPIError(error_code, error_message, response)
        
        # Check for success=false pattern
        if 'success' in response and response['success'] is False:
            error_message = response.get('message', 'Salesforce operation failed')
            logger.error(
                f"Salesforce operation failed: {error_message}",
                extra={"full_response": response}
            )
            raise SalesforceAPIError('OPERATION_FAILED', error_message, response)
        
        # Check for empty records with error indicators
        if 'records' in response and not response['records'] and 'done' in response and not response['done']:
            logger.warning(
                "Salesforce query returned no records but indicates more data available - possible query issue",
                extra={"full_response": response}
            )
    
    def _optimize_query_for_salesforce(self, operation: str, **params) -> Optional[str]:
        """
        Generate optimized SOQL queries for better data retrieval performance.
        
        Args:
            operation: The operation being performed
            **params: Parameters for the query
            
        Returns:
            Optimized SOQL query string or None if no optimization available
        """
        if not self.salesforce_settings.get('query_optimization', False):
            return None
        
        query_template = None
        
        if operation == 'get_accounts' and params.get('account_name'):
            query_template = self.optimized_queries['get_accounts_by_name']
            self._query_optimization_count += 1
        elif operation == 'get_opportunities':
            query_template = self.optimized_queries['get_recent_opportunities']
            self._query_optimization_count += 1
        elif operation == 'get_contacts' and params.get('account_name'):
            query_template = self.optimized_queries['get_contacts_by_account']
            self._query_optimization_count += 1
        
        if query_template:
            try:
                # Format the query with provided parameters
                formatted_query = query_template.format(
                    account_name=params.get('account_name', ''),
                    limit=params.get('limit', 5)
                ).strip()
                
                logger.info(
                    f"Using optimized SOQL query for {operation}",
                    extra={
                        "operation": operation,
                        "query_length": len(formatted_query),
                        "optimization_count": self._query_optimization_count
                    }
                )
                
                return formatted_query
            except KeyError as e:
                logger.warning(f"Failed to format optimized query: missing parameter {e}")
                return None
        
        return None
    
    async def _call_mcp_tool_with_retry(
        self, 
        service: str, 
        tool_name: str, 
        arguments: Dict[str, Any],
        max_retries: int = None
    ) -> Dict[str, Any]:
        """
        Call MCP tool with enhanced retry logic and error handling.
        
        Args:
            service: Service name
            tool_name: MCP tool name
            arguments: Tool arguments
            max_retries: Maximum retry attempts (uses service default if None)
            
        Returns:
            Processed result dictionary
            
        Raises:
            MCPHTTPError: If all retry attempts fail
            SalesforceAPIError: If Salesforce API returns an error
        """
        if max_retries is None:
            service_config = self.supported_services.get(service, {})
            settings = service_config.get('settings', {})
            max_retries = settings.get('max_retries', 3)
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                self._call_count += 1
                
                logger.info(
                    f"Calling {service} MCP tool: {tool_name} (attempt {attempt + 1}/{max_retries})",
                    extra={
                        "service": service,
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "attempt": attempt + 1,
                        "max_retries": max_retries
                    }
                )
                
                # Call MCP tool through HTTP manager
                result = await self.mcp_manager.call_tool(service, tool_name, arguments)
                
                # Process and validate result
                processed_result = self._process_mcp_result(result, service)
                
                # Track successful call
                self._last_successful_call = datetime.now()
                
                logger.info(
                    f"Successfully called {service} MCP tool: {tool_name}",
                    extra={
                        "service": service,
                        "tool_name": tool_name,
                        "attempt": attempt + 1,
                        "success": True
                    }
                )
                
                return processed_result
                
            except (MCPHTTPConnectionError, MCPHTTPTimeoutError) as e:
                last_exception = e
                self._error_count += 1
                
                logger.warning(
                    f"MCP connection/timeout error on attempt {attempt + 1}/{max_retries}: {e}",
                    extra={
                        "service": service,
                        "tool_name": tool_name,
                        "attempt": attempt + 1,
                        "error_type": type(e).__name__,
                        "error": str(e)
                    }
                )
                
                # Don't retry on the last attempt
                if attempt == max_retries - 1:
                    break
                
                # Exponential backoff with jitter
                backoff_time = min(1.5 * (1.5 ** attempt), 20.0)
                jitter = 0.1 * backoff_time * (0.5 + 0.5 * hash(str(arguments)) % 100 / 100)
                sleep_time = backoff_time + jitter
                
                logger.info(f"Retrying in {sleep_time:.1f}s...")
                await asyncio.sleep(sleep_time)
                
            except SalesforceAPIError as e:
                # Don't retry Salesforce API errors - they're usually permanent
                self._error_count += 1
                logger.error(
                    f"Salesforce API error (not retrying): {e}",
                    extra={
                        "service": service,
                        "tool_name": tool_name,
                        "error_code": e.error_code,
                        "error_message": e.error_message
                    }
                )
                raise
                
            except Exception as e:
                last_exception = e
                self._error_count += 1
                
                logger.error(
                    f"Unexpected error on attempt {attempt + 1}/{max_retries}: {e}",
                    extra={
                        "service": service,
                        "tool_name": tool_name,
                        "attempt": attempt + 1,
                        "error_type": type(e).__name__,
                        "error": str(e)
                    }
                )
                
                # Don't retry on the last attempt
                if attempt == max_retries - 1:
                    break
                
                # Short backoff for unexpected errors
                await asyncio.sleep(1.0 * (attempt + 1))
        
        # All retries exhausted
        logger.error(
            f"All {max_retries} retry attempts exhausted for {service} tool {tool_name}",
            extra={
                "service": service,
                "tool_name": tool_name,
                "max_retries": max_retries,
                "last_error": str(last_exception)
            }
        )
        
        raise MCPHTTPError(
            f"Failed to call {service} tool {tool_name} after {max_retries} attempts: {last_exception}",
            service,
            "MAX_RETRIES_EXHAUSTED"
        )
    
    async def get_accounts(
        self,
        service: str = 'salesforce',
        account_name: str = None,
        limit: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get accounts from specified CRM service with enhanced error handling and query optimization.
        
        Args:
            service: CRM service to use ('salesforce', 'hubspot', etc.)
            account_name: Filter by account name (optional)
            limit: Maximum number of accounts to return
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing account list and metadata
            
        Raises:
            MCPHTTPError: If HTTP MCP tool call fails
            SalesforceAPIError: If Salesforce API returns an error
            ValueError: If service not supported
        """
        try:
            # Try to use optimized SOQL query for Salesforce
            if service == 'salesforce' and account_name:
                optimized_query = self._optimize_query_for_salesforce(
                    'get_accounts', 
                    account_name=account_name, 
                    limit=limit
                )
                
                if optimized_query:
                    logger.info(f"Using optimized query for account search: {account_name}")
                    return await self.run_soql_query(
                        soql_query=optimized_query,
                        service=service,
                        **kwargs
                    )
            
            # Fall back to standard tool call
            tool_name = self._get_tool_name(service, 'get_accounts')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'limit': limit,
                **kwargs
            }
            
            # Add optional filters if provided
            if account_name:
                arguments['account_name'] = account_name
            
            # Normalize parameters for MCP tool
            normalized_arguments = self._normalize_parameters(service, 'get_accounts', arguments)
            
            logger.info(
                f"Getting accounts via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "limit": limit,
                    "account_name": account_name
                }
            )
            
            # Call MCP tool with enhanced retry logic
            result = await self._call_mcp_tool_with_retry(service, tool_name, normalized_arguments)
            
            logger.info(
                f"Successfully retrieved accounts from {service}",
                extra={
                    "service": service,
                    "account_count": len(result.get('records', [])),
                    "success": True
                }
            )
            
            return result
            
        except (SalesforceAPIError, MCPHTTPError):
            # Re-raise specific errors without wrapping
            raise
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
        stage: str = None,
        limit: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get opportunities from specified CRM service with enhanced error handling and query optimization.
        
        Args:
            service: CRM service to use ('salesforce', 'hubspot', etc.)
            stage: Filter by opportunity stage (optional)
            limit: Maximum number of opportunities to return
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing opportunity list and metadata
            
        Raises:
            MCPHTTPError: If HTTP MCP tool call fails
            SalesforceAPIError: If Salesforce API returns an error
            ValueError: If service not supported
        """
        try:
            # Try to use optimized SOQL query for Salesforce (recent opportunities)
            if service == 'salesforce' and not stage:  # Use optimization for general queries
                optimized_query = self._optimize_query_for_salesforce(
                    'get_opportunities', 
                    limit=limit
                )
                
                if optimized_query:
                    logger.info("Using optimized query for recent opportunities")
                    return await self.run_soql_query(
                        soql_query=optimized_query,
                        service=service,
                        **kwargs
                    )
            
            # Fall back to standard tool call
            tool_name = self._get_tool_name(service, 'get_opportunities')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'limit': limit,
                **kwargs
            }
            
            # Add optional filters if provided
            if stage:
                arguments['stage'] = stage
            
            # Normalize parameters for MCP tool
            normalized_arguments = self._normalize_parameters(service, 'get_opportunities', arguments)
            
            logger.info(
                f"Getting opportunities via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "limit": limit,
                    "stage": stage
                }
            )
            
            # Call MCP tool with enhanced retry logic
            result = await self._call_mcp_tool_with_retry(service, tool_name, normalized_arguments)
            
            logger.info(
                f"Successfully retrieved opportunities from {service}",
                extra={
                    "service": service,
                    "opportunity_count": len(result.get('records', [])),
                    "success": True
                }
            )
            
            return result
            
        except (SalesforceAPIError, MCPHTTPError):
            # Re-raise specific errors without wrapping
            raise
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
        account_name: str = None,
        limit: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get contacts from specified CRM service with enhanced error handling and query optimization.
        
        Args:
            service: CRM service to use ('salesforce', 'hubspot', etc.)
            account_name: Filter by account name (optional)
            limit: Maximum number of contacts to return
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing contact list and metadata
            
        Raises:
            MCPHTTPError: If HTTP MCP tool call fails
            SalesforceAPIError: If Salesforce API returns an error
            ValueError: If service not supported
        """
        try:
            # Try to use optimized SOQL query for Salesforce
            if service == 'salesforce' and account_name:
                optimized_query = self._optimize_query_for_salesforce(
                    'get_contacts', 
                    account_name=account_name, 
                    limit=limit
                )
                
                if optimized_query:
                    logger.info(f"Using optimized query for contact search: {account_name}")
                    return await self.run_soql_query(
                        soql_query=optimized_query,
                        service=service,
                        **kwargs
                    )
            
            # Fall back to standard tool call
            tool_name = self._get_tool_name(service, 'get_contacts')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'limit': limit,
                **kwargs
            }
            
            # Add optional filters if provided
            if account_name:
                arguments['account_name'] = account_name
            
            # Normalize parameters for MCP tool
            normalized_arguments = self._normalize_parameters(service, 'get_contacts', arguments)
            
            logger.info(
                f"Getting contacts via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "limit": limit,
                    "account_name": account_name
                }
            )
            
            # Call MCP tool with enhanced retry logic
            result = await self._call_mcp_tool_with_retry(service, tool_name, normalized_arguments)
            
            logger.info(
                f"Successfully retrieved contacts from {service}",
                extra={
                    "service": service,
                    "contact_count": len(result.get('records', [])),
                    "success": True
                }
            )
            
            return result
            
        except (SalesforceAPIError, MCPHTTPError):
            # Re-raise specific errors without wrapping
            raise
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
        objects: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search records in specified CRM service with enhanced error handling.
        
        Args:
            search_term: Search query string
            service: CRM service to use ('salesforce', 'hubspot', etc.)
            objects: List of object types to search (e.g., ['Account', 'Contact'])
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing search results
            
        Raises:
            MCPHTTPError: If HTTP MCP tool call fails
            SalesforceAPIError: If Salesforce API returns an error
            ValueError: If service not supported or search_term missing
        """
        if not search_term:
            raise ValueError("search_term is required for searching records")
        
        try:
            tool_name = self._get_tool_name(service, 'search_records')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'search_term': search_term,
                **kwargs
            }
            
            # Add optional object types if provided
            if objects:
                arguments['objects'] = objects
            
            # Normalize parameters for MCP tool
            normalized_arguments = self._normalize_parameters(service, 'search_records', arguments)
            
            logger.info(
                f"Searching records via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "search_term": search_term,
                    "objects": objects
                }
            )
            
            # Call MCP tool with enhanced retry logic
            result = await self._call_mcp_tool_with_retry(service, tool_name, normalized_arguments)
            
            logger.info(
                f"Successfully searched records in {service}",
                extra={
                    "service": service,
                    "search_term": search_term,
                    "result_count": len(result.get('records', result.get('results', []))),
                    "success": True
                }
            )
            
            return result
            
        except (SalesforceAPIError, MCPHTTPError):
            # Re-raise specific errors without wrapping
            raise
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
        soql_query: str = None,
        query: str = None,
        service: str = 'salesforce',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run SOQL query in Salesforce with enhanced error handling (Salesforce-specific operation).
        
        Args:
            soql_query: SOQL query string (user-friendly parameter name)
            query: SOQL query string (alternative parameter name for backward compatibility)
            service: Must be 'salesforce' for SOQL queries
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing query results
            
        Raises:
            MCPHTTPError: If HTTP MCP tool call fails
            SalesforceAPIError: If Salesforce API returns an error
            ValueError: If service is not Salesforce or query missing
        """
        # Accept either soql_query or query parameter
        actual_query = soql_query or query
        
        if not actual_query:
            raise ValueError("soql_query or query is required for SOQL operations")
        
        if service != 'salesforce':
            raise ValueError("SOQL queries are only supported on Salesforce service")
        
        try:
            tool_name = self._get_tool_name(service, 'run_soql_query')
            
            # Prepare arguments for MCP tool call
            # Note: Using 'soql_query' as user-friendly parameter name
            arguments = {
                'soql_query': actual_query,  # This will be normalized to 'query' for MCP tool
                **kwargs
            }
            
            # Normalize parameters for MCP tool (soql_query -> query)
            normalized_arguments = self._normalize_parameters(service, 'run_soql_query', arguments)
            
            logger.info(
                f"Running SOQL query via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "query": actual_query[:100] + "..." if len(actual_query) > 100 else actual_query
                }
            )
            
            # Call MCP tool with enhanced retry logic
            result = await self._call_mcp_tool_with_retry(service, tool_name, normalized_arguments)
            
            logger.info(
                f"Successfully executed SOQL query in {service}",
                extra={
                    "service": service,
                    "record_count": len(result.get('records', [])),
                    "success": True
                }
            )
            
            return result
            
        except (SalesforceAPIError, MCPHTTPError):
            # Re-raise specific errors without wrapping
            raise
        except Exception as e:
            logger.error(
                f"Failed to run SOQL query in {service}: {e}",
                extra={
                    "service": service,
                    "query": actual_query[:100] + "..." if len(actual_query) > 100 else actual_query,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"SOQL query failed: {e}", service, "SOQL_QUERY_FAILED")
    
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
            'service_id': service,
            'transport': 'http',
            'settings': service_config.get('settings', {})
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the CRM agent.
        
        Returns:
            Dictionary containing performance metrics
        """
        success_rate = 0.0
        if self._call_count > 0:
            success_rate = (self._call_count - self._error_count) / self._call_count
        
        return {
            'total_calls': self._call_count,
            'error_count': self._error_count,
            'success_rate': success_rate,
            'last_successful_call': self._last_successful_call.isoformat() if self._last_successful_call else None,
            'query_optimization_count': self._query_optimization_count,
            'supported_services': self.get_supported_services(),
            'salesforce_settings': self.salesforce_settings
        }
    
    async def check_service_health(self, service: str) -> Dict[str, Any]:
        """
        Check health status of a specific CRM service with enhanced diagnostics.
        
        Args:
            service: Service name to check
            
        Returns:
            Dictionary containing health status
        """
        try:
            self._validate_service(service)
            
            # Get health status from HTTP MCP manager
            health_status = await self.mcp_manager.get_service_health(service)
            
            # Enhanced health check for Salesforce
            enhanced_status = {
                'service': service,
                'is_healthy': health_status.is_healthy,
                'last_check': health_status.last_check.isoformat(),
                'response_time_ms': health_status.response_time_ms,
                'available_tools': health_status.available_tools,
                'error_message': health_status.error_message,
                'connection_status': health_status.connection_status,
                'transport': 'http'
            }
            
            # Add service-specific diagnostics
            if service == 'salesforce':
                enhanced_status.update({
                    'salesforce_specific': {
                        'max_retries': self.salesforce_settings['max_retries'],
                        'timeout': self.salesforce_settings['timeout'],
                        'connection_pool_size': self.salesforce_settings['connection_pool_size'],
                        'query_optimization': self.salesforce_settings['query_optimization']
                    }
                })
                
                # Try a simple API call to verify Salesforce connectivity
                if health_status.is_healthy:
                    try:
                        # Test with a simple SOQL query (should be fast)
                        test_query = "SELECT Id, Name FROM Account LIMIT 1"
                        test_result = await asyncio.wait_for(
                            self.run_soql_query(soql_query=test_query, service='salesforce'),
                            timeout=15.0  # Short timeout for health check
                        )
                        enhanced_status['api_test'] = {
                            'success': True,
                            'test_type': 'soql_query',
                            'response_received': True,
                            'record_count': len(test_result.get('records', []))
                        }
                    except asyncio.TimeoutError:
                        enhanced_status['api_test'] = {
                            'success': False,
                            'test_type': 'soql_query',
                            'error': 'Timeout after 15s'
                        }
                        enhanced_status['is_healthy'] = False
                    except SalesforceAPIError as e:
                        enhanced_status['api_test'] = {
                            'success': False,
                            'test_type': 'soql_query',
                            'error': f'Salesforce API Error: {e.error_code} - {e.error_message}'
                        }
                        # API errors might indicate auth issues, but connection is working
                        enhanced_status['connection_status'] = 'connected_with_api_errors'
                    except Exception as e:
                        enhanced_status['api_test'] = {
                            'success': False,
                            'test_type': 'soql_query',
                            'error': str(e)
                        }
                        enhanced_status['is_healthy'] = False
            
            return enhanced_status
            
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
                'connection_status': 'failed',
                'transport': 'http'
            }


# Global instance for easy access
_crm_agent_http: Optional[CRMAgentHTTP] = None


def get_crm_agent_http() -> CRMAgentHTTP:
    """
    Get or create global HTTP CRM Agent instance.
    
    Returns:
        CRMAgentHTTP instance
    """
    global _crm_agent_http
    
    if _crm_agent_http is None:
        _crm_agent_http = CRMAgentHTTP()
    
    return _crm_agent_http