"""Test Zoho Invoice OAuth authentication."""
import os
import sys
import requests
from dotenv import load_dotenv, set_key
from pathlib import Path

# Load environment variables
load_dotenv()

# ANSI color codes for pretty output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{text}{RESET}")
    print("=" * len(text))


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def get_data_center_urls(data_center):
    """Get URLs for the specified data center."""
    dc_map = {
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
        },
        'com.au': {
            'accounts': 'https://accounts.zoho.com.au',
            'api': 'https://invoice.zoho.com.au/api/v3'
        },
        'com.cn': {
            'accounts': 'https://accounts.zoho.com.cn',
            'api': 'https://invoice.zoho.com.cn/api/v3'
        }
    }
    return dc_map.get(data_center, dc_map['com'])


def exchange_grant_token(client_id, client_secret, grant_token, redirect_uri, data_center):
    """Exchange grant token for access and refresh tokens."""
    print_header("Step 1: Exchanging Grant Token")
    
    urls = get_data_center_urls(data_center)
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
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if 'access_token' in data and 'refresh_token' in data:
            print_success("Access token obtained")
            print_success("Refresh token obtained")
            print_info(f"Access token expires in: {data.get('expires_in', 3600)} seconds")
            return data['access_token'], data['refresh_token']
        else:
            print_error(f"Unexpected response: {data}")
            return None, None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to exchange grant token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return None, None


def refresh_access_token(client_id, client_secret, refresh_token, data_center):
    """Refresh the access token using refresh token."""
    print_header("Refreshing Access Token")
    
    urls = get_data_center_urls(data_center)
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
        
        if 'access_token' in data:
            print_success("New access token obtained")
            return data['access_token']
        else:
            print_error(f"Unexpected response: {data}")
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to refresh token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        return None


