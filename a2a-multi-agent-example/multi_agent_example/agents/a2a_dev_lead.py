"""
A2A Protocol-based Dev Lead Agent - Orchestrator for development workflows
"""

import uuid
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from a2a.types import Message, Task, TaskStatus
from multi_agent_example.a2a_agent import A2ABaseAgent, AgentCapability, TaskResponse


class TaskPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"  
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DevelopmentTask:
    """Development task managed by Dev Lead"""
    task_id: str
    description: str
    requirements: List[str]
    priority: TaskPriority
    status: str = "pending"
    assigned_agent: Optional[str] = None
    generated_code: Optional[str] = None
    code_file: Optional[str] = None
    review_results: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time())


class A2ADevLeadAgent(A2ABaseAgent):
    """A2A Dev Lead Agent for orchestrating development workflows"""
    
    def __init__(self):
        super().__init__(
            "Dev Lead Agent",
            8005,
            "A2A-based development workflow orchestrator and team coordinator"
        )
        self.active_tasks: Dict[str, DevelopmentTask] = {}
        self.workflow_phases = [
            "Developer Assignment",
            "Code Generation", 
            "Multi-Agent Review",
            "Final Decision & Summary"
        ]
    
    async def initialize(self):
        """Initialize team coordination"""
        self.console.print("👨‍💼 Dev Lead initializing team coordination...")
        self.console.print("🎯 Ready to orchestrate development workflows")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return dev lead capabilities"""
        return [
            AgentCapability(
                name="create_development_task",
                description="Create and manage development tasks with A2A coordination",
                input_schema={"type": "object", "properties": {"description": {"type": "string"}, "requirements": {"type": "array"}, "priority": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"task_id": {"type": "string"}, "status": {"type": "string"}}}
            ),
            AgentCapability(
                name="orchestrate_development_workflow", 
                description="Orchestrate complete development workflow with multiple A2A agents",
                input_schema={"type": "object", "properties": {"task_id": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"workflow_complete": {"type": "boolean"}, "summary": {"type": "object"}}}
            )
        ]
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Process A2A message"""
        message_content = message.parts[0].text if hasattr(message, 'parts') and message.parts and hasattr(message.parts[0], 'text') else str(message)
        
        if "orchestrate_development_workflow" in message_content:
            # Create and run a development task
            task = self.create_development_task(
                description="Create a simple hello world function for testing trace propagation",
                requirements=[
                    "Create a function that prints 'Hello World'",
                    "Add proper docstring", 
                    "Include error handling"
                ],
                priority=TaskPriority.HIGH
            )
            
            result = await self.orchestrate_development_workflow(task.task_id)
            return {"status": "completed", "result": result}
        
        return {"status": "unknown_message", "message": "Unknown message type"}
    
    async def process_task(self, task: Task) -> TaskResponse:
        """Process A2A task"""
        if hasattr(task, 'type') and task.type == "development_workflow":
            description = task.data.get("description", "Generate code")
            requirements = task.data.get("requirements", [])
            priority = TaskPriority(task.data.get("priority", "MEDIUM"))
            
            dev_task = self.create_development_task(description, requirements, priority)
            result = await self.orchestrate_development_workflow(dev_task.task_id)
            
            return TaskResponse(
                status="completed", 
                result=result,
                message=f"Development workflow completed for task {dev_task.task_id}"
            )
        
        return TaskResponse(
            status="failed",
            result={},
            message=f"Unknown task type: {getattr(task, 'type', 'unknown')}"
        )
    
    async def perform_analysis(self, target: str) -> Dict[str, Any]:
        """Create and orchestrate development workflow"""
        # Parse the target as development request
        lines = target.strip().split('\n')
        description = lines[0] if lines else "Development task"
        
        requirements = []
        for line in lines[1:]:
            if line.strip().startswith('-') or line.strip().startswith('•'):
                requirements.append(line.strip().lstrip('-• '))
        
        if not requirements:
            requirements = ["Implement the requested functionality", "Add proper error handling", "Include documentation"]
        
        # Create development task
        task = self.create_development_task(description, requirements, TaskPriority.HIGH)
        
        # Orchestrate the workflow
        result = await self.orchestrate_development_workflow(task.task_id)
        
        return result
    
    def create_development_task(
        self, 
        description: str, 
        requirements: List[str], 
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> DevelopmentTask:
        """Create a new development task"""
        task_id = f"task_{uuid.uuid4().hex[:3]}"
        
        task = DevelopmentTask(
            task_id=task_id,
            description=description,
            requirements=requirements,
            priority=priority
        )
        
        self.active_tasks[task_id] = task
        
        # Display task creation
        from rich.panel import Panel
        task_panel = Panel(
            f"📋 {description}\n\n"
            f"📁 File: generated_code.py\n"
            f"⚡ Priority: {priority.value}\n\n"
            f"Requirements:\n" + 
            "\n".join(f"  • {req}" for req in requirements),
            title=f"🆕 Development Task {task_id}",
            border_style="green"
        )
        self.console.print(task_panel)
        
        return task
    
    async def orchestrate_development_workflow(self, task_id: str) -> Dict[str, Any]:
        """Orchestrate complete A2A development workflow"""
        if task_id not in self.active_tasks:
            return {"error": f"Task {task_id} not found"}
        
        task = self.active_tasks[task_id]
        
        self.console.print(f"🚀 Starting Development Workflow for {task_id}")
        
        try:
            # Phase 1: Developer Assignment
            self.console.print(f"👨‍💻 Phase 1: {self.workflow_phases[0]}")
            await self._refresh_agent_discovery()
            
            developer_assigned = await self._assign_to_developer(task)
            if not developer_assigned:
                return {"error": "No developer agent available", "phase": "assignment"}
            
            # Phase 2: Code Generation
            self.console.print(f"⚡ Phase 2: {self.workflow_phases[1]}")
            code_generated = await self._request_code_generation(task)
            if not code_generated:
                return {"error": "Code generation failed", "phase": "generation"}
            
            # Phase 3: Multi-Agent Review
            self.console.print(f"🔍 Phase 3: {self.workflow_phases[2]}")
            reviews_complete = await self._coordinate_code_reviews(task)
            
            # Phase 4: Final Decision
            self.console.print(f"⚖️ Phase 4: {self.workflow_phases[3]}")
            final_summary = await self._generate_final_summary(task)
            
            task.status = "completed"
            
            return {
                "task_id": task_id,
                "status": "completed",
                "workflow_phases_completed": len(self.workflow_phases),
                "code_generated": task.generated_code is not None,
                "reviews_completed": len(task.review_results),
                "final_summary": final_summary,
                "analysis_type": "A2A Development Workflow"
            }
            
        except Exception as e:
            self.logger.error(f"Development workflow failed: {e}")
            task.status = "failed"
            return {"error": str(e), "task_id": task_id, "status": "failed"}
    
    async def _refresh_agent_discovery(self):
        """Refresh agent discovery to find all available agents"""
        self.console.print("🔍 Dev Lead discovering peers...")
        await self.discover_agents()
    
    async def _assign_to_developer(self, task: DevelopmentTask) -> bool:
        """Assign task to developer agent"""
        # Find developer agent
        developer_agents = [
            agent_id for agent_id, agent_info in self.discovered_agents.items()
            if "developer" in agent_info.get("name", "").lower()
        ]
        
        if not developer_agents:
            self.console.print("❌ No developer agents found")
            return False
        
        developer_id = developer_agents[0]
        task.assigned_agent = developer_id
        
        self.console.print("✅ Task assigned to Developer Agent")
        return True
    
    async def _request_code_generation(self, task: DevelopmentTask) -> bool:
        """Request code generation from developer agent"""
        if not task.assigned_agent:
            return False
        
        try:
            # Send A2A message to developer
            message_data = {
                "type": "develop_code",
                "data": {
                    "task_id": task.task_id,
                    "description": task.description,
                    "requirements": task.requirements
                }
            }
            
            response = await self.send_message(task.assigned_agent, message_data)
            
            self.console.print(f"🔍 Dev Lead received response: {response}")
            
            if response and response.get("status") == "completed":
                result = response.get("result", {})
                self.console.print(f"🔍 Result structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                task.generated_code = result.get("code")
                task.code_file = result.get("filename", "/tmp/generated_code.py")
                
                self.console.print("✅ Code generation completed successfully!")
                return True
            else:
                self.console.print("❌ Code generation failed!")
                self.console.print(f"🔍 Response was: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Code generation request failed: {e}")
            return False
    
    async def _coordinate_code_reviews(self, task: DevelopmentTask) -> Dict[str, Any]:
        """Coordinate multi-agent code reviews"""
        if not task.code_file:
            return {}
        
        self.console.print(f"📝 Saved generated code to {task.code_file}")
        
        # Find review agents
        review_agents = {
            "security": [aid for aid, info in self.discovered_agents.items() 
                        if "security" in info.get("name", "").lower()],
            "quality": [aid for aid, info in self.discovered_agents.items() 
                       if "reviewer" in info.get("name", "").lower() or "quality" in info.get("name", "").lower()],
            "documentation": [aid for aid, info in self.discovered_agents.items() 
                             if "documentation" in info.get("name", "").lower()]
        }
        
        # Send review requests
        review_tasks = []
        
        for review_type, agents in review_agents.items():
            if agents:
                agent_id = agents[0]
                review_request = {
                    "type": f"{review_type}_request" if review_type != "quality" else "review_request",
                    "data": {"file_path": task.code_file}
                }
                
                review_tasks.append((review_type, agent_id, review_request))
        
        # Execute reviews concurrently
        review_results = {}
        for review_type, agent_id, request in review_tasks:
            try:
                response = await self.send_message(agent_id, request)
                if response and response.get("status") == "completed":
                    review_results[review_type] = response.get("result", {})
            except Exception as e:
                self.logger.error(f"{review_type} review failed: {e}")
                review_results[review_type] = {"error": str(e)}
        
        task.review_results = review_results
        
        # Display review summary
        self._display_review_summary(task)
        
        return review_results
    
    def _display_review_summary(self, task: DevelopmentTask):
        """Display review summary table"""
        from rich.table import Table
        
        table = Table(title=f"📋 Review Summary - {task.task_id}")
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Status", style="green", justify="center")
        table.add_column("Issues", style="red", justify="center") 
        table.add_column("Score", style="yellow", justify="center")
        
        for review_type, result in task.review_results.items():
            if isinstance(result, dict) and "error" not in result:
                agent_name = review_type.title()
                status = "✅ Good" if review_type == "quality" else "🔒 Secure" if review_type == "security" else "📚 Well Documented"
                issues = str(result.get("total_issues", result.get("vulnerabilities", 0) if isinstance(result.get("vulnerabilities"), int) else len(result.get("vulnerabilities", []))))
                
                # Get appropriate score
                if review_type == "security":
                    score = f"{result.get('risk_score', 0)}/100"
                elif review_type == "quality": 
                    score = f"{result.get('quality_score', 0)}/100"
                elif review_type == "documentation":
                    score = f"{result.get('coverage_score', 0)}%"
                else:
                    score = "N/A"
                
                table.add_row(agent_name, status, issues, score)
        
        self.console.print(table)
    
    async def _generate_final_summary(self, task: DevelopmentTask) -> Dict[str, Any]:
        """Generate final workflow summary"""
        from rich.panel import Panel
        
        # Analyze overall results
        total_issues = 0
        security_score = 100.0
        quality_score = 100.0
        doc_coverage = 100.0
        
        strengths = []
        issues_found = []
        recommendations = []
        
        for review_type, result in task.review_results.items():
            if isinstance(result, dict) and "error" not in result:
                if review_type == "security":
                    security_issues = result.get("vulnerabilities", [])
                    if isinstance(security_issues, list):
                        total_issues += len(security_issues)
                    security_score = 100 - result.get("risk_score", 0)
                    if len(security_issues) == 0:
                        strengths.append("No security vulnerabilities detected")
                
                elif review_type == "quality":
                    quality_issues = result.get("issues", [])
                    total_issues += len(quality_issues)
                    quality_score = result.get("quality_score", 100.0)
                
                elif review_type == "documentation":
                    doc_issues = result.get("missing_documentation", [])
                    total_issues += len(doc_issues)
                    doc_coverage = result.get("coverage_score", 100.0)
        
        # Determine overall assessment
        if total_issues == 0 and security_score >= 80 and quality_score >= 80:
            overall_assessment = "EXCELLENT"
        elif total_issues <= 5 and security_score >= 60 and quality_score >= 60:
            overall_assessment = "GOOD"
        elif total_issues <= 10:
            overall_assessment = "FAIR"
        else:
            overall_assessment = "NEEDS_IMPROVEMENT"
        
        # Generate issues and recommendations
        if security_score < 80:
            issues_found.append("Low security score")
            recommendations.append("Review and fix security vulnerabilities")
        
        if quality_score < 80:
            issues_found.append("Low code quality score")
            recommendations.append("Refactor code to improve quality metrics")
        
        if doc_coverage < 80:
            issues_found.append("Poor documentation coverage")
            recommendations.append("Add comprehensive docstrings and comments")
        
        if not issues_found:
            strengths.append("High quality code with good security and documentation")
        
        # Display final summary
        summary_panel = Panel(
            f"📊 Overall Assessment: [bold]{overall_assessment}[/bold]\n\n"
            f"✅ Strengths:\n" + "\n".join(f"  • {s}" for s in (strengths or ["Code generated successfully"])) + "\n\n" +
            (f"⚠️ Issues Found:\n" + "\n".join(f"  • {i}" for i in issues_found) + "\n\n" if issues_found else "") +
            (f"📋 Recommendations:\n" + "\n".join(f"  • {r}" for r in recommendations) if recommendations else ""),
            title=f"🎯 Final Decision - {task.task_id}",
            border_style="blue"
        )
        self.console.print(summary_panel)
        
        return {
            "overall_assessment": overall_assessment,
            "total_issues": total_issues,
            "security_score": security_score,
            "quality_score": quality_score, 
            "documentation_coverage": doc_coverage,
            "strengths": strengths,
            "issues_found": issues_found,
            "recommendations": recommendations,
            "workflow_success": overall_assessment in ["EXCELLENT", "GOOD"]
        }