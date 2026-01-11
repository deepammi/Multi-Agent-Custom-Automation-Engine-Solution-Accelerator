"""
Category-Based Email Agent for Multi-Service Email Operations.

This agent replaces brand-specific email agents (GmailAgent) with a unified
category-based approach that accepts service parameters to route operations
to appropriate email service backends.

**Feature: mcp-http-transport-migration, HTTP Transport**
**Validates: Requirements 2.1, 2.5**
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.mcp_http_client import get_mcp_http_manager, MCPHTTPError

logger = logging.getLogger(__name__)


class EmailAgent:
    """
    Category-based agent for email operations across multiple services.
    
    This agent provides a unified interface for email operations while supporting
    multiple email service providers through service parameters. It uses proper
    MCP protocol for all external service communications.
    
    Supported Services:
    - gmail: Google Gmail via MCP
    - outlook: Microsoft Outlook via MCP (future)
    - exchange: Microsoft Exchange via MCP (future)
    """
    
    def __init__(self, mcp_manager=None):
        """
        Initialize Email Agent with HTTP MCP client manager.
        
        Args:
            mcp_manager: HTTP MCP client manager instance (optional, will use global if None)
        """
        self.mcp_manager = mcp_manager or get_mcp_http_manager()
        self.supported_services = {
            'gmail': {
                'name': 'Gmail',
                'display_name': 'Google Gmail',
                'tools': {
                    'list_messages': 'gmail_list_messages',
                    'send_message': 'gmail_send_message', 
                    'get_message': 'gmail_get_message',
                    'search_messages': 'gmail_search_messages',
                    'get_profile': 'gmail_get_profile'
                },
                'search_operators': {
                    'from': 'from:',
                    'to': 'to:',
                    'subject': 'subject:',
                    'newer_than': 'newer_than:',
                    'older_than': 'older_than:',
                    'has_attachment': 'has:attachment',
                    'is_unread': 'is:unread',
                    'is_important': 'is:important'
                }
            },
            # Future Outlook support - ready for implementation
            'outlook': {
                'name': 'Outlook',
                'display_name': 'Microsoft Outlook',
                'tools': {
                    'list_messages': 'outlook_list_messages',
                    'send_message': 'outlook_send_message',
                    'get_message': 'outlook_get_message', 
                    'search_messages': 'outlook_search_messages',
                    'get_profile': 'outlook_get_profile'
                },
                'search_operators': {
                    'from': 'from:',
                    'to': 'to:',
                    'subject': 'subject:',
                    'received': 'received:',
                    'sent': 'sent:',
                    'has_attachment': 'hasattachment:true',
                    'is_unread': 'isread:false',
                    'importance': 'importance:'
                }
            },
            # Future Exchange support - ready for implementation
            'exchange': {
                'name': 'Exchange',
                'display_name': 'Microsoft Exchange',
                'tools': {
                    'list_messages': 'exchange_list_messages',
                    'send_message': 'exchange_send_message',
                    'get_message': 'exchange_get_message',
                    'search_messages': 'exchange_search_messages',
                    'get_profile': 'exchange_get_profile'
                },
                'search_operators': {
                    'from': 'from:',
                    'to': 'to:',
                    'subject': 'subject:',
                    'received': 'received:',
                    'sent': 'sent:',
                    'has_attachment': 'hasattachment:true',
                    'is_unread': 'isread:false'
                }
            }
        }
        
        logger.info(
            "Email Agent initialized with multi-provider support",
            extra={
                "supported_services": list(self.supported_services.keys()),
                "default_service": "gmail",
                "total_services": len(self.supported_services)
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
                f"Unsupported email service: '{service}'. "
                f"Supported services: {supported}"
            )
    
    def _get_tool_name(self, service: str, operation: str) -> str:
        """
        Get the MCP tool name for a service operation.
        
        Args:
            service: Service name (e.g., 'gmail')
            operation: Operation name (e.g., 'list_messages')
            
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
    
    async def list_messages(
        self, 
        service: str = 'gmail',
        max_results: int = 10,
        query: str = "",
        **kwargs
        ) -> Dict[str, Any]:
        """
        List email messages from specified email service.
        
        Args:
            service: Email service to use ('gmail', 'outlook', etc.)
            max_results: Maximum number of messages to return
            query: Search query to filter messages
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing message list and metadata
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported
        """
        try:
            tool_name = self._get_tool_name(service, 'list_messages')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'max_results': max_results,
                'query': query,
                **kwargs
            }
            
            logger.info(
                f"Listing messages via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "max_results": max_results,
                    "query": query
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully listed messages from {service}",
                extra={
                    "service": service,
                    "message_count": len(result.get('messages', [])),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to list messages from {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Email listing failed: {e}", service, "LIST_MESSAGES_FAILED")
    
    async def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        service: str = 'gmail',
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        **kwargs
        ) -> Dict[str, Any]:
        """
        Send an email message via specified email service.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            service: Email service to use ('gmail', 'outlook', etc.)
            cc: Optional CC recipient
            bcc: Optional BCC recipient
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing send result and message metadata
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported or required parameters missing
        """
        # Validate required parameters
        if not to or not subject:
            raise ValueError("Both 'to' and 'subject' are required for sending email")
        
        try:
            tool_name = self._get_tool_name(service, 'send_message')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'to': to,
                'subject': subject,
                'body': body or "",
                **kwargs
            }
            
            # Add optional parameters if provided
            if cc:
                arguments['cc'] = cc
            if bcc:
                arguments['bcc'] = bcc
            
            logger.info(
                f"Sending message via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "to": to,
                    "subject": subject,
                    "has_cc": cc is not None,
                    "has_bcc": bcc is not None
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully sent message via {service}",
                extra={
                    "service": service,
                    "to": to,
                    "subject": subject,
                    "message_id": result.get('id', 'unknown'),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to send message via {service}: {e}",
                extra={
                    "service": service,
                    "to": to,
                    "subject": subject,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Email sending failed: {e}", service, "SEND_MESSAGE_FAILED")
    
    async def get_message(
        self,
        message_id: str,
        service: str = 'gmail',
        include_body_html: bool = False,
        **kwargs
        ) -> Dict[str, Any]:
        """
        Get a specific email message from specified email service.
        
        Args:
            message_id: Unique message identifier
            service: Email service to use ('gmail', 'outlook', etc.)
            include_body_html: Whether to include HTML body content
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing message details
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported or message_id missing
        """
        if not message_id:
            raise ValueError("message_id is required for getting email message")
        
        try:
            tool_name = self._get_tool_name(service, 'get_message')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'message_id': message_id,
                'include_body_html': include_body_html,
                **kwargs
            }
            
            logger.info(
                f"Getting message via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "message_id": message_id,
                    "include_body_html": include_body_html
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully retrieved message from {service}",
                extra={
                    "service": service,
                    "message_id": message_id,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to get message from {service}: {e}",
                extra={
                    "service": service,
                    "message_id": message_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Email retrieval failed: {e}", service, "GET_MESSAGE_FAILED")
    
    async def search_messages(
        self,
        query: str,
        service: str = 'gmail',
        max_results: int = 10,
        **kwargs
        ) -> Dict[str, Any]:
        """
        Search email messages in specified email service.
        
        Args:
            query: Search query string
            service: Email service to use ('gmail', 'outlook', etc.)
            max_results: Maximum number of results to return
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing search results
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported or query missing
        """
        if not query:
            raise ValueError("query is required for searching email messages")
        
        try:
            tool_name = self._get_tool_name(service, 'search_messages')
            
            # Prepare arguments for MCP tool call
            arguments = {
                'query': query,
                'max_results': max_results,
                **kwargs
            }
            
            logger.info(
                f"Searching messages via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name,
                    "query": query,
                    "max_results": max_results
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully searched messages in {service}",
                extra={
                    "service": service,
                    "query": query,
                    "result_count": len(result.get('messages', [])),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to search messages in {service}: {e}",
                extra={
                    "service": service,
                    "query": query,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Email search failed: {e}", service, "SEARCH_MESSAGES_FAILED")
    
    async def get_profile(
        self,
        service: str = 'gmail',
        **kwargs
        ) -> Dict[str, Any]:
        """
        Get user profile information from specified email service.
        
        Args:
            service: Email service to use ('gmail', 'outlook', etc.)
            **kwargs: Additional service-specific parameters
            
        Returns:
            Dictionary containing profile information
            
        Raises:
            MCPError: If MCP tool call fails
            ValueError: If service not supported
        """
        try:
            tool_name = self._get_tool_name(service, 'get_profile')
            
            # Prepare arguments for MCP tool call
            arguments = kwargs
            
            logger.info(
                f"Getting profile via {service}",
                extra={
                    "service": service,
                    "tool_name": tool_name
                }
            )
            
            # Call MCP tool through manager
            result = await self.mcp_manager.call_tool(service, tool_name, arguments)
            
            logger.info(
                f"Successfully retrieved profile from {service}",
                extra={
                    "service": service,
                    "email": result.get('emailAddress', 'unknown'),
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to get profile from {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise MCPHTTPError(f"Profile retrieval failed: {e}", service, "GET_PROFILE_FAILED")
    
    def get_supported_services(self) -> List[str]:
        """
        Get list of supported email services.
        
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
            'display_name': service_config.get('display_name', service_config['name']),
            'operations': list(service_config['tools'].keys()),
            'service_id': service,
            'search_operators': service_config.get('search_operators', {})
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
        Check health status of a specific email service.
        
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
        Check health status of all supported email services.
        
        Returns:
            Dictionary mapping service names to their health status
        """
        health_results = {}
        
        for service in self.supported_services.keys():
            health_results[service] = await self.check_service_health(service)
        
        return health_results


    def get_search_operators(self, service: str) -> Dict[str, str]:
        """
        Get search operators for a specific email service.
        
        Args:
            service: Service name
            
        Returns:
            Dictionary mapping operator names to their syntax
            
        Raises:
            ValueError: If service not supported
        """
        self._validate_service(service)
        
        service_config = self.supported_services[service]
        return service_config.get('search_operators', {})
    
    def build_search_query(self, service: str, **criteria) -> str:
        """
        Build a search query using service-specific operators.
        
        Args:
            service: Service name
            **criteria: Search criteria (from_email, to_email, subject, etc.)
            
        Returns:
            Formatted search query string
            
        Raises:
            ValueError: If service not supported
        """
        operators = self.get_search_operators(service)
        query_parts = []
        
        # Map common criteria to service-specific operators
        criteria_mapping = {
            'from_email': 'from',
            'to_email': 'to', 
            'subject_contains': 'subject',
            'newer_than': 'newer_than',
            'older_than': 'older_than',
            'has_attachment': 'has_attachment',
            'is_unread': 'is_unread'
        }
        
        for criterion, value in criteria.items():
            if criterion in criteria_mapping:
                operator_key = criteria_mapping[criterion]
                if operator_key in operators:
                    operator = operators[operator_key]
                    
                    # Handle boolean operators
                    if isinstance(value, bool):
                        if value:
                            query_parts.append(operator)
                    else:
                        query_parts.append(f"{operator}{value}")
            elif criterion == 'keywords':
                # Add keywords directly
                if isinstance(value, list):
                    query_parts.extend(value)
                else:
                    query_parts.append(str(value))
        
        return ' '.join(query_parts)
    
    def is_service_available(self, service: str) -> bool:
        """
        Check if a service is available for use.
        
        Args:
            service: Service name
            
        Returns:
            True if service is available, False otherwise
        """
        try:
            self._validate_service(service)
            # Could add additional availability checks here
            # (e.g., MCP server health, authentication status)
            return True
        except ValueError:
            return False


# Global instance for backward compatibility and easy access
_email_agent: Optional[EmailAgent] = None


def get_email_agent() -> EmailAgent:
    """
    Get or create global Email Agent instance.
    
    Returns:
        EmailAgent instance
    """
    global _email_agent
    
    if _email_agent is None:
        _email_agent = EmailAgent()
    
    return _email_agent


# Backward compatibility wrapper for existing Gmail-specific code
class GmailAgentLegacy:
    """
    Legacy wrapper that maintains Gmail-specific interface while using
    the new category-based Email Agent internally.
    
    This allows existing code to work without changes while benefiting
    from proper MCP protocol implementation.
    """
    
    def __init__(self):
        self._email_agent = get_email_agent()
        self.service = 'gmail'  # Fixed to Gmail for backward compatibility
        
        logger.warning(
            "Using legacy GmailAgentLegacy wrapper. "
            "Consider migrating to EmailAgent for multi-service support."
        )
    
    async def list_messages(self, max_results: int = 10, query: str = "") -> Dict[str, Any]:
        """Legacy interface for listing Gmail messages."""
        return await self._email_agent.list_messages(
            service=self.service,
            max_results=max_results,
            query=query
        )
    
    async def send_message(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        cc: Optional[str] = None
    ) -> Dict[str, Any]:
        """Legacy interface for sending Gmail messages."""
        return await self._email_agent.send_message(
            to=to,
            subject=subject,
            body=body,
            service=self.service,
            cc=cc
        )
    
    async def get_message(
        self, 
        message_id: str, 
        include_body_html: bool = False
    ) -> Dict[str, Any]:
        """Legacy interface for getting Gmail messages."""
        return await self._email_agent.get_message(
            message_id=message_id,
            service=self.service,
            include_body_html=include_body_html
        )
    
    async def search_messages(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Legacy interface for searching Gmail messages."""
        return await self._email_agent.search_messages(
            query=query,
            service=self.service,
            max_results=max_results
        )
    
    async def get_profile(self) -> Dict[str, Any]:
        """Legacy interface for getting Gmail profile."""
        return await self._email_agent.get_profile(service=self.service)


def get_gmail_agent() -> GmailAgentLegacy:
    """
    Get Gmail agent instance for backward compatibility.
    
    Returns:
        GmailAgentLegacy instance that wraps EmailAgent
    """
    return GmailAgentLegacy()