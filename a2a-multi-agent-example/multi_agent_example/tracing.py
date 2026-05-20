"""Traceloop SDK setup with FastAPI instrumentation for cross-agent tracing"""

import os
from rich.console import Console

console = Console()

def setup_openllmetry():
    """Setup Traceloop SDK with auto-instrumentation and FastAPI support"""
    try:
        from traceloop.sdk import Traceloop
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry import trace
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        
        # Initialize Traceloop SDK with enhanced configuration
        Traceloop.init(
            app_name="multi-agent-code-quality-system",
            api_key=os.getenv("TRACELOOP_API_KEY"),
            api_endpoint=os.getenv("TRACELOOP_BASE_URL", "https://api.traceloop.com"),
            disable_batch=False,
            resource_attributes={
                "service.name": "multi-agent-system",
                "service.version": "1.0.0",
                "deployment.environment": os.getenv("ENVIRONMENT", "development")
            }
        )
        
        console.print("✅ [green]Traceloop SDK initialized[/green]")
        
        # Enable FastAPI auto-instrumentation for cross-agent trace propagation
        try:
            FastAPIInstrumentor().instrument()
            console.print("🚀 [green]FastAPI instrumentation enabled[/green]")
        except Exception as e:
            console.print(f"⚠️ [yellow]FastAPI instrumentation failed: {e}[/yellow]")
        
        # Enable HTTPX client instrumentation for outbound HTTP calls
        try:
            HTTPXClientInstrumentor().instrument(
                # Ensure proper request/response hook for trace propagation
                request_hook=None,  # Use default request hook which handles trace propagation
                response_hook=None  # Use default response hook
            )
            console.print("📡 [green]HTTPX client instrumentation enabled[/green]")
        except Exception as e:
            console.print(f"⚠️ [yellow]HTTPX instrumentation failed: {e}[/yellow]")
        
        console.print("🔗 [cyan]Cross-agent trace propagation activated[/cyan]")
        
        if os.getenv("TRACELOOP_API_KEY"):
            base_url = os.getenv("TRACELOOP_BASE_URL", "https://api.traceloop.com")
            console.print(f"📊 [green]Traces will be exported to Traceloop: {base_url}[/green]")
            console.print("🔍 [blue]View traces at: https://app.traceloop.com[/blue]")
        else:
            console.print("⚠️  [yellow]Set TRACELOOP_API_KEY to export traces to dashboard[/yellow]")
            console.print("💡 [dim]Get your API key from https://app.traceloop.com[/dim]")
        
        return True
        
    except ImportError as e:
        console.print(f"⚠️  [yellow]Traceloop SDK not available: {e}[/yellow]")
        console.print("📦 [blue]Install with: uv sync --dev[/blue]")
        return False
        
    except Exception as e:
        console.print(f"❌ [red]Failed to setup Traceloop: {e}[/red]")
        return False

def instrument_fastapi_app(app):
    """Instrument a specific FastAPI app instance for tracing"""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        
        # Instrument this specific app
        FastAPIInstrumentor.instrument_app(app)
        return True
        
    except ImportError:
        return False
    except Exception:
        return False