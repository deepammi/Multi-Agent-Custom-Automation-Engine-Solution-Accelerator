"""
Environment Configuration Module for Multi-Agent Invoice Workflow.

This module provides centralized environment variable management with support for
environment-controlled mock modes as specified in NFR3.2.

Environment Variables:
- USE_MOCK_MODE: Enable/disable mock mode for MCP services (true/false)
- USE_MOCK_LLM: Enable/disable mock mode for LLM services (true/false)
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MockModeConfig:
    """Configuration for mock mode settings."""
    use_mock_mode: bool
    use_mock_llm: bool
    mock_mode_reason: Optional[str] = None
    
    def __post_init__(self):
        """Log mock mode configuration on initialization."""
        if self.use_mock_mode or self.use_mock_llm:
            logger.info(
                f"🎭 Mock mode configuration: MCP={self.use_mock_mode}, LLM={self.use_mock_llm}",
                extra={
                    "use_mock_mode": self.use_mock_mode,
                    "use_mock_llm": self.use_mock_llm,
                    "reason": self.mock_mode_reason
                }
            )


class EnvironmentConfig:
    """
    Centralized environment configuration with mock mode support.
    
    This class provides environment-controlled mock mode activation as required by NFR3.2.
    Mock modes are only enabled when explicitly set via environment variables.
    """
    
    _instance: Optional['EnvironmentConfig'] = None
    _mock_config: Optional[MockModeConfig] = None
    
    def __new__(cls) -> 'EnvironmentConfig':
        """Singleton pattern to ensure consistent configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize environment configuration."""
        # Always reload configuration on new instance
        self._load_configuration()
        self._initialized = True
    
    def _load_configuration(self) -> None:
        """Load configuration from environment variables."""
        # Mock mode configuration
        use_mock_mode = self._parse_boolean_env("USE_MOCK_MODE", default=False)
        use_mock_llm = self._parse_boolean_env("USE_MOCK_LLM", default=False)
        
        # Determine mock mode reason
        mock_reason = None
        if use_mock_mode or use_mock_llm:
            mock_reason = "Environment variable explicitly enabled"
        
        self._mock_config = MockModeConfig(
            use_mock_mode=use_mock_mode,
            use_mock_llm=use_mock_llm,
            mock_mode_reason=mock_reason
        )
        
        logger.info(
            "🔧 Environment configuration loaded",
            extra={
                "use_mock_mode": use_mock_mode,
                "use_mock_llm": use_mock_llm,
                "mock_reason": mock_reason
            }
        )
    
    def _parse_boolean_env(self, env_var: str, default: bool = False) -> bool:
        """
        Parse boolean environment variable with validation.
        
        Args:
            env_var: Environment variable name
            default: Default value if not set
            
        Returns:
            bool: Parsed boolean value
        """
        value = os.getenv(env_var, str(default)).lower().strip()
        
        # Accept various boolean representations
        true_values = {"true", "1", "yes", "on", "enabled"}
        false_values = {"false", "0", "no", "off", "disabled"}
        
        if value in true_values:
            return True
        elif value in false_values:
            return False
        else:
            logger.warning(
                f"⚠️ Invalid boolean value for {env_var}: '{value}', using default: {default}",
                extra={"env_var": env_var, "value": value, "default": default}
            )
            return default
    
    @property
    def mock_config(self) -> MockModeConfig:
        """Get mock mode configuration."""
        if self._mock_config is None:
            self._load_configuration()
        return self._mock_config
    
    def is_mock_mode_enabled(self) -> bool:
        """
        Check if MCP mock mode is enabled via environment variable.
        
        Returns:
            bool: True if USE_MOCK_MODE=true, False otherwise
        """
        return self.mock_config.use_mock_mode
    
    def is_mock_llm_enabled(self) -> bool:
        """
        Check if LLM mock mode is enabled via environment variable.
        
        Returns:
            bool: True if USE_MOCK_LLM=true, False otherwise
        """
        return self.mock_config.use_mock_llm
    
    def should_use_mock_data(self, service_type: str = "mcp") -> bool:
        """
        Determine if mock data should be used for a service type.
        
        Args:
            service_type: Type of service ("mcp" or "llm")
            
        Returns:
            bool: True if mock mode is enabled for the service type
        """
        if service_type.lower() == "llm":
            return self.is_mock_llm_enabled()
        elif service_type.lower() == "mcp":
            return self.is_mock_mode_enabled()
        else:
            logger.warning(f"Unknown service type: {service_type}, defaulting to false")
            return False
    
    def get_mock_mode_status(self) -> Dict[str, Any]:
        """
        Get comprehensive mock mode status for monitoring.
        
        Returns:
            Dict with mock mode status information
        """
        config = self.mock_config
        
        return {
            "use_mock_mode": config.use_mock_mode,
            "use_mock_llm": config.use_mock_llm,
            "mock_mode_reason": config.mock_mode_reason,
            "environment_variables": {
                "USE_MOCK_MODE": os.getenv("USE_MOCK_MODE", "not set"),
                "USE_MOCK_LLM": os.getenv("USE_MOCK_LLM", "not set")
            },
            "effective_settings": {
                "mcp_services_use_mock": config.use_mock_mode,
                "llm_services_use_mock": config.use_mock_llm
            }
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate environment configuration and return validation results.
        
        Returns:
            Dict with validation results
        """
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "configuration": self.get_mock_mode_status()
        }
        
        # Check for conflicting settings
        if self.is_mock_mode_enabled() and not self.is_mock_llm_enabled():
            validation_results["warnings"].append(
                "MCP mock mode enabled but LLM mock mode disabled - may cause inconsistent behavior"
            )
        
        # Check environment variable format
        for env_var in ["USE_MOCK_MODE", "USE_MOCK_LLM"]:
            value = os.getenv(env_var, "").lower().strip()
            if value and value not in {"true", "false", "1", "0", "yes", "no", "on", "off", "enabled", "disabled"}:
                validation_results["warnings"].append(
                    f"Environment variable {env_var} has unusual value: '{value}'"
                )
        
        # Log validation results
        if validation_results["warnings"]:
            logger.warning(
                f"Environment configuration validation warnings: {validation_results['warnings']}"
            )
        
        if validation_results["errors"]:
            logger.error(
                f"Environment configuration validation errors: {validation_results['errors']}"
            )
            validation_results["valid"] = False
        
        return validation_results


# Global instance
_env_config: Optional[EnvironmentConfig] = None


def get_environment_config() -> EnvironmentConfig:
    """
    Get or create global environment configuration instance.
    
    Returns:
        EnvironmentConfig: Global configuration instance
    """
    global _env_config
    
    if _env_config is None:
        _env_config = EnvironmentConfig()
    
    return _env_config


def is_mock_mode_enabled() -> bool:
    """
    Convenience function to check if MCP mock mode is enabled.
    
    Returns:
        bool: True if USE_MOCK_MODE=true, False otherwise
    """
    return get_environment_config().is_mock_mode_enabled()


def is_mock_llm_enabled() -> bool:
    """
    Convenience function to check if LLM mock mode is enabled.
    
    Returns:
        bool: True if USE_MOCK_LLM=true, False otherwise
    """
    return get_environment_config().is_mock_llm_enabled()


def should_use_mock_data(service_type: str = "mcp") -> bool:
    """
    Convenience function to determine if mock data should be used.
    
    Args:
        service_type: Type of service ("mcp" or "llm")
        
    Returns:
        bool: True if mock mode is enabled for the service type
    """
    return get_environment_config().should_use_mock_data(service_type)