"""
A2A Protocol Multi-Agent System - Main Orchestrator
"""

import asyncio
import signal
import sys
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Import all A2A agents
from multi_agent_example.agents.a2a_security_scanner import A2ASecurityScannerAgent
from multi_agent_example.agents.a2a_code_reviewer import A2ACodeReviewerAgent  
from multi_agent_example.agents.a2a_documentation import A2ADocumentationAgent
from multi_agent_example.agents.a2a_dev_lead import A2ADevLeadAgent
from multi_agent_example.agents.a2a_developer import A2ADeveloperAgent

# Import tracing
from multi_agent_example.tracing import setup_openllmetry


class A2AMultiAgentOrchestrator:
    """Orchestrator for A2A Protocol Multi-Agent System"""
    
    def __init__(self):
        self.console = Console()
        self.agents: List = []
        self.agent_classes = [
            A2ASecurityScannerAgent,
            A2ACodeReviewerAgent,
            A2ADocumentationAgent,
            A2ADevLeadAgent,
            A2ADeveloperAgent
        ]
        self.running = False
    
    async def initialize(self):
        """Initialize all A2A agents"""
        self.console.print("🚀 [bold cyan]A2A Multi-Agent System[/bold cyan]")
        self.console.print("🎯 Initializing Agent-to-Agent Protocol Communication")
        
        # Setup tracing
        setup_openllmetry()
        
        self.console.print("\n🤖 Initializing agents...")
        
        # Initialize all agents
        for agent_class in self.agent_classes:
            try:
                agent = agent_class()
                self.agents.append(agent)
            except Exception as e:
                self.console.print(f"❌ Failed to create {agent_class.__name__}: {e}")
        
        # Start all agents with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Starting agents...", total=len(self.agents))
            
            for agent in self.agents:
                try:
                    await agent.start()
                    progress.advance(task)
                except Exception as e:
                    self.console.print(f"❌ Failed to start {agent.name}: {e}")
        
        # Wait for all agents to fully start and then refresh discovery
        await asyncio.sleep(2)
        
        # Refresh agent discovery for all agents
        self.console.print("🔄 [blue]Refreshing A2A agent discovery network...[/blue]")
        for agent in self.agents:
            try:
                await agent.discover_agents()
            except Exception as e:
                self.console.print(f"⚠️ Discovery refresh failed for {agent.name}: {e}")
        
        # Display agent network overview
        self._display_agent_overview()
        
        self.running = True
        self.console.print(f"\n🌐 [green]All agents initialized! {len(self.agents)} agents active[/green]")
    
    def _display_agent_overview(self):
        """Display comprehensive agent network overview"""
        table = Table(title="🎭 A2A Agent Network Overview")
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Port", style="magenta", justify="center")
        table.add_column("Capabilities", style="green")
        table.add_column("Status", style="yellow", justify="center")
        
        for agent in self.agents:
            capabilities = agent.get_capabilities()
            cap_text = ", ".join([cap.name for cap in capabilities[:2]])
            if len(capabilities) > 2:
                cap_text += f", +{len(capabilities)-2} more"
            
            table.add_row(
                agent.name,
                str(agent.port),
                cap_text,
                "● Active"
            )
        
        self.console.print()
        self.console.print(table)
    
    async def run_code_analysis_workflow(self, target: str = None) -> Dict[str, Any]:
        """Run code analysis workflow using A2A Protocol"""
        if target is None:
            target = "/Users/galklm/development/multi-agent-example"
        
        self.console.print(f"\n🔍 [blue]Starting A2A Code Quality Analysis...[/blue]")
        self.console.print(f"🎯 Target: {target}")
        
        results = {}
        
        # Run analysis through each specialized agent
        for agent in self.agents:
            if hasattr(agent, 'perform_analysis') and agent.name != "Dev Lead Agent":
                try:
                    self.console.print(f"\n📊 Running {agent.name} analysis...")
                    result = await agent.perform_analysis(target)
                    results[agent.name] = result
                except Exception as e:
                    self.console.print(f"❌ {agent.name} analysis failed: {e}")
                    results[agent.name] = {"error": str(e)}
        
        return results
    
    async def run_development_workflow(
        self, 
        task_description: str = None,
        requirements: List[str] = None
    ) -> Dict[str, Any]:
        """Run A2A development workflow"""
        if task_description is None:
            task_description = "Create a simple hello world function for testing A2A trace propagation"
        
        if requirements is None:
            requirements = [
                "Create a function that prints 'Hello World'",
                "Add proper docstring", 
                "Include error handling"
            ]
        
        # Find Dev Lead agent
        dev_lead = None
        for agent in self.agents:
            if isinstance(agent, A2ADevLeadAgent):
                dev_lead = agent
                break
        
        if not dev_lead:
            return {"error": "Dev Lead agent not found"}
        
        # Create task specification
        task_spec = f"{task_description}\n\nRequirements:\n" + "\n".join(f"- {req}" for req in requirements)
        
        # Run development workflow
        self.console.print(f"\n🚀 [blue]Starting A2A Development Workflow...[/blue]")
        result = await dev_lead.perform_analysis(task_spec)
        
        return result
    
    async def demonstrate_a2a_communication(self):
        """Demonstrate A2A Protocol agent communication"""
        self.console.print(f"\n🎯 [yellow]Demonstrating A2A Protocol Communication[/yellow]")
        
        if len(self.agents) < 2:
            self.console.print("❌ Need at least 2 agents for communication demo")
            return
        
        # Get first two agents for demo
        sender = self.agents[0]
        receiver = self.agents[1] 
        
        # Send test A2A message that the Code Reviewer can handle
        message_data = {
            "type": "code_review",
            "data": {"message": "Please review this demo code via A2A Protocol!", "file_path": "/tmp/demo_code.py"}
        }
        
        try:
            self.console.print(f"📤 {sender.name} sending A2A message to {receiver.name}...")
            response = await sender.send_message(receiver.agent_id, message_data)
            
            if response:
                self.console.print(f"✅ A2A message successfully delivered!")
                self.console.print(f"📥 Response: {response}")
            else:
                self.console.print("❌ A2A message delivery failed")
                
        except Exception as e:
            self.console.print(f"❌ A2A communication error: {e}")
    
    async def shutdown(self):
        """Shutdown all A2A agents gracefully"""
        import asyncio
        
        if not self.running:
            return
        
        self.console.print("\n🛑 [yellow]Shutting down A2A agents...[/yellow]")
        
        # Allow time for any ongoing operations to complete
        self.console.print("⏱️ [dim]Waiting for operations to complete...[/dim]")
        await asyncio.sleep(2.0)
        
        # Shutdown agents gracefully
        for agent in self.agents:
            try:
                await agent.stop()
            except Exception as e:
                self.console.print(f"⚠️ Error shutting down {agent.name}: {e}")
        
        # Additional delay to allow servers to fully shut down
        await asyncio.sleep(1.0)
        
        self.running = False
        self.console.print("✅ [green]All A2A agents stopped[/green]")
        self.console.print("✅ [green]Test cleanup complete[/green]")


