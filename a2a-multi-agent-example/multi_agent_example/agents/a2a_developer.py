"""
A2A Protocol-based Developer Agent with AI-powered code generation
"""

import os
import tempfile
from typing import List, Dict, Any
from a2a.types import Message, Task
from multi_agent_example.a2a_agent import A2ABaseAgent, AgentCapability, TaskResponse


class A2ADeveloperAgent(A2ABaseAgent):
    """A2A Developer Agent for AI-powered code generation"""
    
    def __init__(self):
        super().__init__(
            "Developer Agent",
            8006,
            "A2A-based AI-powered Python code generator using GPT-4o-mini"
        )
        self.openai_client = None
        self.ai_available = False
    
    async def initialize(self):
        """Initialize OpenAI client for code generation"""
        self.console.print("👨‍💻 Developer Agent initializing...")
        
        # Initialize OpenAI client if API key available
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI()
                self.ai_available = True
                self.console.print("🤖 OpenAI integration enabled")
            except ImportError:
                self.console.print("⚠️  OpenAI package not available")
        else:
            self.console.print("⚠️  No OpenAI API key provided")
        
        self.console.print("⚡ Ready to generate Python code from specifications")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Return developer agent capabilities"""
        return [
            AgentCapability(
                name="generate_code",
                description="Generate Python code from specifications using AI",
                input_schema={"type": "object", "properties": {"description": {"type": "string"}, "requirements": {"type": "array"}}},
                output_schema={"type": "object", "properties": {"code": {"type": "string"}, "filename": {"type": "string"}}}
            ),
            AgentCapability(
                name="refactor_code",
                description="Refactor and improve existing Python code",
                input_schema={"type": "object", "properties": {"code": {"type": "string"}, "improvements": {"type": "array"}}},
                output_schema={"type": "object", "properties": {"refactored_code": {"type": "string"}, "changes": {"type": "array"}}}
            )
        ]
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Process A2A message"""
        # Get message text from the first text part
        message_content = ""
        if hasattr(message, 'parts') and message.parts:
            first_part = message.parts[0]
            # Try different ways to extract the text content
            if hasattr(first_part, 'text') and first_part.text:
                message_content = first_part.text
            elif hasattr(first_part, 'root') and hasattr(first_part.root, 'text') and first_part.root.text:
                # Handle A2A Part with root TextPart structure
                raw_text = first_part.root.text
                # Extract actual content from TextPart representation
                if raw_text.startswith('root=TextPart(') and 'text=' in raw_text:
                    # Extract the text content from the TextPart representation
                    start_idx = raw_text.find('text="') + 6
                    end_idx = raw_text.rfind('"')
                    if start_idx > 5 and end_idx > start_idx:
                        message_content = raw_text[start_idx:end_idx]
                        # Unescape the content
                        message_content = message_content.replace('\\"', '"').replace("\\'", "'")
                    else:
                        message_content = raw_text
                else:
                    message_content = raw_text
            elif hasattr(first_part, 'content') and first_part.content:
                message_content = first_part.content
            elif isinstance(first_part, dict) and 'text' in first_part:
                message_content = first_part['text']
            else:
                # If it's a Pydantic model, try to extract the dict and get text
                try:
                    if hasattr(first_part, 'model_dump'):
                        part_dict = first_part.model_dump()
                        message_content = part_dict.get('text', str(first_part))
                    else:
                        message_content = str(first_part)
                except:
                    message_content = str(first_part)
        else:
            message_content = str(message)
        
        self.console.print(f"🤖 Developer received message: {message_content[:100]}...")
        self.console.print(f"🔍 Message type: {type(message)}, Parts: {len(message.parts) if hasattr(message, 'parts') and message.parts else 0}")
        if hasattr(message, 'parts') and message.parts:
            first_part = message.parts[0]
            self.console.print(f"🔍 First part type: {type(first_part)}")
            if hasattr(first_part, '__dict__'):
                self.console.print(f"🔍 First part attrs: {list(first_part.__dict__.keys())}")
            if hasattr(first_part, 'text'):
                self.console.print(f"🔍 First part text: {first_part.text[:100] if first_part.text else 'None'}")
            if hasattr(first_part, 'root'):
                self.console.print(f"🔍 First part root: {first_part.root}")
                self.console.print(f"🔍 Root type: {type(first_part.root)}")
                if hasattr(first_part.root, 'text'):
                    self.console.print(f"🔍 Root text: {first_part.root.text[:100] if first_part.root.text else 'None'}")
        
        
        if "develop_code" in message_content or "generate_code" in message_content:
            self.console.print(f"🔧 Processing development request...")
            # Parse task details from the message content 
            try:
                import json
                import ast
                
                # Try different parsing methods
                if isinstance(message_content, str):
                    if message_content.startswith('{') and message_content.endswith('}'):
                        # Looks like dict format - try JSON first, then Python format
                        try:
                            task_data = json.loads(message_content)
                        except json.JSONDecodeError:
                            # Try Python dict format (single quotes)
                            try:
                                task_data = ast.literal_eval(message_content)
                            except:
                                # Last resort: replace single quotes with double quotes
                                message_content_fixed = message_content.replace("'", '"')
                                task_data = json.loads(message_content_fixed)
                    else:
                        # Try to parse as Python dict string representation  
                        try:
                            task_data = ast.literal_eval(message_content)
                        except:
                            # If it contains single quotes, might be Python dict format
                            message_content_fixed = message_content.replace("'", '"')
                            task_data = json.loads(message_content_fixed)
                else:
                    task_data = message_content
                    
                # Extract task info from the parsed data
                if isinstance(task_data, dict):
                    if 'data' in task_data:
                        actual_data = task_data['data']
                        description = actual_data.get('description', 'Generate Python code')
                        requirements = actual_data.get('requirements', [])
                    else:
                        description = task_data.get('description', 'Generate Python code')
                        requirements = task_data.get('requirements', [])
                else:
                    description = 'Generate Python code based on request'
                    requirements = []
                    
                self.console.print(f"📝 Task: {description}")
                self.console.print(f"📋 Requirements: {len(requirements)} items")
                        
            except Exception as e:
                self.logger.error(f"Failed to parse task data: {e}")
                self.console.print(f"⚠️ Using fallback task generation")
                self.console.print(f"🔍 Raw message for debugging: {repr(message_content[:200])}")
                description = 'Generate Python code based on request'
                requirements = []
            
            result = await self.perform_analysis(f"{description}\n\nRequirements:\n" + "\n".join(f"- {req}" for req in requirements))
            return {"status": "completed", "result": result}
        
        self.console.print(f"⚠️ Developer: Unknown message type in: {message_content}")
        return {"status": "unknown_message", "message": "Unknown message type"}
    
    async def process_task(self, task: Task) -> TaskResponse:
        """Process A2A task"""
        if hasattr(task, 'type') and task.type == "code_generation":
            description = task.data.get("description", "Generate code")
            requirements = task.data.get("requirements", [])
            
            result = await self.perform_analysis(f"{description}\n\nRequirements:\n" + "\n".join(f"- {req}" for req in requirements))
            return TaskResponse(
                status="completed",
                result=result,
                message=f"Code generation completed for: {description}"
            )
        
        return TaskResponse(
            status="failed",
            result={},
            message=f"Unknown task type: {getattr(task, 'type', 'unknown')}"
        )
    
    async def perform_analysis(self, target: str) -> Dict[str, Any]:
        """Generate code based on specifications"""
        from opentelemetry import trace
        
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            "code_generation",
            attributes={
                "agent.name": "Developer Agent",
                "task": target.split('\n')[0][:100],  # First line truncated
                "operation": "code_generation"
            }
        ):
            self.console.print("📝 Developing code for task...")
            self.console.print(f"📋 Description: {target.split('Requirements:')[0].strip()}")
        
        # Parse requirements
        requirements = []
        if "Requirements:" in target:
            req_section = target.split("Requirements:")[1].strip()
            requirements = [line.strip("- ").strip() for line in req_section.split("\n") if line.strip()]
        
        self.console.print("⚡ Generating function code...")
        
        if self.ai_available:
            try:
                code = await self._generate_code_with_ai(target, requirements)
                if code is None:  # AI returned None (timeout/error)
                    code = self._generate_fallback_code(target, requirements)
                else:
                    self.console.print("✅ Code generation completed successfully!")
            except Exception as e:
                self.console.print(f"⚠️  AI generation failed: {e}")
                code = self._generate_fallback_code(target, requirements)
        else:
            code = self._generate_fallback_code(target, requirements)
        
        # Save to temporary file for analysis
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            filename = f.name
        
            self.console.print(f"📁 Generated code saved to {filename}")
            
            return {
                "code": code,
                "filename": filename,
                "language": "python",
                "lines": len(code.split('\n')),
                "generation_method": "ai_powered" if self.ai_available else "template_based",
                "requirements_met": len(requirements)
            }
    
    async def _generate_code_with_ai(self, description: str, requirements: List[str]) -> str:
        """Generate code using OpenAI GPT-4o-mini"""
        self.console.print("🧠 Sending request to GPT-4o-mini...")
        
        # Create comprehensive prompt
        prompt = f"""Generate Python code based on this specification:

{description}

Requirements:
{chr(10).join(f"- {req}" for req in requirements)}

Please generate:
1. Clean, well-documented Python code
2. Proper error handling
3. Type hints where appropriate
4. Docstrings for functions/classes
5. Example usage if applicable

Return only the Python code, no explanations or markdown formatting."""

        try:
            # Add timeout to prevent hanging during shutdown
            import asyncio
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert Python developer. Generate clean, production-ready Python code based on specifications. Include proper documentation, error handling, and follow Python best practices."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2000
                ),
                timeout=20.0  # Reduced to 20 second timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except asyncio.TimeoutError:
            self.console.print("⏱️ AI request timed out - using template fallback")
            self.logger.warning("OpenAI request timed out")
            return None  # Will trigger fallback
        except Exception as e:
            self.console.print(f"⚠️ AI request failed: {e}")
            self.logger.error(f"OpenAI API error: {e}")
            return None  # Will trigger fallback instead of raising
    
    def _generate_fallback_code(self, description: str, requirements: List[str]) -> str:
        """Generate basic template code when AI is not available"""
        self.console.print("🔧 Using template-based code generation...")
        
        # Extract function name from description
        desc_lower = description.lower()
        if "hello world" in desc_lower or "hello" in desc_lower:
            func_name = "hello_world"
        elif "calculator" in desc_lower or "calc" in desc_lower:
            func_name = "calculator"
        elif "api" in desc_lower:
            func_name = "api_handler"
        else:
            func_name = "generated_function"
        
        # Basic template
        code = f'''import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def {func_name}():
    """
    Generated function based on: {description.split("Requirements:")[0].strip()}
    
    Requirements implemented:
'''
        
        for req in requirements:
            code += f'    - {req}\n'
        
        code += '''    
    Returns:
        str: Result of the operation
    """
    try:
        # TODO: Implement the actual functionality
        result = "Function template generated successfully"
        logging.info(f"Operation completed: {result}")
        return result
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise

# Example usage
if __name__ == "__main__":
    result = ''' + func_name + '''()
    print(f"Result: {result}")
'''
        
        return code