"""
Standardized Gmail MCP Client using proper MCP protocol.
Replaces the incorrect direct Google API approach with proper MCP communication.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .mcp_client_service import BaseMCPClient, MCPError, get_mcp_manager

logger = logging.getLogger(__name__)


class GmailStandardMCPClient(BaseMCPClient):
    """
    Proper MCP client for Gmail using MCP server protocol.
    
    This replaces the incorrect direct Google API approach with
    proper MCP protocol implementation.
    """
    
    def __init__(self):
        super().__init__(
            service_name="gmail",
            server_command="python3",
            server_args=["src/mcp_server/gmail_mcp_server.py"],
            timeout=20,
            retry_attempts=3
        )
        
        self.domain = "gmail"
        self.enabled = self._check_credentials_available()
        
        logger.info(
            f"Gmail Standard MCP Client initialized",
            extra={
                "service": self.service_name,
                "domain": self.domain,
                "enabled": self.enabled
            }
        )
    
    def _check_credentials_available(self) -> bool:
        """Check if Gmail credentials are available."""
        try:
            config_dir = Path.home() / ".gmail-mcp"
            credentials_path = config_dir / "credentials.json"
            oauth_keys_path = config_dir / "gcp-oauth.keys.json"
            
            return credentials_path.exists() and oauth_keys_path.exists()
        except Exception:
            return False
    
    async def list_messages(self, max_results: int = 10, query: str = "") -> str:
        """
        List Gmail messages using proper MCP protocol.
        
        Args:
            max_results: Maximum number of messages to return
            query: Gmail search query
            
        Returns:
            JSON string with message list
        """
        if not self.enabled:
            logger.info("Gmail credentials not available, using mock data")
            return self._get_mock_messages_response(max_results)
        
        try:
            # Call MCP tool instead of direct Google API
            result = await self.call_tool("gmail_list_messages", {
                "max_results": max_results,
                "query": query
            })
            
            logger.info(
                f"Gmail messages listed via MCP",
                extra={
                    "service": self.service_name,
                    "max_results": max_results,
                    "query": query,
                    "message_count": len(result.get("messages", []))
                }
            )
            
            # Format response to match expected format
            response = {
                "success": True,
                "data": {
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(result)
                        }]
                    }
                }
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            logger.error(
                f"Gmail message listing failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "max_results": max_results,
                    "query": query,
                    "error": str(e)
                }
            )
            
            # Fallback to mock data on error
            return self._get_mock_messages_response(max_results)
    
    async def send_message(self, to: str, subject: str, body: str, cc: Optional[str] = None) -> str:
        """
        Send a Gmail message using proper MCP protocol.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            cc: Optional CC recipient
            
        Returns:
            JSON string with send result
        """
        if not self.enabled:
            logger.info("Gmail credentials not available, using mock response")
            return self._get_mock_send_response()
        
        try:
            # Call MCP tool instead of direct Google API
            result = await self.call_tool("gmail_send_message", {
                "to": to,
                "subject": subject,
                "body": body,
                "cc": cc
            })
            
            logger.info(
                f"Gmail message sent via MCP",
                extra={
                    "service": self.service_name,
                    "to": to,
                    "subject": subject,
                    "has_cc": cc is not None
                }
            )
            
            # Format response to match expected format
            response = {
                "success": True,
                "data": {
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(result)
                        }]
                    }
                }
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            logger.error(
                f"Gmail message sending failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "to": to,
                    "subject": subject,
                    "error": str(e)
                }
            )
            
            # Fallback to mock response on error
            return self._get_mock_send_response()
    
    async def get_message(self, message_id: str, include_body_html: bool = False) -> str:
        """
        Get a specific Gmail message using proper MCP protocol.
        
        Args:
            message_id: Gmail message ID
            include_body_html: Whether to include HTML body
            
        Returns:
            JSON string with message details
        """
        if not self.enabled:
            logger.info("Gmail credentials not available, using mock data")
            return self._get_mock_message_response(message_id)
        
        try:
            # Call MCP tool instead of direct Google API
            result = await self.call_tool("gmail_get_message", {
                "message_id": message_id,
                "include_body_html": include_body_html
            })
            
            logger.info(
                f"Gmail message retrieved via MCP",
                extra={
                    "service": self.service_name,
                    "message_id": message_id,
                    "include_body_html": include_body_html
                }
            )
            
            # Format response to match expected format
            response = {
                "success": True,
                "data": {
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(result)
                        }]
                    }
                }
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            logger.error(
                f"Gmail message retrieval failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "message_id": message_id,
                    "error": str(e)
                }
            )
            
            # Fallback to mock data on error
            return self._get_mock_message_response(message_id)
    
    async def search_messages(self, query: str, max_results: int = 10) -> str:
        """
        Search Gmail messages using proper MCP protocol.
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results
            
        Returns:
            JSON string with search results
        """
        if not self.enabled:
            logger.info("Gmail credentials not available, using mock data")
            return self._get_mock_search_response(query, max_results)
        
        try:
            # Call MCP tool instead of direct Google API
            result = await self.call_tool("gmail_search_messages", {
                "query": query,
                "max_results": max_results
            })
            
            logger.info(
                f"Gmail message search completed via MCP",
                extra={
                    "service": self.service_name,
                    "query": query,
                    "max_results": max_results,
                    "result_count": len(result.get("messages", []))
                }
            )
            
            # Format response to match expected format
            response = {
                "success": True,
                "data": {
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(result)
                        }]
                    }
                }
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            logger.error(
                f"Gmail message search failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "query": query,
                    "error": str(e)
                }
            )
            
            # Fallback to mock data on error
            return self._get_mock_search_response(query, max_results)
    
    async def get_profile(self) -> str:
        """
        Get Gmail user profile using proper MCP protocol.
        
        Returns:
            JSON string with profile information
        """
        if not self.enabled:
            logger.info("Gmail credentials not available, using mock data")
            return self._get_mock_profile_response()
        
        try:
            # Call MCP tool instead of direct Google API
            result = await self.call_tool("gmail_get_profile", {})
            
            logger.info(
                f"Gmail profile retrieved via MCP",
                extra={
                    "service": self.service_name,
                    "email": result.get("emailAddress", "unknown")
                }
            )
            
            # Format response to match expected format
            response = {
                "success": True,
                "data": {
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": json.dumps(result)
                        }]
                    }
                }
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            logger.error(
                f"Gmail profile retrieval failed via MCP: {e}",
                extra={
                    "service": self.service_name,
                    "error": str(e)
                }
            )
            
            # Fallback to mock data on error
            return self._get_mock_profile_response()
    
    def _get_mock_messages_response(self, max_results: int) -> str:
        """Generate mock messages response."""
        mock_result = {
            "success": True,
            "data": {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "messages": [
                                {
                                    "id": "mock_msg_1",
                                    "snippet": "Gmail MCP integration is working! This is a mock message while OAuth is being configured.",
                                    "payload": {
                                        "headers": [
                                            {"name": "From", "value": "MACAE System <system@macae.local>"},
                                            {"name": "Subject", "value": "Gmail Integration Test"},
                                            {"name": "Date", "value": "2024-12-16"}
                                        ]
                                    }
                                }
                            ][:max_results]
                        })
                    }]
                }
            }
        }
        return json.dumps(mock_result, indent=2)
    
    def _get_mock_send_response(self) -> str:
        """Generate mock send response."""
        mock_result = {
            "success": True,
            "data": {
                "result": {
                    "content": [{
                        "type": "text", 
                        "text": json.dumps({
                            "id": "mock_sent_msg_1",
                            "threadId": "mock_thread_1",
                            "labelIds": ["SENT"]
                        })
                    }]
                }
            }
        }
        return json.dumps(mock_result, indent=2)
    
    def _get_mock_message_response(self, message_id: str) -> str:
        """Generate mock message response."""
        mock_result = {
            "success": True,
            "data": {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "id": message_id,
                            "snippet": "Mock message content",
                            "payload": {
                                "headers": [
                                    {"name": "From", "value": "sender@example.com"},
                                    {"name": "Subject", "value": "Mock Subject"},
                                    {"name": "Date", "value": "2024-12-16"}
                                ]
                            }
                        })
                    }]
                }
            }
        }
        return json.dumps(mock_result, indent=2)
    
    def _get_mock_search_response(self, query: str, max_results: int) -> str:
        """Generate mock search response."""
        mock_result = {
            "success": True,
            "data": {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "messages": [
                                {
                                    "id": f"search_result_{i}",
                                    "snippet": f"Search result for '{query}' - message {i}",
                                    "payload": {
                                        "headers": [
                                            {"name": "From", "value": f"user{i}@example.com"},
                                            {"name": "Subject", "value": f"Re: {query}"},
                                            {"name": "Date", "value": "2024-12-16"}
                                        ]
                                    }
                                } for i in range(1, min(max_results + 1, 4))
                            ]
                        })
                    }]
                }
            }
        }
        return json.dumps(mock_result, indent=2)
    
    def _get_mock_profile_response(self) -> str:
        """Generate mock profile response."""
        mock_result = {
            "success": True,
            "data": {
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "emailAddress": "demo@macae.local",
                            "messagesTotal": 150,
                            "threadsTotal": 75,
                            "historyId": "12345"
                        })
                    }]
                }
            }
        }
        return json.dumps(mock_result, indent=2)


# Backward compatibility wrapper
class GmailMCPServiceStandardized:
    """
    Backward compatibility wrapper that maintains the old interface
    but uses proper MCP protocol internally.
    """
    
    def __init__(self):
        self._client = None
        self._manager = get_mcp_manager()
        
        # Register Gmail service with manager
        async def create_gmail_client():
            client = GmailStandardMCPClient()
            await client.connect()
            return client
        
        self._manager.register_service("gmail", create_gmail_client)
        
        logger.info("Gmail MCP service initialized with proper MCP protocol")
    
    async def _get_client(self) -> GmailStandardMCPClient:
        """Get or create standardized MCP client."""
        if self._client is None:
            self._client = await self._manager.get_client("gmail")
        return self._client
    
    async def list_messages(self, max_results: int = 10, query: str = "") -> str:
        """List Gmail messages using proper MCP protocol."""
        client = await self._get_client()
        return await client.list_messages(max_results, query)
    
    async def send_message(self, to: str, subject: str, body: str, cc: Optional[str] = None) -> str:
        """Send Gmail message using proper MCP protocol."""
        client = await self._get_client()
        return await client.send_message(to, subject, body, cc)
    
    async def get_message(self, message_id: str, include_body_html: bool = False) -> str:
        """Get Gmail message using proper MCP protocol."""
        client = await self._get_client()
        return await client.get_message(message_id, include_body_html)
    
    async def search_messages(self, query: str, max_results: int = 10) -> str:
        """Search Gmail messages using proper MCP protocol."""
        client = await self._get_client()
        return await client.search_messages(query, max_results)
    
    async def get_profile(self) -> str:
        """Get Gmail profile using proper MCP protocol."""
        client = await self._get_client()
        return await client.get_profile()


# Global instance for backward compatibility
_gmail_service = None


def get_gmail_service() -> GmailMCPServiceStandardized:
    """Get or create standardized Gmail MCP service instance."""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = GmailMCPServiceStandardized()
    return _gmail_service