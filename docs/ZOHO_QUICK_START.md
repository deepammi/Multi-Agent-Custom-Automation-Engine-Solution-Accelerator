# Zoho Invoice OAuth - Quick Start

Follow these steps to test your Zoho Invoice connection.

## Prerequisites

- Zoho Invoice account (free tier works)
- Python 3.8+
- `requests` library

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd backend
pip install requests python-dotenv
```

### 2. Create Zoho API Client

1. Go to [Zoho API Console](https://api-console.zoho.com/)
2. Click **"Add Client"** → **"Self Client"**
3. Fill in:
   - Client Name: `Zoho Invoice MCP`
   - Homepage URL: `http://localhost:8000`
   - Authorized Redirect URI: `http://localhost:8000/oauth/callback`
4. Click **"Create"**
5. **Copy your Client ID and Client Secret**

### 3. Find Your Organization ID

1. Log in to [Zoho Invoice](https://invoice.zoho.com)
2. Go to **Settings** → **Organization Profile**
3. Copy your **Organization ID** (or check the URL)

### 4. Configure Environment Variables

Edit `backend/.env` and add:

```bash
ZOHO_CLIENT_ID=1000.XXXXXXXXXXXXX
ZOHO_CLIENT_SECRET=your_secret_here
ZOHO_ORGANIZATION_ID=your_org_id_here
ZOHO_DATA_CENTER=com
```

**Data Center Options:**
- `com` - United States (default)
- `eu` - Europe
- `in` - India
- `com.au` - Australia
- `com.cn` - China

### 5. Generate Grant Token

1. Go back to [Zoho API Console](https://api-console.zoho.com/)
2. Click on your Self-Client
3. Click **"Generate Code"** (or "Self Client" tab)
4. Select scopes:
   - `ZohoInvoice.invoices.READ`
   - `ZohoInvoice.customers.READ`
   - `ZohoInvoice.settings.READ`
5. Set duration: **3 minutes**
6. Click **"Generate"**
7. **Copy the grant token immediately!**

### 6. Add Grant Token to .env

```bash
ZOHO_GRANT_TOKEN=1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 7. Run OAuth Test

**Important:** Run this within 3 minutes of generating the grant token!

```bash
python3 test_zoho_oauth.py
```

### 8. Expected Output

```
🔐 Zoho Invoice OAuth Test
========================================

Step 1: Exchanging Grant Token
===============================
ℹ️  Requesting tokens from: https://accounts.zoho.com/oauth/v2/token
✅ Access token obtained
✅ Refresh token obtained
ℹ️  Access token expires in: 3600 seconds

Step 2: Testing API Connection
===============================
ℹ️  Fetching organization info from: https://invoice.zoho.com/api/v3/organizations/123456
✅ Successfully connected to Zoho Invoice API
ℹ️  Organization: Your Company Name
ℹ️  Organization ID: 123456789
ℹ️  Currency: USD

Step 3: Fetching Invoices
==========================
ℹ️  Fetching invoices from: https://invoice.zoho.com/api/v3/invoices
✅ Found 2 invoice(s)

  1. Invoice #INV-001
     Customer: Acme Corp
     Amount: $1,500.00
     Status: sent
     Date: 2025-01-15

  2. Invoice #INV-002
     Customer: Tech Solutions
     Amount: $2,750.00
     Status: paid
     Date: 2025-01-20

Step 4: Saving Refresh Token
=============================
✅ Refresh token saved to .env
ℹ️  You can now use this refresh token for future API calls

🎉 OAuth Setup Complete!

Your Zoho Invoice API is now configured and working.

Next steps:
1. ✅ OAuth authentication verified
2. 🔄 Create Zoho Invoice MCP Server
3. 🔄 Integrate with backend agents
4. 🔄 Test end-to-end workflow
```

## Troubleshooting

### "Invalid Grant Token"
- Grant tokens expire in 3 minutes
- Generate a new one and run the test immediately

### "Invalid Client"
- Check your Client ID and Client Secret
- Make sure there are no extra spaces

### "Organization Not Found"
- Verify your Organization ID
- Check that you're using the correct data center

### "Insufficient Scope"
- Make sure you selected the required scopes when generating the grant token
- Minimum: `ZohoInvoice.invoices.READ`, `ZohoInvoice.customers.READ`

## What Happens Next?

After successful OAuth testing:

1. **Refresh Token Saved**: Your `.env` file now contains `ZOHO_REFRESH_TOKEN`
2. **No More Grant Tokens Needed**: The refresh token doesn't expire
3. **Automatic Token Refresh**: Access tokens are refreshed automatically
4. **Ready for MCP Server**: You can now build the full integration

## Security Notes

- ✅ `.env` is in `.gitignore` - credentials won't be committed
- ✅ Refresh tokens don't expire (but can be revoked)
- ✅ Access tokens expire in 1 hour (auto-refreshed)
- ⚠️ Never share your Client Secret or Refresh Token

## Next Steps

Once OAuth is working, let me know and I'll create:
1. Zoho Invoice MCP Server
2. Backend integration service
3. Zoho agent node for LangGraph
4. Full end-to-end testing

Ready to proceed? 🚀
