"""
Bill.com health check MCP tools for configuration validation and connectivity testing.
"""

import json
import logging
from typing import Dict, Any

from services.bill_com_health_service import get_health_service
from config.bill_com_config import validate_bill_com_setup, BillComConfigValidator

logger = logging.getLogger(__name__)


async def bill_com_health_check(comprehensive: bool = False) -> str:
    """
    Check Bill.com service health and connectivity.
    
    Args:
        comprehensive: If True, performs full health check. If False, uses cached results when available.
    
    Returns:
        JSON string containing health status and diagnostics
    """
    try:
        health_service = get_health_service()
        
        if comprehensive:
            result = await health_service.comprehensive_health_check()
        else:
            result = await health_service.quick_health_check()
        
        logger.info(f"Health check completed: {result.get('overall_status', 'unknown')}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_result = {
            "timestamp": "unknown",
            "overall_status": "error",
            "error": str(e),
            "message": "Health check service failed"
        }
        return json.dumps(error_result, indent=2)


async def bill_com_config_validation() -> str:
    """
    Validate Bill.com configuration and environment variables.
    
    Returns:
        JSON string containing configuration validation results
    """
    try:
        validation_result = validate_bill_com_setup()
        
        # Add setup instructions if configuration is invalid
        if not validation_result["valid"]:
            validation_result["setup_instructions"] = BillComConfigValidator.get_setup_instructions()
        
        logger.info(f"Configuration validation: {'valid' if validation_result['valid'] else 'invalid'}")
        return json.dumps(validation_result, indent=2)
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        error_result = {
            "valid": False,
            "error": str(e),
            "message": "Configuration validation service failed"
        }
        return json.dumps(error_result, indent=2)


async def bill_com_setup_guide() -> str:
    """
    Get Bill.com setup instructions and configuration guide.
    
    Returns:
        JSON string containing setup instructions
    """
    try:
        setup_instructions = BillComConfigValidator.get_setup_instructions()
        
        # Get current validation status
        validation_result = validate_bill_com_setup()
        
        result = {
            "setup_instructions": setup_instructions,
            "current_status": {
                "valid": validation_result["valid"],
                "missing_required": validation_result.get("missing_required", []),
                "missing_optional": validation_result.get("missing_optional", []),
                "warnings": validation_result.get("warnings", [])
            },
            "next_steps": []
        }
        
        # Generate next steps based on current status
        if validation_result.get("missing_required"):
            result["next_steps"].append("Set required environment variables")
        
        if validation_result["valid"]:
            result["next_steps"].append("Run health check to test connectivity")
        else:
            result["next_steps"].append("Fix configuration issues and retry")
        
        logger.info("Setup guide generated")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Setup guide generation failed: {e}")
        error_result = {
            "error": str(e),
            "message": "Setup guide service failed"
        }
        return json.dumps(error_result, indent=2)


async def bill_com_connection_test() -> str:
    """
    Test Bill.com API connection and basic functionality.
    
    Returns:
        JSON string containing connection test results
    """
    try:
        health_service = get_health_service()
        
        # Perform comprehensive health check focused on connectivity
        health_result = await health_service.comprehensive_health_check()
        
        # Extract connection-specific information
        connection_result = {
            "timestamp": health_result["timestamp"],
            "connection_status": health_result["overall_status"],
            "tests": {
                "configuration": health_result["checks"].get("configuration", {}),
                "network": health_result["checks"].get("network", {}),
                "authentication": health_result["checks"].get("authentication", {}),
                "api_functionality": health_result["checks"].get("api_functionality", {})
            },
            "summary": health_result["summary"],
            "recommendations": health_result["recommendations"]
        }
        
        logger.info(f"Connection test completed: {connection_result['connection_status']}")
        return json.dumps(connection_result, indent=2)
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        error_result = {
            "connection_status": "error",
            "error": str(e),
            "message": "Connection test service failed"
        }
        return json.dumps(error_result, indent=2)


async def bill_com_diagnostics() -> str:
    """
    Get comprehensive Bill.com integration diagnostics.
    
    Returns:
        JSON string containing detailed diagnostic information
    """
    try:
        # Get configuration validation
        config_validation = validate_bill_com_setup()
        
        # Get health check results
        health_service = get_health_service()
        health_result = await health_service.comprehensive_health_check()
        
        # Compile diagnostics
        diagnostics = {
            "timestamp": health_result["timestamp"],
            "overall_status": health_result["overall_status"],
            "configuration": {
                "valid": config_validation["valid"],
                "errors": config_validation.get("errors", []),
                "warnings": config_validation.get("warnings", []),
                "missing_required": config_validation.get("missing_required", []),
                "missing_optional": config_validation.get("missing_optional", [])
            },
            "connectivity": {
                "network": health_result["checks"].get("network", {}),
                "authentication": health_result["checks"].get("authentication", {}),
                "api_functionality": health_result["checks"].get("api_functionality", {})
            },
            "performance": {
                "rate_limits": health_result["checks"].get("rate_limits", {})
            },
            "summary": health_result["summary"],
            "recommendations": health_result["recommendations"],
            "troubleshooting": {
                "common_issues": [
                    "Missing or incorrect environment variables",
                    "Network connectivity issues",
                    "Invalid Bill.com credentials",
                    "Incorrect organization ID",
                    "API rate limiting",
                    "Firewall blocking API requests"
                ],
                "debug_steps": [
                    "1. Verify all required environment variables are set",
                    "2. Test network connectivity to Bill.com API",
                    "3. Validate credentials in Bill.com web interface",
                    "4. Check organization ID in Bill.com settings",
                    "5. Review API rate limiting configuration",
                    "6. Check firewall and proxy settings"
                ]
            }
        }
        
        logger.info("Diagnostics generated successfully")
        return json.dumps(diagnostics, indent=2)
        
    except Exception as e:
        logger.error(f"Diagnostics generation failed: {e}")
        error_result = {
            "overall_status": "error",
            "error": str(e),
            "message": "Diagnostics service failed"
        }
        return json.dumps(error_result, indent=2)