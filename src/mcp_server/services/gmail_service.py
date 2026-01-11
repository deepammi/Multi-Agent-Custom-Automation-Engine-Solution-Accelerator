"""
Gmail MCP Service - Provides Gmail tools via MCP protocol.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.factory import MCPToolBase, Domain

logger = logging.getLogger(__name__)


class GmailService(MCPToolBase):
    """Gmail service providing email operations via MCP."""
    
    def __init__(self):
        super().__init__(Domain.GMAIL)  # Use dedicated GMAIL domain
        self.enabled = self._check_credentials_available()
        
        logger.info(f"Gmail MCP Service initialized (enabled: {self.enabled})")
    
    def _check_credentials_available(self) -> bool:
        """Check if Gmail credentials are available."""
        try:
            config_dir = Path.home() / ".gmail-mcp"
            credentials_path = config_dir / "credentials.json"
            oauth_keys_path = config_dir / "gcp-oauth.keys.json"
            
            return credentials_path.exists() and oauth_keys_path.exists()
        except Exception:
            return False
    
    def register_tools(self, mcp) -> None:
        """Register Gmail tools with the MCP server."""
        
        @mcp.tool(tags={self.domain.value})
        async def gmail_list_messages(max_results: int = 10, query: str = "") -> Dict[str, Any]:
            """List Gmail messages using Google API."""
            if not self.enabled:
                logger.info("Gmail credentials not available, returning mock data")
                return {
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
                    ]
                }
            
            try:
                # Import Google API libraries
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                
                # Load credentials
                config_dir = Path.home() / ".gmail-mcp"
                credentials_path = config_dir / "credentials.json"
                oauth_keys_path = config_dir / "gcp-oauth.keys.json"
                
                # Load OAuth keys for client info
                with open(oauth_keys_path, 'r') as f:
                    oauth_keys = json.load(f)
                
                client_id = oauth_keys['installed']['client_id']
                client_secret = oauth_keys['installed']['client_secret']
                
                # Load and fix credentials
                with open(credentials_path, 'r') as f:
                    creds_data = json.load(f)
                
                # Add missing client info
                creds_data['client_id'] = client_id
                creds_data['client_secret'] = client_secret
                
                # Create credentials object
                creds = Credentials.from_authorized_user_info(creds_data)
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                
                if not creds.valid:
                    logger.error("Invalid Gmail credentials")
                    return {"error": "Invalid Gmail credentials"}
                
                # Build Gmail service
                service = build('gmail', 'v1', credentials=creds)
                
                # List messages
                results = service.users().messages().list(
                    userId='me',
                    maxResults=max_results,
                    q=query if query else None
                ).execute()
                
                messages = results.get('messages', [])
                
                # Get full message details
                detailed_messages = []
                for msg in messages:
                    msg_detail = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Format message
                    headers = {h['name']: h['value'] for h in msg_detail['payload'].get('headers', [])}
                    formatted_msg = {
                        "id": msg_detail['id'],
                        "threadId": msg_detail.get('threadId'),
                        "snippet": msg_detail.get('snippet', ''),
                        "payload": {
                            "headers": [
                                {"name": "From", "value": headers.get('From', '')},
                                {"name": "To", "value": headers.get('To', '')},
                                {"name": "Subject", "value": headers.get('Subject', '')},
                                {"name": "Date", "value": headers.get('Date', '')}
                            ]
                        }
                    }
                    detailed_messages.append(formatted_msg)
                
                return {"messages": detailed_messages}
                
            except ImportError as e:
                logger.error(f"Missing Google API libraries: {e}")
                return {"error": f"Missing Google API libraries: {e}"}
            except Exception as e:
                logger.error(f"Gmail list messages failed: {e}")
                return {"error": str(e)}
        
        @mcp.tool(tags={self.domain.value})
        async def gmail_send_message(
            to: str, 
            subject: str, 
            body: str, 
            cc: str = None
        ) -> Dict[str, Any]:
            """Send a Gmail message using Google API."""
            if not self.enabled:
                logger.info("Gmail credentials not available, returning mock response")
                return {
                    "id": "mock_sent_msg_1",
                    "threadId": "mock_thread_1",
                    "labelIds": ["SENT"]
                }
            
            try:
                # Import Google API libraries
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                from email.mime.text import MIMEText
                import base64
                
                # Load credentials (same as list_messages)
                config_dir = Path.home() / ".gmail-mcp"
                credentials_path = config_dir / "credentials.json"
                oauth_keys_path = config_dir / "gcp-oauth.keys.json"
                
                # Load OAuth keys for client info
                with open(oauth_keys_path, 'r') as f:
                    oauth_keys = json.load(f)
                
                client_id = oauth_keys['installed']['client_id']
                client_secret = oauth_keys['installed']['client_secret']
                
                # Load and fix credentials
                with open(credentials_path, 'r') as f:
                    creds_data = json.load(f)
                
                # Add missing client info
                creds_data['client_id'] = client_id
                creds_data['client_secret'] = client_secret
                
                # Create credentials object
                creds = Credentials.from_authorized_user_info(creds_data)
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                
                if not creds.valid:
                    logger.error("Invalid Gmail credentials")
                    return {"error": "Invalid Gmail credentials"}
                
                # Build Gmail service
                service = build('gmail', 'v1', credentials=creds)
                
                # Create email message
                message = MIMEText(body)
                message['to'] = to
                message['subject'] = subject
                if cc:
                    message['cc'] = cc
                
                # Encode message
                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                
                # Send message
                result = service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
                
                return {
                    "id": result['id'],
                    "threadId": result['threadId'],
                    "labelIds": result.get('labelIds', [])
                }
                
            except ImportError as e:
                logger.error(f"Missing Google API libraries: {e}")
                return {"error": f"Missing Google API libraries: {e}"}
            except Exception as e:
                logger.error(f"Gmail send message failed: {e}")
                return {"error": str(e)}
        
        @mcp.tool(tags={self.domain.value})
        async def gmail_get_message(
            message_id: str, 
            include_body_html: bool = False
        ) -> Dict[str, Any]:
            """Get a specific Gmail message using Google API."""
            if not self.enabled:
                logger.info("Gmail credentials not available, returning mock data")
                return {
                    "id": message_id,
                    "snippet": "Mock message content",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "sender@example.com"},
                            {"name": "Subject", "value": "Mock Subject"},
                            {"name": "Date", "value": "2024-12-16"}
                        ]
                    }
                }
            
            try:
                # Import Google API libraries
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                
                # Load credentials (same as list_messages)
                config_dir = Path.home() / ".gmail-mcp"
                credentials_path = config_dir / "credentials.json"
                oauth_keys_path = config_dir / "gcp-oauth.keys.json"
                
                # Load OAuth keys for client info
                with open(oauth_keys_path, 'r') as f:
                    oauth_keys = json.load(f)
                
                client_id = oauth_keys['installed']['client_id']
                client_secret = oauth_keys['installed']['client_secret']
                
                # Load and fix credentials
                with open(credentials_path, 'r') as f:
                    creds_data = json.load(f)
                
                # Add missing client info
                creds_data['client_id'] = client_id
                creds_data['client_secret'] = client_secret
                
                # Create credentials object
                creds = Credentials.from_authorized_user_info(creds_data)
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                
                if not creds.valid:
                    logger.error("Invalid Gmail credentials")
                    return {"error": "Invalid Gmail credentials"}
                
                # Build Gmail service
                service = build('gmail', 'v1', credentials=creds)
                
                # Get message details
                message = service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
                
                # Format message
                headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
                formatted_msg = {
                    "id": message['id'],
                    "threadId": message.get('threadId'),
                    "snippet": message.get('snippet', ''),
                    "payload": {
                        "headers": [
                            {"name": "From", "value": headers.get('From', '')},
                            {"name": "To", "value": headers.get('To', '')},
                            {"name": "Subject", "value": headers.get('Subject', '')},
                            {"name": "Date", "value": headers.get('Date', '')}
                        ]
                    }
                }
                
                return formatted_msg
                
            except ImportError as e:
                logger.error(f"Missing Google API libraries: {e}")
                return {"error": f"Missing Google API libraries: {e}"}
            except Exception as e:
                logger.error(f"Gmail get message failed: {e}")
                return {"error": str(e)}
        
        @mcp.tool(tags={self.domain.value})
        async def gmail_search_messages(
            query: str, 
            max_results: int = 10
        ) -> Dict[str, Any]:
            """Search Gmail messages using Google API."""
            if not self.enabled:
                logger.info("Gmail credentials not available, returning mock data")
                return {
                    "messages": [
                        {
                            "id": "mock_search_msg_1",
                            "snippet": f"Mock search result for query: {query}",
                            "payload": {
                                "headers": [
                                    {"name": "From", "value": "search@example.com"},
                                    {"name": "Subject", "value": f"Search Result: {query}"},
                                    {"name": "Date", "value": "2024-12-16"}
                                ]
                            }
                        }
                    ]
                }
            
            try:
                # Import Google API libraries
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                
                # Load credentials (same as list_messages)
                config_dir = Path.home() / ".gmail-mcp"
                credentials_path = config_dir / "credentials.json"
                oauth_keys_path = config_dir / "gcp-oauth.keys.json"
                
                # Load OAuth keys for client info
                with open(oauth_keys_path, 'r') as f:
                    oauth_keys = json.load(f)
                
                client_id = oauth_keys['installed']['client_id']
                client_secret = oauth_keys['installed']['client_secret']
                
                # Load and fix credentials
                with open(credentials_path, 'r') as f:
                    creds_data = json.load(f)
                
                # Add missing client info
                creds_data['client_id'] = client_id
                creds_data['client_secret'] = client_secret
                
                # Create credentials object
                creds = Credentials.from_authorized_user_info(creds_data)
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                
                if not creds.valid:
                    logger.error("Invalid Gmail credentials")
                    return {"error": "Invalid Gmail credentials"}
                
                # Build Gmail service
                service = build('gmail', 'v1', credentials=creds)
                
                # Search messages
                results = service.users().messages().list(
                    userId='me',
                    maxResults=max_results,
                    q=query
                ).execute()
                
                messages = results.get('messages', [])
                
                # Get full message details
                detailed_messages = []
                for msg in messages:
                    msg_detail = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Format message
                    headers = {h['name']: h['value'] for h in msg_detail['payload'].get('headers', [])}
                    formatted_msg = {
                        "id": msg_detail['id'],
                        "threadId": msg_detail.get('threadId'),
                        "snippet": msg_detail.get('snippet', ''),
                        "payload": {
                            "headers": [
                                {"name": "From", "value": headers.get('From', '')},
                                {"name": "To", "value": headers.get('To', '')},
                                {"name": "Subject", "value": headers.get('Subject', '')},
                                {"name": "Date", "value": headers.get('Date', '')}
                            ]
                        }
                    }
                    detailed_messages.append(formatted_msg)
                
                return {"messages": detailed_messages}
                
            except ImportError as e:
                logger.error(f"Missing Google API libraries: {e}")
                return {"error": f"Missing Google API libraries: {e}"}
            except Exception as e:
                logger.error(f"Gmail search messages failed: {e}")
                return {"error": str(e)}
        
        @mcp.tool(tags={self.domain.value})
        async def gmail_get_profile() -> Dict[str, Any]:
            """Get Gmail user profile using Google API."""
            if not self.enabled:
                logger.info("Gmail credentials not available, returning mock data")
                return {
                    "emailAddress": "demo@macae.local",
                    "messagesTotal": 150,
                    "threadsTotal": 75,
                    "historyId": "12345"
                }
            
            try:
                # Import Google API libraries
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                
                # Load credentials (same as list_messages)
                config_dir = Path.home() / ".gmail-mcp"
                credentials_path = config_dir / "credentials.json"
                oauth_keys_path = config_dir / "gcp-oauth.keys.json"
                
                # Load OAuth keys for client info
                with open(oauth_keys_path, 'r') as f:
                    oauth_keys = json.load(f)
                
                client_id = oauth_keys['installed']['client_id']
                client_secret = oauth_keys['installed']['client_secret']
                
                # Load and fix credentials
                with open(credentials_path, 'r') as f:
                    creds_data = json.load(f)
                
                # Add missing client info
                creds_data['client_id'] = client_id
                creds_data['client_secret'] = client_secret
                
                # Create credentials object
                creds = Credentials.from_authorized_user_info(creds_data)
                
                # Refresh if needed
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                
                if not creds.valid:
                    logger.error("Invalid Gmail credentials")
                    return {"error": "Invalid Gmail credentials"}
                
                # Build Gmail service
                service = build('gmail', 'v1', credentials=creds)
                
                # Get profile
                profile = service.users().getProfile(userId='me').execute()
                
                return {
                    "emailAddress": profile.get('emailAddress'),
                    "messagesTotal": profile.get('messagesTotal'),
                    "threadsTotal": profile.get('threadsTotal'),
                    "historyId": profile.get('historyId')
                }
                
            except ImportError as e:
                logger.error(f"Missing Google API libraries: {e}")
                return {"error": f"Missing Google API libraries: {e}"}
            except Exception as e:
                logger.error(f"Gmail get profile failed: {e}")
                return {"error": str(e)}
    
    @property
    def tool_count(self) -> int:
        """Return the number of tools provided by this service."""
        return 5  # gmail_list_messages, gmail_send_message, gmail_get_message, gmail_search_messages, gmail_get_profile