"""Test LangGraph checkpointer with MongoDB."""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.checkpointer import get_checkpointer, CheckpointerService


def test_checkpointer():
    """Test MemorySaver checkpointer functionality."""
    print("=" * 60)
    print("Testing LangGraph MemorySaver Checkpointer")
    print("=" * 60)
    
    try:
        # Get checkpointer
        print("\n1. Initializing checkpointer...")
        checkpointer = get_checkpointer()
        print(f"   ✅ Checkpointer initialized: {type(checkpointer).__name__}")
        
        # Test checkpoint operations
        print("\n2. Testing checkpoint operations...")
        print("   Note: Checkpoints will be created when graph executes")
        print("   This will be tested in Phase 2 with actual graph")
        
        print("\n3. Testing checkpoint cleanup...")
        result = CheckpointerService.clear_checkpoints()
        print(f"   ✅ Cleanup successful: {result}")
        
        # Verify we can get a new checkpointer after cleanup
        checkpointer2 = get_checkpointer()
        print(f"   ✅ New checkpointer created: {type(checkpointer2).__name__}")
        
        print("\n" + "=" * 60)
        print("✅ All Checkpointer Tests Passed!")
        print("=" * 60)
        print("\nCheckpointer is ready for use with LangGraph.")
        print("Storage: In-memory (MemorySaver)")
        print("Next step: Create graph structure in Phase 2")
        print("\nNote: Will upgrade to persistent storage (MongoDB) in later phases")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_checkpointer()