async def main():
    """Main entry point for A2A Multi-Agent System"""
    console = Console()
    orchestrator = None
    
    def signal_handler(sig, frame):
        console.print(f"\n🛑 [yellow]Received signal {sig}, shutting down...[/yellow]")
        if orchestrator:
            asyncio.create_task(orchestrator.shutdown())
        sys.exit(0)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize orchestrator
        orchestrator = A2AMultiAgentOrchestrator()
        await orchestrator.initialize()
        
        # Run development workflow demo
        console.print("\n" + "="*80)
        console.print("🎯 [bold]A2A DEVELOPMENT WORKFLOW DEMO[/bold]")
        console.print("="*80)
        
        result = await orchestrator.run_development_workflow()
        
        console.print("\n" + "="*80) 
        console.print("✅ [bold green]A2A MULTI-AGENT SYSTEM DEMO COMPLETE![/bold green]")
        console.print("="*80)
        
        # Display final results
        if "error" not in result:
            console.print(f"📊 Workflow Status: {result.get('status', 'completed')}")
            console.print(f"🔧 Phases Completed: {result.get('workflow_phases_completed', 0)}")
            console.print(f"💻 Code Generated: {'Yes' if result.get('code_generated') else 'No'}")
            console.print(f"🔍 Reviews Completed: {result.get('reviews_completed', 0)}")
        
        # Demonstrate A2A communication
        await orchestrator.demonstrate_a2a_communication()
        
        # Keep running for a moment to show active system
        console.print(f"\n💡 [cyan]A2A System running with {len(orchestrator.agents)} active agents[/cyan]")
        console.print("Press Ctrl+C to exit...")
        
        # Wait for user interruption
        try:
            await asyncio.sleep(300)  # 5 minutes
        except asyncio.CancelledError:
            pass
            
    except Exception as e:
        console.print(f"❌ [red]System error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
    finally:
        if orchestrator:
            await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())