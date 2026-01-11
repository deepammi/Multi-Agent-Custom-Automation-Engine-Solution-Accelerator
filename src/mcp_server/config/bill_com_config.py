"""
Bill.com configuration management with environment validation and health checking.
Supports both staging and production environments with comprehensive validation.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class BillComEnvironment(Enum):
    """Bill.com environment types."""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


@dataclass
class BillComConfig:
    """Bill.com configuration with validation and environment support."""
    
    # Required credentials
    username: str
    password: str
    organization_id: str
    dev_key: str
    
    # Environment settings
    environment: BillComEnvironment = BillComEnvironment.SANDBOX
    base_url: Optional[str] = None
    
    # Connection settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Logging and debugging
    enable_debug_logging: bool = False
    log_api_requests: bool = False
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Set base URL based on environment if not provided
        if not self.base_url:
            if self.environment == BillComEnvironment.SANDBOX:
                self.base_url = "https://gateway.stage.bill.com"  # Fixed: removed /connect
            else:
                self.base_url = "https://api.bill.com/api/v2"
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration parameters."""
        errors = []
        
        # Required field validation
        if not self.username:
            errors.append("Username is required")
        if not self.password:
            errors.append("Password is required")
        if not self.organization_id:
            errors.append("Organization ID is required")
        if not self.dev_key:
            errors.append("Developer key is required")
        
        # Format validation
        if self.username and "@" not in self.username:
            errors.append("Username should be a valid email address")
        
        if self.organization_id and len(self.organization_id) < 10:
            errors.append("Organization ID appears to be invalid (too short)")
        
        # Numeric validation
        if self.timeout <= 0:
            errors.append("Timeout must be positive")
        if self.max_retries < 0:
            errors.append("Max retries cannot be negative")
        if self.retry_delay < 0:
            errors.append("Retry delay cannot be negative")
        
        if errors:
            raise ValueError(f"Bill.com configuration errors: {'; '.join(errors)}")
    
    @classmethod
    def from_env(cls) -> 'BillComConfig':
        """Create configuration from environment variables."""
        try:
            # Get environment type
            env_str = os.getenv("BILL_COM_ENVIRONMENT", "sandbox").lower()
            try:
                environment = BillComEnvironment(env_str)
            except ValueError:
                logger.warning(f"Invalid environment '{env_str}', defaulting to sandbox")
                environment = BillComEnvironment.SANDBOX
            
            config = cls(
                username=os.getenv("BILL_COM_USERNAME", ""),
                password=os.getenv("BILL_COM_PASSWORD", ""),
                organization_id=os.getenv("BILL_COM_ORG_ID", ""),
                dev_key=os.getenv("BILL_COM_DEV_KEY", ""),
                environment=environment,
                base_url=os.getenv("BILL_COM_BASE_URL"),
                timeout=int(os.getenv("BILL_COM_TIMEOUT", "30")),
                max_retries=int(os.getenv("BILL_COM_MAX_RETRIES", "3")),
                retry_delay=float(os.getenv("BILL_COM_RETRY_DELAY", "1.0")),
                rate_limit_requests=int(os.getenv("BILL_COM_RATE_LIMIT_REQUESTS", "100")),
                rate_limit_window=int(os.getenv("BILL_COM_RATE_LIMIT_WINDOW", "60")),
                enable_debug_logging=os.getenv("BILL_COM_DEBUG", "false").lower() == "true",
                log_api_requests=os.getenv("BILL_COM_LOG_REQUESTS", "false").lower() == "true"
            )
            
            logger.info(f"Bill.com configuration loaded for {environment.value} environment")
            return config
            
        except ValueError as e:
            logger.error(f"Bill.com configuration validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load Bill.com configuration: {e}")
            raise ValueError(f"Configuration loading error: {e}")
    
    def validate_connection_settings(self) -> List[str]:
        """Validate connection-specific settings."""
        warnings = []
        
        if self.timeout > 60:
            warnings.append("Timeout is very high (>60s), may cause performance issues")
        
        if self.max_retries > 5:
            warnings.append("Max retries is high (>5), may cause long delays on failures")
        
        if self.rate_limit_requests > 1000:
            warnings.append("Rate limit is very high, ensure it matches Bill.com limits")
        
        return warnings
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for logging/debugging."""
        return {
            "environment": self.environment.value,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "rate_limit": f"{self.rate_limit_requests}/{self.rate_limit_window}s",
            "debug_enabled": self.enable_debug_logging,
            "request_logging": self.log_api_requests
        }
    
    def is_production(self) -> bool:
        """Check if this is a production configuration."""
        return self.environment == BillComEnvironment.PRODUCTION
    
    def is_complete(self) -> bool:
        """Check if all required configuration is present."""
        return all([
            self.username,
            self.password,
            self.organization_id,
            self.dev_key
        ])
    
    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields."""
        missing = []
        
        if not self.username:
            missing.append("BILL_COM_USERNAME")
        if not self.password:
            missing.append("BILL_COM_PASSWORD")
        if not self.organization_id:
            missing.append("BILL_COM_ORG_ID")
        if not self.dev_key:
            missing.append("BILL_COM_DEV_KEY")
        
        return missing
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        data = {
            "username": self.username if include_sensitive else "***",
            "organization_id": self.organization_id,
            "environment": self.environment.value,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_window": self.rate_limit_window,
            "enable_debug_logging": self.enable_debug_logging,
            "log_api_requests": self.log_api_requests
        }
        
        if not include_sensitive:
            data["password"] = "***"
            data["dev_key"] = "***"
        else:
            data["password"] = self.password
            data["dev_key"] = self.dev_key
        
        return data


