"""Debug Zoho OAuth issues with detailed logging."""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_section(title):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"   {msg}")

print_section("Zoho OAuth Debug Tool")

# Load and validate configuration
client_id = os.getenv('ZOHO_CLIENT_ID', '').strip()
client_secret = os.getenv('ZOHO_CLIENT_SECRET', '').strip()
redirect_uri = os.getenv('ZOHO_REDIRECT_URI', '').strip()
data_center = os.getenv('ZOHO_DATA_CENTER', 'com').strip()
organization_id = os.getenv('ZOHO_ORGANIZATION_ID', '').strip()
grant_token = os.getenv('ZOHO_GRANT_TOKEN', '').strip()

print_section("Configuration Check")

# Check Client ID
print("\n1. Client ID:")
if not client_id:
    print_error("ZOHO_CLIENT_ID is empty")
elif '#' in client_id:
    print_error(f"Client ID contains '#' character - this is wrong!")
    print_info(f"Current value: {client_id}")
    print_warning("Client ID should look like: 1000.XXXXXXXXXXXXX")
    print_warning("It should NOT contain '#' symbols")
    
    # Try to extract the correct part
    parts = client_id.split('#')
    if len(parts) > 0:
        suggested_id = parts[0]
        print_info(f"Suggested Client ID: {suggested_id}")
else:
    print_success(f"Client ID format looks correct")
    print_info(f"Value: {client_id[:20]}...{client_id[-10:]}")

# Check Client Secret
print("\n2. Client Secret:")
if not client_secret:
    print_error("ZOHO_CLIENT_SECRET is empty")
elif '#' in client_secret:
    print_error(f"Client Secret contains '#' character - this is wrong!")
    print_info(f"Current value: {client_secret}")
    print_warning("Client Secret should be a single continuous string")
    print_warning("It should NOT contain '#' symbols")
    
    # Try to extract the correct part
    parts = client_secret.split('#')
    if len(parts) > 0:
        suggested_secret = parts[0]
        print_info(f"Suggested Client Secret: {suggested_secret}")
else:
    print_success(f"Client Secret format looks correct")
    print_info(f"Value: {client_secret[:10]}...{client_secret[-10:]}")

# Check Redirect URI
print("\n3. Redirect URI:")
if not redirect_uri:
    print_error("ZOHO_REDIRECT_URI is empty")
else:
    print_success(f"Redirect URI: {redirect_uri}")

# Check Data Center
print("\n4. Data Center:")
valid_dcs = ['com', 'eu', 'in', 'com.au', 'com.cn']
if data_center in valid_dcs:
    print_success(f"Data Center: {data_center}")
else:
    print_warning(f"Unusual data center: {data_center}")
    print_info(f"Valid options: {', '.join(valid_dcs)}")

# Check Organization ID
print("\n5. Organization ID:")
if not organization_id:
    print_error("ZOHO_ORGANIZATION_ID is empty")
else:
    print_success(f"Organization ID: {organization_id}")

# Check Grant Token
print("\n6. Grant Token:")
if not grant_token:
    print_error("ZOHO_GRANT_TOKEN is empty")
    print_info("You need to generate a grant token from Zoho API Console")
elif len(grant_token) < 50:
    print_warning(f"Grant token seems too short: {len(grant_token)} characters")
    print_info(f"Value: {grant_token}")
else:
    print_success(f"Grant token present ({len(grant_token)} characters)")
    print_info(f"Value: {grant_token[:30]}...{grant_token[-20:]}")

# Attempt to fix common issues
print_section("Suggested Fixes")

fixes_needed = False

if '#' in client_id:
    fixes_needed = True
    correct_id = client_id.split('#')[0]
    print(f"\n{YELLOW}Fix Client ID:{RESET}")
    print(f"  Current: {client_id}")
    print(f"  Correct: {correct_id}")
    print(f"\n  Update your .env file:")
    print(f"  ZOHO_CLIENT_ID={correct_id}")

if '#' in client_secret:
    fixes_needed = True
    correct_secret = client_secret.split('#')[0]
    print(f"\n{YELLOW}Fix Client Secret:{RESET}")
    print(f"  Current: {client_secret}")
    print(f"  Correct: {correct_secret}")
    print(f"\n  Update your .env file:")
    print(f"  ZOHO_CLIENT_SECRET={correct_secret}")

if not fixes_needed:
    print_success("No obvious configuration issues found")
    print_info("The problem might be:")
    print_info("  1. Grant token expired (they expire in 3 minutes)")
    print_info("  2. Wrong data center")
    print_info("  3. Incorrect redirect URI in API Console")
    print_info("  4. Scopes not properly set")

# Test API endpoint
print_section("Testing API Endpoint")

dc_urls = {
    'com': 'https://accounts.zoho.com',
    'eu': 'https://accounts.zoho.eu',
    'in': 'https://accounts.zoho.in',
    'com.au': 'https://accounts.zoho.com.au',
    'com.cn': 'https://accounts.zoho.com.cn'
}

accounts_url = dc_urls.get(data_center, dc_urls['com'])
token_url = f"{accounts_url}/oauth/v2/token"

print_info(f"Token URL: {token_url}")

try:
    response = requests.get(accounts_url, timeout=5)
    print_success(f"Can reach {accounts_url} (Status: {response.status_code})")
except Exception as e:
    print_error(f"Cannot reach {accounts_url}: {e}")

# Attempt token exchange with detailed error
if client_id and client_secret and grant_token and not fixes_needed:
    print_section("Attempting Token Exchange")
    
    payload = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'code': grant_token
    }
    
    print_info("Request payload:")
    for key, value in payload.items():
        if key in ['client_secret', 'code']:
            print_info(f"  {key}: {value[:20]}...{value[-10:]}")
        else:
            print_info(f"  {key}: {value}")
    
    try:
        print_info(f"\nSending POST request to: {token_url}")
        response = requests.post(token_url, data=payload, timeout=10)
        
        print_info(f"Response Status: {response.status_code}")
        print_info(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Token exchange successful!")
            print_info(f"Response: {data}")
        else:
            print_error(f"Token exchange failed: {response.status_code}")
            print_info(f"Response content type: {response.headers.get('content-type')}")
            
            # Try to parse as JSON
            try:
                error_data = response.json()
                print_error(f"Error: {error_data}")
            except:
                # It's HTML
                print_error("Response is HTML (not JSON) - this means Zoho rejected the request")
                print_info("First 500 characters of response:")
                print_info(response.text[:500])
                
                # Common causes
                print(f"\n{YELLOW}Common causes:{RESET}")
                print_info("1. Grant token expired (generate a new one)")
                print_info("2. Client ID or Secret is incorrect")
                print_info("3. Redirect URI doesn't match API Console")
                print_info("4. Wrong data center")
                
    except Exception as e:
        print_error(f"Request failed: {e}")

print_section("Next Steps")

if fixes_needed:
    print_warning("Fix the configuration issues above first")
    print_info("1. Update your .env file with the correct values")
    print_info("2. Generate a new grant token")
    print_info("3. Run this debug script again")
else:
    print_info("1. Generate a NEW grant token from Zoho API Console")
    print_info("2. Update ZOHO_GRANT_TOKEN in .env immediately")
    print_info("3. Run: python3 test_zoho_oauth.py within 3 minutes")

print(f"\n{BLUE}{'='*60}{RESET}\n")
