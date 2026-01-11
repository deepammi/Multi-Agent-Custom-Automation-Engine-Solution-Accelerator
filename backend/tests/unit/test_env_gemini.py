#!/usr/bin/env python3
"""
Test if Gemini is configured correctly in .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_env_config():
    """Test environment configuration."""
    print("🧪 Testing Gemini Environment Configuration")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env file")
        print("   Please add: GOOGLE_API_KEY=your-api-key-here")
        return False
    
    if api_key == "your-gemini-api-key-here":
        print("❌ GOOGLE_API_KEY is still the placeholder value")
        print("   Please replace with your actual API key from:")
        print("   https://makersuite.google.com/app/apikey")
        return False
    
    print(f"✅ GOOGLE_API_KEY found: {api_key[:10]}...")
    
    # Check provider
    provider = os.getenv("LLM_PROVIDER")
    if provider != "gemini":
        print(f"⚠️  LLM_PROVIDER is '{provider}', should be 'gemini'")
        print("   Add to .env: LLM_PROVIDER=gemini")
    else:
        print(f"✅ LLM_PROVIDER: {provider}")
    
    # Check model
    model = os.getenv("GEMINI_MODEL", "gemini-pro")
    print(f"✅ GEMINI_MODEL: {model}")
    
    # Check package
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ langchain-google-genai package available")
    except ImportError:
        print("❌ langchain-google-genai package not installed")
        print("   Run: pip install langchain-google-genai")
        return False
    
    print("\n🎉 Environment configuration looks good!")
    print("   Ready to test with: python3 test_gemini_simple.py")
    
    return True

if __name__ == "__main__":
    success = test_env_config()
    
    if not success:
        print("\n🔧 To fix configuration:")
        print("1. Edit .env file and add your Gemini API key")
        print("2. Or run: python3 setup_env_gemini.py")
        exit(1)
    else:
        print("\n🚀 Ready to test Gemini integration!")
        exit(0)