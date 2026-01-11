"""
MCP Client Configuration System

Provides configuration management for MCP client settings including:
- Server connection parameters
- Environment variable handling
- Service-specific configurations
- Connection pooling and health monitoring settings
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for MCP server connection."""
    service_name: str
    server_command: str
    server_args: List[str]
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 60
    working_directory: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.service_name:
            raise ValueError("service_name is required")
        if not self.server_command:
            raise ValueError("server_command is required")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")


@dataclass
class ConnectionRecoveryConfig:
    """Configuration for connection recovery behavior."""
    max_retry_attempts: int = 5
    base_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    jitter_enabled: bool = True
    timeout_detection_threshold: int = 3
    health_check_failure_threshold: int = 3
    auto_recovery_enabled: bool = True


@dataclass
class MCPClientConfig:
    """Configuration for MCP client manager."""
    servers: List[MCPServerConfig] = field(default_factory=list)
    connection_pool_size: int = 10
    default_timeout: int = 30
    enable_health_monitoring: bool = True
    log_level: str = "INFO"
    recovery_config: ConnectionRecoveryConfig = field(default_factory=ConnectionRecoveryConfig)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.connection_pool_size <= 0:
            raise ValueError("connection_pool_size must be positive")
        if self.default_timeout <= 0:
            raise ValueError("default_timeout must be positive")
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("log_level must be a valid logging level")


