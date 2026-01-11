# Bill.com Integration Setup Guide

This guide provides step-by-step instructions for setting up and configuring the Bill.com integration in the Multi-Agent Custom Automation Engine (MACAE).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Setup](#quick-setup)
3. [Detailed Configuration](#detailed-configuration)
4. [Testing Your Setup](#testing-your-setup)
5. [Agent Integration](#agent-integration)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Python 3.8 or higher
- Node.js 16 or higher (for frontend)
- Git
- Internet connection for Bill.com API access

### Bill.com Account Requirements

1. **Bill.com Account**: Active Bill.com account with API access
2. **Developer Key**: Obtained from Bill.com Developer Portal
3. **Organization ID**: Found in your Bill.com account settings
4. **API Permissions**: Ensure your account has necessary permissions

### Getting Bill.com Credentials

#### Step 1: Get Developer Key

1. Visit [Bill.com Developer Portal](https://developer.bill.com/)
2. Sign up for a developer account (if you don't have one)
3. Create a new application
4. Copy your Developer Key

#### Step 2: Find Organization ID

1. Log into your Bill.com account
2. Go to **Settings** → **Company Profile**
3. Find and copy your **Organization ID**

#### Step 3: Verify API Access

1. Ensure your Bill.com account has API access enabled
2. For production use, contact Bill.com support if needed
3. Test with sandbox environment first

## Quick Setup

### 1. Clone and Install

```bash
# Clone the repository
git clone <repository-url>
cd Multi-Agent-Custom-Automation-Engine-Solution-Accelerator

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for frontend)
cd src/frontend
npm install
cd ../..
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required Bill.com Credentials
BILL_COM_USERNAME=your-email@company.com
BILL_COM_PASSWORD=your-secure-password
BILL_COM_ORG_ID=your-organization-id
BILL_COM_DEV_KEY=your-developer-key

# Environment (start with sandbox)
BILL_COM_ENVIRONMENT=sandbox
```

### 3. Validate Configuration

```bash
# Run the setup validation script
python3 scripts/bill_com_setup_check.py
```

### 4. Start Services

```bash
# Terminal 1: Start MCP Server
cd src/mcp_server
python3 mcp_server.py

# Terminal 2: Start Backend
cd backend
python3 -m uvicorn app.main:app --reload

# Terminal 3: Start Frontend
cd src/frontend
npm run dev
```

### 5. Test Integration

1. Open the frontend at `http://localhost:3000`
2. Submit a task: "Get recent invoices from Bill.com"
3. Verify the Invoice Agent responds with Bill.com integration

## Detailed Configuration

### Environment Variables Reference

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BILL_COM_USERNAME` | Your Bill.com login email | `user@company.com` |
| `BILL_COM_PASSWORD` | Your Bill.com password | `SecurePassword123!` |
| `BILL_COM_ORG_ID` | Organization ID from Bill.com | `00D000000000000EAA` |
| `BILL_COM_DEV_KEY` | Developer key from portal | `abcd1234-5678-90ef-ghij` |

#### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BILL_COM_ENVIRONMENT` | `sandbox` | `sandbox` or `production` |
| `BILL_COM_BASE_URL` | Auto-detected | Custom API base URL |
| `BILL_COM_TIMEOUT` | `30` | Request timeout (seconds) |
| `BILL_COM_MAX_RETRIES` | `3` | Maximum retry attempts |
| `BILL_COM_RETRY_DELAY` | `1.0` | Delay between retries (seconds) |
| `BILL_COM_DEBUG` | `false` | Enable debug logging |
| `BILL_COM_LOG_REQUESTS` | `false` | Log API requests/responses |

### Environment-Specific Configuration

#### Sandbox Environment (Recommended for Testing)

```bash
BILL_COM_ENVIRONMENT=sandbox
# Uses: https://api-stage.bill.com/api/v2
```

- Safe for testing and development
- No real financial data affected
- Full API functionality available
- Recommended for initial setup

#### Production Environment

```bash
BILL_COM_ENVIRONMENT=production
# Uses: https://api.bill.com/api/v2
```

- **⚠️ WARNING**: Uses real financial data
- Only use after thorough testing in sandbox
- Ensure proper security measures
- Monitor API usage and costs

### Advanced Configuration

#### Performance Tuning

```bash
# For high-volume usage
BILL_COM_TIMEOUT=60
BILL_COM_MAX_RETRIES=5
BILL_COM_RATE_LIMIT_REQUESTS=200
BILL_COM_RATE_LIMIT_WINDOW=60
```

#### Debug Configuration

```bash
# For troubleshooting (development only)
BILL_COM_DEBUG=true
BILL_COM_LOG_REQUESTS=true
```

**⚠️ Security Warning**: Never enable debug logging in production as it may log sensitive information.

## Testing Your Setup

### 1. Configuration Validation

```bash
# Run comprehensive validation
python3 scripts/bill_com_setup_check.py

# Expected output:
# ✅ Configuration is valid
# ✅ Network connectivity successful
# ✅ API authentication successful
```

### 2. Health Check Tools

Use the MCP health check tools:

```bash
# Start MCP server first
cd src/mcp_server
python3 mcp_server.py

# In another terminal, test health tools
# (These would be called via the agent interface)
```

### 3. Agent Integration Test

1. Start all services (MCP server, backend, frontend)
2. Open frontend at `http://localhost:3000`
3. Submit test tasks:

**Invoice Agent Tests:**
- "Get recent invoices from Bill.com"
- "Show me vendor information"
- "Find invoice INV-12345"

**Audit Agent Tests:**
- "Check for compliance exceptions"
- "Get audit trail for invoice INV-12345"
- "Detect audit anomalies"

### 4. Integration Test Suite

Run the automated integration tests:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run integration tests
python3 -m pytest tests/integration/ -v
```

## Agent Integration

### Invoice Agent Capabilities

With Bill.com integration, the Invoice Agent can:

- **List Invoices**: Get recent invoices with filtering
- **Search Invoices**: Find specific invoices by number or vendor
- **Invoice Details**: Retrieve complete invoice information
- **Vendor Information**: Access vendor data and relationships
- **Payment Status**: Check payment history and status

### Audit Agent Capabilities

With the generic audit interface, the Audit Agent can:

- **Audit Trails**: Retrieve modification history for invoices
- **Exception Detection**: Find compliance issues and anomalies
- **Audit Reports**: Generate comprehensive compliance reports
- **Real-time Monitoring**: Continuous compliance checking
- **Multi-provider Support**: Works with different AP providers

### Closing Agent (Future)

The Closing Agent will support:

- **Reconciliation**: Automated account reconciliation
- **Variance Analysis**: Detect and analyze variances
- **Journal Entries**: Automated journal entry generation
- **GL Anomalies**: Identify general ledger issues

Currently shows development progress message.

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Symptoms:**
```
❌ API authentication failed: 401 Unauthorized
```

**Solutions:**
1. Verify username and password in Bill.com web interface
2. Check organization ID in Bill.com settings
3. Ensure developer key is correct and active
4. Verify account has API access enabled

#### 2. Network Connectivity Issues

**Symptoms:**
```
❌ Network connectivity failed: Connection timeout
```

**Solutions:**
1. Check internet connectivity
2. Verify firewall allows outbound HTTPS (port 443)
3. Test with: `curl -I https://api-stage.bill.com/api/v2`
4. Check corporate proxy settings

#### 3. Configuration Errors

**Symptoms:**
```
❌ Configuration validation failed: Missing required variables
```

**Solutions:**
1. Run: `python3 scripts/bill_com_setup_check.py`
2. Check `.env` file exists and is readable
3. Verify all required variables are set
4. Check for typos in variable names

#### 4. MCP Server Issues

**Symptoms:**
```
❌ Cannot connect to host localhost:9000
```

**Solutions:**
1. Ensure MCP server is running: `cd src/mcp_server && python3 mcp_server.py`
2. Check port 9000 is not in use by another process
3. Verify no firewall blocking localhost connections
4. Check MCP server logs for errors

#### 5. Agent Integration Issues

**Symptoms:**
- Agents don't respond to Bill.com requests
- Generic responses instead of Bill.com data

**Solutions:**
1. Verify MCP server is running and healthy
2. Check Bill.com configuration is valid
3. Test health check tools
4. Review agent logs for errors

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Add to .env file
BILL_COM_DEBUG=true
BILL_COM_LOG_REQUESTS=true

# Restart services and check logs
```

**⚠️ Important**: Disable debug mode in production.

### Getting Help

#### Self-Diagnosis

1. **Run Setup Validator**: `python3 scripts/bill_com_setup_check.py`
2. **Check Health Status**: Use MCP health check tools
3. **Review Logs**: Check MCP server and backend logs
4. **Test Connectivity**: Verify network and API access

#### Log Analysis

```bash
# Check MCP server logs
tail -f logs/mcp_server.log

# Search for specific errors
grep -i "error\|fail" logs/mcp_server.log

# Check Bill.com specific issues
grep -i "bill.com\|billcom" logs/mcp_server.log
```

#### Support Resources

- **Configuration Guide**: `docs/BILL_COM_CONFIGURATION_GUIDE.md`
- **API Documentation**: [Bill.com Developer Portal](https://developer.bill.com/)
- **Integration Tests**: `tests/integration/`
- **Health Check Tools**: Available via MCP server

### Performance Optimization

#### For High-Volume Usage

```bash
# Increase timeouts and retries
BILL_COM_TIMEOUT=60
BILL_COM_MAX_RETRIES=5

# Adjust rate limiting
BILL_COM_RATE_LIMIT_REQUESTS=500
BILL_COM_RATE_LIMIT_WINDOW=60
```

#### For Development

```bash
# Faster failure detection
BILL_COM_TIMEOUT=10
BILL_COM_MAX_RETRIES=1

# Enable debugging
BILL_COM_DEBUG=true
```

## Security Best Practices

### Credential Management

1. **Never commit credentials to version control**
2. **Use environment variables or secure vaults**
3. **Rotate credentials regularly**
4. **Use least-privilege accounts**
5. **Monitor API access logs**

### Environment Security

```bash
# Production security settings
BILL_COM_ENVIRONMENT=production
BILL_COM_DEBUG=false
BILL_COM_LOG_REQUESTS=false
```

### Network Security

1. **Use HTTPS only** (enforced by default)
2. **Implement proper firewall rules**
3. **Use VPN for production access**
4. **Monitor network traffic**

## Next Steps

After successful setup:

1. **Explore Agent Capabilities**: Test different Bill.com requests
2. **Configure Additional Providers**: Add other AP providers to audit interface
3. **Customize Workflows**: Adapt agents for your specific use cases
4. **Monitor Performance**: Set up logging and monitoring
5. **Plan Production Deployment**: Prepare for production environment

## Support

For additional help:

- Review the comprehensive configuration guide
- Run the diagnostic tools
- Check the troubleshooting section
- Review integration test examples