"""
Phase 2 Validation Tests
Tests data models and basic API endpoints.
"""
import asyncio
import sys
import httpx

BASE_URL = "http://localhost:8000"


async def test_health_check():
    """Test health check endpoint."""
    print("Testing health check endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Health check endpoint working")
                return True
            else:
                print(f"❌ Health check failed with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


async def test_process_request():
    """Test POST /api/v3/process_request endpoint."""
    print("\nTesting POST /api/v3/process_request...")
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "description": "Test task for Phase 2 validation"
            }
            response = await client.post(f"{BASE_URL}/api/v3/process_request", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "plan_id" in data and "session_id" in data and "status" in data:
                    print(f"✅ Process request successful")
                    print(f"   Plan ID: {data['plan_id']}")
                    print(f"   Session ID: {data['session_id']}")
                    return True, data
                else:
                    print(f"❌ Response missing required fields: {data}")
                    return False, None
            else:
                print(f"❌ Process request failed with status: {response.status_code}")
                return False, None
    except Exception as e:
        print(f"❌ Process request error: {e}")
        return False, None


async def test_get_plans():
    """Test GET /api/v3/plans endpoint."""
    print("\nTesting GET /api/v3/plans...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/v3/plans")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ Get plans successful (returned {len(data)} plans)")
                    return True
                else:
                    print(f"❌ Response is not a list: {type(data)}")
                    return False
            else:
                print(f"❌ Get plans failed with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Get plans error: {e}")
        return False


async def test_get_plan_by_id(plan_id: str):
    """Test GET /api/v3/plan endpoint."""
    print("\nTesting GET /api/v3/plan...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["plan", "messages", "m_plan", "team", "streaming_message"]
                if all(field in data for field in required_fields):
                    print(f"✅ Get plan by ID successful")
                    print(f"   Plan status: {data['plan']['status']}")
                    print(f"   Steps: {len(data['plan']['steps'])}")
                    return True
                else:
                    print(f"❌ Response missing required fields")
                    return False
            else:
                print(f"❌ Get plan by ID failed with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Get plan by ID error: {e}")
        return False


async def test_data_models():
    """Test data model serialization."""
    print("\nTesting data models...")
    try:
        from app.models.plan import Plan, Step
        from app.models.message import AgentMessage
        from app.models.team import TeamConfiguration, Agent
        
        # Test Plan model
        plan = Plan(
            id="test-plan-123",
            session_id="test-session-123",
            description="Test plan",
            steps=[
                Step(id="step-1", description="Test step", agent="TestAgent")
            ]
        )
        plan_dict = plan.model_dump()
        
        # Test AgentMessage model
        message = AgentMessage(
            plan_id="test-plan-123",
            agent_name="TestAgent",
            agent_type="test",
            content="Test message"
        )
        message_dict = message.model_dump()
        
        # Test TeamConfiguration model
        team = TeamConfiguration(
            team_id="test-team-123",
            name="Test Team",
            description="Test team description",
            agents=[
                Agent(name="Agent1", role="test", instructions="Test instructions")
            ]
        )
        team_dict = team.model_dump()
        
        print("✅ All data models serialize correctly")
        return True
        
    except Exception as e:
        print(f"❌ Data model error: {e}")
        return False


async def run_all_tests():
    """Run all Phase 2 validation tests."""
    print("=" * 60)
    print("PHASE 2 VALIDATION TESTS")
    print("=" * 60)
    print("\n⚠️  Make sure the backend server is running:")
    print("   python -m app.main")
    print()
    
    results = []
    plan_id = None
    
    # Test 1: Health Check
    results.append(await test_health_check())
    
    # Test 2: Data Models
    results.append(await test_data_models())
    
    # Test 3: Process Request
    success, response_data = await test_process_request()
    results.append(success)
    if success and response_data:
        plan_id = response_data.get("plan_id")
    
    # Test 4: Get Plans
    results.append(await test_get_plans())
    
    # Test 5: Get Plan by ID
    if plan_id:
        results.append(await test_get_plan_by_id(plan_id))
    else:
        print("\n⚠️  Skipping get plan by ID test (no plan_id available)")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Health Check: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Data Models: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"POST /api/v3/process_request: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"GET /api/v3/plans: {'✅ PASS' if results[3] else '❌ FAIL'}")
    print(f"GET /api/v3/plan: {'✅ PASS' if results[4] else '❌ FAIL'}")
    print("=" * 60)
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 All Phase 2 tests PASSED!")
        print("✅ Ready to proceed to Phase 3")
    else:
        print("\n❌ Some tests FAILED. Please fix issues before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
