# Salesforce MCP Server Integration Guide

This guide walks you through setting up a Salesforce MCP server and integrating it with your Multi-Agent application.

## Overview

We'll integrate the Salesforce DX MCP server as a tool available to your LangGraph agents, allowing them to query and interact with Salesforce data.

## Phase 1: Prerequisites & Environment Setup

### 1.1 Verify Node.js & npm
✅ **Already Installed**
- Node.js: v22.12.0
- npm: v11.5.2

### 1.2 Install Salesforce CLI

```bash
npm install -g @salesforce/cli
```

Verify installation:
```bash
sf --version
```

### 1.3 Authorize Your Salesforce Dev Org

1. Log in to your Salesforce Developer Org:
```bash
sf org login web
```

2. Follow the browser prompts to authenticate
3. The CLI will assign an org alias (e.g., `MyDevOrg`)
4. Verify your org is connected:
```bash
sf org list
```

### 1.4 Create Salesforce DX Project (Optional)

If you want to keep Salesforce configuration separate:
```bash
mkdir salesforce-mcp-config
cd salesforce-mcp-config
sf project generate -n SalesforceMCP
cd SalesforceMCP
```

## Phase 2: Configure MCP Server for Your Application

### 2.1 Create MCP Configuration

We'll configure the Salesforce MCP server to be accessible by your backend agents.

Create or update `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "salesforce": {
      "command": "npx",
      "args": [
        "-y",
        "@salesforce/mcp@latest",
        "--orgs",
        "DEFAULT_TARGET_ORG",
        "--toolsets",
        "data,orgs"
      ],
      "disabled": false,
      "autoApprove": [
        "data/run_soql_query",
        "orgs/list_orgs"
      ]
    }
  }
}
```

**Configuration Explained:**
- `command`: Uses `npx` to run the Salesforce MCP server
- `args`: 
  - `-y`: Auto-confirm package installation
  - `@salesforce/mcp@latest`: Latest Salesforce MCP package
  - `--orgs DEFAULT_TARGET_ORG`: Use your authorized org
  - `--toolsets data,orgs`: Expose data and org management tools
- `autoApprove`: Pre-approve safe read-only operations

### 2.2 Alternative: Use Specific Org Alias

If you want to use a specific org alias instead of the default:

```json
{
  "mcpServers": {
    "salesforce": {
      "command": "npx",
      "args": [
        "-y",
        "@salesforce/mcp@latest",
        "--orgs",
        "MyDevOrg",
        "--toolsets",
        "data,orgs,apex"
      ],
      "disabled": false
    }
  }
}
```

## Phase 3: Backend Integration

### 3.1 Create Salesforce MCP Client Service

Create `backend/app/services/salesforce_mcp_service.py`:

