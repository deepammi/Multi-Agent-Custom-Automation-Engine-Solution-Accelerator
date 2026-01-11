#!/usr/bin/env python3
"""
Setup Gemini API key in .env file
"""
import os
from pathlib import Path


def setup_gemini_env():
    """Setup Gemini configuration in .env file."""
    print("🔧 Gemini .env Configuration Setup")
    print("=" * 40)
    
    # Find .env file
    env_file = Path(".env")
    if not env_file.exists():
        env_file = Path("../.env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("   Please run this from the backend/ directory")
        return False
    
    print(f"✅ Found .env file: {env_file}")
    
    # Read current .env content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Check if Gemini config already exists
    if "GOOGLE_API_KEY=" in content and not "your-gemini-api-key-here" in content:
        print("✅ Gemini API key already configured in .env")
        
        # Check if it's set correctly
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key and api_key.startswith("AIza"):
            print(f"✅ Valid API key found: {api_key[:10]}...")
            print("✅ LLM_PROVIDER:", os.getenv("LLM_PROVIDER", "not set"))
            print("✅ GEMINI_MODEL:", os.getenv("GEMINI_MODEL", "not set"))
            return True
        else:
            print("⚠️  API key format looks incorrect")
    
    # Get API key from user
    print("\n📋 Gemini API Key Setup")
    print("1. Visit: https://makersuite.google.com/app/apikey")
    print("2. Sign in with your Google account")
    print("3. Click 'Create API Key'")
    print("4. Copy the generated key (starts with 'AIza...')")
    
    try:
        api_key = input("\n🔑 Enter your Gemini API key: ").strip()
        
        if not api_key:
            print("❌ No API key entered")
            return False
        
        if not api_key.startswith("AIza"):
            print("⚠️  Warning: API key doesn't start with 'AIza' - this might be incorrect")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                return False
        
        # Update .env file
        lines = content.split('\n')
        updated = False
        
        # Update existing lines or add new ones
        gemini_config = {
            "GOOGLE_API_KEY": api_key,
            "LLM_PROVIDER": "gemini",
            "GEMINI_MODEL": "gemini-pro",
            "LLM_TEMPERATURE": "0.7",
            "LLM_TIMEOUT": "60"
        }
        
        for key, value in gemini_config.items():
            found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    found = True
                    break
            
            if not found:
                # Add new line
                if not any("Gemini AI Configuration" in line for line in lines):
                    lines.append("")
                    lines.append("# Gemini AI Configuration")
                lines.append(f"{key}={value}")
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print("✅ .env file updated successfully!")
        print(f"   GOOGLE_API_KEY: {api_key[:10]}...")
        print("   LLM_PROVIDER: gemini")
        print("   GEMINI_MODEL: gemini-pro")
        
        return True
        
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled")
        return False
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False


def test_gemini_config():
    """Test if Gemini is configured correctly."""
    print("\n🧪 Testing Gemini Configuration")
    print("=" * 40)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GOOGLE_API_KEY")
        provider = os.getenv("LLM_PROVIDER")
        model = os.getenv("GEMINI_MODEL")
        
        if not api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return False
        
        if provider != "gemini":
            print(f"⚠️  LLM_PROVIDER is '{provider}', should be 'gemini'")
        
        print(f"✅ GOOGLE_API_KEY: {api_key[:10]}...")
        print(f"✅ LLM_PROVIDER: {provider}")
        print(f"✅ GEMINI_MODEL: {model}")
        
        # Test import
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            print("✅ langchain-google-genai package available")
        except ImportError:
            print("❌ langchain-google-genai package not installed")
            print("   Run: pip install langchain-google-genai")
            return False
        
        print("\n🎉 Gemini configuration looks good!")
        print("   You can now run: python3 test_gemini_simple.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Gemini Environment Setup")
    print("=" * 50)
    
    if setup_gemini_env():
        test_gemini_config()
    else:
        print("❌ Setup failed")