class MCPConfigManager:
    """
    Manages MCP client configuration from multiple sources.
    
    Configuration sources (in order of precedence):
    1. Environment variables
    2. Configuration files (YAML/JSON)
    3. Default values
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file
        self._config: Optional[MCPClientConfig] = None
        
    def load_config(self) -> MCPClientConfig:
        """
        Load configuration from all sources.
        
        Returns:
            Complete MCP client configuration
        """
        if self._config is not None:
            return self._config
            
        # Start with default configuration
        config = self._get_default_config()
        
        # Override with file configuration if available
        if self.config_file and os.path.exists(self.config_file):
            file_config = self._load_config_file(self.config_file)
            config = self._merge_configs(config, file_config)
        
        # Override with environment variables
        env_config = self._load_env_config()
        config = self._merge_configs(config, env_config)
        
        # Validate final configuration
        self._validate_config(config)
        
        self._config = config
        logger.info(
            f"MCP configuration loaded successfully",
            extra={
                "servers": len(config.servers),
                "pool_size": config.connection_pool_size,
                "health_monitoring": config.enable_health_monitoring
            }
        )
        
        return config
    
    def _get_default_config(self) -> MCPClientConfig:
        """Get default MCP client configuration."""
        return MCPClientConfig(
            servers=[
                MCPServerConfig(
                    service_name="bill_com",
                    server_command="python3",
                    server_args=["src/mcp_server/mcp_server.py"],
                    environment={},
                    timeout=30,
                    retry_attempts=3,
                    health_check_interval=60
                ),
                MCPServerConfig(
                    service_name="gmail",
                    server_command="python3",
                    server_args=["src/mcp_server/gmail_mcp_server.py"],
                    environment={},
                    timeout=20,
                    retry_attempts=3,
                    health_check_interval=60
                ),
                MCPServerConfig(
                    service_name="zoho",
                    server_command="python3",
                    server_args=["src/mcp_server/zoho_mcp_server.py"],
                    environment={},
                    timeout=25,
                    retry_attempts=3,
                    health_check_interval=60
                ),
                MCPServerConfig(
                    service_name="salesforce",
                    server_command="python3",
                    server_args=["src/mcp_server/salesforce_mcp_server.py"],
                    environment={},
                    timeout=30,
                    retry_attempts=3,
                    health_check_interval=60
                )
            ],
            connection_pool_size=10,
            default_timeout=30,
            enable_health_monitoring=True,
            log_level="INFO"
        )
    
    def _load_config_file(self, config_file: str) -> Dict[str, Any]:
        """
        Load configuration from file (YAML or JSON).
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    return yaml.safe_load(f) or {}
                elif config_file.endswith('.json'):
                    return json.load(f) or {}
                else:
                    logger.warning(f"Unknown config file format: {config_file}")
                    return {}
        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e}")
            return {}
    
    def _load_env_config(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.
        
        Environment variable format:
        - MCP_POOL_SIZE: Connection pool size
        - MCP_DEFAULT_TIMEOUT: Default timeout in seconds
        - MCP_HEALTH_MONITORING: Enable health monitoring (true/false)
        - MCP_LOG_LEVEL: Logging level
        - MCP_<SERVICE>_COMMAND: Server command for service
        - MCP_<SERVICE>_ARGS: Server arguments (comma-separated)
        - MCP_<SERVICE>_TIMEOUT: Timeout for service
        - MCP_<SERVICE>_ENV_<VAR>: Environment variable for service
        
        Returns:
            Configuration dictionary from environment
        """
        config = {}
        
        # Global settings
        if pool_size := os.getenv("MCP_POOL_SIZE"):
            try:
                config["connection_pool_size"] = int(pool_size)
            except ValueError:
                logger.warning(f"Invalid MCP_POOL_SIZE: {pool_size}")
        
        if timeout := os.getenv("MCP_DEFAULT_TIMEOUT"):
            try:
                config["default_timeout"] = int(timeout)
            except ValueError:
                logger.warning(f"Invalid MCP_DEFAULT_TIMEOUT: {timeout}")
        
        if health_monitoring := os.getenv("MCP_HEALTH_MONITORING"):
            config["enable_health_monitoring"] = health_monitoring.lower() in ("true", "1", "yes")
        
        if log_level := os.getenv("MCP_LOG_LEVEL"):
            config["log_level"] = log_level.upper()
        
        # Service-specific settings
        services = ["bill_com", "gmail", "zoho", "salesforce"]
        server_configs = []
        
        for service in services:
            service_upper = service.upper()
            service_config = {"service_name": service}
            
            # Server command
            if command := os.getenv(f"MCP_{service_upper}_COMMAND"):
                service_config["server_command"] = command
            
            # Server arguments
            if args := os.getenv(f"MCP_{service_upper}_ARGS"):
                service_config["server_args"] = [arg.strip() for arg in args.split(",")]
            
            # Timeout
            if timeout := os.getenv(f"MCP_{service_upper}_TIMEOUT"):
                try:
                    service_config["timeout"] = int(timeout)
                except ValueError:
                    logger.warning(f"Invalid MCP_{service_upper}_TIMEOUT: {timeout}")
            
            # Environment variables
            env_vars = {}
            for key, value in os.environ.items():
                if key.startswith(f"MCP_{service_upper}_ENV_"):
                    env_key = key[len(f"MCP_{service_upper}_ENV_"):]
                    env_vars[env_key] = value
            
            if env_vars:
                service_config["environment"] = env_vars
            
            # Only add service config if we have customizations
            if len(service_config) > 1:  # More than just service_name
                server_configs.append(service_config)
        
        if server_configs:
            config["servers"] = server_configs
        
        return config
    
    def _merge_configs(self, base_config: MCPClientConfig, override_config: Dict[str, Any]) -> MCPClientConfig:
        """
        Merge configuration dictionaries with override precedence.
        
        Args:
            base_config: Base configuration
            override_config: Override configuration dictionary
            
        Returns:
            Merged configuration
        """
        # Convert base config to dict for easier merging
        config_dict = {
            "servers": [
                {
                    "service_name": server.service_name,
                    "server_command": server.server_command,
                    "server_args": server.server_args,
                    "environment": server.environment,
                    "timeout": server.timeout,
                    "retry_attempts": server.retry_attempts,
                    "health_check_interval": server.health_check_interval,
                    "working_directory": server.working_directory
                }
                for server in base_config.servers
            ],
            "connection_pool_size": base_config.connection_pool_size,
            "default_timeout": base_config.default_timeout,
            "enable_health_monitoring": base_config.enable_health_monitoring,
            "log_level": base_config.log_level,
            "recovery_config": {
                "max_retry_attempts": base_config.recovery_config.max_retry_attempts,
                "base_backoff_seconds": base_config.recovery_config.base_backoff_seconds,
                "max_backoff_seconds": base_config.recovery_config.max_backoff_seconds,
                "backoff_multiplier": base_config.recovery_config.backoff_multiplier,
                "jitter_enabled": base_config.recovery_config.jitter_enabled,
                "timeout_detection_threshold": base_config.recovery_config.timeout_detection_threshold,
                "health_check_failure_threshold": base_config.recovery_config.health_check_failure_threshold,
                "auto_recovery_enabled": base_config.recovery_config.auto_recovery_enabled
            }
        }
        
        # Merge global settings
        for key in ["connection_pool_size", "default_timeout", "enable_health_monitoring", "log_level"]:
            if key in override_config:
                config_dict[key] = override_config[key]
        
        # Merge recovery config
        if "recovery_config" in override_config:
            config_dict["recovery_config"].update(override_config["recovery_config"])
        
        # Merge server configurations
        if "servers" in override_config:
            # Create a map of existing servers by service name
            server_map = {server["service_name"]: server for server in config_dict["servers"]}
            
            # Update or add servers from override config
            for override_server in override_config["servers"]:
                service_name = override_server["service_name"]
                if service_name in server_map:
                    # Update existing server config
                    server_map[service_name].update(override_server)
                else:
                    # Add new server config
                    server_map[service_name] = override_server
            
            config_dict["servers"] = list(server_map.values())
        
        # Convert back to dataclass
        return MCPClientConfig(
            servers=[
                MCPServerConfig(
                    service_name=server["service_name"],
                    server_command=server["server_command"],
                    server_args=server["server_args"],
                    environment=server.get("environment", {}),
                    timeout=server.get("timeout", 30),
                    retry_attempts=server.get("retry_attempts", 3),
                    health_check_interval=server.get("health_check_interval", 60),
                    working_directory=server.get("working_directory")
                )
                for server in config_dict["servers"]
            ],
            connection_pool_size=config_dict["connection_pool_size"],
            default_timeout=config_dict["default_timeout"],
            enable_health_monitoring=config_dict["enable_health_monitoring"],
            log_level=config_dict["log_level"],
            recovery_config=ConnectionRecoveryConfig(**config_dict["recovery_config"])
        )
    
    def _validate_config(self, config: MCPClientConfig) -> None:
        """
        Validate the final configuration.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Check for duplicate service names
        service_names = [server.service_name for server in config.servers]
        if len(service_names) != len(set(service_names)):
            duplicates = [name for name in service_names if service_names.count(name) > 1]
            raise ValueError(f"Duplicate service names found: {duplicates}")
        
        # Validate server configurations
        for server in config.servers:
            if not server.server_command:
                raise ValueError(f"Server command required for service: {server.service_name}")
            
            if not server.server_args:
                raise ValueError(f"Server args required for service: {server.service_name}")
        
        logger.debug("MCP configuration validation passed")
    
    def get_server_config(self, service_name: str) -> Optional[MCPServerConfig]:
        """
        Get configuration for a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Server configuration or None if not found
        """
        config = self.load_config()
        for server in config.servers:
            if server.service_name == service_name:
                return server
        return None
    
    def save_config(self, config_file: str, config: MCPClientConfig) -> None:
        """
        Save configuration to file.
        
        Args:
            config_file: Path to save configuration
            config: Configuration to save
        """
        config_dict = {
            "servers": [
                {
                    "service_name": server.service_name,
                    "server_command": server.server_command,
                    "server_args": server.server_args,
                    "environment": server.environment,
                    "timeout": server.timeout,
                    "retry_attempts": server.retry_attempts,
                    "health_check_interval": server.health_check_interval
                }
                for server in config.servers
            ],
            "connection_pool_size": config.connection_pool_size,
            "default_timeout": config.default_timeout,
            "enable_health_monitoring": config.enable_health_monitoring,
            "log_level": config.log_level,
            "recovery_config": {
                "max_retry_attempts": config.recovery_config.max_retry_attempts,
                "base_backoff_seconds": config.recovery_config.base_backoff_seconds,
                "max_backoff_seconds": config.recovery_config.max_backoff_seconds,
                "backoff_multiplier": config.recovery_config.backoff_multiplier,
                "jitter_enabled": config.recovery_config.jitter_enabled,
                "timeout_detection_threshold": config.recovery_config.timeout_detection_threshold,
                "health_check_failure_threshold": config.recovery_config.health_check_failure_threshold,
                "auto_recovery_enabled": config.recovery_config.auto_recovery_enabled
            }
        }
        
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                with open(config_file, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                with open(config_file, 'w') as f:
                    json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to: {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise


# Global configuration manager instance
_config_manager: Optional[MCPConfigManager] = None


def get_mcp_config_manager(config_file: Optional[str] = None) -> MCPConfigManager:
    """
    Get global MCP configuration manager instance.
    
    Args:
        config_file: Path to configuration file (optional)
        
    Returns:
        Configuration manager instance
    """
    global _config_manager
    
    if _config_manager is None:
        # Look for config file in standard locations if not provided
        if config_file is None:
            possible_locations = [
                "config/mcp_clients.yaml",
                "config/mcp_clients.yml", 
                "config/mcp_clients.json",
                "../config/mcp_clients.yaml",
                "../config/mcp_clients.yml",
                "../config/mcp_clients.json"
            ]
            
            for location in possible_locations:
                if os.path.exists(location):
                    config_file = location
                    break
        
        _config_manager = MCPConfigManager(config_file)
    
    return _config_manager


def load_mcp_config() -> MCPClientConfig:
    """
    Load MCP configuration using the global manager.
    
    Returns:
        MCP client configuration
    """
    manager = get_mcp_config_manager()
    return manager.load_config()