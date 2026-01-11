#!/usr/bin/env python3
"""
Test Bill.com API service with real credentials.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add paths
project_root = Path('.')
sys.path.insert(0, str(project_root / 'src' / 'mcp_server'))

async def test_bill_com_service():
    try:
        from services.bill_com_service import BillComAPIService
        
        print('🔧 Testing Bill.com API Service...')
        
        async with BillComAPIService(plan_id='test', agent='validation') as service:
            print(f'✅ Service created successfully')
            print(f'   Environment: {service.config.environment}')
            print(f'   Base URL: {service.config.base_url}')
            print(f'   Username: {service.config.username}')
            print(f'   Org ID: {service.config.organization_id}')
            
            # Test authentication
            print('🔐 Testing authentication...')
            auth_result = await service.authenticate()
            
            if auth_result:
                print('✅ Authentication successful!')
                print(f'   Session ID: {service.session.session_id[:8]}...')
                print(f'   User ID: {service.session.user_id}')
                print(f'   Expires: {service.session.expires_at}')
                
                # Test a simple API call
                print('📋 Testing invoice retrieval...')
                invoices = await service.get_invoices(limit=5)
                print(f'✅ Retrieved {len(invoices)} invoices')
                
                if invoices:
                    print('   Sample invoice:')
                    invoice = invoices[0]
                    print(f'     ID: {invoice.get("id", "N/A")}')
                    print(f'     Number: {invoice.get("invoiceNumber", "N/A")}')
                    print(f'     Vendor: {invoice.get("vendorName", "N/A")}')
                    print(f'     Amount: ${invoice.get("amount", 0)}')
                    print(f'     Status: {invoice.get("status", "N/A")}')
                
                # Test vendor retrieval
                print('🏢 Testing vendor retrieval...')
                vendors = await service.get_vendors(limit=3)
                print(f'✅ Retrieved {len(vendors)} vendors')
                
                if vendors:
                    print('   Sample vendor:')
                    vendor = vendors[0]
                    print(f'     ID: {vendor.get("id", "N/A")}')
                    print(f'     Name: {vendor.get("name", "N/A")}')
                    print(f'     Email: {vendor.get("email", "N/A")}')
                
            else:
                print('❌ Authentication failed')
                
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bill_com_service())