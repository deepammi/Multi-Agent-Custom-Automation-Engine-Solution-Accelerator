#!/usr/bin/env python3
"""
Salesforce MCP Server - Dedicated server for Salesforce tools.
This server provides Salesforce-specific tools via MCP protocol.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from services.salesforce_service import SalesforceService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_salesforce_mcp_server():
    """Create and configure Salesforce MCP server."""
    try:
        # Create MCP server
        mcp_server = FastMCP("Salesforce MCP Server")
        
        # Create and register Salesforce service
        salesforce_service = SalesforceService()
        salesforce_service.register_tools(mcp_server)
        
        logger.info("✅ Salesforce MCP server created successfully")
        logger.info(f"✅ Registered {salesforce_service.tool_count} Salesforce tools")
        
        return mcp_server

    except ImportError as e:
        logger.error(f"❌ FastMCP not available: {e}")
        logger.error("Install with: pip install fastmcp")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to create Salesforce MCP server: {e}")
        return None


# Create server instance
mcp = create_salesforce_mcp_server()


def main():
    """Main entry point for the Salesforce MCP server."""
    parser = argparse.ArgumentParser(description="Salesforce MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="http",
                       help="Transport method (default: http)")
    parser.add_argument("--port", type=int, default=9001,
                       help="Port for HTTP transport (default: 9001)")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                       help="Host for HTTP transport (default: 0.0.0.0)")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if mcp is None:
        logger.error("❌ Failed to create MCP server")
        sys.exit(1)
    
    logger.info(f"🚀 Starting Salesforce MCP server with {args.transport} transport")
    
    try:
        if args.transport == "stdio":
            # Run with stdio transport (legacy compatibility)
            mcp.run()
        elif args.transport == "http":
            # Run with HTTP transport (default for concurrent connections)
            logger.info(f"📡 Salesforce MCP server listening on http://{args.host}:{args.port}/mcp")
            mcp.run(transport="http", host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("👋 Salesforce MCP server stopped")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()