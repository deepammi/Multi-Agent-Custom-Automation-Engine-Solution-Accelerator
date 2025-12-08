"""Test Zoho Invoice API with proper scopes."""
import os
import requests
from dotenv import load_dotenv, set_key
from pathlib import Path

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

print_header("🔍 Zoho Invoice Scope Checker")

# Load config
client_id = os.getenv('ZOHO_CLIENT_ID', '').strip()
client_secret = os.getenv('ZOHO_CLIENT_SECRET', '').strip()
refresh_token = os.getenv('ZOHO_REFRESH_TOKEN', '').strip()
data_center = os.getenv('ZOHO_DATA_CENTER', 'com').strip()
organization_id = os.getenv('ZOHO_ORGANIZATION_ID', '').strip()

if not refresh_token:
    print_error("No ZOHO_REFRESH_TOKEN found in .env")
    print_info("You need to complete OAuth first")
    exit(1)

# Get fresh access token
print_header("Step 1: Refreshing Access Token")

dc_urls = {
    'com': {'accounts': 'https://accounts.zoho.com', 'api': 'https://invoice.zoho.com/api/v3'},
    'eu': {'accounts': 'https://accounts.zoho.eu', 'api': 'https://invoice.zoho.eu/api/v3'},
    'in': {'accounts': 'https://accounts.zoho.in', 'api': 'https://invoice.zoho.in/api/v3'},
}

urls = dc_urls.get(data_center, dc_urls['com'])
token_url = f"{urls['accounts']}/oauth/v2/token"

payload = {
    'grant_type': 'refresh_token',
    'client_id': client_id,
    'client_secret': client_secret,
    'refresh_token': refresh_token
}

try:
    response = requests.post(token_url, data=payload)
    response.raise_for_status()
    data = response.json()
    access_token = data.get('access_token')
    print_success("Access token refreshed")
except Exception as e:
    print_error(f"Failed to refresh token: {e}")
    exit(1)

# Test different API endpoints to see what works
print_header("Step 2: Testing API Endpoints")

headers = {
    'Authorization': f'Zoho-oauthtoken {access_token}',
    'X-com-zoho-invoice-organizationid': organization_id
}

# Test 1: List invoices (most basic operation)
print("\n1. Testing: List Invoices")
print_info(f"Endpoint: {urls['api']}/invoices")
print_info(f"Required scope: ZohoInvoice.invoices.READ")

try:
    response = requests.get(f"{urls['api']}/invoices", headers=headers, params={'per_page': 1})
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            print_success(f"✓ Can list invoices ({data.get('page_context', {}).get('total', 0)} total)")
        else:
            print_warning(f"API returned: {data.get('message')}")
    elif response.status_code == 401:
        error = response.json()
        print_error(f"Unauthorized: {error.get('message')}")
        print_warning("Missing scope: ZohoInvoice.invoices.READ")
    else:
        print_error(f"Failed: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 2: List customers
print("\n2. Testing: List Customers")
print_info(f"Endpoint: {urls['api']}/contacts")
print_info(f"Required scope: ZohoInvoice.contacts.READ")

try:
    response = requests.get(f"{urls['api']}/contacts", headers=headers, params={'per_page': 1})
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            print_success(f"✓ Can list customers ({data.get('page_context', {}).get('total', 0)} total)")
        else:
            print_warning(f"API returned: {data.get('message')}")
    elif response.status_code == 401:
        error = response.json()
        print_error(f"Unauthorized: {error.get('message')}")
        print_warning("Missing scope: ZohoInvoice.contacts.READ")
    else:
        print_error(f"Failed: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 3: Get settings (includes org info)
print("\n3. Testing: Get Settings")
print_info(f"Endpoint: {urls['api']}/settings/preferences")
print_info(f"Required scope: ZohoInvoice.settings.READ")

try:
    response = requests.get(f"{urls['api']}/settings/preferences", headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            print_success("✓ Can read settings")
            prefs = data.get('preferences', {})
            print_info(f"Organization: {prefs.get('organization_name', 'N/A')}")
        else:
            print_warning(f"API returned: {data.get('message')}")
    elif response.status_code == 401:
        error = response.json()
        print_error(f"Unauthorized: {error.get('message')}")
        print_warning("Missing scope: ZohoInvoice.settings.READ")
    else:
        print_error(f"Failed: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

# Test 4: List items
print("\n4. Testing: List Items")
print_info(f"Endpoint: {urls['api']}/items")
print_info(f"Required scope: ZohoInvoice.items.READ")

try:
    response = requests.get(f"{urls['api']}/items", headers=headers, params={'per_page': 1})
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            print_success(f"✓ Can list items ({data.get('page_context', {}).get('total', 0)} total)")
        else:
            print_warning(f"API returned: {data.get('message')}")
    elif response.status_code == 401:
        error = response.json()
        print_error(f"Unauthorized: {error.get('message')}")
        print_warning("Missing scope: ZohoInvoice.items.READ")
    else:
        print_error(f"Failed: {response.status_code}")
except Exception as e:
    print_error(f"Error: {e}")

# Summary
print_header("Summary & Next Steps")

print(f"\n{BOLD}Required Scopes for Full Functionality:{RESET}")
print("  ✓ ZohoInvoice.invoices.READ")
print("  ✓ ZohoInvoice.invoices.CREATE")
print("  ✓ ZohoInvoice.invoices.UPDATE")
print("  ✓ ZohoInvoice.contacts.READ")
print("  ✓ ZohoInvoice.contacts.CREATE")
print("  ✓ ZohoInvoice.items.READ")
print("  ✓ ZohoInvoice.settings.READ")

print(f"\n{BOLD}To Fix Authorization Issues:{RESET}")
print("\n1. Go to: https://api-console.zoho.com/")
print("2. Select your Self-Client")
print("3. Click 'Generate Code' or 'Self Client' tab")
print("4. In the 'Scope' field, enter ALL of these (comma-separated):")
print(f"\n{YELLOW}ZohoInvoice.invoices.READ,ZohoInvoice.invoices.CREATE,ZohoInvoice.invoices.UPDATE,ZohoInvoice.contacts.READ,ZohoInvoice.contacts.CREATE,ZohoInvoice.items.READ,ZohoInvoice.settings.READ{RESET}")
print("\n5. Set Time Duration: 3 minutes")
print("6. Click 'Generate'")
print("7. Copy the grant token")
print("8. Update .env: ZOHO_GRANT_TOKEN=<your_new_token>")
print("9. Run: python3 test_zoho_oauth.py")

print(f"\n{BOLD}Alternative: Use Scope Helper URL{RESET}")
print(f"\nVisit this URL to generate a grant token with all scopes:")
scope_list = "ZohoInvoice.invoices.READ,ZohoInvoice.invoices.CREATE,ZohoInvoice.invoices.UPDATE,ZohoInvoice.contacts.READ,ZohoInvoice.contacts.CREATE,ZohoInvoice.items.READ,ZohoInvoice.settings.READ"
auth_url = f"{urls['accounts']}/oauth/v2/auth?scope={scope_list}&client_id={client_id}&response_type=code&access_type=offline&redirect_uri=http://localhost:8000/oauth/callback"
print(f"\n{BLUE}{auth_url}{RESET}")

print("\n" + "="*60 + "\n")
