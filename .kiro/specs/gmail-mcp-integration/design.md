# Design Document

## Overview

This design document outlines the integration of Gmail MCP (Model Context Protocol) client into the Multi-Agent Custom Automation Engine (MACAE) LangGraph system. The integration follows the established patterns used for Bill.com, Salesforce, and Zoho integrations, providing Gmail API access through MCP tools that can be used by specialized agents for email-based business automation.

The solution adds Gmail API wrapper functions to the existing MCP server, handles OAuth 2.0 authentication and token management, and provides email management tools for agents to read, send, search, and analyze emails within business workflows.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   LangGraph     │
│   Agents        │
│ (Invoice/Audit/ │
│   Email/etc.)   │
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
│ Gmail MCP       │
│   Service       │
│   Wrapper       │
└────────┬────────┘
         │ HTTPS/REST
         ▼
┌─────────────────┐
│   Gmail API     │
│ (googleapis.com)│
└─────────────────┘
```

### Component Interaction Flow

1. **Agent requests email operation** → Calls MCP tool (e.g., "get_gmail_messages")
2. **MCP Server receives call** → Routes to Gmail MCP service wrapper
3. **Authentication check** → Validates/refreshes OAuth 2.0 tokens
4. **API call execution** → Makes authenticated request to Gmail API
5. **Response processing** → Formats data into standardized structure
6. **Result return** → Sends formatted data back to agent
7. **Agent processing** → Uses email data for analysis/workflow

## Components and Interfaces

### 1. Gmail MCP Service (`src/mcp_server/services/gmail_mcp_service.py`)

**Purpose**: Core service for Gmail API authentication and email operations.

```python
import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
from dataclasses import dataclass
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


@dataclass
class GmailConfig:
    """Gmail API configuration."""
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str]
    credentials_file: Optional[str] = None
    token_file: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'GmailConfig':
        """Load configuration from environment variables."""
        scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        
        return cls(
            client_id=os.getenv("GMAIL_CLIENT_ID"),
            client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
            redirect_uri=os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8080/callback"),
            scopes=scopes,
            credentials_file=os.getenv("GMAIL_CREDENTIALS_FILE", "gmail_credentials.json"),
            token_file=os.getenv("GMAIL_TOKEN_FILE", "gmail_token.json")
        )
    
    def validate(self) -> bool:
        """Validate that all required fields are present."""
        required_fields = [self.client_id, self.client_secret]
        return all(field is not None for field in required_fields)


