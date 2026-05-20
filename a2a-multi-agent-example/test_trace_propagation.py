#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'multi_agent_example'))

from load_env import load_environment
from tracing import setup_openllmetry
from opentelemetry import trace

async def test_simple_a2a_trace_propagation():
    """Test trace propagation between two A2A agents"""
    
    # Load environment and setup tracing
    load_environment()
    setup_openllmetry()
    
    # Import after tracing is setup
    from agents.a2a_security_scanner import A2ASecurityScannerAgent
    from agents.a2a_code_reviewer import A2ACodeReviewerAgent
    
    print("🧪 Testing A2A Trace Propagation")
    print("=" * 50)
    
    # Get tracer
    tracer = trace.get_tracer(__name__)
    
    # Create a root span for our test
    with tracer.start_as_current_span("test_a2a_propagation") as root_span:
        root_trace_id = root_span.get_span_context().trace_id
        print(f"🔍 Root trace_id: {root_trace_id:032x}")
        
        # Initialize agents
        scanner = A2ASecurityScannerAgent()
        reviewer = A2ACodeReviewerAgent()
        
        # Start agents
        await asyncio.gather(
            scanner.start(),
            reviewer.start()
        )
        
        # Wait for startup
        await asyncio.sleep(3)
        
        # Let agents discover each other
        await scanner.discover_agents()
        await reviewer.discover_agents()
        
        # Send a message from scanner to reviewer within our trace
        print(f"📤 Sending message from Scanner to Reviewer...")
        
        # Add instrumentation to see what happens during the send
        with tracer.start_as_current_span("send_test_message") as send_span:
            send_trace_id = send_span.get_span_context().trace_id
            print(f"🔍 Send span trace_id: {send_trace_id:032x}")
            
            response = await scanner.send_message("code_reviewer_agent", {
                "type": "test_trace_propagation",
                "message": "Testing trace propagation between A2A agents",
                "test_data": "This should be in the same trace"
            })
            
            print(f"📥 Response received: {response}")
        
        # Allow time for trace export
        await asyncio.sleep(2)
        
        # Stop agents gracefully
        await scanner.stop()
        await reviewer.stop()
        
        # Final delay to ensure clean shutdown
        await asyncio.sleep(1)
        
        print(f"✅ Test completed - check Traceloop for unified traces with ID: {root_trace_id:032x}")

if __name__ == "__main__":
    asyncio.run(test_simple_a2a_trace_propagation())