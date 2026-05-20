#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'multi_agent_example'))

from load_env import load_environment
from tracing import setup_openllmetry
import logging
from opentelemetry import trace, propagate
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
import httpx

# Load environment and setup tracing
load_environment()
setup_openllmetry()

async def debug_trace_propagation():
    """Debug trace propagation to understand what's happening"""
    
    # Get tracer
    tracer = trace.get_tracer(__name__)
    
    # Create a root span to start our trace
    with tracer.start_as_current_span("debug_root_span") as root_span:
        print(f"🔍 Root span trace_id: {root_span.get_span_context().trace_id:032x}")
        print(f"🔍 Root span span_id: {root_span.get_span_context().span_id:016x}")
        
        # Test 1: Check if we can extract current context
        headers = {}
        propagate.inject(headers)
        print(f"📤 Injected headers: {headers}")
        
        # Test 2: Check if we can extract context back
        extracted_context = propagate.extract(headers)
        print(f"📥 Extracted context type: {type(extracted_context)}")
        
        # Test 3: Use the extracted context to create a child span
        with tracer.start_as_current_span("child_span_from_extracted", context=extracted_context) as child_span:
            print(f"🧩 Child span trace_id: {child_span.get_span_context().trace_id:032x}")
            print(f"🧩 Child span span_id: {child_span.get_span_context().span_id:016x}")
            parent_info = f"{child_span.parent.span_id:016x}" if child_span.parent else "None"
            print(f"🧩 Child span parent: {parent_info}")
            
            # Test 4: Try HTTP request with manual headers
            async with httpx.AsyncClient() as client:
                try:
                    # Simulate sending to one of our agents
                    test_headers = {}
                    propagate.inject(test_headers)
                    print(f"🌐 HTTP Request headers: {test_headers}")
                    
                    # Don't actually send the request, just show what headers would be sent
                    print("✅ Trace propagation mechanism seems to be working")
                    
                except Exception as e:
                    print(f"❌ HTTP test failed: {e}")
        
        # Test 5: Verify TraceContextTextMapPropagator directly
        propagator = TraceContextTextMapPropagator()
        direct_headers = {}
        propagator.inject(direct_headers)
        print(f"🔧 Direct propagator headers: {direct_headers}")
        
        # Test 6: Check if Traceloop is interfering
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry import trace as otel_trace
        
        current_provider = otel_trace.get_tracer_provider()
        print(f"🏭 Current tracer provider: {type(current_provider)}")
        
        if hasattr(current_provider, '_active_span_processor'):
            processors = getattr(current_provider, '_active_span_processor', None)
            print(f"🔄 Span processors: {type(processors)}")

if __name__ == "__main__":
    asyncio.run(debug_trace_propagation())