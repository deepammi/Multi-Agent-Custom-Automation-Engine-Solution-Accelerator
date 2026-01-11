# Gmail MCP Integration - Simplified Design

## Overview

This design document outlines the minimal integration of the existing Shinzo Labs Gmail MCP server into the MACAE LangGraph system. The approach leverages the pre-built Gmail MCP server to minimize new code development while providing essential email functionality for business automation workflows.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   LangGraph     │
│   Gmail Agent   │
└────────┬────────┘
         │ MCP Tool Calls
         ▼
┌─────────────────┐
│   Existing      │
│   MCP Server    │
│   (FastMCP)     │
└────────┬────────┘
         │ Subprocess Call
         ▼
┌─────────────────┐
│ Shinzo Labs     │
│ Gmail MCP       │
│ Server (NPX)    │
└────────┬────────┘
         │ Gmail API
         ▼
┌─────────────────┐
│   Gmail API     │
│ (googleapis.com)│
└─────────────────┘
```

### Integration Flow

1. **Gmail Agent** calls MCP tool (e.g., "list_gmail_messages")
2. **FastMCP Server** routes call to Gmail MCP subprocess
3. **Gmail MCP Server** authenticates and calls Gmail API
4. **Response** flows back through the chain to the agent

## Components and Interfaces

### 1. Gmail MCP Service Wrapper (`backend/app/services/gmail_mcp_service.py`)

**Purpose**: Minimal wrapper that calls the existing Gmail MCP server as a subprocess.

```python
import subprocess
import json
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class GmailMCPService:
    """Minimal service wrapper for Shinzo Labs Gmail MCP server."""
    
    def __init__(self):
        self.domain = "gmail"
        self.server_command = ["npx", "@shinzolabs/gmail-mcp"]
        self._setup_oauth_config()
        logger.info("GmailMCPService initialized")
    
    def _setup_oauth_config(self):
        """Setup OAuth configuration from client_secret.json."""
        try:
            # Create .gmail-mcp directory if it doesn't exist
            config_dir = os.path.expanduser("~/.gmail-mcp")
            os.makedirs(config_dir, exist_ok=True)
            
            # Copy client_secret.json to expected location
            client_secret_path = "client_secret.json"
            oauth_keys_path = os.path.join(config_dir, "gcp-oauth.keys.json")
            
            if os.path.exists(client_secret_path) and not os.path.exists(oauth_keys_path):
                import shutil
                shutil.copy2(client_secret_path, oauth_keys_path)
                logger.info(f"Copied OAuth keys to {oauth_keys_path}")
                
        except Exception as e:
            logger.error(f"Failed to setup OAuth config: {e}")
    
    async def call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the Gmail MCP server."""
        try:
            # Prepare MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                }
            }
            
            # Call the MCP server
            process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=json.dumps(mcp_request))
            
            if process.returncode != 0:
                logger.error(f"Gmail MCP server error: {stderr}")
                return {"success": False, "error": stderr}
            
            # Parse response
            response = json.loads(stdout)
            return {"success": True, "data": response}
            
        except Exception as e:
            logger.error(f"Failed to call Gmail MCP tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_messages(self, max_results: int = 10, query: str = "") -> str:
        """List Gmail messages."""
        result = await self.call_mcp_tool("list_messages", {
            "maxResults": max_results,
            "q": query
        })
        return json.dumps(result, indent=2)
    
    async def send_message(self, to: str, subject: str, body: str) -> str:
        """Send a Gmail message."""
        result = await self.call_mcp_tool("send_message", {
            "to": [to],
            "subject": subject,
            "body": body
        })
        return json.dumps(result, indent=2)
    
    async def get_message(self, message_id: str) -> str:
        """Get a specific Gmail message."""
        result = await self.call_mcp_tool("get_message", {
            "id": message_id
        })
        return json.dumps(result, indent=2)
```

### 2. Gmail Agent Node (`backend/app/agents/gmail_agent_node.py`)

**Purpose**: LangGraph agent node that uses Gmail MCP tools.

```python
from typing import Dict, Any
import logging
from ..services.gmail_mcp_service import GmailMCPService

logger = logging.getLogger(__name__)

class GmailAgentNode:
    """Gmail agent node for LangGraph workflows."""
    
    def __init__(self):
        self.gmail_service = GmailMCPService()
        self.name = "gmail_agent"
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process Gmail-related tasks."""
        try:
            task = state.get("task", "")
            
            if "read emails" in task.lower() or "check emails" in task.lower():
                result = await self._read_recent_emails()
            elif "send email" in task.lower():
                result = await self._send_email(state)
            else:
                result = "Gmail agent: Task not recognized. Available actions: read emails, send email"
            
            return {
                **state,
                "gmail_result": result,
                "last_agent": self.name
            }
            
        except Exception as e:
            logger.error(f"Gmail agent error: {e}")
            return {
                **state,
                "gmail_result": f"Gmail agent error: {str(e)}",
                "last_agent": self.name
            }
    
    async def _read_recent_emails(self) -> str:
        """Read recent emails from Gmail."""
        try:
            messages = await self.gmail_service.list_messages(max_results=10)
            return f"Retrieved recent emails: {messages}"
        except Exception as e:
            return f"Failed to read emails: {str(e)}"
    
    async def _send_email(self, state: Dict[str, Any]) -> str:
        """Send an email via Gmail."""
        try:
            # Extract email details from state or use defaults
            to = state.get("email_to", "")
            subject = state.get("email_subject", "Automated Email")
            body = state.get("email_body", "This is an automated email from MACAE.")
            
            if not to:
                return "Cannot send email: recipient address not specified"
            
            result = await self.gmail_service.send_message(to, subject, body)
            return f"Email sent: {result}"
        except Exception as e:
            return f"Failed to send email: {str(e)}"
