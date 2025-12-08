# Zoho Invoice Setup Checklist

Use this checklist to track your progress.

## Phase 1: Account Setup

- [ ] Create Zoho Invoice account (free tier)
- [ ] Complete organization setup
- [ ] Note your Organization ID

## Phase 2: API Console Setup

- [ ] Access Zoho API Console (https://api-console.zoho.com/)
- [ ] Create Self-Client application
- [ ] Copy Client ID
- [ ] Copy Client Secret
- [ ] Set redirect URI: `http://localhost:8000/oauth/callback`

## Phase 3: Environment Configuration

- [ ] Add `ZOHO_CLIENT_ID` to `backend/.env`
- [ ] Add `ZOHO_CLIENT_SECRET` to `backend/.env`
- [ ] Add `ZOHO_ORGANIZATION_ID` to `backend/.env`
- [ ] Set `ZOHO_DATA_CENTER` (com/eu/in/com.au/com.cn)

## Phase 4: OAuth Testing

- [ ] Install Python dependencies: `pip install requests python-dotenv`
- [ ] Generate grant token from API Console
- [ ] Add `ZOHO_GRANT_TOKEN` to `backend/.env`
- [ ] Run `python3 test_zoho_oauth.py` within 3 minutes
- [ ] Verify refresh token is saved
- [ ] Confirm API connection successful
- [ ] Verify invoice data retrieval

## Phase 5: MCP Server (Next)

- [ ] Create Zoho Invoice MCP server
- [ ] Add Zoho tools (list invoices, create invoice, etc.)
- [ ] Test MCP server standalone
- [ ] Configure MCP client in `.kiro/settings/mcp.json`

## Phase 6: Backend Integration (Next)

- [ ] Create `zoho_mcp_service.py`
- [ ] Create `zoho_agent_node.py`
- [ ] Update LangGraph configuration
- [ ] Update supervisor router
- [ ] Add Zoho keywords to planner

## Phase 7: Testing (Next)

- [ ] Test Zoho agent via backend
- [ ] Test via frontend UI
- [ ] Verify invoice listing
- [ ] Verify invoice creation
- [ ] Test error handling

## Current Status

**Phase 1-4:** OAuth Setup and Testing
**Status:** 🔄 In Progress

---

## Quick Commands

```bash
# Install dependencies
pip install requests python-dotenv

# Test OAuth
python3 backend/test_zoho_oauth.py

# Check configuration
cat backend/.env | grep ZOHO
```

## Need Help?

- 📖 Full Guide: `docs/ZOHO_OAUTH_SETUP.md`
- 🚀 Quick Start: `docs/ZOHO_QUICK_START.md`
- 🔗 Zoho API Docs: https://www.zoho.com/invoice/api/v3/
