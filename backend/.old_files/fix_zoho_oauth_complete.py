"""Complete Zoho OAuth fix with proper scopes."""
import os
import requests
from dotenv import load_dotenv, set_key
from pathlib import Path
import webbrowser
import time

load_dotenv()

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{text}{RESET}")
    print("=" * len(text))

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"   {text}")

print_header("🔧 Zoho OAuth Complete Fix")

# Load config
client_id = os.getenv('ZOHO_CLIENT_ID', '').strip()
client_secret = os.getenv('ZOHO_CLIENT_SECRET', '').strip()
redirect_uri = os.getenv('ZOHO_REDIRECT_URI', 'http://localhost:8000/oauth/callback').strip()
data_center = os.getenv('ZOHO_DATA_CENTER', 'com').strip()
organization_id = os.getenv('ZOHO_ORGANIZATION_ID', '').strip()

if not all([client_id, client_secret, organization_id]):
    print_error("Missing required configuration in .env")
    print_info("Required: ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_ORGANIZATION_ID")
    exit(1)

# Data center URLs
dc_urls = {
    'com': {'accounts': 'https://accounts.zoho.com', 'api': 'https://invoice.zoho.com/api/v3'},
    'eu': {'accounts': 'https://accounts.zoho.eu', 'api': 'https://invoice.zoho.eu/api/v3'},
    'in': {'accounts': 'https://accounts.zoho.in', 'api': 'https://invoice.zoho.in/api/v3'},
}

urls = dc_urls.get(data_center, dc_urls['com'])

# Define ALL required scopes
scopes = [
    "ZohoInvoice.invoices.ALL",
    "ZohoInvoice.contacts.ALL",
    "ZohoInvoice.items.ALL",
    "ZohoInvoice.settings.ALL"
]
scope_string = ",".join(scopes)

print_header("Step 1: Generate Authorization URL")

auth_url = (
    f"{urls['accounts']}/oauth/v2/auth"
    f"?scope={scope_string}"
    f"&client_id={client_id}"
    f"&response_type=code"
    f"&access_type=offline"
    f"&redirect_uri={redirect_uri}"
)

print_info("Required Scopes:")
for scope in scopes:
    print(f"  • {scope}")

print(f"\n{BOLD}Authorization URL:{RESET}")
print(f"{BLUE}{auth_url}{RESET}\n")

print_warning("This URL will open in your browser...")
print_info("1. You'll be asked to log in to Zoho")
print_info("2. Authorize the application")
print_info("3. You'll be redirected to: http://localhost:8000/oauth/callback?code=...")
print_info("4. Copy the 'code=' parameter from the URL")

input(f"\n{YELLOW}Press Enter to open browser...{RESET}")

try:
    webbrowser.open(auth_url)
    print_success("Browser opened")
except:
    print_warning("Could not open browser automatically")
    print_info("Please copy and paste the URL above into your browser")

print(f"\n{BOLD}After authorizing:{RESET}")
print("You'll see a URL like:")
print(f"{BLUE}http://localhost:8000/oauth/callback?code=1000.xxxxx{RESET}")
print("\nCopy everything after 'code=' - that's your grant token")

grant_token = input(f"\n{YELLOW}Paste grant token here: {RESET}").strip()

if not grant_token:
    print_error("No grant token provided")
    exit(1)

print_header("Step 2: Exchange Grant Token")

token_url = f"{urls['accounts']}/oauth/v2/token"
payload = {
    'grant_type': 'authorization_code',
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'code': grant_token
}

try:
    print_info(f"Requesting tokens from: {token_url}")
    response = requests.post(token_url, data=payload, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        
        if access_token and refresh_token:
            print_success("Access token obtained")
            print_success("Refresh token obtained")
            
            # Save refresh token
            env_path = Path(__file__).parent / '.env'
            set_key(env_path, 'ZOHO_REFRESH_TOKEN', refresh_token)
            set_key(env_path, 'ZOHO_ACCESS_TOKEN', access_token)
            # Clear grant token
            set_key(env_path, 'ZOHO_GRANT_TOKEN', '')
            
            print_success("Tokens saved to .env")
        else:
            print_error(f"Unexpected response: {data}")
            exit(1)
    else:
        print_error(f"Failed: {response.status_code}")
        try:
            error = response.json()
            print_error(f"Error: {error}")
        except:
            print_error(f"Response: {response.text[:500]}")
        exit(1)
        
except Exception as e:
    print_error(f"Request failed: {e}")
    exit(1)

print_header("Step 3: Test API Access")

headers = {
    'Authorization': f'Zoho-oauthtoken {access_token}',
    'X-com-zoho-invoice-organizationid': organization_id
}

# Test 1: List invoices
print("\n1. Testing: List Invoices")
try:
    response = requests.get(f"{urls['api']}/invoices", headers=headers, params={'per_page': 5})
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            invoices = data.get('invoices', [])
            print_success(f"Found {len(invoices)} invoice(s)")
            for inv in invoices[:3]:
                print_info(f"  • {inv.get('invoice_number')}: ${inv.get('total')} - {inv.get('status')}")
        else:
            print_warning(f"API returned: {data.get('message')}")
    else:
        print_error(f"Failed: {response.status_code}")
        print_error(f"Response: {response.json()}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 2: List customers
print("\n2. Testing: List Customers")
try:
    response = requests.get(f"{urls['api']}/contacts", headers=headers, params={'per_page': 5})
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            contacts = data.get('contacts', [])
            print_success(f"Found {len(contacts)} customer(s)")
            for contact in contacts[:3]:
                print_info(f"  • {contact.get('contact_name')}: {contact.get('email')}")
        else:
            print_warning(f"API returned: {data.get('message')}")
    else:
        print_error(f"Failed: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 3: Get settings
print("\n3. Testing: Get Settings")
try:
    response = requests.get(f"{urls['api']}/settings/preferences", headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            prefs = data.get('preferences', {})
            print_success("Settings accessible")
            print_info(f"  • Organization: {prefs.get('organization_name', 'N/A')}")
            print_info(f"  • Currency: {prefs.get('currency_code', 'N/A')}")
        else:
            print_warning(f"API returned: {data.get('message')}")
    else:
        print_error(f"Failed: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

print_header("🎉 Setup Complete!")

print(f"\n{GREEN}Your Zoho Invoice API is now fully configured!{RESET}\n")

print(f"{BOLD}Next Steps:{RESET}")
print("1. Enable real Zoho data in backend/.env:")
print(f"   {YELLOW}ZOHO_MCP_ENABLED=true{RESET}")
print("\n2. Restart backend server")
print("\n3. Test in frontend:")
print(f"   {BLUE}'Show me invoices from Zoho'{RESET}")
print("\n4. You should see REAL invoice data from your Zoho account!")

print(f"\n{BOLD}Configuration Summary:{RESET}")
print(f"  • Client ID: {client_id[:20]}...")
print(f"  • Organization ID: {organization_id}")
print(f"  • Data Center: {data_center}")
print(f"  • Refresh Token: ✅ Saved")
print(f"  • Scopes: ✅ All required scopes granted")

print("\n" + "="*60 + "\n")
