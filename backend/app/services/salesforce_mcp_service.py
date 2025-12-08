"""Salesforce MCP client service for interacting with Salesforce data."""
import logging
import asyncio
import json
import os
import subprocess
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SalesforceMCPService:
    """Service for interacting with Salesforce via MCP."""
    
    def __init__(self):
        self.mcp_client = None
        self._initialized = False
        self.org_alias = os.getenv("SALESFORCE_ORG_ALIAS", "DEFAULT_TARGET_ORG")
        self.enabled = os.getenv("SALESFORCE_MCP_ENABLED", "false").lower() == "true"
    
    async def initialize(self):
        """Initialize MCP client connection."""
        if self._initialized:
            return
        
        if not self.enabled:
            logger.warning("Salesforce MCP is disabled. Set SALESFORCE_MCP_ENABLED=true to enable.")
            return
        
        try:
            logger.info(f"Initializing Salesforce MCP client for org: {self.org_alias}...")
            
            # Test Salesforce CLI connection
            result = await self._run_sf_command(["org", "list", "--json"])
            if result.get("status") == 0:
                orgs = result.get("result", {}).get("nonScratchOrgs", [])
                logger.info(f"✅ Found {len(orgs)} connected Salesforce org(s)")
                self._initialized = True
            else:
                logger.error("Failed to connect to Salesforce CLI")
                raise Exception("Salesforce CLI not properly configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize Salesforce MCP client: {e}")
            raise
    
    async def _run_sf_command(self, args: List[str]) -> Dict[str, Any]:
        """
        Run Salesforce CLI command.
        
        Args:
            args: Command arguments
            
        Returns:
            Command result as dictionary
        """
        try:
            cmd = ["sf"] + args
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return json.loads(stdout.decode())
            else:
                logger.error(f"SF command failed: {stderr.decode()}")
                return {"status": 1, "error": stderr.decode()}
                
        except Exception as e:
            logger.error(f"Failed to run SF command: {e}")
            return {"status": 1, "error": str(e)}
    
    def is_enabled(self) -> bool:
        """Check if Salesforce MCP is enabled."""
        return self.enabled
    
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
        
        # If not enabled, use mock data for demonstration
        if not self.enabled:
            logger.info("Using mock data (Salesforce MCP not enabled)")
            return self._get_mock_query_result(query)
        
        try:
            logger.info(f"Executing SOQL query: {query}")
            
            # Use Salesforce CLI to execute query
            sf_result = await self._run_sf_command([
                "data", "query",
                "--query", query,
                "--target-org", self.org_alias,
                "--json"
            ])
            
            if sf_result.get("status") == 0:
                result_data = sf_result.get("result", {})
                result = {
                    "success": True,
                    "totalSize": result_data.get("totalSize", 0),
                    "records": result_data.get("records", [])
                }
                logger.info(f"Query returned {result.get('totalSize', 0)} records")
                return result
            else:
                error_msg = sf_result.get("error", "Unknown error")
                logger.error(f"Query failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
            
        except Exception as e:
            logger.error(f"SOQL query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
    
    async def list_orgs(self) -> List[Dict[str, Any]]:
        """
        List connected Salesforce orgs.
        
        Returns:
            List of org information
        """
        if not self._initialized:
            await self.initialize()
        
        # If not enabled, return mock org data
        if not self.enabled:
            logger.info("Using mock org data (Salesforce MCP not enabled)")
            return [
                {
                    "alias": "MockDevOrg",
                    "username": "demo@example.com",
                    "orgId": "00Dxx0000001gEREAY",
                    "instanceUrl": "https://na1.salesforce.com",
                    "isDefaultOrg": True
                }
            ]
        
        try:
            logger.info("Listing Salesforce orgs...")
            
            # Use Salesforce CLI to list orgs
            sf_result = await self._run_sf_command(["org", "list", "--json"])
            
            if sf_result.get("status") == 0:
                result_data = sf_result.get("result", {})
                orgs = result_data.get("nonScratchOrgs", []) + result_data.get("scratchOrgs", [])
                
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
                
                return formatted_orgs
            else:
                logger.error("Failed to list orgs")
                return []
            
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
            # Escape single quotes in account name
            account_name_escaped = account_name.replace("'", "\\'")
            query = f"SELECT Id, Name, Phone, Industry, AnnualRevenue FROM Account WHERE Name LIKE '%{account_name_escaped}%' ORDER BY CreatedDate DESC LIMIT {limit}"
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
    
    async def get_contact_info(self, limit: int = 5) -> Dict[str, Any]:
        """
        Get contact information from Salesforce.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            Contact information
        """
        query = f"SELECT Id, Name, Email, Phone, Title, Account.Name FROM Contact ORDER BY CreatedDate DESC LIMIT {limit}"
        return await self.run_soql_query(query)
    
    async def search_records(self, search_term: str, objects: List[str] = None) -> Dict[str, Any]:
        """
        Search for records across multiple objects using SOSL.
        
        Args:
            search_term: Search term
            objects: List of object types to search (default: Account, Contact, Opportunity)
            
        Returns:
            Search results
        """
        if not objects:
            objects = ["Account", "Contact", "Opportunity"]
        
        # For mock mode, just return account results
        logger.info(f"Searching for '{search_term}' in {', '.join(objects)}")
        return await self.get_account_info(account_name=search_term, limit=10)


# Singleton instance
_salesforce_service = None


def get_salesforce_service() -> SalesforceMCPService:
    """Get or create Salesforce MCP service instance."""
    global _salesforce_service
    if _salesforce_service is None:
        _salesforce_service = SalesforceMCPService()
    return _salesforce_service
