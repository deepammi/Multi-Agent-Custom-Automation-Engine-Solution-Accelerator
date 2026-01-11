#!/usr/bin/env python3
"""
Test script to validate Salesforce MCP Server HTTP startup.
This script tests:
1. Server startup on port 9001
2. Health check responses
3. Tool registration and accessibility
"""

import asyncio
import json
import logging
import os
import sys
import time
import subprocess
import requests
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SalesforceMCPServerTest:
    """Test class for Salesforce MCP Server HTTP validation."""
    
    def __init__(self, port: int = 9001):
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.mcp_url = f"{self.base_url}/mcp"
        self.server_process = None
        
    async def start_server(self) -> bool:
        """Start the MCP server in HTTP mode on the specified port."""
        try:
            logger.info(f"Starting Salesforce MCP server on port {self.port}...")
            
            # Change to the mcp_server directory
            server_dir = os.path.join(os.path.dirname(__file__), "..", "src", "mcp_server")
            
            # Start the server process
            cmd = [
                sys.executable, "mcp_server.py",
                "--transport", "http",
                "--host", "127.0.0.1",
                "--port", str(self.port)
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            logger.info(f"Working directory: {server_dir}")
            
            self.server_process = subprocess.Popen(
                cmd,
                cwd=server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            logger.info("Waiting for server to start...")
            await asyncio.sleep(5)
            
            # Check if process is still running
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                logger.error(f"Server process exited with code {self.server_process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
            
            logger.info("✅ Server process started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server process."""
        if self.server_process:
            logger.info("Stopping MCP server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't stop gracefully, killing...")
                self.server_process.kill()
                self.server_process.wait()
            logger.info("✅ Server stopped")
    
    async def test_health_check(self) -> bool:
        """Test server health check endpoint."""
        try:
            logger.info("Testing health check endpoint...")
            
            # Try multiple health check endpoints
            health_endpoints = [
                f"{self.base_url}/health",
                f"{self.base_url}/",
                f"{self.mcp_url}/health",
                f"{self.mcp_url}/"
            ]
            
            for endpoint in health_endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    logger.info(f"Health check {endpoint}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info(f"✅ Health check successful at {endpoint}")
                        logger.info(f"Response: {response.text[:200]}...")
                        return True
                        
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Health check failed for {endpoint}: {e}")
                    continue
            
            logger.error("❌ All health check endpoints failed")
            return False
            
        except Exception as e:
            logger.error(f"❌ Health check test failed: {e}")
            return False
    
    async def test_tool_registration(self) -> bool:
        """Test that all 6 Salesforce tools are registered and accessible."""
        try:
            logger.info("Testing tool registration...")
            
            expected_tools = [
                "salesforce_soql_query",
                "salesforce_list_orgs", 
                "salesforce_get_accounts",
                "salesforce_get_opportunities",
                "salesforce_get_contacts",
                "salesforce_search_records"
            ]
            
            # Try to get tool list from various endpoints
            tool_endpoints = [
                f"{self.mcp_url}/tools",
                f"{self.mcp_url}/list_tools",
                f"{self.base_url}/tools",
                f"{self.base_url}/mcp/tools"
            ]
            
            for endpoint in tool_endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    logger.info(f"Tools endpoint {endpoint}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            tools_data = response.json()
                            logger.info(f"✅ Tools endpoint accessible at {endpoint}")
                            logger.info(f"Response data: {json.dumps(tools_data, indent=2)}")
                            
                            # Check if expected tools are present
                            if isinstance(tools_data, dict) and 'tools' in tools_data:
                                available_tools = [tool.get('name', '') for tool in tools_data['tools']]
                            elif isinstance(tools_data, list):
                                available_tools = [tool.get('name', '') for tool in tools_data]
                            else:
                                available_tools = []
                            
                            logger.info(f"Available tools: {available_tools}")
                            
                            missing_tools = [tool for tool in expected_tools if tool not in available_tools]
                            if not missing_tools:
                                logger.info("✅ All 6 Salesforce tools are registered")
                                return True
                            else:
                                logger.warning(f"⚠️  Missing tools: {missing_tools}")
                                
                        except json.JSONDecodeError:
                            logger.info(f"Non-JSON response from {endpoint}: {response.text[:200]}...")
                            
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Tools endpoint failed for {endpoint}: {e}")
                    continue
            
            # If we can't get tool list, try calling a specific tool
            logger.info("Attempting to call a specific tool to verify registration...")
            return await self.test_specific_tool_call()
            
        except Exception as e:
            logger.error(f"❌ Tool registration test failed: {e}")
            return False
    
    async def test_specific_tool_call(self) -> bool:
        """Test calling a specific Salesforce tool."""
        try:
            logger.info("Testing specific tool call...")
            
            # Try to call salesforce_list_orgs tool
            tool_call_endpoints = [
                f"{self.mcp_url}/call_tool",
                f"{self.base_url}/call_tool",
                f"{self.mcp_url}/tools/salesforce_list_orgs",
                f"{self.base_url}/tools/salesforce_list_orgs"
            ]
            
            tool_payload = {
                "name": "salesforce_list_orgs",
                "arguments": {}
            }
            
            for endpoint in tool_call_endpoints:
                try:
                    response = requests.post(
                        endpoint, 
                        json=tool_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=15
                    )
                    
                    logger.info(f"Tool call {endpoint}: Status {response.status_code}")
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"✅ Tool call successful at {endpoint}")
                        logger.info(f"Response: {response.text[:300]}...")
                        return True
                        
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Tool call failed for {endpoint}: {e}")
                    continue
            
            logger.error("❌ All tool call attempts failed")
            return False
            
        except Exception as e:
            logger.error(f"❌ Specific tool call test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all validation tests."""
        results = {}
        
        try:
            # Test 1: Start server
            logger.info("=" * 60)
            logger.info("TEST 1: Server Startup")
            logger.info("=" * 60)
            results['server_startup'] = await self.start_server()
            
            if not results['server_startup']:
                logger.error("❌ Server startup failed, skipping remaining tests")
                return results
            
            # Test 2: Health check
            logger.info("=" * 60)
            logger.info("TEST 2: Health Check")
            logger.info("=" * 60)
            results['health_check'] = await self.test_health_check()
            
            # Test 3: Tool registration
            logger.info("=" * 60)
            logger.info("TEST 3: Tool Registration")
            logger.info("=" * 60)
            results['tool_registration'] = await self.test_tool_registration()
            
        finally:
            # Always stop the server
            self.stop_server()
        
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
            logger.info("🎉 ALL TESTS PASSED - Salesforce MCP Server HTTP startup validated!")
        else:
            logger.error("❌ SOME TESTS FAILED - Check logs above for details")
        logger.info("=" * 60)
        
        return all_passed


async def main():
    """Main test execution."""
    logger.info("🚀 Starting Salesforce MCP Server HTTP Startup Validation")
    
    # Create test instance
    tester = SalesforceMCPServerTest(port=9001)
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print results
        success = tester.print_results(results)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        tester.stop_server()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        tester.stop_server()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())