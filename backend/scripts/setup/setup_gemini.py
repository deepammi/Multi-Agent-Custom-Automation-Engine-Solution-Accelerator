#!/usr/bin/env python3
"""
Setup script for Gemini AI integration.
Helps configure environment variables and install required packages.
"""
import os
import subprocess
import sys


def check_package_installed(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name.replace('-', '_'))
        return True
    except ImportError:
        return False


def install_package(package_name):
    """Install a Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False


def setup_gemini():
    """Setup Gemini AI integration."""
    print("🚀 Gemini AI Setup")
    print("=" * 50)
    
    # Step 1: Check for required package
    print("1️⃣  Checking for langchain-google-genai package...")
    
    if check_package_installed("langchain_google_genai"):
        print("   ✅ langchain-google-genai is already installed")
    else:
        print("   📦 Installing langchain-google-genai...")
        if install_package("langchain-google-genai"):
            print("   ✅ langchain-google-genai installed successfully")
        else:
            print("   ❌ Failed to install langchain-google-genai")
            print("   Please run manually: pip install langchain-google-genai")
            return False
    
    # Step 2: Check for API key
    print("\n2️⃣  Checking for Google API key...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"   ✅ GOOGLE_API_KEY found: {api_key[:10]}...")
    else:
        print("   ❌ GOOGLE_API_KEY not found")
        print("\n📋 To get a Google AI API key:")
        print("   1. Visit: https://makersuite.google.com/app/apikey")
        print("   2. Sign in with your Google account")
        print("   3. Click 'Create API Key'")
        print("   4. Copy the generated key")
        print("\n💡 To set the API key:")
        print("   export GOOGLE_API_KEY='your-api-key-here'")
        print("   # Or add to your .env file:")
        print("   echo 'GOOGLE_API_KEY=your-api-key-here' >> .env")
        
        # Ask if user wants to set it now
        try:
            user_key = input("\n🔑 Enter your Google API key (or press Enter to skip): ").strip()
            if user_key:
                os.environ["GOOGLE_API_KEY"] = user_key
                print("   ✅ API key set for this session")
                
                # Offer to save to .env file
                save_to_env = input("💾 Save to .env file? (y/n): ").strip().lower()
                if save_to_env in ['y', 'yes']:
                    try:
                        with open('.env', 'a') as f:
                            f.write(f'\nGOOGLE_API_KEY={user_key}\n')
                        print("   ✅ API key saved to .env file")
                    except Exception as e:
                        print(f"   ❌ Failed to save to .env: {e}")
            else:
                print("   ⏭️  Skipping API key setup")
                return False
        except KeyboardInterrupt:
            print("\n   ⏭️  Skipping API key setup")
            return False
    
    # Step 3: Test configuration
    print("\n3️⃣  Testing Gemini configuration...")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Test initialization
        llm = ChatGoogleGenerativeAI(
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            model="gemini-1.5-pro",
            temperature=0.7
        )
        print("   ✅ Gemini LLM initialized successfully")
        
        # Test simple call
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Say 'Hello from Gemini!'")])
        print(f"   ✅ Test call successful: {response.content[:50]}...")
        
    except Exception as e:
        print(f"   ❌ Gemini test failed: {e}")
        return False
    
    # Step 4: Create environment configuration
    print("\n4️⃣  Creating environment configuration...")
    
    env_config = """
# Gemini AI Configuration
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-pro
LLM_TEMPERATURE=0.7
LLM_TIMEOUT=60
"""
    
    print("   📝 Recommended environment variables:")
    print(env_config)
    
    try:
        save_config = input("💾 Add these to .env file? (y/n): ").strip().lower()
        if save_config in ['y', 'yes']:
            with open('.env', 'a') as f:
                f.write(env_config)
            print("   ✅ Configuration saved to .env file")
    except KeyboardInterrupt:
        print("   ⏭️  Skipping configuration save")
    
    # Success!
    print("\n🎉 Gemini AI setup completed successfully!")
    print("\n🚀 Next steps:")
    print("   1. Set LLM_PROVIDER=gemini in your environment")
    print("   2. Run: python3 test_gemini_integration.py")
    print("   3. Run: python3 test_po_workflow_e2e.py")
    
    return True


if __name__ == "__main__":
    success = setup_gemini()
    exit(0 if success else 1)