#!/usr/bin/env python3
"""
Test script to validate Salesforce CLI authentication.
This script tests:
1. Salesforce CLI connectivity with configured org
2. SALESFORCE_ORG_ALIAS environment variable
3. Sample SOQL query execution to confirm authentication
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Dict, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SalesforceCLIAuthTest:
    """Test class for Salesforce CLI authentication validation."""
    
    def __init__(self):
        self.org_alias = os.getenv("SALESFORCE_ORG_ALIAS", "DEFAULT_TARGET_ORG")
        self.enabled = os.getenv("SALESFORCE_MCP_ENABLED", "false").lower() == "true"
        
    def test_environment_variables(self) -> bool:
        """Test that required environment variables are set."""
        logger.info("Testing environment variables...")
        
        # Check SALESFORCE_MCP_ENABLED
        if not self.enabled:
            logger.error("❌ SALESFORCE_MCP_ENABLED is not set to 'true'")
            logger.info(f"Current value: {os.getenv('SALESFORCE_MCP_ENABLED', 'not set')}")
            return False
        
        logger.info(f"✅ SALESFORCE_MCP_ENABLED: {self.enabled}")
        
        # Check SALESFORCE_ORG_ALIAS
        if not self.org_alias or self.org_alias == "DEFAULT_TARGET_ORG":
            logger.warning("⚠️  SALESFORCE_ORG_ALIAS is using default value")
            logger.info(f"Current value: {self.org_alias}")
            logger.info("Consider setting a specific org alias")
        else:
            logger.info(f"✅ SALESFORCE_ORG_ALIAS: {self.org_alias}")
        
        return True
    
    async def test_salesforce_cli_installed(self) -> bool:
        """Test that Salesforce CLI is installed and accessible."""
        logger.info("Testing Salesforce CLI installation...")
        
        try:
            # Check if 'sf' command is available
            process = await asyncio.create_subprocess_exec(
                "sf", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version_info = stdout.decode().strip()
                logger.info(f"✅ Salesforce CLI installed: {version_info}")
                return True
            else:
                logger.error("❌ Salesforce CLI not found or not working")
                logger.error(f"Error: {stderr.decode()}")
                return False
                
        except FileNotFoundError:
            logger.error("❌ Salesforce CLI ('sf' command) not found")
            logger.info("Install with: npm install -g @salesforce/cli")
            return False
        except Exception as e:
            logger.error(f"❌ Error checking Salesforce CLI: {e}")
            return False
    
    async def test_org_list(self) -> bool:
        """Test listing Salesforce orgs to verify authentication."""
        logger.info("Testing Salesforce org listing...")
        
        try:
            # List orgs using Salesforce CLI
            process = await asyncio.create_subprocess_exec(
                "sf", "org", "list", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result_data = json.loads(stdout.decode())
                sf_result = result_data.get("result", {})
                
                # Combine scratch and non-scratch orgs
                orgs = sf_result.get("nonScratchOrgs", []) + sf_result.get("scratchOrgs", [])
                
                if orgs:
                    logger.info(f"✅ Found {len(orgs)} connected org(s):")
                    for org in orgs:
                        alias = org.get("alias", org.get("username", "No alias"))
                        username = org.get("username", "Unknown")
                        is_default = org.get("isDefaultUsername", False)
                        default_marker = " (default)" if is_default else ""
                        logger.info(f"  - {alias}: {username}{default_marker}")
                    
                    # Check if our configured org alias exists
                    org_aliases = [org.get("alias", org.get("username")) for org in orgs]
                    if self.org_alias in org_aliases:
                        logger.info(f"✅ Configured org alias '{self.org_alias}' found in connected orgs")
                        return True
                    else:
                        logger.warning(f"⚠️  Configured org alias '{self.org_alias}' not found in connected orgs")
                        logger.info(f"Available aliases: {org_aliases}")
                        return False
                else:
                    logger.error("❌ No connected Salesforce orgs found")
                    logger.info("Authenticate with: sf org login web")
                    return False
            else:
                error_msg = stderr.decode()
                logger.error(f"❌ Failed to list orgs: {error_msg}")
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse org list JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error listing orgs: {e}")
            return False
    
    async def test_soql_query(self) -> bool:
        """Test executing a sample SOQL query to confirm authentication."""
        logger.info("Testing SOQL query execution...")
        
        # Simple SOQL query to test authentication
        test_query = "SELECT Id, Name FROM Organization LIMIT 1"
        
        try:
            # Execute SOQL query
            process = await asyncio.create_subprocess_exec(
                "sf", "data", "query",
                "--query", test_query,
                "--target-org", self.org_alias,
                "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result_data = json.loads(stdout.decode())
                sf_result = result_data.get("result", {})
                
                total_size = sf_result.get("totalSize", 0)
                records = sf_result.get("records", [])
                
                if total_size > 0 and records:
                    org_record = records[0]
                    org_name = org_record.get("Name", "Unknown")
                    org_id = org_record.get("Id", "Unknown")
                    
                    logger.info(f"✅ SOQL query successful!")
                    logger.info(f"Organization: {org_name} (ID: {org_id})")
                    logger.info(f"Query returned {total_size} record(s)")
                    return True
                else:
                    logger.error("❌ SOQL query returned no results")
                    return False
            else:
                error_msg = stderr.decode()
                logger.error(f"❌ SOQL query failed: {error_msg}")
                
                # Check for common authentication errors
                if "INVALID_LOGIN" in error_msg or "authentication" in error_msg.lower():
                    logger.info("💡 Authentication issue detected. Try: sf org login web")
                elif "No org configuration found" in error_msg:
                    logger.info(f"💡 Org '{self.org_alias}' not found. Check SALESFORCE_ORG_ALIAS")
                
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse SOQL query JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error executing SOQL query: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all authentication validation tests."""
        results = {}
        
        # Test 1: Environment variables
        logger.info("=" * 60)
        logger.info("TEST 1: Environment Variables")
        logger.info("=" * 60)
        results['environment_variables'] = self.test_environment_variables()
        
        # Test 2: Salesforce CLI installation
        logger.info("=" * 60)
        logger.info("TEST 2: Salesforce CLI Installation")
        logger.info("=" * 60)
        results['cli_installed'] = await self.test_salesforce_cli_installed()
        
        if not results['cli_installed']:
            logger.error("❌ Salesforce CLI not available, skipping remaining tests")
            return results
        
        # Test 3: Org listing
        logger.info("=" * 60)
        logger.info("TEST 3: Org Authentication")
        logger.info("=" * 60)
        results['org_authentication'] = await self.test_org_list()
        
        if not results['org_authentication']:
            logger.error("❌ Org authentication failed, skipping SOQL test")
            return results
        
        # Test 4: SOQL query
        logger.info("=" * 60)
        logger.info("TEST 4: SOQL Query Execution")
        logger.info("=" * 60)
        results['soql_query'] = await self.test_soql_query()
        
        return results
    
    def print_results(self, results: Dict[str, bool]):
        """Print test results summary."""
        logger.info("=" * 60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        all_passed = True
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
            if not passed:
                all_passed = False
        
        logger.info("=" * 60)
        if all_passed:
            logger.info("🎉 ALL TESTS PASSED - Salesforce CLI authentication validated!")
        else:
            logger.error("❌ SOME TESTS FAILED - Check configuration and authentication")
            logger.info("")
            logger.info("TROUBLESHOOTING STEPS:")
            logger.info("1. Install Salesforce CLI: npm install -g @salesforce/cli")
            logger.info("2. Authenticate with your org: sf org login web")
            logger.info("3. Set correct org alias in .env: SALESFORCE_ORG_ALIAS=your_org_alias")
            logger.info("4. Enable Salesforce MCP: SALESFORCE_MCP_ENABLED=true")
        logger.info("=" * 60)
        
        return all_passed


async def main():
    """Main test execution."""
    logger.info("🚀 Starting Salesforce CLI Authentication Validation")
    
    # Create test instance
    tester = SalesforceCLIAuthTest()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print results
        success = tester.print_results(results)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())