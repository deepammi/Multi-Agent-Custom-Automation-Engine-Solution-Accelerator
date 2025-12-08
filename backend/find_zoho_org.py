"""Find your correct Zoho organization ID."""
import os
import requests
from dotenv import load_dotenv

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

def print_info(text):
    print(f"   {text}")

print_header("🔍 Finding Your Zoho Organization ID")

# Get configuration
access_token = os.getenv('ZOHO_ACCESS_TOKEN', '').strip()
refresh_token = os.getenv('ZOHO_REFRESH_TOKEN', '').strip()
client_id = os.getenv('ZOHO_CLIENT_ID', '').split('#')[0].strip()
client_secret = os.getenv('ZOHO_CLIENT_SECRET', '').split('#')[0].strip()
data_center = os.getenv('ZOHO_DATA_CENTER', 'com').strip()

# Data center URLs
dc_urls = {
    'com': {
        'accounts': 'https://accounts.zoho.com',
        'api': 'https://invoice.zoho.com/api/v3'
    },
    'eu': {
        'accounts': 'https://accounts.zoho.eu',
        'api': 'https://invoice.zoho.eu/api/v3'
    },
    'in': {
        'accounts': 'https://accounts.zoho.in',
        'api': 'https://invoice.zoho.in/api/v3'
    }
}

urls = dc_urls.get(data_center, dc_urls['com'])

# If no access token, try to get one from refresh token
if not access_token and refresh_token:
    print_info("No access token found, refreshing from refresh token...")
    
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
        print_info("Please run test_zoho_oauth.py first to get tokens")
        exit(1)

if not access_token:
    print_error("No access token available")
    print_info("Please run: python3 test_zoho_oauth.py")
    exit(1)

# Method 1: List all organizations
print_header("Method 1: Listing All Organizations")

api_url = f"{urls['api']}/organizations"
headers = {
    'Authorization': f'Zoho-oauthtoken {access_token}'
}

try:
    print_info(f"Fetching from: {api_url}")
    response = requests.get(api_url, headers=headers)
    
    print_info(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('code') == 0:
            orgs = data.get('organizations', [])
            print_success(f"Found {len(orgs)} organization(s)")
            
            if orgs:
                print(f"\n{BOLD}Your Organizations:{RESET}\n")
                for i, org in enumerate(orgs, 1):
                    print(f"{GREEN}{i}. {org.get('name', 'N/A')}{RESET}")
                    print(f"   Organization ID: {BOLD}{org.get('organization_id')}{RESET}")
                    print(f"   Email: {org.get('email', 'N/A')}")
                    print(f"   Currency: {org.get('currency_code', 'N/A')}")
                    print(f"   Status: {org.get('account_created_date', 'N/A')}")
                    print()
                
                # Show the correct .env configuration
                primary_org = orgs[0]
                print(f"\n{BOLD}{YELLOW}Update your .env file:{RESET}")
                print(f"ZOHO_ORGANIZATION_ID={primary_org.get('organization_id')}")
                
            else:
                print_error("No organizations found")
                print_info("You may need to create an organization in Zoho Invoice")
        else:
            print_error(f"API Error: {data.get('message', 'Unknown error')}")
    else:
        print_error(f"Request failed with status {response.status_code}")
        try:
            error_data = response.json()
            print_error(f"Error: {error_data}")
        except:
            print_error(f"Response: {response.text[:200]}")
            
except Exception as e:
    print_error(f"Request failed: {e}")

# Method 2: Try to get current user info
print_header("Method 2: Getting User Information")

user_url = f"{urls['api']}/users/me"

try:
    print_info(f"Fetching from: {user_url}")
    response = requests.get(user_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            user = data.get('user', {})
            print_success("User info retrieved")
            print_info(f"Name: {user.get('name', 'N/A')}")
            print_info(f"Email: {user.get('email', 'N/A')}")
            print_info(f"User ID: {user.get('user_id', 'N/A')}")
    else:
        print_info(f"User endpoint returned: {response.status_code}")
        
except Exception as e:
    print_info(f"User endpoint not available: {e}")

# Instructions
print_header("📋 Next Steps")

print(f"""
{BOLD}1. Copy the Organization ID from above{RESET}
   The Organization ID is the number shown for your organization

{BOLD}2. Update your .env file:{RESET}
   ZOHO_ORGANIZATION_ID=<the_correct_id>

{BOLD}3. Run the OAuth test again:{RESET}
   python3 test_zoho_oauth.py

{YELLOW}Note:{RESET} If you see multiple organizations, use the one you want to work with.
Most users only have one organization.
""")

print("=" * 60)
