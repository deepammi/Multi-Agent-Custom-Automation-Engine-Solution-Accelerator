"""
Bill.com health check service for connectivity and configuration validation.
Provides comprehensive health monitoring and diagnostics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp

from config.bill_com_config import get_bill_com_config, validate_bill_com_setup, BillComConfig

logger = logging.getLogger(__name__)


class BillComHealthService:
    """Service for monitoring Bill.com connectivity and health."""
    
    def __init__(self):
        self.last_health_check: Optional[datetime] = None
        self.last_health_result: Optional[Dict[str, Any]] = None
        self.health_cache_duration = timedelta(minutes=5)
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of Bill.com integration."""
        health_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "checks": {},
            "summary": "",
            "recommendations": []
        }
        
        try:
            # 1. Configuration validation
            config_check = await self._check_configuration()
            health_result["checks"]["configuration"] = config_check
            
            # 2. Network connectivity
            network_check = await self._check_network_connectivity()
            health_result["checks"]["network"] = network_check
            
            # 3. API authentication (if config is valid)
            auth_check = {"status": "skipped", "reason": "Configuration invalid"}
            if config_check["status"] == "healthy":
                auth_check = await self._check_api_authentication()
            health_result["checks"]["authentication"] = auth_check
            
            # 4. API functionality (if auth is valid)
            api_check = {"status": "skipped", "reason": "Authentication failed"}
            if auth_check["status"] == "healthy":
                api_check = await self._check_api_functionality()
            health_result["checks"]["api_functionality"] = api_check
            
            # 5. Rate limiting status
            rate_limit_check = await self._check_rate_limits()
            health_result["checks"]["rate_limits"] = rate_limit_check
            
            # Determine overall status
            health_result["overall_status"] = self._determine_overall_status(health_result["checks"])
            
            # Generate summary and recommendations
            health_result["summary"] = self._generate_summary(health_result["checks"])
            health_result["recommendations"] = self._generate_recommendations(health_result["checks"])
            
            # Cache the result
            self.last_health_check = datetime.utcnow()
            self.last_health_result = health_result
            
            logger.info(f"Health check completed: {health_result['overall_status']}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_result["overall_status"] = "error"
            health_result["error"] = str(e)
        
        return health_result
    
    async def quick_health_check(self) -> Dict[str, Any]:
        """Perform quick health check (uses cache if recent)."""
        # Use cached result if recent
        if (self.last_health_check and 
            datetime.utcnow() - self.last_health_check < self.health_cache_duration and
            self.last_health_result):
            
            result = self.last_health_result.copy()
            result["cached"] = True
            result["cache_age_seconds"] = (datetime.utcnow() - self.last_health_check).total_seconds()
            return result
        
        # Perform new check
        return await self.comprehensive_health_check()
    
    async def _check_configuration(self) -> Dict[str, Any]:
        """Check Bill.com configuration validity."""
        try:
            validation_result = validate_bill_com_setup()
            
            if validation_result["valid"]:
                config = validation_result["config"]
                return {
                    "status": "healthy",
                    "message": f"Configuration valid for {config.environment.value} environment",
                    "details": {
                        "environment": config.environment.value,
                        "base_url": config.base_url,
                        "timeout": config.timeout,
                        "max_retries": config.max_retries,
                        "warnings": validation_result.get("warnings", [])
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Configuration validation failed",
                    "details": {
                        "errors": validation_result.get("errors", []),
                        "missing_required": validation_result.get("missing_required", []),
                        "missing_optional": validation_result.get("missing_optional", [])
                    }
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Configuration check failed: {e}",
                "details": {"error": str(e)}
            }
    
    async def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity to Bill.com API."""
        try:
            config = get_bill_com_config()
            
            # Test basic connectivity
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = datetime.utcnow()
                
                # Try to reach the API base URL
                async with session.get(config.base_url) as response:
                    response_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    return {
                        "status": "healthy",
                        "message": f"Network connectivity successful (HTTP {response.status})",
                        "details": {
                            "response_time_seconds": response_time,
                            "status_code": response.status,
                            "base_url": config.base_url
                        }
                    }
                    
        except aiohttp.ClientError as e:
            return {
                "status": "unhealthy",
                "message": f"Network connectivity failed: {e}",
                "details": {"error": str(e), "error_type": "network"}
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Network check error: {e}",
                "details": {"error": str(e)}
            }
    
    async def _check_api_authentication(self) -> Dict[str, Any]:
        """Check Bill.com API authentication."""
        try:
            # Import here to avoid circular imports
            from services.bill_com_service import BillComAPIService
            
            config = get_bill_com_config()
            service = BillComAPIService(config)
            
            # Attempt authentication
            start_time = datetime.utcnow()
            await service.authenticate()
            auth_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "message": "API authentication successful",
                "details": {
                    "auth_time_seconds": auth_time,
                    "session_id": service.session.session_id if service.session else None,
                    "organization_id": config.organization_id
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"API authentication failed: {e}",
                "details": {"error": str(e), "error_type": "authentication"}
            }
    
    async def _check_api_functionality(self) -> Dict[str, Any]:
        """Check basic API functionality."""
        try:
            # Import here to avoid circular imports
            from services.bill_com_service import BillComAPIService
            
            config = get_bill_com_config()
            service = BillComAPIService(config)
            
            # Ensure authenticated
            await service.ensure_authenticated()
            
            # Test basic API call (get organization info)
            start_time = datetime.utcnow()
            
            # Try to get a simple list (vendors with limit 1)
            result = await service.get_vendors(limit=1)
            
            api_time = (datetime.utcnow() - start_time).total_seconds()
            
            if result:
                return {
                    "status": "healthy",
                    "message": "API functionality test successful",
                    "details": {
                        "api_call_time_seconds": api_time,
                        "test_operation": "get_vendors",
                        "result_count": len(result)
                    }
                }
            else:
                return {
                    "status": "warning",
                    "message": "API call succeeded but returned no data",
                    "details": {
                        "api_call_time_seconds": api_time,
                        "test_operation": "get_vendors"
                    }
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"API functionality test failed: {e}",
                "details": {"error": str(e), "error_type": "api_functionality"}
            }
    
    async def _check_rate_limits(self) -> Dict[str, Any]:
        """Check rate limiting status."""
        try:
            config = get_bill_com_config()
            
            # This is a basic check - in a real implementation,
            # you'd track actual API calls and rate limit status
            return {
                "status": "healthy",
                "message": "Rate limiting configured",
                "details": {
                    "requests_per_window": config.rate_limit_requests,
                    "window_seconds": config.rate_limit_window,
                    "current_usage": "unknown"  # Would track actual usage
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Rate limit check failed: {e}",
                "details": {"error": str(e)}
            }
    
    def _determine_overall_status(self, checks: Dict[str, Dict[str, Any]]) -> str:
        """Determine overall health status from individual checks."""
        statuses = [check["status"] for check in checks.values()]
        
        if "error" in statuses:
            return "error"
        elif "unhealthy" in statuses:
            return "unhealthy"
        elif "warning" in statuses:
            return "warning"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "unknown"
    
    def _generate_summary(self, checks: Dict[str, Dict[str, Any]]) -> str:
        """Generate human-readable summary of health status."""
        healthy_count = sum(1 for check in checks.values() if check["status"] == "healthy")
        total_count = len(checks)
        
        if healthy_count == total_count:
            return f"All {total_count} health checks passed. Bill.com integration is fully operational."
        elif healthy_count == 0:
            return f"All {total_count} health checks failed. Bill.com integration is not operational."
        else:
            return f"{healthy_count}/{total_count} health checks passed. Bill.com integration has issues."
    
    def _generate_recommendations(self, checks: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on health check results."""
        recommendations = []
        
        # Configuration recommendations
        config_check = checks.get("configuration", {})
        if config_check.get("status") == "unhealthy":
            details = config_check.get("details", {})
            missing_required = details.get("missing_required", [])
            if missing_required:
                recommendations.append(f"Set required environment variables: {', '.join(missing_required)}")
        
        # Network recommendations
        network_check = checks.get("network", {})
        if network_check.get("status") == "unhealthy":
            recommendations.append("Check network connectivity and firewall settings")
        
        # Authentication recommendations
        auth_check = checks.get("authentication", {})
        if auth_check.get("status") == "unhealthy":
            recommendations.append("Verify Bill.com credentials and organization ID")
        
        # API functionality recommendations
        api_check = checks.get("api_functionality", {})
        if api_check.get("status") == "unhealthy":
            recommendations.append("Check Bill.com API status and account permissions")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Bill.com integration is healthy - no action needed")
        
        return recommendations


# Global health service instance
_health_service: Optional[BillComHealthService] = None


def get_health_service() -> BillComHealthService:
    """Get the global health service instance."""
    global _health_service
    if _health_service is None:
        _health_service = BillComHealthService()
    return _health_service