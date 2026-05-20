#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'multi_agent_example'))

from load_env import load_environment
from tracing import setup_openllmetry
import logging

# Set debug logging
logging.basicConfig(level=logging.DEBUG)

async def test_a2a_error():
    """Test A2A message sending to identify the error"""
    
    load_environment()
    setup_openllmetry()
    
    from agents.a2a_dev_lead import A2ADevLeadAgent
    from agents.a2a_developer import A2ADeveloperAgent
    
    print("🧪 Testing A2A Message Error")
    print("=" * 50)
    
    # Initialize agents
    dev_lead = A2ADevLeadAgent()
    developer = A2ADeveloperAgent()
    
    # Start agents
    await asyncio.gather(
        dev_lead.start(),
        developer.start()
    )
    
    # Wait for startup
    await asyncio.sleep(2)
    
    # Let agents discover each other
    await dev_lead.discover_agents()
    await developer.discover_agents()
    
    print("📋 Discovered agents:")
    print(f"  Dev Lead: {list(dev_lead.discovered_agents.keys())}")
    print(f"  Developer: {list(developer.discovered_agents.keys())}")
    
    # Try to send a message from dev lead to developer
    print("📤 Sending message from Dev Lead to Developer...")
    
    try:
        response = await dev_lead.send_message("developer_agent", {
            "type": "develop_code",
            "data": {
                "task_id": "test_123",
                "description": "Test task",
                "requirements": ["Test requirement"]
            }
        })
        print(f"📥 Response: {response}")
    except Exception as e:
        print(f"❌ Exception caught: {type(e).__name__}: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
    
    # Stop agents
    await dev_lead.stop()
    await developer.stop()

if __name__ == "__main__":
    asyncio.run(test_a2a_error())