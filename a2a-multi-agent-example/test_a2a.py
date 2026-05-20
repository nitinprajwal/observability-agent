#!/usr/bin/env python3
"""
Simple test script for A2A Protocol integration
"""

import asyncio
from multi_agent_example.agents.a2a_security_scanner import A2ASecurityScannerAgent
from rich.console import Console

console = Console()

async def test_a2a_agent():
    """Test A2A agent initialization and basic functionality"""
    
    console.print("🧪 [bold yellow]Testing A2A Protocol Integration[/bold yellow]")
    console.print("=" * 60)
    
    agent = None
    
    try:
        # Initialize A2A agent
        agent = A2ASecurityScannerAgent()
        
        console.print("✅ [green]A2A Security Scanner agent created[/green]")
        
        # Start agent
        await agent.start()
        
        console.print("✅ [green]A2A agent started successfully[/green]")
        
        # Test capabilities
        capabilities = agent.get_capabilities()
        console.print(f"📋 [cyan]Agent capabilities: {len(capabilities)}[/cyan]")
        for cap in capabilities:
            console.print(f"  - {cap.name}: {cap.description}")
        
        # Test basic analysis
        test_code = '''
def test_function():
    password = "hardcoded_password"
    return password
'''
        
        console.print("🔍 [blue]Testing security analysis...[/blue]")
        result = await agent.perform_analysis(test_code)
        
        console.print(f"📊 [green]Analysis complete![/green]")
        console.print(f"  - Vulnerabilities found: {len(result.get('vulnerabilities', []))}")
        console.print(f"  - Risk score: {result.get('risk_score', 0)}")
        console.print(f"  - Tools used: {result.get('tool_used', [])}")
        
        # Wait a moment for any background tasks
        await asyncio.sleep(2)
        
        console.print("=" * 60)
        console.print("🎉 [bold green]A2A Protocol integration test successful![/bold green]")
        
    except Exception as e:
        console.print(f"❌ [red]Test failed: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
    finally:
        if agent:
            console.print("🛑 [yellow]Shutting down A2A agent...[/yellow]")
            await agent.stop()
        console.print("✅ [green]Test cleanup complete[/green]")

if __name__ == "__main__":
    asyncio.run(test_a2a_agent())