def test_api_connection(access_token, organization_id, data_center):
    """Test API connection by fetching settings (works with free tier)."""
    print_header("Step 2: Testing API Connection")
    
    urls = get_data_center_urls(data_center)
    api_url = f"{urls['api']}/settings/preferences"
    
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'X-com-zoho-invoice-organizationid': organization_id
    }
    
    try:
        print_info(f"Fetching settings from: {api_url}")
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == 0:
                prefs = data.get('preferences', {})
                print_success("Successfully connected to Zoho Invoice API")
                print_info(f"Organization: {prefs.get('organization_name', 'N/A')}")
                print_info(f"Currency: {prefs.get('currency_code', 'N/A')}")
                print_info(f"Date Format: {prefs.get('date_format', 'N/A')}")
                return True
            else:
                print_error(f"API returned error: {data.get('message', 'Unknown error')}")
                return False
        else:
            print_error(f"Failed with status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error: {error_data.get('message', 'Unknown error')}")
            except:
                print_error(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to connect to API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print_error(f"Error: {error_data}")
            except:
                print_error(f"Response: {e.response.text[:200]}")
        return False


def fetch_invoices(access_token, organization_id, data_center):
    """Fetch sample invoices to verify read access."""
    print_header("Step 3: Fetching Invoices")
    
    urls = get_data_center_urls(data_center)
    api_url = f"{urls['api']}/invoices"
    
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'X-com-zoho-invoice-organizationid': organization_id
    }
    
    params = {
        'per_page': 5
    }
    
    try:
        print_info(f"Fetching invoices from: {api_url}")
        response = requests.get(api_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == 0:
                invoices = data.get('invoices', [])
                page_context = data.get('page_context', {})
                total = page_context.get('total', 0)
                
                print_success(f"Found {total} total invoice(s), showing {len(invoices)}")
                
                if len(invoices) == 0:
                    print_info("No invoices in your account yet")
                    print_info("You can create test invoices in Zoho Invoice web interface")
                else:
                    for i, invoice in enumerate(invoices[:3], 1):
                        print(f"\n  {i}. Invoice #{invoice.get('invoice_number', 'N/A')}")
                        print(f"     Customer: {invoice.get('customer_name', 'N/A')}")
                        print(f"     Amount: {invoice.get('currency_symbol', '$')}{invoice.get('total', 0)}")
                        print(f"     Status: {invoice.get('status', 'N/A')}")
                        print(f"     Date: {invoice.get('date', 'N/A')}")
                
                return True
            else:
                print_warning(f"API returned: {data.get('message', 'Unknown error')}")
                return False
        elif response.status_code == 401:
            try:
                error_data = response.json()
                print_error(f"Unauthorized: {error_data.get('message')}")
                print_warning("Missing scope: ZohoInvoice.invoices.READ")
                print_info("You need to regenerate your grant token with the correct scopes")
            except:
                print_error(f"Unauthorized: {response.text[:200]}")
            return False
        else:
            print_error(f"Failed with status {response.status_code}")
            try:
                error_data = response.json()
                print_error(f"Error: {error_data}")
            except:
                print_error(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to fetch invoices: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print_error(f"Error: {error_data}")
            except:
                print_error(f"Response: {e.response.text[:200]}")
        return False


def save_refresh_token(refresh_token):
    """Save refresh token to .env file."""
    print_header("Step 4: Saving Refresh Token")
    
    env_path = Path(__file__).parent / '.env'
    
    try:
        set_key(env_path, 'ZOHO_REFRESH_TOKEN', refresh_token)
        print_success("Refresh token saved to .env")
        print_info("You can now use this refresh token for future API calls")
        return True
    except Exception as e:
        print_error(f"Failed to save refresh token: {e}")
        print_warning("Please manually add this to your .env file:")
        print(f"ZOHO_REFRESH_TOKEN={refresh_token}")
        return False


def main():
    """Main test function."""
    print(f"\n{BOLD}🔐 Zoho Invoice OAuth Test{RESET}")
    print("=" * 40)
    
    # Load configuration
    client_id = os.getenv('ZOHO_CLIENT_ID')
    client_secret = os.getenv('ZOHO_CLIENT_SECRET')
    redirect_uri = os.getenv('ZOHO_REDIRECT_URI', 'http://localhost:8000/oauth/callback')
    data_center = os.getenv('ZOHO_DATA_CENTER', 'com')
    organization_id = os.getenv('ZOHO_ORGANIZATION_ID')
    grant_token = os.getenv('ZOHO_GRANT_TOKEN')
    refresh_token = os.getenv('ZOHO_REFRESH_TOKEN')
    
    # Validate configuration
    if not client_id or not client_secret:
        print_error("Missing ZOHO_CLIENT_ID or ZOHO_CLIENT_SECRET in .env")
        print_info("Please follow the setup guide in docs/ZOHO_OAUTH_SETUP.md")
        sys.exit(1)
    
    if not organization_id:
        print_error("Missing ZOHO_ORGANIZATION_ID in .env")
        print_info("Find your Organization ID in Zoho Invoice Settings")
        sys.exit(1)
    
    print_info(f"Data Center: {data_center}")
    print_info(f"Organization ID: {organization_id}")
    
    access_token = None
    
    # Check if we have a refresh token
    if refresh_token:
        print_info("Found existing refresh token, attempting to refresh access token...")
        access_token = refresh_access_token(client_id, client_secret, refresh_token, data_center)
    
    # If no refresh token or refresh failed, use grant token
    if not access_token:
        if not grant_token:
            print_error("No ZOHO_GRANT_TOKEN or ZOHO_REFRESH_TOKEN found in .env")
            print_info("\nTo get a grant token:")
            print_info("1. Go to https://api-console.zoho.com/")
            print_info("2. Select your Self-Client")
            print_info("3. Click 'Generate Code'")
            print_info("4. Select scopes and generate")
            print_info("5. Copy the grant token and add to .env as ZOHO_GRANT_TOKEN")
            print_info("6. Run this script within 3 minutes")
            sys.exit(1)
        
        access_token, new_refresh_token = exchange_grant_token(
            client_id, client_secret, grant_token, redirect_uri, data_center
        )
        
        if not access_token:
            print_error("Failed to obtain access token")
            sys.exit(1)
        
        # Save the new refresh token
        if new_refresh_token:
            save_refresh_token(new_refresh_token)
            refresh_token = new_refresh_token
    
    # Test API connection
    if not test_api_connection(access_token, organization_id, data_center):
        print_error("API connection test failed")
        sys.exit(1)
    
    # Fetch sample invoices
    fetch_invoices(access_token, organization_id, data_center)
    
    # Final summary
    print(f"\n{BOLD}{GREEN}🎉 OAuth Setup Complete!{RESET}")
    print("\nYour Zoho Invoice API is now configured and working.")
    print("\nNext steps:")
    print("1. ✅ OAuth authentication verified")
    print("2. 🔄 Create Zoho Invoice MCP Server")
    print("3. 🔄 Integrate with backend agents")
    print("4. 🔄 Test end-to-end workflow")
    
    print(f"\n{BOLD}Configuration Summary:{RESET}")
    print(f"  Client ID: {client_id[:20]}...")
    print(f"  Data Center: {data_center}")
    print(f"  Organization ID: {organization_id}")
    print(f"  Refresh Token: {'✅ Saved' if refresh_token else '❌ Not saved'}")
    
    print(f"\n{BOLD}💡 Troubleshooting:{RESET}")
    print("If you get 401 errors, regenerate grant token with these scopes:")
    print(f"{YELLOW}ZohoInvoice.invoices.READ,ZohoInvoice.invoices.CREATE,ZohoInvoice.contacts.READ,ZohoInvoice.items.READ,ZohoInvoice.settings.READ{RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⚠️  Test interrupted by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
