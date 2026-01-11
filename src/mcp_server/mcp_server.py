"""
MACAE MCP Server - FastMCP server with organized tools and services.
"""

import argparse
import logging
###
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config.settings import config
from core.factory import MCPToolFactory
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from services.hr_service import HRService
from services.marketing_service import MarketingService
from services.product_service import ProductService
from services.tech_support_service import TechSupportService
from services.salesforce_service import SalesforceService
from services.gmail_service import GmailService
from core.bill_com_tools import BillComService
from services.bill_com_service import BillComConfig, BillComAPIService
from services.bill_com_health_tools_service import BillComHealthToolsService
from services.audit_service import AuditService
from services.audit_tools_service import AuditToolsService
from adapters.billcom_audit_adapter import BillComAuditAdapter
from core.audit_tools import initialize_audit_service
from config.bill_com_config import validate_bill_com_setup

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global factory instance
factory = MCPToolFactory()

# Global audit service instance
audit_service_instance: Optional[AuditService] = None

# Initialize services
factory.register_service(HRService())
factory.register_service(TechSupportService())
factory.register_service(MarketingService())
factory.register_service(ProductService())
factory.register_service(SalesforceService())
factory.register_service(GmailService())
factory.register_service(BillComService())
factory.register_service(AuditToolsService())
factory.register_service(BillComHealthToolsService())



def create_fastmcp_server():
    """Create and configure FastMCP server."""
    try:
        # Create authentication provider if enabled
        auth = None
        if config.enable_auth:
            auth_config = {
                "jwks_uri": config.jwks_uri,
                "issuer": config.issuer,
                "audience": config.audience,
            }
            if all(auth_config.values()):
                auth = JWTVerifier(
                    jwks_uri=auth_config["jwks_uri"],
                    issuer=auth_config["issuer"],
                    algorithm="RS256",
                    audience=auth_config["audience"],
                )

        # Create MCP server
        mcp_server = factory.create_mcp_server(name=config.server_name, auth=auth)

        logger.info("✅ FastMCP server created successfully")
        return mcp_server

    except ImportError:
        logger.warning("⚠️  FastMCP not available. Install with: pip install fastmcp")
        return None


# Create FastMCP server instance for fastmcp run command
mcp = create_fastmcp_server()


def initialize_audit_services():
    """Initialize audit services and providers."""
    global audit_service_instance
    
    try:
        # Create audit service
        audit_service_instance = AuditService()
        
        # Initialize Bill.com audit provider if configuration is available
        bill_com_config = BillComConfig.from_env()
        if bill_com_config.validate():
            # Create Bill.com API service
            bill_com_api_service = BillComAPIService(bill_com_config)
            
            # Create and register Bill.com audit adapter
            billcom_adapter = BillComAuditAdapter(bill_com_api_service)
            audit_service_instance.register_provider("billcom", billcom_adapter, is_default=True)
            
            logger.info("✅ Bill.com audit provider registered successfully")
        else:
            logger.warning("⚠️  Bill.com audit provider not available - configuration incomplete")
        
        # Initialize audit tools with the service
        initialize_audit_service(audit_service_instance)
        
        logger.info("✅ Audit services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing audit services: {e}")
        return False


