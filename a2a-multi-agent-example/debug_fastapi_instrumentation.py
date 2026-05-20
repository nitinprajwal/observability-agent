#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'multi_agent_example'))

from load_env import load_environment
from tracing import setup_openllmetry

async def debug_fastapi_instrumentation():
    """Debug FastAPI app structure to understand how to instrument it"""
    
    load_environment()
    setup_openllmetry()
    
    from agents.a2a_security_scanner import A2ASecurityScannerAgent
    
    print("🔍 Debugging FastAPI App Structure")
    print("=" * 50)
    
    # Create an agent
    scanner = A2ASecurityScannerAgent()
    
    print(f"🔍 Agent app type: {type(scanner.app)}")
    print(f"🔍 Agent app attributes: {dir(scanner.app)}")
    
    # Check if it has .app attribute
    if hasattr(scanner.app, 'app'):
        print(f"🔍 Inner app type: {type(scanner.app.app)}")
        print(f"🔍 Inner app attributes (first 10): {dir(scanner.app.app)[:10]}")
        
        # Check if it's a FastAPI app
        try:
            from fastapi import FastAPI
            if isinstance(scanner.app.app, FastAPI):
                print("✅ Found FastAPI app instance!")
            else:
                print(f"❌ Inner app is not FastAPI, it's: {type(scanner.app.app)}")
        except ImportError:
            print("❌ FastAPI not available")
    
    # Try the build method
    if hasattr(scanner.app, 'build'):
        print("🔍 Found build() method - trying to build the app...")
        try:
            built_app = scanner.app.build()
            print(f"🔍 Built app type: {type(built_app)}")
            
            from fastapi import FastAPI
            if isinstance(built_app, FastAPI):
                print("✅ Build method returns FastAPI app!")
            else:
                print(f"❌ Built app is not FastAPI: {type(built_app)}")
                
        except Exception as e:
            print(f"❌ Build failed: {e}")
    
    # Check other potential attributes
    for attr in ['fastapi_app', '_app', 'application']:
        if hasattr(scanner.app, attr):
            app_val = getattr(scanner.app, attr)
            print(f"🔍 Found {attr}: {type(app_val)}")
    
    # Try to start the agent briefly to see what happens
    print("\n🚀 Testing agent startup...")
    try:
        await scanner.start()
        print("✅ Agent started successfully")
        
        # Check if instrumentation worked
        print("🔍 Checking instrumentation...")
        
        await asyncio.sleep(1)
        await scanner.stop()
        print("✅ Agent stopped")
        
    except Exception as e:
        print(f"❌ Agent startup failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(debug_fastapi_instrumentation())