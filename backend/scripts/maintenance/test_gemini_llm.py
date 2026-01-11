#!/usr/bin/env python3
"""
Test script to verify Gemini LLM configuration.
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.llm_service import LLMService

async def test_gemini_configuration():
    """Test that LLM service is configured to use Gemini."""
    
    print("🧪 Testing Gemini LLM Configuration")
    print("=" * 50)
    
    # Check environment variables
    print("\n1. Environment Variables:")
    llm_provider = os.getenv("LLM_PROVIDER", "not_set")
    google_api_key = os.getenv("GOOGLE_API_KEY", "not_set")
    gemini_model = os.getenv("GEMINI_MODEL", "not_set")
    
    print(f"   LLM_PROVIDER: {llm_provider}")
    print(f"   GOOGLE_API_KEY: {'✅ Set' if google_api_key != 'not_set' else '❌ Not set'}")
    print(f"   GEMINI_MODEL: {gemini_model}")
    
    if llm_provider != "gemini":
        print(f"   ❌ LLM_PROVIDER should be 'gemini', but is '{llm_provider}'")
        return False
    
    if google_api_key == "not_set":
        print("   ❌ GOOGLE_API_KEY is not set")
        return False
    
    print("   ✅ Environment variables are configured correctly")
    
    # Test LLM service initialization
    print("\n2. LLM Service Initialization:")
    try:
        # Reset any cached instance
        LLMService.reset()
        
        # Get LLM instance
        llm = LLMService.get_llm_instance()
        
        print(f"   LLM Instance Type: {type(llm).__name__}")
        print(f"   LLM Module: {type(llm).__module__}")
        
        # Check if it's a Gemini instance
        if "google" in type(llm).__module__.lower():
            print("   ✅ Successfully initialized Gemini LLM")
            
            # Test a simple call
            print("\n3. Testing Gemini API Call:")
            from langchain_core.messages import HumanMessage
            
            try:
                response = await llm.ainvoke([HumanMessage(content="Say 'Hello from Gemini!' and nothing else.")])
                print(f"   Response: {response.content}")
                print("   ✅ Gemini API call successful")
                return True
                
            except Exception as e:
                print(f"   ❌ Gemini API call failed: {str(e)}")
                return False
        else:
            print(f"   ❌ Expected Gemini LLM, but got: {type(llm).__name__}")
            return False
            
    except Exception as e:
        print(f"   ❌ LLM service initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gemini_configuration())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Gemini LLM is configured and working correctly!")
    else:
        print("❌ Gemini LLM configuration has issues.")
        print("\nTroubleshooting steps:")
        print("1. Verify GOOGLE_API_KEY is set correctly")
        print("2. Ensure LLM_PROVIDER=gemini in .env file")
        print("3. Check that langchain-google-genai package is installed")
        print("4. Verify API key has proper permissions")