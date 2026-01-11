#!/usr/bin/env python3
"""
Bill.com setup validation script.
Validates configuration and tests connectivity.
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add the mcp_server directory to Python path
project_root = Path(__file__).parent.parent
mcp_server_path = project_root / "src" / "mcp_server"
sys.path.insert(0, str(mcp_server_path))


async def main():
    """Main setup validation function."""
    print("🔧 Bill.com Integration Setup Validator")
    print("=" * 50)
    
    try:
        # Import with absolute paths to avoid relative import issues
        import importlib.util
        
        # Load config module
        config_spec = importlib.util.spec_from_file_location(
            "bill_com_config", 
            mcp_server_path / "config" / "bill_com_config.py"
        )
        config_module = importlib.util.module_from_spec(config_spec)
        config_spec.loader.exec_module(config_module)
        
        validate_bill_com_setup = config_module.validate_bill_com_setup
        BillComConfigValidator = config_module.BillComConfigValidator
        
        # Load health service module
        health_spec = importlib.util.spec_from_file_location(
            "bill_com_health_service",
            mcp_server_path / "services" / "bill_com_health_service.py"
        )
        health_module = importlib.util.module_from_spec(health_spec)
        health_spec.loader.exec_module(health_module)
        
        get_health_service = health_module.get_health_service
        
        # Step 1: Configuration Validation
        print("\n1️⃣ Validating Configuration...")
        config_result = validate_bill_com_setup()
        
        if config_result["valid"]:
            print("✅ Configuration is valid")
            config = config_result["config"]
            print(f"   Environment: {config.environment.value}")
            print(f"   Base URL: {config.base_url}")
            print(f"   Username: {config.username}")
            print(f"   Organization ID: {config.organization_id}")
            
            if config_result.get("warnings"):
                print("⚠️  Configuration warnings:")
                for warning in config_result["warnings"]:
                    print(f"   - {warning}")
        else:
            print("❌ Configuration is invalid")
            
            if config_result.get("missing_required"):
                print("   Missing required variables:")
                for var in config_result["missing_required"]:
                    print(f"   - {var}")
            
            if config_result.get("errors"):
                print("   Configuration errors:")
                for error in config_result["errors"]:
                    print(f"   - {error}")
            
            print("\n📋 Setup Instructions:")
            print(BillComConfigValidator.get_setup_instructions())
            return False
        
        # Step 2: Health Check
        print("\n2️⃣ Testing Connectivity...")
        health_service = get_health_service()
        health_result = await health_service.comprehensive_health_check()
        
        overall_status = health_result["overall_status"]
        print(f"Overall Status: {overall_status.upper()}")
        
        # Show individual check results
        checks = health_result.get("checks", {})
        
        for check_name, check_result in checks.items():
            status = check_result["status"]
            message = check_result["message"]
            
            status_emoji = {
                "healthy": "✅",
                "warning": "⚠️",
                "unhealthy": "❌",
                "error": "💥",
                "skipped": "⏭️"
            }.get(status, "❓")
            
            print(f"   {status_emoji} {check_name.title()}: {message}")
            
            # Show additional details for failed checks
            if status in ["unhealthy", "error"] and "details" in check_result:
                details = check_result["details"]
                if "error" in details:
                    print(f"      Error: {details['error']}")
        
        # Step 3: Summary and Recommendations
        print(f"\n3️⃣ Summary")
        print(f"Status: {overall_status.upper()}")
        print(f"Summary: {health_result.get('summary', 'No summary available')}")
        
        recommendations = health_result.get("recommendations", [])
        if recommendations:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Step 4: Next Steps
        print("\n🚀 Next Steps:")
        
        if overall_status == "healthy":
            print("   ✅ Bill.com integration is ready to use!")
            print("   🔧 Start the MCP server: cd src/mcp_server && python mcp_server.py")
            print("   🧪 Test with agents in the backend application")
        elif overall_status in ["warning", "unhealthy"]:
            print("   🔧 Fix the issues identified above")
            print("   🔄 Run this script again to verify fixes")
        else:
            print("   ❌ Critical issues need to be resolved")
            print("   📖 Review the setup instructions above")
        
        return overall_status == "healthy"
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        print("   Install required dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Setup validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_environment_file():
    """Check if .env file exists and provide guidance."""
    project_root = Path(__file__).parent.parent
    env_files = [
        project_root / ".env",
        project_root / "src" / "mcp_server" / ".env",
        project_root / "backend" / ".env"
    ]
    
    print("📁 Environment File Check:")
    
    found_env = False
    for env_file in env_files:
        if env_file.exists():
            print(f"   ✅ Found: {env_file}")
            found_env = True
        else:
            print(f"   ❌ Not found: {env_file}")
    
    if not found_env:
        print("\n💡 Create a .env file in the project root with your Bill.com credentials:")
        print("   BILL_COM_USERNAME=your-email@company.com")
        print("   BILL_COM_PASSWORD=your-password")
        print("   BILL_COM_ORG_ID=your-organization-id")
        print("   BILL_COM_DEV_KEY=your-developer-key")
        print("   BILL_COM_ENVIRONMENT=sandbox")


if __name__ == "__main__":
    print("🔍 Pre-flight Environment Check")
    check_environment_file()
    
    print("\n" + "=" * 50)
    
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Bill.com integration setup is complete and healthy!")
        exit(0)
    else:
        print("\n❌ Bill.com integration setup needs attention.")
        exit(1)