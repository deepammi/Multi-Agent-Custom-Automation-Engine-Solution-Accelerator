# MCP Client Deployment Guide

This guide covers the deployment of the Multi-Agent Custom Automation Engine (MACAE) backend with standardized MCP client support.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Access to external services (Bill.com, Gmail, Zoho, Salesforce)

## Quick Start

### 1. Environment Setup

Copy the environment template and customize:

```bash
cp .env.mcp.example .env
```

Edit `.env` and add your service credentials:

```bash
# Example service credentials
MCP_BILL_COM_ENV_BILL_COM_API_KEY=your_api_key
MCP_GMAIL_ENV_GMAIL_CREDENTIALS_PATH=/app/credentials/gmail_credentials.json
MCP_ZOHO_ENV_ZOHO_CLIENT_ID=your_client_id
MCP_SALESFORCE_ENV_SALESFORCE_ORG_ALIAS=your_org_alias
```

### 2. Configuration

The system uses a layered configuration approach:

1. **Default Configuration**: Built-in defaults for all services
2. **File Configuration**: `config/mcp_clients.yaml` (optional)
3. **Environment Variables**: Override any setting via environment variables

#### Configuration File (Optional)

Customize `config/mcp_clients.yaml` for advanced settings:

```yaml
# Global settings
connection_pool_size: 10
default_timeout: 30
enable_health_monitoring: true

# Service-specific settings
servers:
  - service_name: "bill_com"
    timeout: 30
    retry_attempts: 3
    environment:
      BILL_COM_API_KEY: "${BILL_COM_API_KEY}"
```

#### Environment Variables

Override any configuration using environment variables:

```bash
# Global settings
MCP_POOL_SIZE=15
MCP_DEFAULT_TIMEOUT=45

# Service-specific settings
MCP_BILL_COM_TIMEOUT=60
MCP_GMAIL_RETRY_ATTEMPTS=5
```

### 3. Docker Deployment

#### Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check service health
curl http://localhost:8000/health
```

#### Production Environment

```bash
# Build and start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor services
docker-compose ps
docker-compose logs backend
```

### 4. Local Development

For local development without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGODB_URL=mongodb://localhost:27017
export MCP_LOG_LEVEL=DEBUG

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration Reference

### Global Settings

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `connection_pool_size` | `MCP_POOL_SIZE` | 10 | Maximum MCP connections |
| `default_timeout` | `MCP_DEFAULT_TIMEOUT` | 30 | Default timeout in seconds |
| `enable_health_monitoring` | `MCP_HEALTH_MONITORING` | true | Enable health monitoring |
| `log_level` | `MCP_LOG_LEVEL` | INFO | Logging level |

### Service Configuration

Each service can be configured using environment variables:

```bash
# Service command and arguments
MCP_<SERVICE>_COMMAND=python3
MCP_<SERVICE>_ARGS=src/mcp_server/service_mcp_server.py

# Service-specific settings
MCP_<SERVICE>_TIMEOUT=30
MCP_<SERVICE>_RETRY_ATTEMPTS=3

# Service environment variables
MCP_<SERVICE>_ENV_<VAR_NAME>=value
```

Where `<SERVICE>` is one of: `BILL_COM`, `GMAIL`, `ZOHO`, `SALESFORCE`

### Service-Specific Environment Variables

#### Bill.com
```bash
MCP_BILL_COM_ENV_BILL_COM_API_KEY=your_api_key
MCP_BILL_COM_ENV_BILL_COM_ORG_ID=your_org_id
```

#### Gmail
```bash
MCP_GMAIL_ENV_GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
MCP_GMAIL_ENV_GMAIL_TOKEN_PATH=/path/to/token.json
```

#### Zoho
```bash
MCP_ZOHO_ENV_ZOHO_CLIENT_ID=your_client_id
MCP_ZOHO_ENV_ZOHO_CLIENT_SECRET=your_client_secret
MCP_ZOHO_ENV_ZOHO_REFRESH_TOKEN=your_refresh_token
```

#### Salesforce
```bash
MCP_SALESFORCE_ENV_SALESFORCE_ORG_ALIAS=your_org_alias
MCP_SALESFORCE_ENV_SALESFORCE_USERNAME=your_username
```

## Health Monitoring

The system provides comprehensive health monitoring for all MCP connections:

### Health Check Endpoint

```bash
# Check overall system health
curl http://localhost:8000/health