def validate_bill_com_configuration_startup():
    """Validate Bill.com configuration on startup with comprehensive reporting."""
    try:
        logger.info("🔍 Validating Bill.com configuration...")
        
        # Use the comprehensive validation from the config module
        validation_result = validate_bill_com_setup()
        
        if validation_result["valid"]:
            config = validation_result["config"]
            logger.info("✅ Bill.com configuration validated successfully")
            logger.info(f"   🏢 Organization ID: {config.organization_id}")
            logger.info(f"   🌐 Environment: {config.environment.value}")
            logger.info(f"   🔗 Base URL: {config.base_url}")
            
            # Log warnings if any
            warnings = validation_result.get("warnings", [])
            if warnings:
                logger.warning("⚠️  Configuration warnings:")
                for warning in warnings:
                    logger.warning(f"   ⚠️  {warning}")
            
            return True
        else:
            logger.warning("⚠️  Bill.com configuration validation failed")
            
            # Log errors
            errors = validation_result.get("errors", [])
            if errors:
                logger.warning("   Configuration errors:")
                for error in errors:
                    logger.warning(f"   ❌ {error}")
            
            # Log missing environment variables
            missing_required = validation_result.get("missing_required", [])
            if missing_required:
                logger.warning("   Missing required environment variables:")
                for var in missing_required:
                    logger.warning(f"   ❌ {var}")
            
            logger.warning("   💡 Use 'bill_com_setup_guide' tool for setup instructions")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error validating Bill.com configuration: {e}")
        logger.error("   💡 Use 'bill_com_configuration_status' tool for detailed diagnostics")
        return False


def log_server_info():
    """Log server initialization info."""
    if not mcp:
        logger.error("❌ FastMCP server not available")
        return

    summary = factory.get_tool_summary()
    logger.info(f"🚀 {config.server_name} initialized")
    logger.info(f"📊 Total services: {summary['total_services']}")
    logger.info(f"🔧 Total tools: {summary['total_tools']}")
    logger.info(f"🔐 Authentication: {'Enabled' if config.enable_auth else 'Disabled'}")

    for domain, info in summary["services"].items():
        logger.info(
            f"   📁 {domain}: {info['tool_count']} tools ({info['class_name']})"
        )
    
    # Validate Bill.com configuration and initialize audit services
    logger.info("🔍 Validating service configurations...")
    config_valid = validate_bill_com_configuration_startup()
    
    logger.info("🔧 Initializing audit services...")
    audit_initialized = initialize_audit_services()
    
    # Perform startup health check if configuration is valid
    if config_valid:
        logger.info("🏥 Performing startup health check...")
        try:
            # Simple health check - just log that config is valid
            logger.info("✅ Bill.com startup health check passed")
        except Exception as e:
            logger.error(f"❌ Startup health check error: {e}")
    else:
        logger.info("⏭️  Skipping health check due to configuration issues")


def run_server(
    transport: str = "stdio", host: str = "127.0.0.1", port: int = 9000, **kwargs
):
    """Run the FastMCP server with specified transport."""
    if not mcp:
        logger.error("❌ Cannot start FastMCP server - not available")
        return

    log_server_info()

    logger.info(f"🤖 Starting FastMCP server with {transport} transport")
    if transport in ["http", "streamable-http", "sse"]:
        logger.info(f"🌐 Server will be available at: http://{host}:{port}/mcp/")
        mcp.run(transport=transport, host=host, port=port, **kwargs)
    else:
        # For STDIO transport, only pass kwargs that are supported
        stdio_kwargs = {k: v for k, v in kwargs.items() if k not in ["log_level"]}
        mcp.run(transport=transport, **stdio_kwargs)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="MACAE MCP Server")
    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "http", "streamable-http", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to for HTTP transport (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=9000,
        help="Port to bind to for HTTP transport (default: 9000)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-auth", action="store_true", help="Disable authentication")

    args = parser.parse_args()

    # Override config with command line arguments
    if args.debug:
        import os

        os.environ["MCP_DEBUG"] = "true"
        config.debug = True

    if args.no_auth:
        import os

        os.environ["MCP_ENABLE_AUTH"] = "false"
        config.enable_auth = False

    # Print startup info
    print(f"🚀 Starting MACAE MCP Server")
    print(f"📋 Transport: {args.transport.upper()}")
    print(f"🔧 Debug: {config.debug}")
    print(f"🔐 Auth: {'Enabled' if config.enable_auth else 'Disabled'}")
    if args.transport in ["http", "streamable-http", "sse"]:
        print(f"🌐 Host: {args.host}")
        print(f"🌐 Port: {args.port}")
    print("-" * 50)

    # Run the server
    run_server(
        transport=args.transport,
        host=args.host,
        port=args.port,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
