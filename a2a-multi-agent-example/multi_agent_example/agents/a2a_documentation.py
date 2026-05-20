"""
A2A Protocol-based Documentation Agent
"""

import os
import ast
from typing import List, Dict, Any
from a2a.types import Message, Task
from multi_agent_example.a2a_agent import A2ABaseAgent, AgentCapability, TaskResponse


class A2ADocumentationAgent(A2ABaseAgent):
    """A2A Documentation Agent for analyzing code documentation coverage and quality"""
    
    def __init__(self):
        super().__init__(
            "Documentation Agent",
            8003,
            "A2A-based documentation analyzer for coverage and quality assessment"
        )
    
    async def initialize(self):
        """Initialize documentation analysis tools"""
        self.console.print("📚 Documentation Agent initializing...")
        self.console.print("📖 Ready to analyze code documentation and generate reports")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return documentation agent capabilities"""
        return [
            AgentCapability(
                name="documentation_analysis",
                description="Analyze documentation coverage and quality in Python code",
                input_schema={"type": "object", "properties": {"file_path": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"coverage_score": {"type": "number"}, "quality_score": {"type": "number"}, "missing_docs": {"type": "array"}}}
            ),
            AgentCapability(
                name="generate_documentation",
                description="Generate missing documentation templates",
                input_schema={"type": "object", "properties": {"code": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"documentation": {"type": "string"}, "suggestions": {"type": "array"}}}
            )
        ]
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Process A2A message"""
        message_content = message.parts[0].text if hasattr(message, 'parts') and message.parts and hasattr(message.parts[0], 'text') else str(message)
        
        if "doc_analysis_request" in message_content or "documentation_analysis" in message_content:
            # Extract file path from message
            data = getattr(message, 'data', {}) if hasattr(message, 'data') else {}
            file_path = data.get('file_path', '/tmp/generated_code.py')
            
            result = await self.perform_analysis(file_path)
            return {"status": "completed", "result": result}
        
        return {"status": "unknown_message", "message": "Unknown message type"}
    
    async def process_task(self, task: Task) -> TaskResponse:
        """Process A2A task"""
        if hasattr(task, 'type') and task.type == "documentation_analysis":
            file_path = task.data.get("file_path", "/tmp/generated_code.py")
            
            result = await self.perform_analysis(file_path)
            return TaskResponse(
                status="completed",
                result=result,
                message=f"Documentation analysis completed for {file_path}"
            )
        
        return TaskResponse(
            status="failed",
            result={},
            message=f"Unknown task type: {getattr(task, 'type', 'unknown')}"
        )
    
    async def perform_analysis(self, target: str) -> Dict[str, Any]:
        """Analyze documentation coverage and quality"""
        self.console.print(f"📊 Starting documentation analysis on: {target}")
        
        if not os.path.exists(target):
            return {
                "error": f"File not found: {target}",
                "coverage_score": 0.0,
                "quality_score": 0.0,
                "analysis_type": "A2A Documentation Analysis"
            }
        
        try:
            with open(target, 'r') as f:
                content = f.read()
            
            # Parse AST for analysis
            tree = ast.parse(content)
            
            # Analyze documentation
            doc_stats = self._analyze_documentation(tree, content)
            
            # Calculate scores
            coverage_score = self._calculate_coverage_score(doc_stats)
            quality_score = self._calculate_quality_score(doc_stats)
            
            # Generate missing documentation report
            missing_docs = self._find_missing_documentation(doc_stats)
            
            self.console.print(f"📈 Coverage Score: {coverage_score}%")
            self.console.print(f"⭐ Quality Score: {quality_score}/100")
            
            return {
                "coverage_score": coverage_score,
                "quality_score": quality_score,
                "files_analyzed": 1,
                "functions_documented": doc_stats["functions_with_docs"],
                "functions_total": doc_stats["total_functions"],
                "classes_documented": doc_stats["classes_with_docs"],
                "classes_total": doc_stats["total_classes"],
                "modules_documented": doc_stats["modules_with_docs"],
                "modules_total": doc_stats["total_modules"],
                "missing_documentation": missing_docs,
                "analysis_type": "A2A Documentation Analysis",
                "recommendations": self._generate_recommendations(doc_stats, coverage_score, quality_score)
            }
            
        except Exception as e:
            self.logger.error(f"Documentation analysis failed: {e}")
            return {
                "error": str(e),
                "coverage_score": 0.0,
                "quality_score": 0.0,
                "analysis_type": "A2A Documentation Analysis"
            }
    
    def _analyze_documentation(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze documentation in the AST"""
        stats = {
            "total_functions": 0,
            "functions_with_docs": 0,
            "total_classes": 0,
            "classes_with_docs": 0,
            "total_modules": 1,  # The file itself is a module
            "modules_with_docs": 0,
            "function_details": [],
            "class_details": [],
            "docstring_lengths": [],
            "docstring_quality_scores": []
        }
        
        # Check module-level docstring
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            stats["modules_with_docs"] = 1
            stats["docstring_lengths"].append(len(module_docstring))
            stats["docstring_quality_scores"].append(self._score_docstring_quality(module_docstring))
        
        # Analyze functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                stats["total_functions"] += 1
                docstring = ast.get_docstring(node)
                
                func_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "has_docstring": docstring is not None,
                    "docstring": docstring,
                    "args_count": len(node.args.args)
                }
                
                if docstring:
                    stats["functions_with_docs"] += 1
                    stats["docstring_lengths"].append(len(docstring))
                    stats["docstring_quality_scores"].append(self._score_docstring_quality(docstring))
                
                stats["function_details"].append(func_info)
            
            elif isinstance(node, ast.ClassDef):
                stats["total_classes"] += 1
                docstring = ast.get_docstring(node)
                
                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "has_docstring": docstring is not None,
                    "docstring": docstring,
                    "methods_count": len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                }
                
                if docstring:
                    stats["classes_with_docs"] += 1
                    stats["docstring_lengths"].append(len(docstring))
                    stats["docstring_quality_scores"].append(self._score_docstring_quality(docstring))
                
                stats["class_details"].append(class_info)
        
        return stats
    
    def _score_docstring_quality(self, docstring: str) -> float:
        """Score the quality of a docstring"""
        if not docstring:
            return 0.0
        
        score = 0.0
        lines = docstring.strip().split('\n')
        
        # Length score (up to 30 points)
        if len(docstring) > 50:
            score += 30
        elif len(docstring) > 20:
            score += 20
        else:
            score += 10
        
        # Multi-line score (up to 20 points)
        if len(lines) > 3:
            score += 20
        elif len(lines) > 1:
            score += 10
        
        # Content quality indicators (up to 50 points)
        docstring_lower = docstring.lower()
        
        # Check for common documentation elements
        quality_indicators = [
            ('args:', 'arguments:', 'parameters:', 'param'),
            ('returns:', 'return:'),
            ('raises:', 'raise:', 'exception'),
            ('example:', 'examples:'),
            ('note:', 'warning:')
        ]
        
        for indicators in quality_indicators:
            if any(indicator in docstring_lower for indicator in indicators):
                score += 10
        
        return min(100.0, score)
    
    def _calculate_coverage_score(self, stats: Dict[str, Any]) -> float:
        """Calculate documentation coverage percentage"""
        total_items = stats["total_functions"] + stats["total_classes"] + stats["total_modules"]
        documented_items = stats["functions_with_docs"] + stats["classes_with_docs"] + stats["modules_with_docs"]
        
        if total_items == 0:
            return 100.0
        
        return (documented_items / total_items) * 100.0
    
    def _calculate_quality_score(self, stats: Dict[str, Any]) -> float:
        """Calculate overall documentation quality score"""
        if not stats["docstring_quality_scores"]:
            return 0.0
        
        return sum(stats["docstring_quality_scores"]) / len(stats["docstring_quality_scores"])
    
    def _find_missing_documentation(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find items missing documentation"""
        missing = []
        
        # Check functions
        for func in stats["function_details"]:
            if not func["has_docstring"]:
                missing.append({
                    "type": "Function",
                    "name": func["name"],
                    "file": "generated_code.py",
                    "line": func["line"]
                })
        
        # Check classes
        for cls in stats["class_details"]:
            if not cls["has_docstring"]:
                missing.append({
                    "type": "Class",
                    "name": cls["name"],
                    "file": "generated_code.py",
                    "line": cls["line"]
                })
        
        # Check module
        if stats["modules_with_docs"] == 0:
            missing.append({
                "type": "Module",
                "name": "generated_code.py",
                "file": "generated_code.py",
                "line": 1
            })
        
        return missing
    
    def _generate_recommendations(self, stats: Dict[str, Any], coverage_score: float, quality_score: float) -> List[str]:
        """Generate recommendations for improving documentation"""
        recommendations = []
        
        if coverage_score < 80:
            recommendations.append("Increase documentation coverage by adding docstrings to undocumented functions and classes")
        
        if quality_score < 70:
            recommendations.append("Improve docstring quality by including parameters, return values, and examples")
        
        if stats["total_functions"] > stats["functions_with_docs"]:
            missing_funcs = stats["total_functions"] - stats["functions_with_docs"]
            recommendations.append(f"Add docstrings to {missing_funcs} undocumented function(s)")
        
        if stats["total_classes"] > stats["classes_with_docs"]:
            missing_classes = stats["total_classes"] - stats["classes_with_docs"]
            recommendations.append(f"Add docstrings to {missing_classes} undocumented class(es)")
        
        if stats["modules_with_docs"] == 0:
            recommendations.append("Add a module-level docstring describing the purpose and contents of this file")
        
        if not recommendations:
            recommendations.append("Documentation coverage and quality are excellent!")
        
        return recommendations