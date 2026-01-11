#!/usr/bin/env python3
"""
Test to find specific Bill.com test data: Acme Marketing vendor and invoices 1001, 1002
"""

import asyncio
import sys
import os
import re

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

async def search_bill_com_test_data():
    print('🔍 Searching for Bill.com Test Data')
    print('=' * 60)
    print('🎯 Looking for:')
    print('   - Vendor: Acme Marketing')
    print('   - Invoices: 1001, 1002')
    print('=' * 60)
    
    try:
        from app.services.mcp_http_client import get_mcp_http_manager
        from app.agents.accounts_payable_agent_http import get_accounts_payable_agent_http
        
        manager = get_mcp_http_manager()
        ap_agent = get_accounts_payable_agent_http()
        
        # Test 1: Get all bills with different parameters
        print('\n📋 Test 1: Get All Bills (various parameters)')
        
        test_params = [
            {},  # No parameters
            {'limit': 50},  # Higher limit
            {'limit': 100},  # Even higher limit
            {'vendor_name': 'Acme Marketing'},  # Specific vendor
            {'status': 'all'},  # All statuses
        ]
        
        for i, params in enumerate(test_params, 1):
            print(f'\n   Test 1.{i}: Parameters: {params}')
            try:
                result = await manager.call_tool('bill_com', 'get_bill_com_bills', params)
                
                if isinstance(result, dict) and 'result' in result:
                    result_str = result['result']
                    
                    # Extract count
                    count_match = re.search(r'Count:\*\* (\d+)', result_str)
                    if count_match:
                        count = int(count_match.group(1))
                        print(f'      📊 Bills found: {count}')
                        
                        if count > 0:
                            print('      🎉 Found bills! Extracting details...')
                            # Try to extract bill details from the response
                            if 'Bills:**' in result_str:
                                bills_section = result_str.split('Bills:**')[1].split('**Timestamp:**')[0]
                                print(f'      📄 Bills data: {bills_section[:300]}...')
                        else:
                            print('      📝 No bills found with these parameters')
                    else:
                        print('      ⚠️  Could not parse count from response')
                        print(f'      Raw response: {result_str[:200]}...')
                        
            except Exception as e:
                print(f'      ❌ Error: {e}')
        
        # Test 2: Search for specific invoices
        print('\n🔍 Test 2: Search for Specific Invoices')
        
        search_terms = ['1001', '1002', 'Acme Marketing', 'Acme']
        
        for term in search_terms:
            print(f'\n   Searching for: "{term}"')
            try:
                result = await manager.call_tool('bill_com', 'search_bill_com_bills', {'query': term})
                
                if isinstance(result, dict) and 'result' in result:
                    result_str = result['result']
                    
                    if 'Error' in result_str:
                        print(f'      ❌ Search error: {result_str}')
                    else:
                        # Look for results
                        count_match = re.search(r'Count:\*\* (\d+)', result_str)
                        if count_match:
                            count = int(count_match.group(1))
                            print(f'      📊 Results found: {count}')
                            if count > 0:
                                print('      🎉 Found matching records!')
                        else:
                            print(f'      📄 Response: {result_str[:200]}...')
                            
            except Exception as e:
                print(f'      ❌ Error: {e}')
        
        # Test 3: Get specific invoice by ID
        print('\n🎯 Test 3: Get Specific Invoices by ID')
        
        invoice_ids = ['1001', '1002']
        
        for invoice_id in invoice_ids:
            print(f'\n   Getting invoice: {invoice_id}')
            try:
                result = await manager.call_tool('bill_com', 'get_bill_com_invoice_details', {'invoice_id': invoice_id})
                
                if isinstance(result, dict) and 'result' in result:
                    result_str = result['result']
                    
                    if 'Error' in result_str:
                        print(f'      ❌ Error: {result_str}')
                    else:
                        print(f'      ✅ Response received: {result_str[:200]}...')
                        
            except Exception as e:
                print(f'      ❌ Error: {e}')
        
        # Test 4: Get all vendors
        print('\n👥 Test 4: Get All Vendors')
        try:
            result = await manager.call_tool('bill_com', 'get_bill_com_vendors', {})
            
            if isinstance(result, dict) and 'result' in result:
                result_str = result['result']
                
                # Extract count
                count_match = re.search(r'Count:\*\* (\d+)', result_str)
                if count_match:
                    count = int(count_match.group(1))
                    print(f'   📊 Vendors found: {count}')
                    
                    if count > 0:
                        print('   🎉 Found vendors! Looking for Acme Marketing...')
                        if 'Acme' in result_str or 'Marketing' in result_str:
                            print('   ✅ Found Acme Marketing in vendors!')
                        else:
                            print('   ⚠️  Acme Marketing not found in vendor list')
                            # Show vendor data
                            if 'Vendors:**' in result_str:
                                vendors_section = result_str.split('Vendors:**')[1].split('**Timestamp:**')[0]
                                print(f'   📄 Vendors data: {vendors_section[:300]}...')
                    else:
                        print('   📝 No vendors found')
                else:
                    print('   ⚠️  Could not parse vendor count')
                    print(f'   Raw response: {result_str[:300]}...')
                    
        except Exception as e:
            print(f'   ❌ Error: {e}')
        
        # Test 5: Check available Bill.com tools
        print('\n🔧 Test 5: Available Bill.com Tools')
        try:
            # Try to list available tools (if supported)
            client = await manager.get_client('bill_com')
            print(f'   📊 MCP client created for bill_com')
            print(f'   🔗 Server URL: {client.server_url}')
            
        except Exception as e:
            print(f'   ❌ Error getting client info: {e}')
        
        print('\n' + '=' * 60)
        print('🎯 ANALYSIS & RECOMMENDATIONS')
        print('=' * 60)
        print('If test data exists but we\'re not finding it, possible issues:')
        print('1. 🔍 API parameters might need adjustment')
        print('2. 🔐 Authentication scope might be limited')
        print('3. 📊 Data might be in different format than expected')
        print('4. 🏢 Sandbox environment might need data setup')
        print('5. 🔧 Tool implementations might need parameter fixes')
        
    except Exception as e:
        print(f'❌ CRITICAL ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(search_bill_com_test_data())