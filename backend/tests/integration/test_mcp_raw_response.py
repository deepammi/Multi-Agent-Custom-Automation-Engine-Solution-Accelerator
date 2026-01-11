#!/usr/bin/env python3
"""
Test to examine the raw MCP response before processing
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

async def test_raw_mcp_response():
    from app.services.mcp_http_client import get_mcp_http_manager
    
    print('🔍 Testing Raw MCP Response from Bill.com')
    print('=' * 50)
    
    manager = get_mcp_http_manager()
    
    try:
        # Call the MCP tool directly through the manager
        print('\n📋 Calling get_bill_com_bills directly...')
        raw_result = await manager.call_tool('bill_com', 'get_bill_com_bills', {})
        
        print(f'🔍 Raw result type: {type(raw_result)}')
        print(f'🔍 Raw result: {raw_result}')
        
        if isinstance(raw_result, dict):
            print(f'📊 Dictionary keys: {list(raw_result.keys())}')
            for key, value in raw_result.items():
                print(f'  {key}: {type(value)} - {str(value)[:100]}...')
        
        # Check if it's a CallToolResult object
        if hasattr(raw_result, 'structured_content'):
            print(f'✅ Has structured_content: {raw_result.structured_content}')
        if hasattr(raw_result, 'data'):
            print(f'✅ Has data: {raw_result.data}')
        if hasattr(raw_result, 'content'):
            print(f'✅ Has content: {raw_result.content}')
        
        print('\n🎯 Analysis:')
        if isinstance(raw_result, dict) and 'result' in raw_result:
            result_content = raw_result['result']
            if 'Bill.com' in str(result_content) and 'Retrieved' in str(result_content):
                print('✅ This is a real Bill.com API response!')
                print('✅ MCP server is successfully calling Bill.com API')
                print('✅ HTTP transport is working correctly')
                if 'Count: 0' in str(result_content):
                    print('📊 API returned 0 results (expected in sandbox)')
                else:
                    print('📊 API returned actual data!')
            else:
                print('⚠️  Unexpected response format')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_raw_mcp_response())