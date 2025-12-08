"""Helper script to regenerate Zoho refresh token with correct scopes."""
import os
from dotenv import load_dotenv

load_dotenv()

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

print(f"\n{BOLD}{BLUE}🔄 Zoho Token Regeneration Helper{RESET}\n")

client_id = os.getenv('ZOHO_CLIENT_ID', '').strip()
data_center = os.getenv('ZOHO_DATA_CENTER', 'com').strip()

if not client_id:
    print(f"{RED}❌ ZOHO_CLIENT_ID not found in .env{RESET}")
    exit(1)

# Generate the authorization URL
dc_urls = {
    'com': 'https://accounts.zoho.com',
    'eu': 'https://accounts.zoho.eu',
    'in': 'https://accounts.zoho.in',
    'com.au': 'https://accounts.zoho.com.au',
    'com.cn': 'https://accounts.zoho.com.cn'
}

accounts_url = dc_urls.get(data_center, dc_urls['com'])

# Use .ALL scopes for simplicity
scopes = "ZohoInvoice.invoices.ALL,ZohoInvoice.contacts.ALL,ZohoInvoice.items.ALL,ZohoInvoice.settings.ALL"

auth_url = f"{accounts_url}/oauth/v2/auth"
params = {
    'scope': scopes,
    'client_id': client_id,
    'response_type': 'code',
    'access_type': 'offline',
    'redirect_uri': 'http://localhost:8000/oauth/callback'
}

full_url = auth_url + '?' + '&'.join([f"{k}={v}" for k, v in params.items()])

print(f"{BOLD}Step 1: Get New Grant Token{RESET}")
print("="*60)
print("\nOption A: Use API Console (Recommended)")
print(f"  1. Go to: {YELLOW}https://api-console.zoho.com/{RESET}")
print("  2. Select your Self-Client")
print("  3. Click 'Generate Code'")
print("  4. In 'Scope' field, paste:")
print(f"\n     {GREEN}{scopes}{RESET}\n")
print("  5. Set Time Duration: 3 minutes")
print("  6. Click 'Generate'")
print("  7. Copy the grant token")

print(f"\n{BOLD}Option B: Use Browser Authorization{RESET}")
print("  1. Open this URL in your browser:")
print(f"\n     {BLUE}{full_url}{RESET}\n")
print("  2. Log in and authorize")
print("  3. You'll be redirected to:")
print("     http://localhost:8000/oauth/callback?code=1000.XXXXX")
print("  4. Copy the 'code=' parameter (that's your grant token)")

print(f"\n{BOLD}Step 2: Update .env File{RESET}")
print("="*60)
print("\nEdit backend/.env and update:")
print(f"\n  {YELLOW}ZOHO_GRANT_TOKEN=<paste_your_new_token_here>{RESET}")
print(f"  {YELLOW}ZOHO_REFRESH_TOKEN={RESET}  {RED}# Clear this line{RESET}")
print(f"  {YELLOW}ZOHO_ACCESS_TOKEN={RESET}   {RED}# Clear this line{RESET}")

print(f"\n{BOLD}Step 3: Generate New Refresh Token{RESET}")
print("="*60)
print("\nRun this command within 3 minutes of generating the grant token:")
print(f"\n  {GREEN}python3 backend/test_zoho_oauth.py{RESET}\n")

print(f"{BOLD}Step 4: Verify{RESET}")
print("="*60)
print("\nAfter OAuth succeeds, verify all scopes work:")
print(f"\n  {GREEN}python3 backend/test_zoho_scopes.py{RESET}\n")

print(f"{BOLD}Why This is Necessary:{RESET}")
print("  • Your current refresh token has insufficient scopes")
print("  • Refreshing an access token doesn't add new scopes")
print("  • You must generate a NEW refresh token with correct scopes")
print("  • This requires a NEW grant token with ALL required scopes")

print("\n" + "="*60)
print(f"{YELLOW}⏰ Remember: Grant tokens expire in 3 minutes!{RESET}")
print("="*60 + "\n")
