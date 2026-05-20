"""
A2A Protocol-based Code Reviewer Agent with AI-powered analysis
"""

import os
import subprocess
import ast
from typing import List, Dict, Any
from a2a.types import Message, Task
from multi_agent_example.a2a_agent import A2ABaseAgent, AgentCapability, TaskResponse


class A2ACodeReviewerAgent(A2ABaseAgent):
    """A2A Code Reviewer Agent for quality analysis and AI-powered insights"""
    
    def __init__(self):
        super().__init__(
            "Code Reviewer Agent",
            8002,
            "A2A-based code quality analyzer with AI-powered insights and MCP tools"
        )
        self.openai_client = None
        self.ai_available = False
        self.pylint_available = False
        self.mypy_available = False
        self.mcp_tools = {}
    
    async def initialize(self):
        """Initialize code review tools"""
        self.console.print("📝 Code Reviewer initializing analysis tools...")
        
        # Check for static analysis tools
        try:
            subprocess.run(["pylint", "--version"], capture_output=True, check=True)
            self.pylint_available = True
            self.console.print("✅ Pylint available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.console.print("⚠️  Pylint not available")
        
        try:
            subprocess.run(["mypy", "--version"], capture_output=True, check=True)
            self.mypy_available = True
            self.console.print("✅ MyPy available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.console.print("⚠️  MyPy not available")
        
        # Initialize MCP tools (simulated)
        self._initialize_mcp_tools()
        
        # Initialize OpenAI for AI insights
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI()
                self.ai_available = True
                self.console.print("🤖 AI-powered code review enabled")
            except ImportError:
                self.console.print("⚠️  OpenAI package not available")
        else:
            self.console.print("⚠️  No OpenAI API key for AI insights")
    
    def _initialize_mcp_tools(self):
        """Initialize MCP tools for advanced analysis"""
        self.mcp_tools = {
            "ast_analyzer": self._analyze_ast,
            "complexity_calculator": self._calculate_complexity,
            "style_checker": self._check_style
        }
        self.console.print(f"🛠️  MCP tools initialized: {len(self.mcp_tools)} tools available")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return code reviewer capabilities"""
        return [
            AgentCapability(
                name="code_quality_review",
                description="Perform comprehensive code quality analysis with AI insights",
                input_schema={"type": "object", "properties": {"file_path": {"type": "string"}, "code": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"quality_score": {"type": "number"}, "issues": {"type": "array"}, "suggestions": {"type": "array"}}}
            ),
            AgentCapability(
                name="complexity_analysis",
                description="Analyze code complexity using MCP tools",
                input_schema={"type": "object", "properties": {"code": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"complexity_score": {"type": "number"}, "metrics": {"type": "object"}}}
            )
        ]
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Process A2A message"""
        message_content = message.parts[0].text if hasattr(message, 'parts') and message.parts and hasattr(message.parts[0], 'text') else str(message)
        
        if "review_request" in message_content or "code_review" in message_content:
            # Extract file path from message
            data = getattr(message, 'data', {}) if hasattr(message, 'data') else {}
            file_path = data.get('file_path', '/tmp/generated_code.py')
            
            result = await self.perform_analysis(file_path)
            return {"status": "completed", "result": result}
        
        return {"status": "unknown_message", "message": "Unknown message type"}
    
    async def process_task(self, task: Task) -> TaskResponse:
        """Process A2A task"""
        if hasattr(task, 'type') and task.type == "code_review":
            file_path = task.data.get("file_path", "/tmp/generated_code.py")
            
            result = await self.perform_analysis(file_path)
            return TaskResponse(
                status="completed",
                result=result,
                message=f"Code review completed for {file_path}"
            )
        
        return TaskResponse(
            status="failed",
            result={},
            message=f"Unknown task type: {getattr(task, 'type', 'unknown')}"
        )
    
    async def perform_analysis(self, target: str) -> Dict[str, Any]:
        """Perform comprehensive code quality analysis"""
        self.console.print(f"📋 Starting code review on: {target}")
        
        if not os.path.exists(target):
            return {
                "error": f"File not found: {target}",
                "quality_score": 0.0,
                "issues": [],
                "analysis_type": "A2A Code Review"
            }
        
        issues = []
        quality_metrics = {}
        
        try:
            # Read the code
            with open(target, 'r') as f:
                code_content = f.read()
            
            # MCP Tool: AST Analysis
            ast_analysis = await self.mcp_tools["ast_analyzer"](code_content)
            issues.extend(ast_analysis.get("issues", []))
            quality_metrics["ast"] = ast_analysis.get("metrics", {})
            
            # MCP Tool: Complexity Analysis
            complexity_analysis = await self.mcp_tools["complexity_calculator"](code_content)
            quality_metrics["complexity"] = complexity_analysis
            
            # MCP Tool: Style Analysis
            style_analysis = await self.mcp_tools["style_checker"](target)
            issues.extend(style_analysis.get("issues", []))
            
            # AI-Powered Code Insights
            if self.ai_available:
                self.console.print("🤖 Generating AI-powered code insights...")
                ai_insights = await self._get_ai_code_feedback(code_content, target)
                quality_metrics["ai_insights"] = ai_insights
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(issues, quality_metrics)
            
            # External tools
            if self.pylint_available:
                pylint_issues = await self._run_pylint(target)
                issues.extend(pylint_issues)
            
            if self.mypy_available:
                mypy_issues = await self._run_mypy(target)
                issues.extend(mypy_issues)
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}")
            return {
                "error": str(e),
                "quality_score": 0.0,
                "issues": [],
                "analysis_type": "A2A Code Review"
            }
        
        self.console.print("✅ Excellent code quality!" if quality_score > 80 else "⚠️  Code needs improvement")
        
        return {
            "quality_score": quality_score,
            "issues": issues,
            "metrics": quality_metrics,
            "files_analyzed": 1,
            "total_issues": len(issues),
            "analysis_type": "A2A Code Review with AI",
            "tools_used": self._get_tools_used()
        }
    
    async def _analyze_ast(self, code: str) -> Dict[str, Any]:
        """MCP Tool: Analyze code using AST"""
        try:
            tree = ast.parse(code)
            
            functions = []
            classes = []
            imports = []
            issues = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                    # Check for missing docstrings
                    if not ast.get_docstring(node):
                        issues.append({
                            "type": "missing_docstring",
                            "line": node.lineno,
                            "message": f"Function '{node.name}' missing docstring",
                            "severity": "low"
                        })
                
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    if not ast.get_docstring(node):
                        issues.append({
                            "type": "missing_docstring", 
                            "line": node.lineno,
                            "message": f"Class '{node.name}' missing docstring",
                            "severity": "medium"
                        })
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    else:
                        imports.append(node.module or "relative_import")
            
            return {
                "issues": issues,
                "metrics": {
                    "functions": len(functions),
                    "classes": len(classes),
                    "imports": len(imports),
                    "function_names": functions,
                    "class_names": classes
                }
            }
            
        except SyntaxError as e:
            return {
                "issues": [{"type": "syntax_error", "message": str(e), "severity": "high"}],
                "metrics": {"syntax_valid": False}
            }
    
    async def _calculate_complexity(self, code: str) -> Dict[str, Any]:
        """MCP Tool: Calculate cyclomatic complexity"""
        try:
            tree = ast.parse(code)
            complexity = 1  # Base complexity
            
            for node in ast.walk(tree):
                # Decision points increase complexity
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.Try):
                    complexity += len(node.handlers)
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            complexity_level = "low" if complexity <= 10 else "medium" if complexity <= 20 else "high"
            
            return {
                "cyclomatic_complexity": complexity,
                "complexity_level": complexity_level,
                "maintainability_index": max(0, 100 - complexity * 2)
            }
            
        except SyntaxError:
            return {"cyclomatic_complexity": 0, "complexity_level": "unknown"}
    
    async def _check_style(self, file_path: str) -> Dict[str, Any]:
        """MCP Tool: Check code style compliance"""
        issues = []
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                # Check line length
                if len(line) > 88:  # PEP 8 recommends 79, but 88 is common
                    issues.append({
                        "type": "line_too_long",
                        "line": i,
                        "message": f"Line too long ({len(line)} characters)",
                        "severity": "low"
                    })
                
                # Check for trailing whitespace
                if line.rstrip() != line.rstrip('\n'):
                    issues.append({
                        "type": "trailing_whitespace",
                        "line": i,
                        "message": "Trailing whitespace detected",
                        "severity": "low"
                    })
            
            return {"issues": issues}
            
        except Exception:
            return {"issues": []}
    
    async def _get_ai_code_feedback(self, code: str, file_path: str) -> str:
        """Generate AI-powered code review insights"""
        try:
            prompt = f"""Review this Python code and provide specific feedback:

{code}

Please analyze:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance optimizations
4. Readability improvements
5. Security considerations

Provide specific, actionable feedback in 2-3 sentences."""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Python code reviewer. Provide concise, actionable feedback focusing on code quality, best practices, and potential improvements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"AI feedback generation failed: {e}")
            return "AI insights unavailable"
    
    async def _run_pylint(self, file_path: str) -> List[Dict]:
        """Run Pylint analysis"""
        try:
            result = subprocess.run(
                ["pylint", "--output-format=json", file_path],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                import json
                pylint_output = json.loads(result.stdout)
                return [
                    {
                        "type": "pylint",
                        "line": msg.get("line", 0),
                        "message": msg.get("message", ""),
                        "severity": msg.get("type", "info"),
                        "symbol": msg.get("symbol", "")
                    }
                    for msg in pylint_output
                ]
        except Exception as e:
            self.logger.error(f"Pylint analysis failed: {e}")
        
        return []
    
    async def _run_mypy(self, file_path: str) -> List[Dict]:
        """Run MyPy type checking"""
        try:
            result = subprocess.run(
                ["mypy", "--show-error-codes", file_path],
                capture_output=True,
                text=True
            )
            
            issues = []
            for line in result.stdout.split('\n'):
                if ':' in line and 'error' in line:
                    parts = line.split(':', 3)
                    if len(parts) >= 3:
                        issues.append({
                            "type": "mypy",
                            "line": int(parts[1]) if parts[1].isdigit() else 0,
                            "message": parts[2].strip() if len(parts) > 2 else line,
                            "severity": "medium"
                        })
            
            return issues
            
        except Exception as e:
            self.logger.error(f"MyPy analysis failed: {e}")
        
        return []
    
    def _calculate_quality_score(self, issues: List[Dict], metrics: Dict) -> float:
        """Calculate overall code quality score"""
        base_score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            severity = issue.get("severity", "low")
            if severity == "high":
                base_score -= 10
            elif severity == "medium":
                base_score -= 5
            else:
                base_score -= 2
        
        # Complexity penalty
        complexity = metrics.get("complexity", {})
        if isinstance(complexity, dict):
            complexity_score = complexity.get("cyclomatic_complexity", 0)
            if complexity_score > 20:
                base_score -= 15
            elif complexity_score > 10:
                base_score -= 5
        
        return max(0.0, min(100.0, base_score))
    
    def _get_tools_used(self) -> List[str]:
        """Get list of analysis tools used"""
        tools = ["ast_analyzer", "complexity_calculator", "style_checker"]
        
        if self.pylint_available:
            tools.append("pylint")
        if self.mypy_available:
            tools.append("mypy")
        if self.ai_available:
            tools.append("ai_insights")
        
        return tools