# Check specific service health
curl http://localhost:8000/health/mcp/bill_com
```

### Health Monitoring Features

- **Connection Status**: Real-time connection status for each service
- **Response Time Monitoring**: Track response times and performance
- **Automatic Recovery**: Automatic reconnection on failures
- **Error Rate Tracking**: Monitor success/failure rates
- **Diagnostic Tools**: Comprehensive diagnostic information

## Troubleshooting

### Common Issues

#### 1. MCP Connection Failures

**Symptoms**: Services fail to connect or timeout frequently

**Solutions**:
- Check MCP server scripts are executable: `chmod +x src/mcp_server/*.py`
- Verify Python dependencies: `pip install -r requirements.txt`
- Check service credentials and environment variables
- Increase timeout values: `MCP_DEFAULT_TIMEOUT=60`

#### 2. Authentication Errors

**Symptoms**: Tools fail with authentication errors

**Solutions**:
- Verify service credentials are correctly set
- Check credential file paths are accessible
- Refresh OAuth tokens if needed
- Verify service-specific environment variables

#### 3. Performance Issues

**Symptoms**: Slow response times or timeouts

**Solutions**:
- Increase connection pool size: `MCP_POOL_SIZE=20`
- Adjust service-specific timeouts
- Enable health monitoring for better diagnostics
- Check network connectivity to external services

### Diagnostic Commands

```bash
# Check MCP configuration
docker-compose exec backend python -c "from app.config import load_mcp_config; print(load_mcp_config())"

# Test MCP connections
docker-compose exec backend python -c "
import asyncio
from app.services.mcp_client_service import get_mcp_manager
async def test():
    manager = get_mcp_manager()
    health = await manager.check_all_health()
    print(health)
asyncio.run(test())
"

# View detailed logs
docker-compose logs backend | grep MCP
```

### Log Analysis

MCP operations are logged with structured information:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "service": "bill_com",
  "operation": "tool_call",
  "tool_name": "get_bill_com_invoices",
  "execution_time_ms": 1250,
  "success": true
}
```

## Security Considerations

### Credential Management

- Store sensitive credentials in environment variables, not configuration files
- Use Docker secrets for production deployments
- Rotate credentials regularly
- Limit service permissions to minimum required

### Network Security

- Use TLS for external service connections
- Implement network isolation between services
- Monitor and log all external API calls
- Implement rate limiting to prevent abuse

## Performance Optimization

### Connection Pooling

- Adjust pool size based on concurrent usage: `MCP_POOL_SIZE`
- Monitor connection utilization and adjust as needed
- Use health monitoring to identify bottlenecks

### Timeout Configuration

- Set appropriate timeouts for each service based on typical response times
- Use shorter timeouts for health checks
- Implement exponential backoff for retries

### Monitoring and Alerting

- Monitor MCP connection health and performance
- Set up alerts for connection failures or high error rates
- Track response times and identify performance degradation

## Scaling Considerations

### Horizontal Scaling

- MCP clients are stateless and can be scaled horizontally
- Use load balancers to distribute requests across instances
- Ensure shared configuration across all instances

### Resource Requirements

- **CPU**: Moderate usage, scales with concurrent requests
- **Memory**: ~100MB base + ~10MB per active MCP connection
- **Network**: Depends on external service usage patterns
- **Storage**: Minimal, mainly for logs and configuration

## Support and Maintenance

### Regular Maintenance

- Monitor health check results and error rates
- Update MCP SDK and dependencies regularly
- Review and rotate service credentials
- Analyze performance metrics and optimize configuration

### Backup and Recovery

- Backup configuration files and environment variables
- Document service credential recovery procedures
- Test disaster recovery procedures regularly
- Maintain service account access for all external services

For additional support, refer to the main project documentation or contact the development team.