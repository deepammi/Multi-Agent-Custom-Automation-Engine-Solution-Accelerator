# Bill.com Integration Configuration Guide

This guide provides comprehensive instructions for configuring and troubleshooting the Bill.com integration in the Multi-Agent Custom Automation Engine (MACAE).

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Variables](#environment-variables)
3. [Configuration Validation](#configuration-validation)
4. [Health Monitoring](#health-monitoring)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configuration](#advanced-configuration)
7. [Security Best Practices](#security-best-practices)

## Quick Start

### 1. Get Bill.com Credentials

1. **Developer Account**
   - Visit [Bill.com Developer Portal](https://developer.bill.com/)
   - Sign up for a developer account
   - Obtain your developer key

2. **Organization Information**
   - Log into your Bill.com account
   - Go to Settings → Company Profile
   - Note your Organization ID

3. **API Access**
   - Ensure your account has API access enabled
   - For production use, contact Bill.com support if needed

### 2. Set Environment Variables

Create a `.env` file in your project root:

```bash
# Required Bill.com Credentials
BILL_COM_USERNAME=your-email@company.com
BILL_COM_PASSWORD=your-secure-password
BILL_COM_ORG_ID=your-organization-id
BILL_COM_DEV_KEY=your-developer-key

# Environment (sandbox for testing, production for live data)
BILL_COM_ENVIRONMENT=sandbox
```

### 3. Validate Setup

Run the setup validation script:

```bash
python3 scripts/bill_com_setup_check.py
```

### 4. Start Services

```bash
# Start MCP Server
cd src/mcp_server
python3 mcp_server.py

# Start Backend (in another terminal)
cd backend
python3 -m uvicorn app.main:app --reload
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BILL_COM_USERNAME` | Your Bill.com login email | `user@company.com` |
| `BILL_COM_PASSWORD` | Your Bill.com password | `SecurePassword123!` |
| `BILL_COM_ORG_ID` | Your organization ID from Bill.com | `00D000000000000` |
| `BILL_COM_DEV_KEY` | Developer key from Bill.com portal | `abcd1234-5678-90ef-ghij-klmnopqrstuv` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BILL_COM_ENVIRONMENT` | `sandbox` | Environment: `sandbox` or `production` |
| `BILL_COM_BASE_URL` | Auto-detected | Custom API base URL |
| `BILL_COM_TIMEOUT` | `30` | Request timeout in seconds |
| `BILL_COM_MAX_RETRIES` | `3` | Maximum retry attempts |
| `BILL_COM_RETRY_DELAY` | `1.0` | Delay between retries (seconds) |
| `BILL_COM_RATE_LIMIT_REQUESTS` | `100` | Requests per rate limit window |
| `BILL_COM_RATE_LIMIT_WINDOW` | `60` | Rate limit window (seconds) |
| `BILL_COM_DEBUG` | `false` | Enable debug logging |
| `BILL_COM_LOG_REQUESTS` | `false` | Log API requests/responses |

### Environment-Specific URLs

- **Sandbox**: `https://api-stage.bill.com/api/v2`
- **Production**: `https://api.bill.com/api/v2`

## Configuration Validation

### Automatic Validation

The system automatically validates configuration on startup:

```python
from src.mcp_server.config.bill_com_config import validate_bill_com_setup

result = validate_bill_com_setup()
if result["valid"]:
    print("Configuration is valid!")
else:
    print("Configuration errors:", result["errors"])
```

### Manual Validation

Use the setup script for interactive validation:

```bash
python3 scripts/bill_com_setup_check.py
```

### Validation Checks

The system performs these validation checks:

1. **Required Fields**: All mandatory environment variables are set
2. **Format Validation**: Email format, ID lengths, etc.
3. **Network Connectivity**: Can reach Bill.com API endpoints
4. **Authentication**: Credentials work with Bill.com API
5. **API Functionality**: Basic API operations succeed

## Health Monitoring

### Health Check Tools

The integration provides several MCP tools for health monitoring:

#### `bill_com_health_check`
Comprehensive health check of all integration components.

```bash
# Quick health check (uses cache)
bill_com_health_check

# Comprehensive health check (always fresh)
bill_com_health_check --comprehensive=true
```

#### `bill_com_config_validation`
Validates configuration without testing connectivity.

#### `bill_com_connection_test`
Tests network connectivity and API functionality.

#### `bill_com_diagnostics`
Provides detailed diagnostic information for troubleshooting.

### Health Status Levels

- **Healthy**: All systems operational
- **Warning**: Minor issues that don't prevent operation
- **Unhealthy**: Significant issues affecting functionality
- **Error**: Critical failures preventing operation

### Monitoring Integration

For production deployments, integrate health checks with your monitoring system:

```python
from src.mcp_server.services.bill_com_health_service import get_health_service

async def check_bill_com_health():
    health_service = get_health_service()
    result = await health_service.quick_health_check()
    return result["overall_status"] == "healthy"
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Symptoms:**
- "Authentication failed" errors
- 401 Unauthorized responses

**Solutions:**
- Verify username and password in Bill.com web interface
- Check organization ID in Bill.com settings
- Ensure developer key is correct and active
- Verify account has API access enabled

#### 2. Network Connectivity Issues

**Symptoms:**
- Connection timeout errors
- "Cannot connect to host" messages

**Solutions:**
- Check internet connectivity
- Verify firewall allows outbound HTTPS (port 443)
- Test with curl: `curl -I https://api-stage.bill.com/api/v2`
- Check proxy settings if behind corporate firewall

#### 3. Rate Limiting

**Symptoms:**
- 429 Too Many Requests errors
- Slow API responses

**Solutions:**
- Reduce `BILL_COM_RATE_LIMIT_REQUESTS`
- Increase `BILL_COM_RATE_LIMIT_WINDOW`
- Implement exponential backoff
- Contact Bill.com for rate limit increases

#### 4. Configuration Errors

**Symptoms:**
- "Configuration validation failed" messages
- Missing environment variable warnings

**Solutions:**
- Run `python3 scripts/bill_com_setup_check.py`
- Check `.env` file exists and is readable
- Verify all required variables are set
- Check for typos in variable names

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
BILL_COM_DEBUG=true
BILL_COM_LOG_REQUESTS=true
```

**Warning**: Debug mode logs sensitive information. Only use in development.

### Log Analysis

Check logs for specific error patterns:

```bash
# Search for Bill.com related errors
grep -i "bill.com\|billcom" logs/mcp_server.log

# Search for authentication issues
grep -i "auth\|401\|403" logs/mcp_server.log

# Search for network issues
grep -i "connect\|timeout\|network" logs/mcp_server.log
```

## Advanced Configuration

### Custom API Endpoints

For special deployments or testing:

```bash
BILL_COM_BASE_URL=https://custom-api.bill.com/api/v2
```

### Performance Tuning

For high-volume deployments:

```bash
# Increase timeouts for slow networks
BILL_COM_TIMEOUT=60

# Reduce retries for faster failure detection
BILL_COM_MAX_RETRIES=1

# Adjust rate limiting for your API limits
BILL_COM_RATE_LIMIT_REQUESTS=200
BILL_COM_RATE_LIMIT_WINDOW=60
```

### Multi-Environment Setup

Use different configurations for different environments:

```bash
# Development
BILL_COM_ENVIRONMENT=sandbox
BILL_COM_DEBUG=true

# Staging
BILL_COM_ENVIRONMENT=sandbox
BILL_COM_DEBUG=false

# Production
BILL_COM_ENVIRONMENT=production
BILL_COM_DEBUG=false
BILL_COM_LOG_REQUESTS=false
```

## Security Best Practices

### Credential Management

1. **Never commit credentials to version control**
2. **Use environment variables or secure vaults**
3. **Rotate credentials regularly**
4. **Use least-privilege accounts**

### Network Security

1. **Use HTTPS only (default)**
2. **Implement proper firewall rules**
3. **Monitor API access logs**
4. **Use VPN for production access**

### Logging Security

1. **Never log passwords or API keys**
2. **Sanitize sensitive data in logs**
3. **Secure log storage and access**
4. **Implement log rotation**

### Example Secure Configuration

```bash
# Use strong, unique passwords
BILL_COM_PASSWORD=ComplexPassword123!@#

# Disable debug logging in production
BILL_COM_DEBUG=false
BILL_COM_LOG_REQUESTS=false

# Use production environment only when needed
BILL_COM_ENVIRONMENT=sandbox  # Change to production only when ready
```

## Integration Testing

### Test Scenarios

1. **Configuration Validation**
   ```bash
   python3 scripts/bill_com_setup_check.py
   ```

2. **API Connectivity**
   ```bash
   # Test with MCP tools
   bill_com_connection_test
   ```

3. **Agent Integration**
   ```bash
   # Test invoice agent with Bill.com
   # Submit task: "Get recent invoices from Bill.com"
   ```

### Automated Testing

For CI/CD pipelines:

```bash
#!/bin/bash
# Test script for CI/CD

# Set test credentials (use test account)
export BILL_COM_USERNAME="test@example.com"
export BILL_COM_PASSWORD="TestPassword123"
export BILL_COM_ORG_ID="TestOrgId"
export BILL_COM_DEV_KEY="TestDevKey"
export BILL_COM_ENVIRONMENT="sandbox"

# Run validation
python3 scripts/bill_com_setup_check.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "Bill.com integration tests passed"
else
    echo "Bill.com integration tests failed"
    exit 1
fi
```

## Support and Resources

### Documentation
- [Bill.com API Documentation](https://developer.bill.com/hc/en-us)
- [Bill.com Developer Portal](https://developer.bill.com/)

### Getting Help
- Check the troubleshooting section above
- Run diagnostics: `bill_com_diagnostics`
- Review logs for error details
- Contact Bill.com developer support for API issues

### Updates and Maintenance
- Monitor Bill.com API status page
- Update credentials before expiration
- Review rate limits periodically
- Test configuration after Bill.com updates