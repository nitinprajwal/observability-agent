"""
Environment variable loader for A2A Multi-Agent System
Loads environment variables from .env file if present
"""

import os
from pathlib import Path

def load_environment():
    """Load environment variables from .env file if it exists"""
    try:
        from dotenv import load_dotenv
        
        # Look for .env file in the project root
        env_file = Path(__file__).parent / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Loaded environment variables from {env_file}")
            return True
        else:
            # Check if .env.example exists to give helpful message
            example_file = Path(__file__).parent / ".env.example"
            if example_file.exists():
                print(f"💡 No .env file found. Copy .env.example to .env and configure your API keys")
                print(f"   cp {example_file} {env_file}")
            return False
            
    except ImportError:
        print("⚠️  python-dotenv not installed. Run: uv add python-dotenv")
        return False
    except Exception as e:
        print(f"⚠️  Failed to load .env file: {e}")
        return False

def check_required_keys():
    """Check if required API keys are configured"""
    required_keys = {
        "OPENAI_API_KEY": "OpenAI API key for AI-powered code generation",
        "TRACELOOP_API_KEY": "Traceloop API key for trace visualization"
    }
    
    missing_keys = []
    
    for key, description in required_keys.items():
        value = os.getenv(key)
        if not value or value.startswith("your-") or value.startswith("sk-your-") or value.startswith("tl_your-"):
            missing_keys.append((key, description))
    
    if missing_keys:
        print("\n⚠️  Missing or invalid API keys:")
        for key, description in missing_keys:
            print(f"   • {key}: {description}")
        print("\n📋 To configure:")
        print("   1. Copy .env.example to .env")
        print("   2. Edit .env with your actual API keys")
        print("   3. Get keys from:")
        print("      - OpenAI: https://platform.openai.com/account/api-keys")
        print("      - Traceloop: https://app.traceloop.com/settings/api-keys")
        return False
    
    print("✅ All required API keys are configured")
    return True

if __name__ == "__main__":
    # Can be run directly to check configuration
    print("🔧 A2A Multi-Agent System - Environment Check")
    print("=" * 50)
    
    load_environment()
    check_required_keys()
    
    print("\n📊 Current Configuration:")
    print(f"   OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"   TRACELOOP_API_KEY: {'✅ Set' if os.getenv('TRACELOOP_API_KEY') else '❌ Missing'}")
    print(f"   ENVIRONMENT: {os.getenv('ENVIRONMENT', 'development')}")