```

### 3. OAuth Setup Script (`backend/setup_gmail_oauth.py`)

**Purpose**: One-time script to complete OAuth authentication.

```python
#!/usr/bin/env python3
"""
Gmail OAuth Setup Script
Run this once to authenticate with Gmail using the existing client_secret.json
"""

import subprocess
import os
import sys

def setup_gmail_oauth():
    """Setup Gmail OAuth authentication."""
    print("Setting up Gmail OAuth authentication...")
    
    # Check if client_secret.json exists
    if not os.path.exists("client_secret.json"):
        print("Error: client_secret.json not found in current directory")
        return False
    
    # Create .gmail-mcp directory
    config_dir = os.path.expanduser("~/.gmail-mcp")
    os.makedirs(config_dir, exist_ok=True)
    
    # Copy client_secret.json to expected location
    oauth_keys_path = os.path.join(config_dir, "gcp-oauth.keys.json")
    if not os.path.exists(oauth_keys_path):
        import shutil
        shutil.copy2("client_secret.json", oauth_keys_path)
        print(f"Copied OAuth keys to {oauth_keys_path}")
    
    # Run OAuth authentication
    try:
        print("Starting OAuth authentication...")
        print("A browser window will open. Please sign in and grant permissions.")
        
        result = subprocess.run(
            ["npx", "@shinzolabs/gmail-mcp", "auth"],
            check=True,
            capture_output=True,
            text=True
        )
        
        print("OAuth authentication completed successfully!")
        print("Gmail MCP integration is now ready to use.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"OAuth authentication failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: npx not found. Please install Node.js and npm.")
        return False

if __name__ == "__main__":
    success = setup_gmail_oauth()
    sys.exit(0 if success else 1)
```

## Data Models

### Simplified Email Message Structure

```python
@dataclass
class SimpleGmailMessage:
    """Simplified Gmail message structure for agent use."""
    id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body_text: str
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do.*

### Property 1: OAuth Authentication Success
*For any* valid client_secret.json file, the OAuth authentication process should complete successfully and store refresh tokens
**Validates: Requirements 1.1, 1.2**

### Property 2: Email Retrieval Consistency
*For any* request to list messages, the system should return structured email data with consistent field formats
**Validates: Requirements 2.1, 2.2**

### Property 3: Email Sending Reliability
*For any* valid email composition request (with recipient, subject, body), the system should successfully send the email and return confirmation
**Validates: Requirements 3.1, 3.2**

### Property 4: MCP Integration Compatibility
*For any* Gmail MCP tool call, the integration should work seamlessly with the existing FastMCP server pattern
**Validates: Requirements 4.2**

### Property 5: Configuration Simplicity
*For any* deployment using the existing client_secret.json, the system should require no additional configuration files or infrastructure
**Validates: Requirements 5.1, 5.2, 5.3**

## Error Handling

### Authentication Errors
- **OAuth Flow Failures**: Clear instructions to run setup_gmail_oauth.py
- **Token Expiration**: Automatic refresh handled by Gmail MCP server
- **Missing Credentials**: Clear error messages pointing to setup requirements

### MCP Communication Errors
- **Server Unavailable**: Graceful fallback with informative error messages
- **Tool Call Failures**: Structured error responses for agent decision-making
- **Timeout Handling**: Reasonable timeouts with retry logic

## Testing Strategy

### Unit Testing
- Test Gmail MCP service wrapper with mocked subprocess calls
- Test Gmail agent node with various task inputs
- Test OAuth setup script with mock file operations

### Integration Testing
- Test complete OAuth flow with real Gmail API
- Test email reading and sending with test Gmail account
- Test agent integration within LangGraph workflow

### Property-Based Testing
- Use **Hypothesis** for Python property-based testing
- Generate random email content and verify processing consistency
- Test authentication flows with various credential configurations
- Each property-based test should run a minimum of 100 iterations

## Performance Considerations

### Minimal Overhead
- **Subprocess Calls**: Efficient subprocess management for MCP server communication
- **Caching**: Cache authentication tokens to avoid repeated OAuth flows
- **Connection Reuse**: Let Gmail MCP server handle connection pooling

### Resource Management
- **Process Lifecycle**: Proper cleanup of subprocess resources
- **Memory Usage**: Minimal memory footprint through subprocess delegation
- **Error Recovery**: Graceful handling of subprocess failures

## Security and Privacy

### Credential Management
- **OAuth Tokens**: Handled entirely by Gmail MCP server
- **File Permissions**: Secure permissions on OAuth configuration files
- **No Credential Storage**: No additional credential storage in MACAE system

### Data Protection
- **Email Content**: Minimal processing and storage of email content
- **Access Control**: Leverage existing Gmail MCP server security features
- **Audit Trail**: Basic logging of Gmail operations for troubleshooting

## Deployment

### Prerequisites
- Node.js 18+ installed
- Existing client_secret.json file
- Internet access for OAuth flow

### Setup Steps
1. Run `python3 backend/setup_gmail_oauth.py` once for OAuth authentication
2. Gmail MCP server will be automatically called via npx when needed
3. No additional infrastructure or configuration required

### Monitoring
- Basic logging of Gmail operations
- Error tracking for subprocess communication
- Simple health checks for Gmail MCP server availability