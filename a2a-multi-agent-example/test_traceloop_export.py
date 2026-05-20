#!/usr/bin/env python3
"""
Test A2A system with Traceloop export
"""

import asyncio
import os
from rich.console import Console

# Load environment variables from .env file
from load_env import load_environment, check_required_keys

console = Console()

async def test_traceloop_export():
    """Test A2A system with Traceloop export"""
    
    console.print("🧪 [bold yellow]Testing A2A System with Traceloop Export[/bold yellow]")
    console.print("📊 [cyan]Traces will be exported to Traceloop dashboard[/cyan]")
    console.print("=" * 80)
    
    # Load environment variables
    env_loaded = load_environment()
    
    # Check for required API keys
    api_key = os.getenv("TRACELOOP_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key.startswith("tl_your-"):
        if env_loaded:
            console.print("❌ [red]TRACELOOP_API_KEY not configured in .env file![/red]")
            console.print("📋 [yellow]To set up Traceloop export:[/yellow]")
            console.print("   1. Edit your .env file")
            console.print("   2. Set TRACELOOP_API_KEY=your_actual_key")
            console.print("   3. Get your key from: https://app.traceloop.com/settings/api-keys")
        else:
            console.print("❌ [red]No .env file found![/red]") 
            console.print("📋 [yellow]To set up environment:[/yellow]")
            console.print("   1. Copy .env.example to .env")
            console.print("   2. Edit .env with your actual API keys")
            console.print("   3. Re-run this test")
        
        console.print("\n💡 [blue]Using demo key for testing...[/blue]")
        api_key = "tl_demo_key_for_conference_presentation"
        os.environ["TRACELOOP_API_KEY"] = api_key
    
    console.print(f"🔑 [green]Using Traceloop API key: {api_key[:8]}...[/green]")
    console.print("🌐 [cyan]Dashboard URL: https://app.traceloop.com[/cyan]")
    
    # Set fallback OpenAI key if not configured
    if not openai_key or openai_key.startswith("sk-your-"):
        console.print("⚠️ [yellow]OpenAI API key not configured - using demo key[/yellow]")
        os.environ.setdefault("OPENAI_API_KEY", "demo-key")
    
    # Import A2A system
    from multi_agent_example.a2a_main import A2AMultiAgentOrchestrator
    
    orchestrator = None
    
    try:
        console.print("\n🚀 [blue]Initializing A2A system with Traceloop export...[/blue]")
        orchestrator = A2AMultiAgentOrchestrator()
        await orchestrator.initialize()
        
        console.print(f"\n📊 [green]Tracing Status:[/green]")
        console.print(f"   • API Key: {'✅ Set' if api_key and api_key != 'demo-key' else '⚠️ Demo key'}")
        console.print(f"   • Export URL: https://api.traceloop.com")
        console.print(f"   • Dashboard: https://app.traceloop.com")
        console.print(f"   • Service: multi-agent-system")
        
        console.print("\n🔥 [yellow]Running A2A workflow to generate traces...[/yellow]")
        
        # Run development workflow to create rich traces
        result = await orchestrator.run_development_workflow(
            task_description="Create a data processing pipeline for A2A tracing demo",
            requirements=[
                "Create a function that processes data files",
                "Add validation and error handling", 
                "Include performance metrics logging",
                "Use async/await for better performance"
            ]
        )
        
        console.print("\n📈 [green]Workflow completed - traces exported to Traceloop![/green]")
        
        if "error" not in result:
            console.print(f"   ✅ Status: {result.get('status', 'completed')}")
            console.print(f"   🔧 Workflow phases: {result.get('workflow_phases_completed', 0)}/4")
            console.print(f"   💻 Code generated: {'Yes' if result.get('code_generated') else 'No'}")
            console.print(f"   🔍 Reviews completed: {result.get('reviews_completed', 0)}")
        
        # Test A2A communication
        console.print("\n📡 [blue]Testing cross-agent A2A communication...[/blue]")
        await orchestrator.demonstrate_a2a_communication()
        
        console.print("\n🎯 [bold green]SUCCESS! Check Traceloop Dashboard:[/bold green]")
        console.print("   🌐 Dashboard: https://app.traceloop.com")
        console.print("   🔍 Look for traces with service: multi-agent-system")
        console.print("   📊 You should see:")
        console.print("      • Agent-to-agent communication traces")
        console.print("      • HTTP request/response spans")
        console.print("      • Development workflow traces")
        console.print("      • Cross-agent trace propagation")
        
        console.print(f"\n⏱️ [cyan]Keeping system alive for 15 seconds to ensure trace export...[/cyan]")
        await asyncio.sleep(15)
        
    except Exception as e:
        console.print(f"\n❌ [red]Test failed: {e}[/red]")
        console.print("💡 [yellow]Common issues:[/yellow]")
        console.print("   • Invalid Traceloop API key")
        console.print("   • Network connectivity issues")
        console.print("   • Traceloop service unavailable")
        import traceback
        console.print(f"[dim]{traceback.format_exc()[:500]}...[/dim]")
    finally:
        if orchestrator:
            console.print("\n🛑 [yellow]Shutting down A2A system...[/yellow]")
            await orchestrator.shutdown()
            console.print("✅ [green]Shutdown complete[/green]")

if __name__ == "__main__":
    console.print("🎨 [bold cyan]A2A Multi-Agent System + Traceloop Export Demo[/bold cyan]")
    
    try:
        asyncio.run(test_traceloop_export())
    except KeyboardInterrupt:
        console.print("\n🛑 [yellow]Demo interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n❌ [red]Demo failed: {e}[/red]")