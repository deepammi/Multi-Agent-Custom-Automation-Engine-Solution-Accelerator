#!/usr/bin/env python3
"""
Test LLM configuration to debug why it's in mock mode.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from the root directory (one level up from backend)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from: {env_path}")
except ImportError:
    print("⚠️ python-dotenv not available, environment variables may not be loaded")

def test_llm_config():
    """Test LLM configuration and environment variables."""
    print("🔍 Testing LLM Configuration")
    print("=" * 60)
    
    # Check environment variables
    print("Environment Variables:")
    print(f"  LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'NOT SET')}")
    print(f"  USE_MOCK_LLM: {os.getenv('USE_MOCK_LLM', 'NOT SET')}")
    print(f"  GOOGLE_API_KEY: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
    print(f"  GEMINI_MODEL: {os.getenv('GEMINI_MODEL', 'NOT SET')}")
    print()
    
    # Test environment config
    try:
        from app.config.environment import get_environment_config
        env_config = get_environment_config()
        
        print("Environment Config:")
        print(f"  is_mock_llm_enabled(): {env_config.is_mock_llm_enabled()}")
        print(f"  is_mock_mode_enabled(): {env_config.is_mock_mode_enabled()}")
        print()
        
    except Exception as e:
        print(f"❌ Error loading environment config: {e}")
        return
    
    # Test LLM service
    try:
        from app.services.llm_service import LLMService
        
        print("LLM Service:")
        print(f"  is_mock_mode(): {LLMService.is_mock_mode()}")
        
        # Try to get LLM instance
        try:
            llm = LLMService.get_llm_instance()
            print(f"  LLM instance type: {type(llm).__name__}")
            print(f"  LLM model: {getattr(llm, 'model_name', 'Unknown')}")
            print("  ✅ LLM instance created successfully")
        except Exception as e:
            print(f"  ❌ Error creating LLM instance: {e}")
        
    except Exception as e:
        print(f"❌ Error loading LLM service: {e}")

if __name__ == "__main__":
    test_llm_config()