# Zoho Invoice OAuth Setup Guide

This guide walks you through setting up OAuth authentication with Zoho Invoice API.

## Overview

Zoho uses OAuth 2.0 for API authentication. You'll need to:
1. Create a Zoho API Console account
2. Register a self-client application
3. Generate OAuth credentials
4. Test the connection

## Phase 1: Create Zoho Developer Account

### 1.1 Sign Up for Zoho Invoice (Free Tier)

1. Go to [Zoho Invoice](https://www.zoho.com/invoice/)
2. Sign up for a free account
3. Complete the organization setup
4. Note your **organization ID** (you'll need this later)

### 1.2 Access Zoho API Console

1. Go to [Zoho API Console](https://api-console.zoho.com/)
2. Sign in with your Zoho account
3. You'll be redirected to the API Console dashboard

## Phase 2: Register Self-Client Application

### 2.1 Create Self-Client

1. In the API Console, click **"Add Client"**
2. Select **"Self Client"** (recommended for server-to-server applications)
3. Fill in the details:
   - **Client Name**: `Zoho Invoice MCP Server` (or any name you prefer)
   - **Homepage URL**: `http://localhost:8000` (your backend URL)
   - **Authorized Redirect URIs**: `http://localhost:8000/oauth/callback`

4. Click **"Create"**

### 2.2 Note Your Credentials

After creating the client, you'll see:
- **Client ID**: A long string (e.g., `1000.XXXXXXXXXXXXX`)
- **Client Secret**: Another long string
- **Scope**: You'll need to set this in the next step

**⚠️ Important:** Save these credentials securely. You'll need them for authentication.

### 2.3 Set Required Scopes

For Zoho Invoice, you need these scopes:
```
ZohoInvoice.invoices.READ
ZohoInvoice.invoices.CREATE
ZohoInvoice.invoices.UPDATE
ZohoInvoice.invoices.DELETE
ZohoInvoice.customers.READ
ZohoInvoice.customers.CREATE
ZohoInvoice.items.READ
ZohoInvoice.settings.READ
```

**Minimal scopes for testing:**
```
ZohoInvoice.invoices.READ
ZohoInvoice.customers.READ
```

## Phase 3: Generate Initial Access Token

### 3.1 Generate Grant Token (One-Time)

Zoho requires a one-time "grant token" to generate your first access token.

1. In the API Console, go to your Self-Client
2. Click on the **"Generate Code"** button (or similar)
3. Select the scopes you need
4. Set the **Time Duration**: 3 minutes (default)
5. Click **"Generate"**
6. **Copy the grant token immediately** (it expires in 3 minutes!)

The grant token looks like: `1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 3.2 Exchange Grant Token for Access Token

You'll use the grant token to get:
- **Access Token**: Used for API calls (expires in 1 hour)
- **Refresh Token**: Used to get new access tokens (doesn't expire)

We'll do this programmatically in the test script.

## Phase 4: Determine Your Data Center

Zoho has different data centers based on your region:
- **US**: `https://invoice.zoho.com` (accounts.zoho.com)
- **EU**: `https://invoice.zoho.eu` (accounts.zoho.eu)
- **IN**: `https://invoice.zoho.in` (accounts.zoho.in)
- **AU**: `https://invoice.zoho.com.au` (accounts.zoho.com.au)
- **CN**: `https://invoice.zoho.com.cn` (accounts.zoho.com.cn)

**To find your data center:**
1. Log in to Zoho Invoice
2. Check the URL in your browser
3. Note the domain (`.com`, `.eu`, `.in`, etc.)

## Phase 5: Configuration

### 5.1 Create Environment Variables

Add these to `backend/.env`:

```bash
# Zoho Invoice Configuration
ZOHO_CLIENT_ID=1000.XXXXXXXXXXXXX
ZOHO_CLIENT_SECRET=your_client_secret_here
ZOHO_REDIRECT_URI=http://localhost:8000/oauth/callback
ZOHO_DATA_CENTER=com
ZOHO_ORGANIZATION_ID=your_org_id_here

# OAuth Tokens (will be generated)
ZOHO_REFRESH_TOKEN=
ZOHO_ACCESS_TOKEN=
```

### 5.2 Find Your Organization ID

1. Log in to [Zoho Invoice](https://invoice.zoho.com)
2. Go to **Settings** → **Organization Profile**
3. Your Organization ID is displayed at the top
4. Or check the URL: `https://invoice.zoho.com/app/ORGANIZATION_ID#/...`

## Phase 6: Test OAuth Connection

### 6.1 Install Required Python Packages

```bash
cd backend
pip install requests python-dotenv
```

### 6.2 Run OAuth Test Script

We'll create a test script that:
1. Exchanges your grant token for access/refresh tokens
2. Tests API connectivity
3. Retrieves sample invoice data

```bash
python3 test_zoho_oauth.py
```

### 6.3 Expected Output

```
🔐 Zoho OAuth Test
==================

Step 1: Exchanging grant token for access token...
✅ Access token obtained
✅ Refresh token obtained

Step 2: Testing API connection...
✅ Successfully connected to Zoho Invoice API

Step 3: Fetching organization info...
Organization: Your Company Name
Organization ID: 123456789

Step 4: Fetching invoices...
✅ Found 5 invoices

Step 5: Saving refresh token...
✅ Refresh token saved to .env

🎉 OAuth setup complete!
```

## Troubleshooting

### Issue: "Invalid Grant Token"
**Solution:** Grant tokens expire in 3 minutes. Generate a new one and run the test immediately.

### Issue: "Invalid Client"
**Solution:** Double-check your Client ID and Client Secret in `.env`

### Issue: "Scope Mismatch"
**Solution:** Ensure the scopes in your grant token match what you're requesting

### Issue: "Organization Not Found"
**Solution:** Verify your Organization ID in Zoho Invoice settings

### Issue: "Invalid Data Center"
**Solution:** Check your Zoho Invoice URL and set the correct data center in `.env`

## Security Best Practices

1. **Never commit credentials to Git**
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Rotate tokens regularly**
   - Access tokens expire in 1 hour (automatic refresh)
   - Refresh tokens don't expire but should be rotated periodically

3. **Use minimal scopes**
   - Only request the permissions you need
   - Start with READ-only scopes for testing

4. **Secure storage**
   - Store refresh tokens securely
   - Consider using a secrets manager in production

## Next Steps

After successful OAuth testing:
1. ✅ OAuth connection verified
2. 🔄 Create Zoho Invoice MCP Server
3. 🔄 Integrate with backend agents
4. 🔄 Test end-to-end workflow

## Resources

- [Zoho Invoice API Documentation](https://www.zoho.com/invoice/api/v3/)
- [Zoho OAuth 2.0 Guide](https://www.zoho.com/accounts/protocol/oauth.html)
- [Zoho API Console](https://api-console.zoho.com/)
- [Zoho Invoice Scopes](https://www.zoho.com/invoice/api/v3/oauth/)

## Quick Reference

### API Endpoints by Data Center

| Data Center | Accounts URL | API Base URL |
|-------------|--------------|--------------|
| US (.com) | https://accounts.zoho.com | https://invoice.zoho.com/api/v3 |
| EU (.eu) | https://accounts.zoho.eu | https://invoice.zoho.eu/api/v3 |
| IN (.in) | https://accounts.zoho.in | https://invoice.zoho.in/api/v3 |
| AU (.com.au) | https://accounts.zoho.com.au | https://invoice.zoho.com.au/api/v3 |
| CN (.com.cn) | https://accounts.zoho.com.cn | https://invoice.zoho.com.cn/api/v3 |

### Common Scopes

```
# Read-only (safe for testing)
ZohoInvoice.invoices.READ
ZohoInvoice.customers.READ
ZohoInvoice.items.READ
ZohoInvoice.settings.READ

# Write operations
ZohoInvoice.invoices.CREATE
ZohoInvoice.invoices.UPDATE
ZohoInvoice.invoices.DELETE
ZohoInvoice.customers.CREATE
ZohoInvoice.customers.UPDATE
```
