"""
Salesforce MCP Service - Provides Salesforce tools via MCP protocol.
"""

import logging
import os
import json
import asyncio
from typing import Dict, Any, List, Optional

from core.factory import MCPToolBase, Domain

logger = logging.getLogger(__name__)


class SalesforceService(MCPToolBase):
    """Salesforce service providing SOQL queries and org management via MCP."""
    
    def __init__(self):
        super().__init__(Domain.SALESFORCE)  # Use dedicated SALESFORCE domain
        self.org_alias = os.getenv("SALESFORCE_ORG_ALIAS", "DEFAULT_TARGET_ORG")
        self.enabled = os.getenv("SALESFORCE_MCP_ENABLED", "false").lower() == "true"
        
        logger.info(f"Salesforce MCP Service initialized (enabled: {self.enabled})")
    
    # Core methods (private, not decorated) - contain all business logic
    async def _execute_soql_query(self, query: str, org_alias: str = None) -> Dict[str, Any]:
        """Core method to execute a SOQL query against Salesforce using the Salesforce CLI."""
        if not self.enabled:
            logger.info("Salesforce MCP disabled, returning mock data")
            return self._get_mock_query_result(query)
        
        try:
            # Use the provided org_alias or fall back to default
            target_org = org_alias or self.org_alias
            
            logger.info(f"Executing SOQL query via CLI: {query[:100]}...")
            
            # Execute Salesforce CLI command
            cmd = [
                "sf", "data", "query",
                "--query", query,
                "--target-org", target_org,
                "--json"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result_data = json.loads(stdout.decode())
                sf_result = result_data.get("result", {})
                
                return {
                    "success": True,
                    "totalSize": sf_result.get("totalSize", 0),
                    "records": sf_result.get("records", [])
                }
            else:
                error_msg = stderr.decode()
                logger.error(f"Salesforce CLI query failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"Salesforce SOQL query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_orgs(self) -> Dict[str, Any]:
        """Core method to list connected Salesforce orgs using the Salesforce CLI."""
        if not self.enabled:
            logger.info("Salesforce MCP disabled, returning mock data")
            return {
                "success": True,
                "orgs": [
                    {
                        "alias": "MockDevOrg",
                        "username": "demo@example.com",
                        "orgId": "00Dxx0000001gEREAY",
                        "instanceUrl": "https://na1.salesforce.com",
                        "isDefaultOrg": True
                    }
                ]
            }
        
        try:
            logger.info("Listing Salesforce orgs via CLI...")
            
            # Execute Salesforce CLI command
            cmd = ["sf", "org", "list", "--json"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result_data = json.loads(stdout.decode())
                sf_result = result_data.get("result", {})
                
                # Combine scratch and non-scratch orgs
                orgs = sf_result.get("nonScratchOrgs", []) + sf_result.get("scratchOrgs", [])
                
                # Format org data
                formatted_orgs = []
                for org in orgs:
                    formatted_orgs.append({
                        "alias": org.get("alias", org.get("username")),
                        "username": org.get("username"),
                        "orgId": org.get("orgId"),
                        "instanceUrl": org.get("instanceUrl"),
                        "isDefaultOrg": org.get("isDefaultUsername", False)
                    })
                
                return {
                    "success": True,
                    "orgs": formatted_orgs
                }
            else:
                error_msg = stderr.decode()
                logger.error(f"Salesforce CLI org list failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"Salesforce org listing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_accounts(self, account_name: str = None, limit: int = 5, org_alias: str = None) -> Dict[str, Any]:
        """Core method to get account information from Salesforce."""
        # Build SOQL query
        if account_name:
            # Escape single quotes in account name
            account_name_escaped = account_name.replace("'", "\\'")
            query = f"SELECT Id, Name, Phone, Industry, AnnualRevenue FROM Account WHERE Name LIKE '%{account_name_escaped}%' ORDER BY CreatedDate DESC LIMIT {limit}"
        else:
            query = f"SELECT Id, Name, Phone, Industry, AnnualRevenue FROM Account ORDER BY CreatedDate DESC LIMIT {limit}"
        
        # Use the core SOQL query method (not the decorated tool)
        return await self._execute_soql_query(query, org_alias)
    
    async def _get_opportunities(self, limit: int = 5, stage: str = None, org_alias: str = None) -> Dict[str, Any]:
        """Core method to get opportunity information from Salesforce."""
        if stage:
            # Escape single quotes in stage name
            stage_escaped = stage.replace("'", "\\'")
            query = f"SELECT Id, Name, StageName, Amount, CloseDate, Account.Name FROM Opportunity WHERE StageName = '{stage_escaped}' ORDER BY CreatedDate DESC LIMIT {limit}"
        else:
            query = f"SELECT Id, Name, StageName, Amount, CloseDate, Account.Name FROM Opportunity ORDER BY CreatedDate DESC LIMIT {limit}"
        return await self._execute_soql_query(query, org_alias)
    
    async def _get_contacts(self, limit: int = 5, account_name: str = None, org_alias: str = None) -> Dict[str, Any]:
        """Core method to get contact information from Salesforce."""
        if account_name:
            # Escape single quotes in account name
            account_name_escaped = account_name.replace("'", "\\'")
            query = f"SELECT Id, Name, Email, Phone, Title, Account.Name FROM Contact WHERE Account.Name LIKE '%{account_name_escaped}%' ORDER BY CreatedDate DESC LIMIT {limit}"
        else:
            query = f"SELECT Id, Name, Email, Phone, Title, Account.Name FROM Contact ORDER BY CreatedDate DESC LIMIT {limit}"
        return await self._execute_soql_query(query, org_alias)
    
    async def _search_records(self, search_term: str, objects: List[str] = None, org_alias: str = None) -> Dict[str, Any]:
        """Core method to search for records across multiple Salesforce objects."""
        if not objects:
            objects = ["Account", "Contact", "Opportunity"]
        
        # For now, just search accounts as a simplified implementation
        return await self._get_accounts(account_name=search_term, limit=10, org_alias=org_alias)

    def register_tools(self, mcp) -> None:
        """Register Salesforce tools with the MCP server."""
        
        # Capture self reference for closures
        service_instance = self
        
        @mcp.tool(tags={self.domain.value})
        async def salesforce_soql_query(query: str, org_alias: str = None) -> Dict[str, Any]:
            """Execute a SOQL query against Salesforce using the Salesforce CLI."""
            return await service_instance._execute_soql_query(query, org_alias)
        
        @mcp.tool(tags={self.domain.value})
        async def salesforce_list_orgs() -> Dict[str, Any]:
            """List connected Salesforce orgs using the Salesforce CLI."""
            return await service_instance._list_orgs()
        
        @mcp.tool(tags={self.domain.value})
        async def salesforce_get_accounts(
            account_name: str = None, 
            limit: int = 5, 
            org_alias: str = None
        ) -> Dict[str, Any]:
            """Get account information from Salesforce."""
            return await service_instance._get_accounts(account_name, limit, org_alias)
        
        @mcp.tool(tags={self.domain.value})
        async def salesforce_get_opportunities(
            limit: int = 5, 
            stage: str = None,
            org_alias: str = None
        ) -> Dict[str, Any]:
            """Get opportunity information from Salesforce."""
            return await service_instance._get_opportunities(limit, stage, org_alias)
        
        @mcp.tool(tags={self.domain.value})
        async def salesforce_get_contacts(
            limit: int = 5, 
            account_name: str = None,
            org_alias: str = None
        ) -> Dict[str, Any]:
            """Get contact information from Salesforce."""
            return await service_instance._get_contacts(limit, account_name, org_alias)
        
        @mcp.tool(tags={self.domain.value})
        async def salesforce_search_records(
            search_term: str,
            objects: List[str] = None,
            org_alias: str = None
        ) -> Dict[str, Any]:
            """Search for records across multiple Salesforce objects."""
            return await service_instance._search_records(search_term, objects, org_alias)
    
    def _get_mock_query_result(self, query: str) -> Dict[str, Any]:
        """Generate mock query results based on query content."""
        query_lower = query.lower()
        
        if "account" in query_lower:
            return {
                "success": True,
                "totalSize": 3,
                "records": [
                    {
                        "Id": "001xx000003DGb2AAG",
                        "Name": "Acme Corporation",
                        "Phone": "(415) 555-1234",
                        "Industry": "Technology",
                        "AnnualRevenue": 5000000
                    },
                    {
                        "Id": "001xx000003DGb3AAG",
                        "Name": "Global Industries",
                        "Phone": "(212) 555-5678",
                        "Industry": "Manufacturing",
                        "AnnualRevenue": 12000000
                    },
                    {
                        "Id": "001xx000003DGb4AAG",
                        "Name": "Tech Solutions Inc",
                        "Phone": "(650) 555-9012",
                        "Industry": "Technology",
                        "AnnualRevenue": 8500000
                    }
                ]
            }
        elif "opportunity" in query_lower:
            return {
                "success": True,
                "totalSize": 2,
                "records": [
                    {
                        "Id": "006xx000001T2jzAAC",
                        "Name": "Enterprise Software Deal",
                        "StageName": "Negotiation/Review",
                        "Amount": 250000,
                        "CloseDate": "2025-03-15",
                        "Account": {"Name": "Acme Corporation"}
                    },
                    {
                        "Id": "006xx000001T2k0AAC",
                        "Name": "Cloud Migration Project",
                        "StageName": "Proposal/Price Quote",
                        "Amount": 180000,
                        "CloseDate": "2025-04-01",
                        "Account": {"Name": "Global Industries"}
                    }
                ]
            }
        elif "contact" in query_lower:
            return {
                "success": True,
                "totalSize": 2,
                "records": [
                    {
                        "Id": "003xx000001T2jzAAC",
                        "Name": "John Smith",
                        "Email": "john.smith@acme.com",
                        "Phone": "(415) 555-1234",
                        "Title": "VP of Engineering",
                        "Account": {"Name": "Acme Corporation"}
                    },
                    {
                        "Id": "003xx000001T2k0AAC",
                        "Name": "Sarah Johnson",
                        "Email": "sarah.j@globalind.com",
                        "Phone": "(212) 555-5678",
                        "Title": "CTO",
                        "Account": {"Name": "Global Industries"}
                    }
                ]
            }
        else:
            return {
                "success": True,
                "totalSize": 0,
                "records": []
            }
    
    @property
    def tool_count(self) -> int:
        """Return the number of tools provided by this service."""
        return 6  # salesforce_soql_query, salesforce_list_orgs, salesforce_get_accounts, salesforce_get_opportunities, salesforce_get_contacts, salesforce_search_records