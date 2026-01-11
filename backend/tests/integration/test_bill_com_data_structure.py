#!/usr/bin/env python3
"""
Quick test to see the actual data structure returned by Bill.com API
"""

import asyncio
import sys
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "mcp_server"))

from services.bill_com_service import BillComAPIService
import json

async def test_data_structure():
    """Test to see actual data structure."""
    print("🔍 Testing Bill.com API data structure...")
    
    async with BillComAPIService() as service:
        # Authenticate
        if not await service.authenticate():
            print("❌ Authentication failed")
            return
        
        print("✅ Authentication successful")
        
        # Get bills
        print("\n📋 Getting bills...")
        bills = await service.get_bills(limit=5)
        
        print(f"Bills type: {type(bills)}")
        print(f"Bills content: {json.dumps(bills, indent=2)}")
        
        # Get vendors
        print("\n👥 Getting vendors...")
        vendors = await service.get_vendors(limit=5)
        
        print(f"Vendors type: {type(vendors)}")
        print(f"Vendors content: {json.dumps(vendors, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_data_structure())