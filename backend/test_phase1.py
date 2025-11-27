"""
Phase 1 Validation Tests
Tests database connectivity and basic CRUD operations.
"""
import asyncio
import sys
from datetime import datetime

from app.db.mongodb import MongoDB


async def test_mongodb_connection():
    """Test MongoDB connection."""
    print("Testing MongoDB connection...")
    try:
        MongoDB.connect()
        is_connected = await MongoDB.test_connection()
        if is_connected:
            print("✅ MongoDB connection successful")
            return True
        else:
            print("❌ MongoDB connection failed")
            return False
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return False


async def test_crud_operations():
    """Test basic CRUD operations."""
    print("\nTesting CRUD operations...")
    try:
        db = MongoDB.get_database()
        test_collection = db["test_phase1"]
        
        # Create
        test_doc = {
            "test_id": "phase1_test",
            "message": "Hello from Phase 1",
            "timestamp": datetime.utcnow()
        }
        result = await test_collection.insert_one(test_doc)
        print(f"✅ Created document with ID: {result.inserted_id}")
        
        # Read
        retrieved = await test_collection.find_one({"test_id": "phase1_test"})
        if retrieved:
            print(f"✅ Retrieved document: {retrieved['message']}")
        else:
            print("❌ Failed to retrieve document")
            return False
        
        # Update
        await test_collection.update_one(
            {"test_id": "phase1_test"},
            {"$set": {"message": "Updated message"}}
        )
        updated = await test_collection.find_one({"test_id": "phase1_test"})
        if updated and updated["message"] == "Updated message":
            print("✅ Updated document successfully")
        else:
            print("❌ Failed to update document")
            return False
        
        # Delete
        delete_result = await test_collection.delete_one({"test_id": "phase1_test"})
        if delete_result.deleted_count == 1:
            print("✅ Deleted document successfully")
        else:
            print("❌ Failed to delete document")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations error: {e}")
        return False


async def run_all_tests():
    """Run all Phase 1 validation tests."""
    print("=" * 60)
    print("PHASE 1 VALIDATION TESTS")
    print("=" * 60)
    
    results = []
    
    # Test 1: MongoDB Connection
    results.append(await test_mongodb_connection())
    
    # Test 2: CRUD Operations
    if results[0]:  # Only run if connection successful
        results.append(await test_crud_operations())
    else:
        print("\n⚠️  Skipping CRUD tests due to connection failure")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"MongoDB Connection: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"CRUD Operations: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print("=" * 60)
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 All Phase 1 tests PASSED!")
        print("✅ Ready to proceed to Phase 2")
    else:
        print("\n❌ Some tests FAILED. Please fix issues before proceeding.")
    
    # Cleanup
    MongoDB.close()
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