class BillComConfigValidator:
    """Validator for Bill.com configuration with detailed checks."""
    
    @staticmethod
    def validate_environment_variables() -> Dict[str, Any]:
        """Validate all Bill.com environment variables."""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_required": [],
            "missing_optional": [],
            "config": None
        }
        
        try:
            # Check for required variables
            required_vars = [
                "BILL_COM_USERNAME",
                "BILL_COM_PASSWORD", 
                "BILL_COM_ORG_ID",
                "BILL_COM_DEV_KEY"
            ]
            
            missing_required = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_required.append(var)
            
            result["missing_required"] = missing_required
            
            # Check for optional variables
            optional_vars = [
                "BILL_COM_ENVIRONMENT",
                "BILL_COM_BASE_URL",
                "BILL_COM_TIMEOUT",
                "BILL_COM_MAX_RETRIES",
                "BILL_COM_RETRY_DELAY",
                "BILL_COM_RATE_LIMIT_REQUESTS",
                "BILL_COM_RATE_LIMIT_WINDOW",
                "BILL_COM_DEBUG",
                "BILL_COM_LOG_REQUESTS"
            ]
            
            missing_optional = []
            for var in optional_vars:
                if not os.getenv(var):
                    missing_optional.append(var)
            
            result["missing_optional"] = missing_optional
            
            # Try to create configuration
            if not missing_required:
                try:
                    config = BillComConfig.from_env()
                    result["config"] = config
                    
                    # Add connection warnings
                    warnings = config.validate_connection_settings()
                    result["warnings"].extend(warnings)
                    
                    # Environment-specific warnings
                    if config.is_production():
                        result["warnings"].append("Using PRODUCTION environment - ensure credentials are correct")
                    
                except Exception as e:
                    result["valid"] = False
                    result["errors"].append(f"Configuration creation failed: {e}")
            else:
                result["valid"] = False
                result["errors"].append(f"Missing required variables: {', '.join(missing_required)}")
            
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Validation error: {e}")
        
        return result
    
    @staticmethod
    def get_setup_instructions() -> str:
        """Get setup instructions for Bill.com configuration."""
        return """
# Bill.com Configuration Setup

## Required Environment Variables

Set these environment variables in your .env file or system environment:

```bash
# Required - Bill.com Account Credentials
BILL_COM_USERNAME=your-email@company.com
BILL_COM_PASSWORD=your-password
BILL_COM_ORG_ID=your-organization-id
BILL_COM_DEV_KEY=your-developer-key

# Environment Selection (optional, defaults to sandbox)
BILL_COM_ENVIRONMENT=sandbox  # or 'production'
```

## Optional Configuration

```bash
# Connection Settings
BILL_COM_TIMEOUT=30                    # Request timeout in seconds
BILL_COM_MAX_RETRIES=3                 # Maximum retry attempts
BILL_COM_RETRY_DELAY=1.0              # Delay between retries

# Rate Limiting
BILL_COM_RATE_LIMIT_REQUESTS=100      # Requests per window
BILL_COM_RATE_LIMIT_WINDOW=60         # Window size in seconds

# Debugging
BILL_COM_DEBUG=false                   # Enable debug logging
BILL_COM_LOG_REQUESTS=false           # Log API requests/responses

# Custom API URL (optional)
BILL_COM_BASE_URL=https://api-stage.bill.com/api/v2
```

## Getting Bill.com Credentials

1. **Sign up for Bill.com Developer Account**
   - Visit: https://developer.bill.com/
   - Create developer account
   - Get your developer key

2. **Get Organization ID**
   - Log into your Bill.com account
   - Go to Settings > Company Profile
   - Find your Organization ID

3. **Environment Selection**
   - Use `sandbox` for testing (default)
   - Use `production` for live data (be careful!)

## Validation

Run the configuration validator:
```bash
python scripts/bill_com_setup_check.py
```
"""


# Global configuration instance
_config: Optional[BillComConfig] = None


def get_bill_com_config() -> BillComConfig:
    """Get the global Bill.com configuration instance."""
    global _config
    if _config is None:
        _config = BillComConfig.from_env()
    return _config


def reload_bill_com_config():
    """Reload the global configuration from environment."""
    global _config
    _config = None
    return get_bill_com_config()


def validate_bill_com_setup() -> Dict[str, Any]:
    """Validate the current Bill.com setup."""
    return BillComConfigValidator.validate_environment_variables()