class GmailMCPService:
    """Service for Gmail API operations via MCP."""
    
    def __init__(self):
        self.config = GmailConfig.from_env()
        self.credentials: Optional[Credentials] = None
        self.service = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Gmail service with authentication."""
        if self._initialized:
            return
        
        if not self.config.validate():
            logger.error("Gmail configuration is incomplete")
            raise Exception("Gmail configuration missing required fields")
        
        try:
            # Load existing credentials if available
            if os.path.exists(self.config.token_file):
                self.credentials = Credentials.from_authorized_user_file(
                    self.config.token_file, 
                    self.config.scopes
                )
            
            # Refresh credentials if expired
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                self._save_credentials()
            
            # If no valid credentials, need OAuth flow
            if not self.credentials or not self.credentials.valid:
                logger.warning("No valid Gmail credentials found. OAuth flow required.")
                raise Exception("Gmail OAuth authentication required")
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            self._initialized = True
            
            logger.info("✅ Gmail MCP service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            raise
    
    def _save_credentials(self):
        """Save credentials to token file."""
        try:
            with open(self.config.token_file, 'w') as token_file:
                token_file.write(self.credentials.to_json())
            logger.debug("Gmail credentials saved")
        except Exception as e:
            logger.error(f"Failed to save Gmail credentials: {e}")
    
    def get_oauth_url(self) -> str:
        """Get OAuth authorization URL for initial setup."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.config.redirect_uri]
                }
            },
            scopes=self.config.scopes
        )
        flow.redirect_uri = self.config.redirect_uri
        
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url
    
    async def complete_oauth(self, authorization_code: str) -> bool:
        """Complete OAuth flow with authorization code."""
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.config.redirect_uri]
                    }
                },
                scopes=self.config.scopes
            )
            flow.redirect_uri = self.config.redirect_uri
            
            flow.fetch_token(code=authorization_code)
            self.credentials = flow.credentials
            self._save_credentials()
            
            # Initialize service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            self._initialized = True
            
            logger.info("✅ Gmail OAuth completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Gmail OAuth completion failed: {e}")
            return False
    
    async def get_messages(
        self,
        query: str = "",
        max_results: int = 10,
        label_ids: Optional[List[str]] = None,
        include_spam_trash: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get Gmail messages with optional filtering.
        
        Args:
            query: Gmail search query (e.g., "from:example@gmail.com")
            max_results: Maximum number of messages to return
            label_ids: List of label IDs to filter by
            include_spam_trash: Whether to include spam and trash
            
        Returns:
            List of message data
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get message list
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                labelIds=label_ids,
                includeSpamTrash=include_spam_trash
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get full message details
            detailed_messages = []
            for msg in messages:
                msg_detail = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Parse message
                parsed_msg = self._parse_message(msg_detail)
                detailed_messages.append(parsed_msg)
            
            return detailed_messages
            
        except Exception as e:
            logger.error(f"Failed to get Gmail messages: {e}")
            return []
    
    def _parse_message(self, message: Dict) -> Dict[str, Any]:
        """Parse Gmail message into standardized format."""
        headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
        
        # Extract body
        body = self._extract_body(message['payload'])
        
        # Extract attachments info
        attachments = self._extract_attachments_info(message['payload'])
        
        return {
            "id": message['id'],
            "thread_id": message['threadId'],
            "label_ids": message.get('labelIds', []),
            "snippet": message.get('snippet', ''),
            "history_id": message.get('historyId'),
            "internal_date": message.get('internalDate'),
            "size_estimate": message.get('sizeEstimate'),
            "headers": {
                "from": headers.get('From', ''),
                "to": headers.get('To', ''),
                "cc": headers.get('Cc', ''),
                "bcc": headers.get('Bcc', ''),
                "subject": headers.get('Subject', ''),
                "date": headers.get('Date', ''),
                "message_id": headers.get('Message-ID', '')
            },
            "body": body,
            "attachments": attachments,
            "raw_headers": headers
        }
    
    def _extract_body(self, payload: Dict) -> Dict[str, str]:
        """Extract email body content."""
        body = {"text": "", "html": ""}
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain':
                    body['text'] = self._decode_body_data(part.get('body', {}).get('data', ''))
                elif mime_type == 'text/html':
                    body['html'] = self._decode_body_data(part.get('body', {}).get('data', ''))
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            body_data = payload.get('body', {}).get('data', '')
            
            if mime_type == 'text/plain':
                body['text'] = self._decode_body_data(body_data)
            elif mime_type == 'text/html':
                body['html'] = self._decode_body_data(body_data)
        
        return body
    
    def _decode_body_data(self, data: str) -> str:
        """Decode base64url encoded body data."""
        if not data:
            return ""
        
        try:
            # Gmail uses base64url encoding
            decoded_bytes = base64.urlsafe_b64decode(data + '==')
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            logger.warning(f"Failed to decode body data: {e}")
            return ""
    
    def _extract_attachments_info(self, payload: Dict) -> List[Dict[str, Any]]:
        """Extract attachment metadata."""
        attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    attachment = {
                        "filename": part['filename'],
                        "mime_type": part.get('mimeType', ''),
                        "size": part.get('body', {}).get('size', 0),
                        "attachment_id": part.get('body', {}).get('attachmentId')
                    }
                    attachments.append(attachment)
        
        return attachments
    
    async def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email message.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html_body: HTML body content
            
        Returns:
            Send result with message ID
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create message
            if html_body:
                message = MIMEMultipart('alternative')
                text_part = MIMEText(body, 'plain')
                html_part = MIMEText(html_body, 'html')
                message.attach(text_part)
                message.attach(html_part)
            else:
                message = MIMEText(body)
            
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send message
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                "success": True,
                "message_id": result['id'],
                "thread_id": result['threadId'],
                "label_ids": result.get('labelIds', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to send Gmail message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_messages(
        self,
        search_term: str,
        search_type: str = "subject",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search Gmail messages by various criteria.
        
        Args:
            search_term: Search term
            search_type: Type of search (subject, from, to, body, label)
            max_results: Maximum results to return
            
        Returns:
            List of matching messages
        """
        # Build Gmail search query
        if search_type == "subject":
            query = f"subject:{search_term}"
        elif search_type == "from":
            query = f"from:{search_term}"
        elif search_type == "to":
            query = f"to:{search_term}"
        elif search_type == "body":
            query = search_term
        elif search_type == "label":
            query = f"label:{search_term}"
        else:
            query = search_term
        
        return await self.get_messages(query=query, max_results=max_results)


# Global service instance
_gmail_service: Optional[GmailMCPService] = None


def get_gmail_service() -> GmailMCPService:
    """Get or create Gmail MCP service instance."""
    global _gmail_service
    
    if _gmail_service is None:
        _gmail_service = GmailMCPService()
    
    return _gmail_service
```

### 2. Gmail MCP Tools (`src/mcp_server/core/gmail_tools.py`)

**Purpose**: Define MCP tools that wrap Gmail API operations for agent use.

```python
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime

from ..services.gmail_mcp_service import get_gmail_service

logger = logging.getLogger(__name__)


async def get_gmail_messages(
    query: str = "",
    max_results: int = 10,
    include_body: bool = True,
    include_attachments: bool = False
) -> str:
    """
    Get Gmail messages with optional filtering.
    
    Args:
        query: Gmail search query (e.g., "from:example@gmail.com", "subject:invoice")
        max_results: Maximum number of messages (default 10, max 50)
        include_body: Whether to include message body content
        include_attachments: Whether to include attachment metadata
    
    Returns:
        JSON string with messages list and metadata
    """
    try:
        service = get_gmail_service()
        
        # Validate max_results
        max_results = min(max(1, max_results), 50)
        
        # Get messages from Gmail
        messages = await service.get_messages(
            query=query,
            max_results=max_results
        )
        
        # Format response
        formatted_messages = []
        for message in messages:
            formatted_msg = {
                "id": message["id"],
                "thread_id": message["thread_id"],
                "subject": message["headers"]["subject"],
                "from": message["headers"]["from"],
                "to": message["headers"]["to"],
                "date": message["headers"]["date"],
                "snippet": message["snippet"],
                "labels": message["label_ids"]
            }
            
            if include_body:
                formatted_msg["body"] = message["body"]
            
            if include_attachments:
                formatted_msg["attachments"] = message["attachments"]
            
            formatted_messages.append(formatted_msg)
        
        result = {
            "success": True,
            "messages": formatted_messages,
            "count": len(formatted_messages),
            "query": query,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to get Gmail messages: {e}")
        error_result = {
            "success": False,
            "error": str(e),
            "messages": [],
            "count": 0
        }
        return json.dumps(error_result, indent=2)


async def send_gmail_message(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html_body: Optional[str] = None
) -> str:
    """
    Send an email via Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text body content
        cc: CC recipients (comma-separated)
        bcc: BCC recipients (comma-separated)
        html_body: HTML body content (optional)
    
    Returns:
        JSON string with send result
    """
    try:
        service = get_gmail_service()
        
        # Send message
        result = await service.send_message(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            html_body=html_body
        )
        
        if result["success"]:
            response = {
                "success": True,
                "message_id": result["message_id"],
                "thread_id": result["thread_id"],
                "to": to,
                "subject": subject,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            response = {
                "success": False,
                "error": result["error"],
                "to": to,
                "subject": subject
            }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to send Gmail message: {e}")
        error_result = {
            "success": False,
            "error": str(e),
            "to": to,
            "subject": subject
        }
        return json.dumps(error_result, indent=2)


async def search_gmail_messages(
    search_term: str,
    search_type: str = "subject",
    max_results: int = 10
) -> str:
    """
    Search Gmail messages by various criteria.
    
    Args:
        search_term: Search term or phrase
        search_type: Type of search (subject, from, to, body, label)
        max_results: Maximum number of results (default 10, max 50)
    
    Returns:
        JSON string with search results
    """
    try:
        service = get_gmail_service()
        
        # Validate inputs
        max_results = min(max(1, max_results), 50)
        valid_search_types = ["subject", "from", "to", "body", "label"]
        
        if search_type not in valid_search_types:
            raise ValueError(f"Invalid search_type. Must be one of: {valid_search_types}")
        
        # Search messages
        messages = await service.search_messages(
            search_term=search_term,
            search_type=search_type,
            max_results=max_results
        )
        
        # Format results
        formatted_messages = []
        for message in messages:
            formatted_msg = {
                "id": message["id"],
                "subject": message["headers"]["subject"],
                "from": message["headers"]["from"],
                "to": message["headers"]["to"],
                "date": message["headers"]["date"],
                "snippet": message["snippet"]
            }
            formatted_messages.append(formatted_msg)
        
        result = {
            "success": True,
            "messages": formatted_messages,
            "count": len(formatted_messages),
            "search_term": search_term,
            "search_type": search_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to search Gmail messages: {e}")
        error_result = {
            "success": False,
            "error": str(e),
            "messages": [],
            "count": 0,
            "search_term": search_term,
            "search_type": search_type
        }
        return json.dumps(error_result, indent=2)


async def get_gmail_message_details(message_id: str) -> str:
    """
    Get detailed information for a specific Gmail message.
    
    Args:
        message_id: Gmail message ID
    
    Returns:
        JSON string with detailed message information
    """
    try:
        service = get_gmail_service()
        
        # Get single message by ID
        messages = await service.get_messages(query=f"rfc822msgid:{message_id}", max_results=1)
        
        if not messages:
            return json.dumps({
                "success": False,
                "error": f"Message {message_id} not found",
                "message": None
            })
        
        message = messages[0]
        
        # Format detailed response
        detailed_message = {
            "id": message["id"],
            "thread_id": message["thread_id"],
            "headers": message["headers"],
            "body": message["body"],
            "attachments": message["attachments"],
            "labels": message["label_ids"],
            "snippet": message["snippet"],
            "size_estimate": message["size_estimate"],
            "internal_date": message["internal_date"]
        }
        
        result = {
            "success": True,
            "message": detailed_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to get Gmail message details for {message_id}: {e}")
        error_result = {
            "success": False,
            "error": str(e),
            "message": None
        }
        return json.dumps(error_result, indent=2)


async def gmail_oauth_setup() -> str:
    """
    Get Gmail OAuth setup instructions and authorization URL.
    
    Returns:
        JSON string with OAuth setup information
    """
    try:
        service = get_gmail_service()
        
        # Check if already authenticated
        try:
            await service.initialize()
            return json.dumps({
                "success": True,
                "authenticated": True,
                "message": "Gmail is already authenticated and ready to use",
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            # Not authenticated, provide OAuth URL
            auth_url = service.get_oauth_url()
            
            return json.dumps({
                "success": True,
                "authenticated": False,
                "oauth_url": auth_url,
                "instructions": [
                    "1. Visit the OAuth URL provided",
                    "2. Sign in to your Google account",
                    "3. Grant permissions to the application",
                    "4. Copy the authorization code from the redirect URL",
                    "5. Use the 'complete_gmail_oauth' tool with the authorization code"
                ],
                "timestamp": datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Failed to get Gmail OAuth setup: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "authenticated": False
        })


async def complete_gmail_oauth(authorization_code: str) -> str:
    """
    Complete Gmail OAuth flow with authorization code.
    
    Args:
        authorization_code: Authorization code from OAuth callback
    
    Returns:
        JSON string with OAuth completion result
    """
    try:
        service = get_gmail_service()
        
        # Complete OAuth flow
        success = await service.complete_oauth(authorization_code)
        
        if success:
            return json.dumps({
                "success": True,
                "message": "Gmail OAuth completed successfully. Gmail is now ready to use.",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return json.dumps({
                "success": False,
                "error": "Failed to complete OAuth flow. Please check the authorization code.",
                "timestamp": datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Failed to complete Gmail OAuth: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })
```

### 3. Gmail MCP Tools Service (`src/mcp_server/services/gmail_tools_service.py`)

**Purpose**: Service class that provides Gmail functionality as MCP tools following the factory pattern.

```python
"""
Gmail MCP tools service for LangGraph agent integration.
Provides email management functionality as MCP tools.
"""

import logging
from typing import Dict, Any

from core.gmail_tools import (
    get_gmail_messages,
    send_gmail_message,
    search_gmail_messages,
    get_gmail_message_details,
    gmail_oauth_setup,
    complete_gmail_oauth
)

logger = logging.getLogger(__name__)


class GmailToolsService:
    """Service that provides Gmail functionality as MCP tools."""
    
    def __init__(self):
        self.domain = "gmail"
        logger.info("GmailToolsService initialized")
    
    async def get_gmail_messages(
        self,
        query: str = "",
        max_results: int = 10,
        include_body: bool = True,
        include_attachments: bool = False
    ) -> str:
        """Get Gmail messages with optional filtering."""
        return await get_gmail_messages(query, max_results, include_body, include_attachments)
    
    async def send_gmail_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = None,
        bcc: str = None,
        html_body: str = None
    ) -> str:
        """Send an email via Gmail."""
        return await send_gmail_message(to, subject, body, cc, bcc, html_body)
    
    async def search_gmail_messages(
        self,
        search_term: str,
        search_type: str = "subject",
        max_results: int = 10
    ) -> str:
        """Search Gmail messages by various criteria."""
        return await search_gmail_messages(search_term, search_type, max_results)
    
    async def get_gmail_message_details(self, message_id: str) -> str:
        """Get detailed information for a specific Gmail message."""
        return await get_gmail_message_details(message_id)
    
    async def gmail_oauth_setup(self) -> str:
        """Get Gmail OAuth setup instructions and authorization URL."""
        return await gmail_oauth_setup()
    
    async def complete_gmail_oauth(self, authorization_code: str) -> str:
        """Complete Gmail OAuth flow with authorization code."""
        return await complete_gmail_oauth(authorization_code)
```

### 4. Environment Configuration

**Purpose**: Configuration for Gmail API credentials and settings.

Add to `backend/.env`:
```bash
# Gmail API Configuration
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REDIRECT_URI=http://localhost:8080/callback
GMAIL_CREDENTIALS_FILE=gmail_credentials.json
GMAIL_TOKEN_FILE=gmail_token.json
```

Add to `src/mcp_server/.env.example`:
```bash
# Gmail API Configuration
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REDIRECT_URI=http://localhost:8080/callback
GMAIL_CREDENTIALS_FILE=gmail_credentials.json
GMAIL_TOKEN_FILE=gmail_token.json
```

## Data Models

### Email Message Structure

```python
@dataclass
class GmailMessage:
    """Standardized Gmail message data structure."""
    id: str
    thread_id: str
    subject: str
    sender: str
    recipients: List[str]
    cc: Optional[List[str]]
    bcc: Optional[List[str]]
    date: str
    body_text: str
    body_html: Optional[str]
    attachments: List[Dict[str, Any]]
    labels: List[str]
    snippet: str
    size_estimate: int
    internal_date: str
```

### API Response Format

All Gmail tools return responses in this standardized format:

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

### Property 1: Authentication Consistency
*For any* valid Gmail API credentials, the authentication process should succeed and establish a valid session
**Validates: Requirements 1.1**

### Property 2: Message Retrieval Reliability
*For any* agent request to read emails, the system should return structured message data with consistent field formats
**Validates: Requirements 1.2**

### Property 3: Content Parsing Completeness
*For any* retrieved email message, the system should successfully parse headers, body content, and attachment metadata
**Validates: Requirements 1.3**

### Property 4: Pagination and Filtering Accuracy
*For any* request with pagination or filtering parameters, all returned messages should match the specified criteria
**Validates: Requirements 1.4**

### Property 5: Privacy Settings Compliance
*For any* email content containing sensitive information, the system should handle data according to configured privacy rules
**Validates: Requirements 1.5**

### Property 6: Email Sending Reliability
*For any* valid email composition request, the system should successfully send the email and return confirmation
**Validates: Requirements 2.1**

### Property 7: Format Support Consistency
*For any* email content, the system should correctly handle both plain text and HTML formats
**Validates: Requirements 2.2**

### Property 8: Template Population Accuracy
*For any* email template with dynamic data, the system should correctly populate all template variables
**Validates: Requirements 2.3**

### Property 9: Error Reporting Completeness
*For any* failed email operation, the system should return detailed error information with actionable context
**Validates: Requirements 2.4**

### Property 10: Success Confirmation Logging
*For any* successful email operation, the system should log the action and return confirmation details
**Validates: Requirements 2.5**

### Property 11: Search Syntax Support
*For any* Gmail search query using advanced syntax, the system should correctly interpret and execute the search
**Validates: Requirements 3.1**

### Property 12: Content Analysis Extraction
*For any* email content analysis request, the system should extract relevant key information accurately
**Validates: Requirements 3.2**

### Property 13: Business Context Search
*For any* search by business identifiers (customer names, invoice numbers), the system should return relevant matches
**Validates: Requirements 3.3**

### Property 14: Search Result Processing
*For any* search results, the system should provide consistent relevance scoring and sorting options
**Validates: Requirements 3.4**

### Property 15: Query Optimization Performance
*For any* complex search query, the system should optimize for both performance and accuracy
**Validates: Requirements 3.5**

### Property 16: OAuth Implementation Security
*For any* OAuth 2.0 authentication flow, the system should use appropriate scopes and secure token handling
**Validates: Requirements 4.1**

### Property 17: Credential Encryption Security
*For any* stored authentication tokens, the system should encrypt credentials before storage
**Validates: Requirements 4.2**

### Property 18: Token Refresh Automation
*For any* expired authentication token, the system should automatically refresh without user intervention
**Validates: Requirements 4.3**

### Property 19: Access Revocation Handling
*For any* revoked access scenario, the system should handle failures gracefully and notify administrators
**Validates: Requirements 4.4**

### Property 20: Audit Trail Completeness
*For any* Gmail API operation, the system should log the action with timestamp and user context
**Validates: Requirements 4.5**

### Property 21: Tool Registration Accuracy
*For any* agent configuration, Gmail tools should be registered with appropriate agents based on their roles
**Validates: Requirements 5.1**

### Property 22: Concurrent Operation Safety
*For any* multiple agents accessing Gmail simultaneously, operations should complete without conflicts
**Validates: Requirements 5.2**

### Property 23: Integration Compatibility
*For any* workflow using Gmail with other integrations (Bill.com, Salesforce, Zoho), operations should work seamlessly
**Validates: Requirements 5.3**

### Property 24: Error Context Provision
*For any* error condition, the system should provide detailed context to help agents make informed decisions
**Validates: Requirements 5.4**

### Property 25: Transaction Consistency
*For any* email operations within larger workflows, the system should maintain transactional consistency
**Validates: Requirements 5.5**

## Error Handling

### Authentication Errors
- **OAuth Flow Failures**: Provide clear instructions for re-authentication
- **Token Expiration**: Automatic refresh with fallback to re-authentication
- **Scope Insufficient**: Clear error messages indicating required permissions

### API Rate Limiting
- **Quota Exceeded**: Implement exponential backoff and retry logic
- **Rate Limit Headers**: Monitor and respect Gmail API rate limits
- **Batch Operations**: Use batch requests where possible to optimize quota usage

### Network and Connectivity
- **Connection Timeouts**: Configurable timeout values with retry logic
- **Network Errors**: Graceful degradation with informative error messages
- **Service Unavailable**: Fallback mechanisms and status reporting

## Testing Strategy

### Unit Testing
- Test individual Gmail API wrapper functions
- Mock Gmail API responses for consistent testing
- Validate data parsing and formatting functions
- Test error handling scenarios

### Property-Based Testing
- Use **Hypothesis** for Python property-based testing
- Generate random email content and verify parsing consistency
- Test authentication flows with various credential configurations
- Validate search functionality across different query types
- Each property-based test should run a minimum of 100 iterations
- Tag each test with the corresponding correctness property number

### Integration Testing
- Test complete OAuth flow with real Gmail API
- Verify email sending and receiving functionality
- Test concurrent access scenarios
- Validate integration with existing LangGraph agents

### Security Testing
- Verify credential encryption and secure storage
- Test OAuth flow security and token handling
- Validate privacy settings compliance
- Test access revocation scenarios

## Performance Considerations

### API Optimization
- **Batch Requests**: Use Gmail API batch endpoints where available
- **Partial Responses**: Request only needed fields to reduce payload size
- **Caching**: Cache frequently accessed data like labels and user profile
- **Connection Pooling**: Reuse HTTP connections for multiple requests

### Memory Management
- **Streaming**: Stream large email content instead of loading into memory
- **Pagination**: Implement proper pagination for large result sets
- **Cleanup**: Properly dispose of resources and close connections

### Rate Limiting
- **Quota Management**: Monitor and respect Gmail API quotas
- **Backoff Strategy**: Implement exponential backoff for rate limit errors
- **Request Prioritization**: Prioritize critical operations over bulk operations

## Security and Privacy

### Data Protection
- **Encryption**: Encrypt all stored credentials and sensitive email content
- **Access Control**: Implement role-based access to email operations
- **Audit Logging**: Log all email access and operations for compliance
- **Data Retention**: Implement configurable data retention policies

### OAuth Security
- **Scope Minimization**: Request only necessary OAuth scopes
- **Token Security**: Secure storage and transmission of OAuth tokens
- **Refresh Handling**: Secure token refresh without exposing credentials
- **Revocation Support**: Handle access revocation gracefully

### Privacy Compliance
- **Content Filtering**: Filter sensitive information based on privacy settings
- **User Consent**: Ensure proper user consent for email access
- **Data Anonymization**: Anonymize email content where required
- **Compliance Reporting**: Generate compliance reports for audit purposes