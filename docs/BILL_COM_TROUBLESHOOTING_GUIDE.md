# Bill.com Integration Troubleshooting Guide

This guide provides comprehensive troubleshooting information for the Bill.com integration in MACAE.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Error Messages](#error-messages)
4. [Configuration Problems](#configuration-problems)
5. [Network and Connectivity](#network-and-connectivity)
6. [Agent Integration Issues](#agent-integration-issues)
7. [Performance Issues](#performance-issues)
8. [Debug Mode](#debug-mode)
9. [Log Analysis](#log-analysis)
10. [Recovery Procedures](#recovery-procedures)

## Quick Diagnostics

### 1. Run Automated Diagnostics

```bash
# Comprehensive setup validation
python3 scripts/bill_com_setup_check.py

# Expected healthy output:
# ✅ Configuration is valid
# ✅ Network connectivity successful  
# ✅ API authentication successful
# ✅ All tests passed
```

### 2. Check Service Status

```bash
# Check if MCP server is running
curl -f http://localhost:9000/health || echo "MCP server not responding"

# Check if backend is running
curl -f http://localhost:8000/health || echo "Backend not responding"

# Check if frontend is running
curl -f http://localhost:3000 || echo "Frontend not responding"
```

### 3. Verify Configuration

```bash
# Check environment variables
env | grep BILL_COM_

# Should show:
# BILL_COM_USERNAME=your-email@company.com
# BILL_COM_ORG_ID=your-org-id
# BILL_COM_ENVIRONMENT=sandbox
# (password and dev_key should be set but not displayed)
```

## Common Issues

### Issue 1: Authentication Failures

**Symptoms:**
- "Authentication failed" errors
- 401 Unauthorized responses
- "Invalid credentials" messages

**Diagnosis:**
```bash
# Test credentials manually
python3 -c "
import os
from src.mcp_server.config.bill_com_config import validate_bill_com_setup
result = validate_bill_com_setup()
print('Valid:', result['valid'])
if not result['valid']:
    print('Errors:', result.get('errors', []))
"
```

**Solutions:**

1. **Verify Credentials in Bill.com Web Interface**
   ```bash
   # Test login at https://app.bill.com (production) or https://app-stage.bill.com (sandbox)
   ```

2. **Check Organization ID**
   - Log into Bill.com
   - Go to Settings → Company Profile
   - Verify Organization ID matches `BILL_COM_ORG_ID`

3. **Verify Developer Key**
   - Check [Bill.com Developer Portal](https://developer.bill.com/)
   - Ensure key is active and not expired
   - Regenerate if necessary

4. **Check API Access**
   - Ensure account has API access enabled
   - Contact Bill.com support if needed

### Issue 2: Network Connectivity Problems

**Symptoms:**
- Connection timeout errors
- "Cannot connect to host" messages
- Network-related failures

**Diagnosis:**
```bash
# Test basic connectivity
curl -I https://api-stage.bill.com/api/v2
curl -I https://api.bill.com/api/v2

# Test with verbose output
curl -v https://api-stage.bill.com/api/v2
```

**Solutions:**

1. **Check Internet Connectivity**
   ```bash
   ping google.com
   ```

2. **Verify Firewall Settings**
   - Ensure outbound HTTPS (port 443) is allowed
   - Check corporate firewall rules
   - Test from different network if possible

3. **Check Proxy Settings**
   ```bash
   # If behind corporate proxy
   export https_proxy=http://proxy.company.com:8080
   export http_proxy=http://proxy.company.com:8080
   ```

4. **DNS Resolution**
   ```bash
   nslookup api-stage.bill.com
   nslookup api.bill.com
   ```

### Issue 3: MCP Server Connection Issues

**Symptoms:**
- "Cannot connect to host localhost:9000"
- MCP server not responding
- Agent fallback messages

**Diagnosis:**
```bash
# Check if MCP server is running
ps aux | grep mcp_server
netstat -an | grep 9000
lsof -i :9000
```

**Solutions:**

1. **Start MCP Server**
   ```bash
   cd src/mcp_server
   python3 mcp_server.py
   ```

2. **Check Port Availability**
   ```bash
   # Kill process using port 9000
   lsof -ti:9000 | xargs kill -9
   
   # Or use different port
   export MCP_SERVER_PORT=9001
   ```

3. **Check MCP Server Logs**
   ```bash
   cd src/mcp_server
   python3 mcp_server.py 2>&1 | tee mcp_server.log
   ```

4. **Verify Dependencies**
   ```bash
   pip install fastmcp
   pip install -r requirements.txt
   ```

### Issue 4: Configuration Validation Errors

**Symptoms:**
- "Configuration validation failed"
- Missing environment variables
- Invalid configuration format

**Diagnosis:**
```bash
# Check .env file exists and is readable
ls -la .env
cat .env | grep BILL_COM_

# Validate configuration
python3 scripts/bill_com_setup_check.py
```

**Solutions:**

1. **Create/Fix .env File**
   ```bash
   # Create .env file in project root
   cat > .env << EOF
   BILL_COM_USERNAME=your-email@company.com
   BILL_COM_PASSWORD=your-password
   BILL_COM_ORG_ID=your-org-id
   BILL_COM_DEV_KEY=your-dev-key
   BILL_COM_ENVIRONMENT=sandbox
   EOF
   ```

2. **Check Variable Names**
   - Ensure exact spelling: `BILL_COM_USERNAME` (not `BILLCOM_USERNAME`)
   - No spaces around equals sign: `BILL_COM_USERNAME=value`
   - No quotes unless needed: `BILL_COM_USERNAME=user@example.com`

3. **Validate Email Format**
   ```bash
   # Username should be valid email
   BILL_COM_USERNAME=user@company.com  # ✅ Good
   BILL_COM_USERNAME=username          # ❌ Bad
   ```

4. **Check Organization ID Format**
   ```bash
   # Should be alphanumeric, typically 15-18 characters
   BILL_COM_ORG_ID=00D000000000000EAA  # ✅ Good
   BILL_COM_ORG_ID=123                 # ❌ Too short
   ```

## Error Messages

### "Authentication failed: 401 Unauthorized"

**Cause:** Invalid credentials or expired session

**Solutions:**
1. Verify username and password
2. Check organization ID
3. Ensure developer key is valid
4. Test credentials in Bill.com web interface

### "Network connectivity failed: Connection timeout"

**Cause:** Network or firewall issues

**Solutions:**
1. Check internet connectivity
2. Verify firewall allows HTTPS outbound
3. Test with different network
4. Check proxy settings

### "Configuration validation failed: Missing required variables"

**Cause:** Missing or incorrectly named environment variables

**Solutions:**
1. Check .env file exists
2. Verify all required variables are set
3. Check variable names for typos
4. Ensure proper format

### "Cannot connect to host localhost:9000"

**Cause:** MCP server not running or port blocked

**Solutions:**
1. Start MCP server
2. Check port availability
3. Verify no firewall blocking localhost
4. Use different port if needed

### "Bill.com service unavailable"

**Cause:** MCP server or Bill.com API issues

**Solutions:**
1. Check MCP server status
2. Verify Bill.com API status
3. Test network connectivity
4. Check configuration

## Configuration Problems

### Environment Variables Not Loading

**Symptoms:**
- Configuration shows default values
- Environment variables not recognized

**Diagnosis:**
```bash
# Check if .env file is in correct location
pwd
ls -la .env

# Check environment loading
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Username:', os.getenv('BILL_COM_USERNAME', 'NOT SET'))
"
```

**Solutions:**
1. Ensure .env file is in project root
2. Install python-dotenv: `pip install python-dotenv`
3. Check file permissions: `chmod 644 .env`
4. Restart services after changing .env

### Wrong Environment (Sandbox vs Production)

**Symptoms:**
- Data doesn't match expectations
- Authentication works but no data

**Diagnosis:**
```bash
# Check current environment
echo $BILL_COM_ENVIRONMENT

# Check configuration
python3 -c "
from src.mcp_server.config.bill_com_config import get_bill_com_config
config = get_bill_com_config()
print('Environment:', config.environment.value)
print('Base URL:', config.base_url)
"
```

**Solutions:**
1. Set correct environment: `BILL_COM_ENVIRONMENT=sandbox` or `production`
2. Verify credentials match environment
3. Check data exists in target environment

### Invalid Configuration Format

**Symptoms:**
- Configuration parsing errors
- Type conversion errors

**Diagnosis:**
```bash
# Test configuration parsing
python3 -c "
from src.mcp_server.config.bill_com_config import BillComConfig
try:
    config = BillComConfig.from_env()
    print('Configuration valid')
except Exception as e:
    print('Configuration error:', e)
"
```

**Solutions:**
1. Check numeric values: `BILL_COM_TIMEOUT=30` (not `30s`)
2. Check boolean values: `BILL_COM_DEBUG=true` (not `True`)
3. Remove quotes unless needed
4. Check for special characters

## Network and Connectivity

### Firewall Issues

**Symptoms:**
- Connection timeouts
- "Connection refused" errors

**Diagnosis:**
```bash
# Test outbound HTTPS
curl -v https://api-stage.bill.com/api/v2

# Check firewall rules (Linux)
sudo iptables -L

# Check firewall rules (macOS)
sudo pfctl -sr
```

**Solutions:**
1. Allow outbound HTTPS (port 443)
2. Add Bill.com domains to allowlist
3. Configure proxy if required
4. Test from different network

### Proxy Configuration

**Symptoms:**
- Connection issues in corporate environment
- Proxy authentication errors

**Diagnosis:**
```bash
# Check proxy environment variables
env | grep -i proxy

# Test with proxy
curl --proxy http://proxy.company.com:8080 https://api-stage.bill.com/api/v2
```

**Solutions:**
1. Set proxy environment variables:
   ```bash
   export https_proxy=http://proxy.company.com:8080
   export http_proxy=http://proxy.company.com:8080
   ```
2. Configure proxy authentication if needed
3. Add proxy bypass for localhost
4. Use corporate CA certificates if required

### DNS Resolution Issues

**Symptoms:**
- "Name resolution failed" errors
- Intermittent connectivity

**Diagnosis:**
```bash
# Test DNS resolution
nslookup api-stage.bill.com
dig api-stage.bill.com

# Check DNS servers
cat /etc/resolv.conf
```

**Solutions:**
1. Use public DNS servers (8.8.8.8, 1.1.1.1)
2. Clear DNS cache
3. Check corporate DNS settings
4. Use IP addresses if DNS fails

## Agent Integration Issues

### Agents Not Recognizing Bill.com Requests

**Symptoms:**
- Generic responses instead of Bill.com integration
- No mention of Bill.com in agent responses

**Diagnosis:**
```bash
# Test agent directly
python3 -c "
import asyncio
from backend.app.agents.state import AgentState
from backend.app.agents.nodes import invoice_agent_node

async def test():
    state = AgentState(
        task_description='Get invoices from Bill.com',
        plan_id='test',
        messages=[],
        current_agent='Invoice'
    )
    result = await invoice_agent_node(state)
    print('Response:', result['final_result'][:200])

asyncio.run(test())
"
```

**Solutions:**
1. Ensure MCP server is running
2. Check Bill.com configuration
3. Verify agent integration code
4. Test with explicit Bill.com keywords

### Agent Fallback Messages

**Symptoms:**
- "Service unavailable" messages
- Fallback to simulated responses

**Expected Behavior:**
- This is normal when MCP server is not running
- Agents should provide helpful guidance

**Solutions:**
1. Start MCP server if you want real integration
2. Check MCP server health
3. Verify Bill.com configuration
4. Review agent logs for errors

### Integration Service Errors

**Symptoms:**
- HTTP connection errors
- MCP tool call failures

**Diagnosis:**
```bash
# Test integration service
python3 -c "
import asyncio
from backend.app.services.bill_com_integration_service import get_bill_com_service

async def test():
    service = get_bill_com_service()
    result = await service.check_bill_com_health()
    print('Health check:', result)
    await service.close()

asyncio.run(test())
"
```

**Solutions:**
1. Ensure MCP server is running on correct port
2. Check network connectivity to localhost:9000
3. Verify MCP server has Bill.com tools registered
4. Check for port conflicts

## Performance Issues

### Slow API Responses

**Symptoms:**
- Long delays in agent responses
- Timeout errors

**Diagnosis:**
```bash
# Test API response time
time curl https://api-stage.bill.com/api/v2

# Check timeout settings
echo $BILL_COM_TIMEOUT
```

**Solutions:**
1. Increase timeout: `BILL_COM_TIMEOUT=60`
2. Check network latency
3. Verify Bill.com API status
4. Use production environment if faster

### Rate Limiting Issues

**Symptoms:**
- 429 "Too Many Requests" errors
- Throttled responses

**Diagnosis:**
```bash
# Check rate limit settings
echo $BILL_COM_RATE_LIMIT_REQUESTS
echo $BILL_COM_RATE_LIMIT_WINDOW
```

**Solutions:**
1. Reduce request rate: `BILL_COM_RATE_LIMIT_REQUESTS=50`
2. Increase window: `BILL_COM_RATE_LIMIT_WINDOW=120`
3. Implement exponential backoff
4. Contact Bill.com for higher limits

### Memory or Resource Issues

**Symptoms:**
- Out of memory errors
- Process crashes

**Diagnosis:**
```bash
# Check memory usage
ps aux | grep python
top -p $(pgrep -f mcp_server)

# Check disk space
df -h
```

**Solutions:**
1. Increase available memory
2. Optimize query parameters (use limits)
3. Implement pagination
4. Monitor resource usage

## Debug Mode

### Enabling Debug Mode

```bash
# Add to .env file
BILL_COM_DEBUG=true
BILL_COM_LOG_REQUESTS=true

# Restart all services
```

### Debug Output Analysis

**Configuration Debug:**
```
DEBUG: Loading Bill.com configuration from environment
DEBUG: Environment: sandbox
DEBUG: Base URL: https://api-stage.bill.com/api/v2
DEBUG: Timeout: 30s
```

**API Request Debug:**
```
DEBUG: Making API request to /api/v2/Login.json
DEBUG: Request headers: {'Content-Type': 'application/json'}
DEBUG: Request body: {'userName': 'user@example.com', ...}
DEBUG: Response status: 200
DEBUG: Response body: {'response_status': 0, 'response_message': 'Success'}
```

**Authentication Debug:**
```
DEBUG: Authenticating with Bill.com
DEBUG: Session ID received: abc123...
DEBUG: Session expires: 2024-01-01T12:00:00Z
```

### Security Warning

**⚠️ IMPORTANT**: Debug mode logs sensitive information including:
- API requests and responses
- Authentication tokens
- Potentially sensitive data

**Never enable debug mode in production!**

## Log Analysis

### MCP Server Logs

```bash
# View real-time logs
cd src/mcp_server
python3 mcp_server.py 2>&1 | tee logs/mcp_server.log

# Search for errors
grep -i error logs/mcp_server.log
grep -i "bill.com" logs/mcp_server.log

# Search for authentication issues
grep -i "auth\|401\|403" logs/mcp_server.log
```

### Backend Logs

```bash
# View backend logs
cd backend
python3 -m uvicorn app.main:app --reload 2>&1 | tee logs/backend.log

# Search for Bill.com integration issues
grep -i "bill.com\|integration" logs/backend.log
```

### Common Log Patterns

**Successful Authentication:**
```
INFO: Bill.com configuration validated successfully
INFO: API authentication successful
INFO: Session ID: abc123...
```

**Configuration Issues:**
```
WARNING: Bill.com configuration incomplete
ERROR: Missing required environment variables
ERROR: Configuration validation failed
```

**Network Issues:**
```
ERROR: Network connectivity failed: Connection timeout
ERROR: Cannot connect to host api-stage.bill.com
WARNING: Retrying request (attempt 2/3)
```

**API Issues:**
```
ERROR: API authentication failed: 401 Unauthorized
ERROR: Rate limit exceeded: 429 Too Many Requests
WARNING: API response time: 15.2s (slow)
```

## Recovery Procedures

### Complete Reset

If all else fails, perform a complete reset:

```bash
# 1. Stop all services
pkill -f mcp_server
pkill -f uvicorn
pkill -f npm

# 2. Clear configuration
rm .env

# 3. Recreate configuration
cat > .env << EOF
BILL_COM_USERNAME=your-email@company.com
BILL_COM_PASSWORD=your-password
BILL_COM_ORG_ID=your-org-id
BILL_COM_DEV_KEY=your-dev-key
BILL_COM_ENVIRONMENT=sandbox
EOF

# 4. Validate configuration
python3 scripts/bill_com_setup_check.py

# 5. Restart services
cd src/mcp_server && python3 mcp_server.py &
cd backend && python3 -m uvicorn app.main:app --reload &
cd src/frontend && npm run dev &
```

### Configuration Recovery

```bash
# Backup current configuration
cp .env .env.backup

# Reset to minimal configuration
cat > .env << EOF
BILL_COM_USERNAME=your-email@company.com
BILL_COM_PASSWORD=your-password
BILL_COM_ORG_ID=your-org-id
BILL_COM_DEV_KEY=your-dev-key
BILL_COM_ENVIRONMENT=sandbox
EOF

# Test minimal configuration
python3 scripts/bill_com_setup_check.py

# Add optional settings if needed
```

### Service Recovery

```bash
# Check what's running
ps aux | grep -E "(mcp_server|uvicorn|npm)"

# Kill stuck processes
pkill -f mcp_server
pkill -f uvicorn
pkill -f "npm.*dev"

# Restart in order
cd src/mcp_server && python3 mcp_server.py &
sleep 5
cd backend && python3 -m uvicorn app.main:app --reload &
sleep 5
cd src/frontend && npm run dev &
```

### Network Recovery

```bash
# Reset network configuration
sudo dscacheutil -flushcache  # macOS
sudo systemctl restart systemd-resolved  # Linux

# Test connectivity
curl -I https://api-stage.bill.com/api/v2

# Reset proxy settings if needed
unset http_proxy https_proxy
```

## Getting Additional Help

### Self-Service Resources

1. **Run Diagnostics**: `python3 scripts/bill_com_setup_check.py`
2. **Check Documentation**: Review setup and configuration guides
3. **Test Integration**: Use provided test scenarios
4. **Review Logs**: Analyze error messages and patterns

### Support Information

When seeking help, provide:

1. **Configuration Status**: Output of setup validation script
2. **Error Messages**: Exact error messages and stack traces
3. **Environment Info**: OS, Python version, network setup
4. **Steps to Reproduce**: What you were trying to do
5. **Log Excerpts**: Relevant log entries (sanitized)

### Useful Commands for Support

```bash
# System information
python3 --version
node --version
uname -a

# Configuration summary
python3 scripts/bill_com_setup_check.py > support_info.txt

# Recent logs
tail -100 logs/mcp_server.log > recent_logs.txt

# Network test
curl -v https://api-stage.bill.com/api/v2 > network_test.txt 2>&1
```

Remember to sanitize any sensitive information before sharing logs or configuration details.