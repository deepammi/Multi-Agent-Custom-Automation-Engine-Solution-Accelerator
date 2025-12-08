# Fix Zoho Scope Authorization Issue

## The Problem

Your refresh token was created with insufficient scopes. Refreshing it doesn't add new permissions - you need to generate a **brand new** refresh token with all required scopes.

## Solution: Generate New Refresh Token

### Step 1: Generate New Grant Token with ALL Scopes

1. Go to: https://api-console.zoho.com/
2. Click on your Self-Client
3. Click **"Generate Code"** or go to **"Self Client"** tab
4. **IMPORTANT:** In the "Scope" field, paste this EXACT text:

```
ZohoInvoice.invoices.ALL,ZohoInvoice.contacts.ALL,ZohoInvoice.items.ALL,ZohoInvoice.settings.ALL
```

**OR use individual scopes:**

```
ZohoInvoice.invoices.READ,ZohoInvoice.invoices.CREATE,ZohoInvoice.invoices.UPDATE,ZohoInvoice.invoices.DELETE,ZohoInvoice.contacts.READ,ZohoInvoice.contacts.CREATE,ZohoInvoice.contacts.UPDATE,ZohoInvoice.items.READ,ZohoInvoice.items.CREATE,ZohoInvoice.settings.READ
```

5. Set **Time Duration**: 3 minutes
6. Click **"Generate"**
7. **IMMEDIATELY copy the grant token** (it expires in 3 minutes!)

### Step 2: Clear Old Tokens in .env

Edit `backend/.env` and update these lines:

```bash
# Replace with your NEW grant token
ZOHO_GRANT_TOKEN=1000.YOUR_NEW_GRANT_TOKEN_HERE

# Clear the old refresh token (it will be regenerated)
ZOHO_REFRESH_TOKEN=

# Clear the old access token
ZOHO_ACCESS_TOKEN=
```

### Step 3: Run OAuth Test to Generate New Refresh Token

```bash
python3 backend/test_zoho_oauth.py
```

This will:
1. Exchange your new grant token for a new access token
2. Generate a **NEW refresh token with correct scopes**
3. Save the new refresh token to `.env`
4. Test API access

### Step 4: Verify It Works

After the OAuth test succeeds, run:

```bash
python3 backend/test_zoho_scopes.py
```

You should see ✅ for all API endpoints.

## Why This Happens

- **Scopes are tied to the refresh token**, not the access token
- When you refresh an access token, it inherits the scopes from the refresh token
- To get new scopes, you must generate a new refresh token from scratch
- This requires a new grant token with the correct scopes

## Quick Checklist

- [ ] Go to Zoho API Console
- [ ] Generate new grant token with ALL scopes (use `.ALL` for simplicity)
- [ ] Copy grant token immediately
- [ ] Update `ZOHO_GRANT_TOKEN` in `.env`
- [ ] Clear `ZOHO_REFRESH_TOKEN` in `.env`
- [ ] Run `python3 backend/test_zoho_oauth.py` within 3 minutes
- [ ] Verify new refresh token is saved
- [ ] Run `python3 backend/test_zoho_scopes.py` to confirm all scopes work

## Alternative: Use Scope Helper

If you're having trouble with the API Console, you can also generate a grant token by visiting this URL in your browser (replace CLIENT_ID):

```
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoInvoice.invoices.ALL,ZohoInvoice.contacts.ALL,ZohoInvoice.items.ALL,ZohoInvoice.settings.ALL&client_id=YOUR_CLIENT_ID&response_type=code&access_type=offline&redirect_uri=http://localhost:8000/oauth/callback
```

After authorizing, you'll be redirected to a URL like:
```
http://localhost:8000/oauth/callback?code=1000.XXXXX
```

The `code=` parameter is your grant token!
