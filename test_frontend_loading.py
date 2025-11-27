"""
Quick test to verify frontend is loading properly.
"""
import asyncio
import httpx

async def test_frontend_loading():
    """Test that frontend can initialize properly."""
    print("Testing Frontend Loading...")
    print("=" * 60)
    
    try:
        # Test 1: Check if frontend is serving
        print("\n1. Checking if frontend is serving...")
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3001/")
            if response.status_code == 200:
                print("   ✅ Frontend is serving HTML")
            else:
                print(f"   ❌ Frontend returned {response.status_code}")
                return False
        
        # Test 2: Check if config.json is accessible
        print("\n2. Checking if config.json is accessible...")
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3001/config.json")
            if response.status_code == 200:
                config = response.json()
                print(f"   ✅ Config loaded: API_URL = {config.get('API_URL')}")
            else:
                print(f"   ❌ Config not accessible: {response.status_code}")
                return False
        
        # Test 3: Check if backend health endpoint works
        print("\n3. Checking backend health...")
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("   ✅ Backend is healthy")
            else:
                print(f"   ❌ Backend health check failed: {response.status_code}")
                return False
        
        # Test 4: Check if user_browser_language endpoint works
        print("\n4. Checking user_browser_language endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/user_browser_language",
                json={"language": "en-US"}
            )
            if response.status_code == 200:
                print("   ✅ user_browser_language endpoint working")
            else:
                print(f"   ❌ user_browser_language failed: {response.status_code}")
                return False
        
        # Test 5: Test creating a task (full flow)
        print("\n5. Testing task creation flow...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v3/process_request",
                json={"description": "Test frontend loading"}
            )
            if response.status_code == 200:
                data = response.json()
                plan_id = data.get("plan_id")
                print(f"   ✅ Task created: {plan_id}")
            else:
                print(f"   ❌ Task creation failed: {response.status_code}")
                return False
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("\n🌐 Frontend should now be loading properly at:")
        print("   http://localhost:3001")
        print("\n📝 Next steps:")
        print("   1. Open http://localhost:3001 in your browser")
        print("   2. Check browser console (F12) for any errors")
        print("   3. Try creating a task from the UI")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = asyncio.run(test_frontend_loading())
    sys.exit(0 if success else 1)