```python
"""Salesforce MCP client service for interacting with Salesforce data."""
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SalesforceMCPService:
    """Service for interacting with Salesforce via MCP."""
    
    def __init__(self):
        self.mcp_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize MCP client connection."""
        if self._initialized:
            return
        
        try:
            # TODO: Initialize MCP client connection
            # This will connect to the Salesforce MCP server
            logger.info("Initializing Salesforce MCP client...")
            self._initialized = True
            logger.info("✅ Salesforce MCP client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Salesforce MCP client: {e}")
            raise
    
    async def run_soql_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a SOQL query against Salesforce.
        
        Args:
            query: SOQL query string
            
        Returns:
            Query results as dictionary
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Executing SOQL query: {query}")
            
            # TODO: Call MCP tool
            # result = await self.mcp_client.call_tool(
            #     "data/run_soql_query",
            #     {"query": query}
            # )
            
            # Mock response for now
            result = {
                "success": True,
                "records": [],
                "totalSize": 0
            }
            
            logger.info(f"Query returned {result.get('totalSize', 0)} records")
            return result
            
        except Exception as e:
            logger.error(f"SOQL query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_orgs(self) -> List[Dict[str, Any]]:
        """
        List connected Salesforce orgs.
        
        Returns:
            List of org information
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info("Listing Salesforce orgs...")
            
            # TODO: Call MCP tool
            # result = await self.mcp_client.call_tool("orgs/list_orgs", {})
            
            # Mock response for now
            result = {
                "success": True,
                "orgs": []
            }
            
            return result.get("orgs", [])
            
        except Exception as e:
            logger.error(f"Failed to list orgs: {e}")
            return []
    
    async def get_account_info(self, account_name: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        """
        Get account information from Salesforce.
        
        Args:
            account_name: Optional account name filter
            limit: Maximum number of records to return
            
        Returns:
            Account information
        """
        if account_name:
            query = f"SELECT Id, Name, Phone, Industry, AnnualRevenue FROM Account WHERE Name LIKE '%{account_name}%' ORDER BY CreatedDate DESC LIMIT {limit}"
        else:
            query = f"SELECT Id, Name, Phone, Industry, AnnualRevenue FROM Account ORDER BY CreatedDate DESC LIMIT {limit}"
        
        return await self.run_soql_query(query)
    
    async def get_opportunity_info(self, limit: int = 5) -> Dict[str, Any]:
        """
        Get opportunity information from Salesforce.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            Opportunity information
        """
        query = f"SELECT Id, Name, StageName, Amount, CloseDate, Account.Name FROM Opportunity ORDER BY CreatedDate DESC LIMIT {limit}"
        return await self.run_soql_query(query)


# Singleton instance
_salesforce_service = None


def get_salesforce_service() -> SalesforceMCPService:
    """Get or create Salesforce MCP service instance."""
    global _salesforce_service
    if _salesforce_service is None:
        _salesforce_service = SalesforceMCPService()
    return _salesforce_service
```

### 3.2 Add Salesforce Agent Node

Create `backend/app/agents/salesforce_node.py`:

```python
"""Salesforce agent node for LangGraph."""
import logging
from typing import Dict, Any

from app.agents.state import AgentState
from app.services.salesforce_mcp_service import get_salesforce_service

logger = logging.getLogger(__name__)


async def salesforce_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Salesforce agent node - handles Salesforce data queries and operations.
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Salesforce Agent processing task for plan {plan_id}")
    
    try:
        sf_service = get_salesforce_service()
        await sf_service.initialize()
        
        # Analyze task to determine what Salesforce operation to perform
        task_lower = task.lower()
        
        if "account" in task_lower:
            # Query accounts
            result = await sf_service.get_account_info(limit=10)
            
            if result.get("success"):
                records = result.get("records", [])
                response = f"Salesforce Agent: Found {len(records)} accounts:\n\n"
                for record in records:
                    response += f"- {record.get('Name', 'N/A')}\n"
                    response += f"  Phone: {record.get('Phone', 'N/A')}\n"
                    response += f"  Industry: {record.get('Industry', 'N/A')}\n\n"
            else:
                response = f"Salesforce Agent: Failed to query accounts - {result.get('error', 'Unknown error')}"
        
        elif "opportunity" in task_lower or "deal" in task_lower:
            # Query opportunities
            result = await sf_service.get_opportunity_info(limit=10)
            
            if result.get("success"):
                records = result.get("records", [])
                response = f"Salesforce Agent: Found {len(records)} opportunities:\n\n"
                for record in records:
                    response += f"- {record.get('Name', 'N/A')}\n"
                    response += f"  Stage: {record.get('StageName', 'N/A')}\n"
                    response += f"  Amount: ${record.get('Amount', 0):,.2f}\n"
                    response += f"  Close Date: {record.get('CloseDate', 'N/A')}\n\n"
            else:
                response = f"Salesforce Agent: Failed to query opportunities - {result.get('error', 'Unknown error')}"
        
        else:
            # Generic Salesforce query
            response = "Salesforce Agent: I can help you query Salesforce data. Please specify what you'd like to retrieve (accounts, opportunities, etc.)"
        
        return {
            "messages": [response],
            "current_agent": "Salesforce",
            "final_result": response
        }
        
    except Exception as e:
        logger.error(f"Salesforce agent error: {e}")
        error_response = f"Salesforce Agent: Error processing request - {str(e)}"
        return {
            "messages": [error_response],
            "current_agent": "Salesforce",
            "final_result": error_response
        }
```

### 3.3 Update LangGraph to Include Salesforce Agent

Update `backend/app/agents/graph.py`:

