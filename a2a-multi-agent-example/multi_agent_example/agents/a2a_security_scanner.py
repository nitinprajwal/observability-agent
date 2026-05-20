"""
A2A Protocol-based Security Scanner Agent
"""

import os
import subprocess
import tempfile
from typing import List, Dict, Any
from a2a.types import Message, Task
from multi_agent_example.a2a_agent import A2ABaseAgent, AgentCapability, TaskResponse


class A2ASecurityScannerAgent(A2ABaseAgent):
    """A2A Security Scanner Agent for vulnerability detection"""
    
    def __init__(self):
        super().__init__(
            "Security Scanner",
            8001,
            "A2A-based security vulnerability scanner using Bandit, Semgrep and pattern matching"
        )
        self.bandit_available = False
        self.semgrep_available = False
    
    async def initialize(self):
        """Initialize security tools"""
        self.console.print("🔐 Security Scanner initializing security tools...")
        
        # Check for Bandit
        try:
            subprocess.run(["bandit", "--version"], capture_output=True, check=True)
            self.bandit_available = True
            self.console.print("✅ Bandit available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.console.print("⚠️  Bandit not available")
        
        # Check for Semgrep
        try:
            subprocess.run(["semgrep", "--version"], capture_output=True, check=True)
            self.semgrep_available = True
            self.console.print("✅ Semgrep available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.console.print("⚠️  Semgrep not available")
        
        if not self.bandit_available and not self.semgrep_available:
            self.console.print("⚠️  No security tools available, using basic pattern matching")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return security scanner capabilities"""
        return [
            AgentCapability(
                name="vulnerability_scan",
                description="Scan code for security vulnerabilities",
                input_schema={"type": "object", "properties": {"file_path": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"vulnerabilities": {"type": "array"}, "risk_score": {"type": "number"}}}
            ),
            AgentCapability(
                name="security_report",
                description="Generate comprehensive security report",
                input_schema={"type": "object", "properties": {"scan_results": {"type": "object"}}},
                output_schema={"type": "object", "properties": {"report": {"type": "string"}, "recommendations": {"type": "array"}}}
            )
        ]
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Process A2A message"""
        message_content = message.parts[0].text if hasattr(message, 'parts') and message.parts and hasattr(message.parts[0], 'text') else str(message)
        
        if "scan_request" in message_content:
            # Extract file path from message data (this needs to be parsed from text)
            import json
            try:
                if isinstance(message_content, str) and message_content.startswith('{'):
                    data = json.loads(message_content)
                    file_path = data.get("file_path")
                else:
                    file_path = None
            except:
                file_path = None
            if file_path:
                result = await self.perform_analysis(file_path)
                return {"status": "completed", "result": result}
        
        return {"status": "unknown_message_type", "message": f"Unknown message content: {message_content[:100]}..."}
    
    async def process_task(self, task: Task) -> TaskResponse:
        """Process A2A task"""
        if task.type == "security_scan":
            file_path = task.data.get("file_path")
            if file_path:
                result = await self.perform_analysis(file_path)
                return TaskResponse(
                    status="completed",
                    result=result,
                    message=f"Security scan completed for {file_path}"
                )
        
        return TaskResponse(
            status="failed",
            result={},
            message=f"Unknown task type: {task.type}"
        )
    
    async def perform_analysis(self, target: str) -> Dict[str, Any]:
        """Perform security analysis using A2A protocol"""
        self.console.print(f"🔍 Starting A2A security scan on: {target}")
        
        vulnerabilities = []
        risk_score = 0.0
        
        # Check if target is a file path or code content
        if os.path.exists(target):
            file_path = target
        else:
            # Create temporary file for code content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(target)
                file_path = f.name
        
        try:
            # Run Bandit if available
            if self.bandit_available:
                vulnerabilities.extend(await self._run_bandit(file_path))
            
            # Run Semgrep if available
            if self.semgrep_available:
                vulnerabilities.extend(await self._run_semgrep(file_path))
            
            # Run pattern-based analysis
            vulnerabilities.extend(await self._pattern_analysis(file_path))
            
            # Calculate risk score
            risk_score = min(len(vulnerabilities) * 8.33, 100.0)
            
        finally:
            # Cleanup temporary file if created
            if not os.path.exists(target) and os.path.exists(file_path):
                os.unlink(file_path)
        
        self.console.print(f"✅ A2A security scan complete: {len(vulnerabilities)} issues found")
        
        return {
            "vulnerabilities": vulnerabilities,
            "risk_score": risk_score,
            "scan_type": "A2A Security Analysis",
            "tool_used": self._get_tools_used()
        }
    
    async def _run_bandit(self, file_path: str) -> List[Dict[str, Any]]:
        """Run Bandit security scanner"""
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                return [
                    {
                        "tool": "bandit",
                        "severity": issue.get("issue_severity", "UNKNOWN"),
                        "confidence": issue.get("issue_confidence", "UNKNOWN"),
                        "description": issue.get("issue_text", "Unknown issue"),
                        "line": issue.get("line_number", 0)
                    }
                    for issue in data.get("results", [])
                ]
        except Exception as e:
            self.logger.error(f"Bandit scan failed: {e}")
        
        return []
    
    async def _run_semgrep(self, file_path: str) -> List[Dict[str, Any]]:
        """Run Semgrep security scanner"""
        try:
            result = subprocess.run(
                ["semgrep", "--config=auto", "--json", file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                return [
                    {
                        "tool": "semgrep",
                        "severity": finding.get("extra", {}).get("severity", "INFO"),
                        "description": finding.get("extra", {}).get("message", "Semgrep finding"),
                        "line": finding.get("start", {}).get("line", 0),
                        "rule": finding.get("check_id", "unknown")
                    }
                    for finding in data.get("results", [])
                ]
        except Exception as e:
            self.logger.error(f"Semgrep scan failed: {e}")
        
        return []
    
    async def _pattern_analysis(self, file_path: str) -> List[Dict[str, Any]]:
        """Basic pattern-based security analysis"""
        patterns = {
            "hardcoded_password": [r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"],
            "sql_injection": [r"execute\(.*%.*\)", "Potential SQL injection"],
            "command_injection": [r"os\.system\(.*\+.*\)", "Potential command injection"],
            "hardcoded_secret": [r"(secret|token|key)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected"]
        }
        
        issues = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                import re
                for line_num, line in enumerate(lines, 1):
                    for pattern_name, (pattern, description) in patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append({
                                "tool": "pattern_analysis",
                                "severity": "MEDIUM",
                                "description": description,
                                "line": line_num,
                                "pattern": pattern_name
                            })
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {e}")
        
        return issues
    
    def _get_tools_used(self) -> List[str]:
        """Get list of tools used in analysis"""
        tools = []
        if self.bandit_available:
            tools.append("bandit")
        if self.semgrep_available:
            tools.append("semgrep")
        tools.append("pattern_analysis")
        return tools