```python
# Add import
from app.agents.salesforce_node import salesforce_agent_node

# In create_agent_graph(), add the node:
workflow.add_node("salesforce", salesforce_agent_node)

# Add routing from planner:
workflow.add_conditional_edges(
    "planner",
    supervisor_router,
    {
        "invoice": "invoice",
        "closing": "closing",
        "audit": "audit",
        "salesforce": "salesforce",  # Add this
        "end": END
    }
)

# Add edge to end:
workflow.add_edge("salesforce", END)
```

### 3.4 Update Supervisor Router

Update `backend/app/agents/supervisor.py` to route Salesforce-related tasks:

```python
def supervisor_router(state: AgentState) -> str:
    """Route to appropriate agent based on task content."""
    task = state["task_description"].lower()
    
    # Check for Salesforce keywords
    if any(word in task for word in ["salesforce", "account", "opportunity", "lead", "contact", "soql"]):
        return "salesforce"
    
    # ... existing routing logic ...
```

## Phase 4: Testing

### 4.1 Test Salesforce CLI Connection

```bash
# List your orgs
sf org list

# Test a simple query
sf data query --query "SELECT Id, Name FROM Account LIMIT 5" --target-org MyDevOrg
```

### 4.2 Test MCP Server Standalone

```bash
# Start the MCP server manually
npx -y @salesforce/mcp@latest --orgs DEFAULT_TARGET_ORG --toolsets data,orgs
```

### 4.3 Test Backend Integration

Create a test script `backend/test_salesforce_mcp.py`:

```python
"""Test Salesforce MCP integration."""
import asyncio
import logging
from app.services.salesforce_mcp_service import get_salesforce_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_salesforce_connection():
    """Test Salesforce MCP connection."""
    logger.info("Testing Salesforce MCP connection...")
    
    sf_service = get_salesforce_service()
    await sf_service.initialize()
    
    # Test listing orgs
    logger.info("Testing list_orgs...")
    orgs = await sf_service.list_orgs()
    logger.info(f"Found {len(orgs)} orgs")
    
    # Test account query
    logger.info("Testing account query...")
    result = await sf_service.get_account_info(limit=5)
    logger.info(f"Query result: {result}")
    
    logger.info("✅ Tests complete!")


if __name__ == "__main__":
    asyncio.run(test_salesforce_connection())
```

Run the test:
```bash
cd backend
python3 test_salesforce_mcp.py
```

### 4.4 Test via Frontend

Submit a task through your frontend:
```
"Retrieve the 5 most recently created accounts from Salesforce with their names and phone numbers"
```

The planner should route this to the Salesforce agent, which will query the data and return results.

## Phase 5: Environment Configuration

### 5.1 Add Salesforce Configuration to Backend .env

```bash
# Salesforce MCP Configuration
SALESFORCE_MCP_ENABLED=true
SALESFORCE_ORG_ALIAS=DEFAULT_TARGET_ORG
SALESFORCE_TOOLSETS=data,orgs,apex
```

### 5.2 Update Backend Configuration

Update `backend/app/config/settings.py` if needed to include Salesforce settings.

## Troubleshooting

### Issue: "sf: command not found"
**Solution:** Install Salesforce CLI globally:
```bash
npm install -g @salesforce/cli
```

### Issue: "No orgs found"
**Solution:** Authorize your org:
```bash
sf org login web
```

### Issue: MCP server not starting
**Solution:** Check Node.js version (requires 18+) and ensure npx is available:
```bash
node -v  # Should be 18+
npx --version
```

### Issue: SOQL query fails
**Solution:** 
1. Verify org is authorized: `sf org list`
2. Test query directly: `sf data query --query "SELECT Id FROM Account LIMIT 1"`
3. Check object permissions in Salesforce

## Next Steps

1. **Install Salesforce CLI** (Phase 1.2)
2. **Authorize your Dev Org** (Phase 1.3)
3. **Create MCP configuration** (Phase 2.1)
4. **Implement backend service** (Phase 3.1-3.4)
5. **Test integration** (Phase 4)

## Resources

- [Salesforce CLI Documentation](https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/)
- [Salesforce MCP Server](https://github.com/salesforce/mcp-server)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [SOQL Reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/)
