"""
A2A Protocol-based agent implementation using the official a2a-sdk
"""

import asyncio
import logging
import uvicorn
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
import uuid
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel

from a2a.client import A2AClient
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import RequestHandler
from a2a.types import Message, Task, TaskStatus, AgentCard, AgentCapabilities, AgentSkill
from pydantic import BaseModel


@dataclass
class AgentCapability:
    """Agent capability definition for A2A"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


class TaskRequest(BaseModel):
    """Task request model for A2A communication"""
    task_type: str
    description: str
    data: Dict[str, Any]


class TaskResponse(BaseModel):
    """Task response model for A2A communication"""
    status: str
    result: Dict[str, Any]
    message: str


class A2ABaseAgent(ABC):
    """Base class for A2A Protocol-based agents"""
    
    def __init__(self, name: str, port: int, description: str = ""):
        self.name = name
        self.agent_id = f"{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        self.port = port
        self.description = description
        self.console = Console()
        self.discovered_agents: Dict[str, Dict] = {}
        
        # Create AgentCard for A2A
        self.agent_card = self._create_agent_card()
        
        # Create request handler
        self.request_handler = self._create_request_handler()
        
        # Create custom context builder that preserves OpenTelemetry trace context
        self.context_builder = self._create_context_builder()
        
        # Initialize A2A FastAPI application
        self.app = A2AFastAPIApplication(
            agent_card=self.agent_card,
            http_handler=self.request_handler,
            context_builder=self.context_builder
        )
        
        # Note: FastAPI instrumentation will be done at server startup
        
        # Initialize A2A client for communication  
        import httpx
        self.httpx_client = httpx.AsyncClient()
        self.client = A2AClient(
            httpx_client=self.httpx_client,
            agent_card=self.agent_card
        )
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"a2a_agent.{self.name.lower()}")
        
        # Setup message and task handlers
        self._setup_handlers()
        
        # Server instance for uvicorn
        self.server = None
    
    def _create_agent_card(self) -> AgentCard:
        """Create A2A AgentCard for this agent"""
        capabilities = self.get_capabilities()
        
        # Convert capabilities to A2A format
        agent_skills = []
        for cap in capabilities:
            skill = AgentSkill(
                id=f"{self.agent_id}_{cap.name}",
                name=cap.name,
                description=cap.description,
                tags=["analysis", "security", "multi-agent"]
            )
            agent_skills.append(skill)
        
        return AgentCard(
            name=self.name,
            description=self.description,
            version="1.0.0",
            url=f"http://localhost:{self.port}",
            default_input_modes=["text"],
            default_output_modes=["text"],
            skills=agent_skills,
            capabilities=AgentCapabilities(
                skills=agent_skills
            ),
            protocol_version="1.0"
        )
    
    def _create_request_handler(self) -> RequestHandler:
        """Create A2A request handler with all required methods"""
        from a2a.types import (
            MessageSendParams, SendStreamingMessageRequest, 
            SendStreamingMessageResponse, GetTaskRequest, GetTaskResponse,
            CancelTaskRequest, CancelTaskResponse, TaskResubscriptionRequest,
            SetTaskPushNotificationConfigRequest, SetTaskPushNotificationConfigResponse,
            GetTaskPushNotificationConfigRequest, GetTaskPushNotificationConfigResponse,
            ListTaskPushNotificationConfigRequest, ListTaskPushNotificationConfigResponse,
            DeleteTaskPushNotificationConfigRequest, DeleteTaskPushNotificationConfigResponse
        )
        from a2a.server.context import ServerCallContext
        
        class CompleteA2ARequestHandler(RequestHandler):
            def __init__(self, agent):
                self.agent = agent
                self.tasks: Dict[str, Task] = {}  # Simple task storage
                self.task_notifications: Dict[str, Dict] = {}  # Notification configs
                
            async def on_message_send(
                self, 
                params: MessageSendParams, 
                context: ServerCallContext = None
            ) -> Task | Message:
                """Handle A2A message sending"""
                try:
                    self.agent.console.print(f"🔄 A2A Message received in {self.agent.name}")
                    
                    # Extract trace context from the OpenTelemetry context preserved by our context builder
                    from opentelemetry import trace, propagate
                    
                    # Try to use the preserved OpenTelemetry context from FastAPI instrumentation
                    extracted_context = None
                    if context and hasattr(context, 'state') and 'otel_context' in context.state:
                        # Use the preserved OpenTelemetry context directly
                        extracted_context = context.state['otel_context']
                    elif context and hasattr(context, 'state') and 'headers' in context.state:
                        # Fallback: extract from headers if no preserved context
                        try:
                            headers = context.state['headers']
                            extracted_context = propagate.extract(headers)
                        except Exception:
                            # Silently fall back to creating new span
                            pass
                    
                    # Process the message through our agent with tracing
                    tracer = trace.get_tracer(__name__)
                    
                    with tracer.start_as_current_span(
                        f"a2a_message_process",
                        context=extracted_context,
                        attributes={
                            "agent.name": self.agent.name,
                            "agent.id": self.agent.agent_id,
                            "message.id": params.message.message_id,
                            "message.role": params.message.role.value,
                            "protocol": "A2A",
                            "a2a.message.type": "receive"
                        }
                    ) as receive_span:
                        result = await self.agent.process_message(params.message)
                    
                    # Return a Message object with the result
                    from a2a.types import Role, TextPart
                    import uuid
                    
                    response_message = Message(
                        message_id=str(uuid.uuid4()),
                        role=Role.agent,
                        parts=[
                            TextPart(
                                text=str(result)
                            )
                        ]
                    )
                    
                    return response_message
                    
                except Exception as e:
                    self.agent.logger.error(f"Message processing failed: {e}")
                    # Return an error message
                    from a2a.types import Role, TextPart
                    import uuid
                    
                    error_message = Message(
                        message_id=str(uuid.uuid4()),
                        role=Role.agent,
                        parts=[
                            TextPart(
                                text=f"Error: {str(e)}"
                            )
                        ]
                    )
                    
                    return error_message
            
            async def on_message_send_stream(
                self, 
                request: SendStreamingMessageRequest, 
                context: ServerCallContext = None
            ) -> SendStreamingMessageResponse:
                """Handle A2A streaming message sending"""
                try:
                    # For demo purposes, treat streaming as regular message
                    message_result = await self.agent.process_message(request.message)
                    
                    return SendStreamingMessageResponse(
                        success=True,
                        data=message_result
                    )
                except Exception as e:
                    return SendStreamingMessageResponse(
                        success=False,
                        error=str(e)
                    )
            
            async def on_get_task(
                self, 
                request: GetTaskRequest, 
                context: ServerCallContext = None
            ) -> GetTaskResponse:
                """Handle A2A task retrieval"""
                task_id = request.task_id
                
                if task_id in self.tasks:
                    return GetTaskResponse(
                        success=True,
                        task=self.tasks[task_id]
                    )
                else:
                    return GetTaskResponse(
                        success=False,
                        error=f"Task {task_id} not found"
                    )
            
            async def on_cancel_task(
                self, 
                request: CancelTaskRequest, 
                context: ServerCallContext = None
            ) -> CancelTaskResponse:
                """Handle A2A task cancellation"""
                task_id = request.task_id
                
                if task_id in self.tasks:
                    # Update task status to cancelled
                    self.tasks[task_id].status = TaskStatus.CANCELLED
                    
                    return CancelTaskResponse(
                        success=True,
                        message=f"Task {task_id} cancelled successfully"
                    )
                else:
                    return CancelTaskResponse(
                        success=False,
                        error=f"Task {task_id} not found"
                    )
            
            async def on_resubscribe_to_task(
                self, 
                request: TaskResubscriptionRequest, 
                context: ServerCallContext = None
            ) -> Dict[str, Any]:
                """Handle A2A task resubscription"""
                return {
                    "success": True,
                    "message": "Task resubscription handled",
                    "task_id": request.task_id
                }
            
            # Task Push Notification Config Methods
            async def on_set_task_push_notification_config(
                self, 
                request: SetTaskPushNotificationConfigRequest, 
                context: ServerCallContext = None
            ) -> SetTaskPushNotificationConfigResponse:
                """Handle setting task push notification configuration"""
                task_id = request.task_id
                config = request.config
                
                self.task_notifications[task_id] = {
                    "config": config,
                    "enabled": True
                }
                
                return SetTaskPushNotificationConfigResponse(
                    success=True,
                    message=f"Push notification config set for task {task_id}"
                )
            
            async def on_get_task_push_notification_config(
                self, 
                request: GetTaskPushNotificationConfigRequest, 
                context: ServerCallContext = None
            ) -> GetTaskPushNotificationConfigResponse:
                """Handle getting task push notification configuration"""
                task_id = request.task_id
                
                if task_id in self.task_notifications:
                    config = self.task_notifications[task_id]["config"]
                    return GetTaskPushNotificationConfigResponse(
                        success=True,
                        config=config
                    )
                else:
                    return GetTaskPushNotificationConfigResponse(
                        success=False,
                        error=f"No notification config found for task {task_id}"
                    )
            
            async def on_list_task_push_notification_config(
                self, 
                request: ListTaskPushNotificationConfigRequest, 
                context: ServerCallContext = None
            ) -> ListTaskPushNotificationConfigResponse:
                """Handle listing task push notification configurations"""
                configs = []
                for task_id, notification_data in self.task_notifications.items():
                    configs.append({
                        "task_id": task_id,
                        "config": notification_data["config"],
                        "enabled": notification_data.get("enabled", True)
                    })
                
                return ListTaskPushNotificationConfigResponse(
                    success=True,
                    configs=configs
                )
            
            async def on_delete_task_push_notification_config(
                self, 
                request: DeleteTaskPushNotificationConfigRequest, 
                context: ServerCallContext = None
            ) -> DeleteTaskPushNotificationConfigResponse:
                """Handle deleting task push notification configuration"""
                task_id = request.task_id
                
                if task_id in self.task_notifications:
                    del self.task_notifications[task_id]
                    return DeleteTaskPushNotificationConfigResponse(
                        success=True,
                        message=f"Notification config deleted for task {task_id}"
                    )
                else:
                    return DeleteTaskPushNotificationConfigResponse(
                        success=False,
                        error=f"No notification config found for task {task_id}"
                    )
        
        return CompleteA2ARequestHandler(self)
    
    def _create_context_builder(self):
        """Create a custom context builder that preserves OpenTelemetry trace context"""
        from a2a.server.apps.jsonrpc.jsonrpc_app import CallContextBuilder
        from a2a.server.context import ServerCallContext
        from a2a.auth.user import UnauthenticatedUser
        from a2a.server.apps.jsonrpc.jsonrpc_app import StarletteUserProxy
        import contextlib
        from opentelemetry import trace
        from opentelemetry.context import get_current
        
        class TracePreservingContextBuilder(CallContextBuilder):
            def build(self, request) -> ServerCallContext:
                """Builds a ServerCallContext from a Starlette Request with OpenTelemetry context preservation."""
                # Build the basic context like the default builder
                user = UnauthenticatedUser()
                state = {}
                with contextlib.suppress(Exception):
                    user = StarletteUserProxy(request.user)
                    state['auth'] = request.auth
                state['headers'] = dict(request.headers)
                
                # Preserve the current OpenTelemetry context from FastAPI instrumentation
                # This ensures the trace context created by FastAPI instrumentation is available
                current_span = trace.get_current_span()
                if current_span and current_span.is_recording():
                    # Store the current OpenTelemetry context in the state
                    state['otel_context'] = get_current()
                    trace_id = current_span.get_span_context().trace_id
                    span_id = current_span.get_span_context().span_id
                    state['trace_info'] = {
                        'trace_id': trace_id,
                        'span_id': span_id
                    }
                else:
                    # Try to extract from headers as fallback when no active span
                    if 'traceparent' in state['headers']:
                        from opentelemetry import propagate
                        try:
                            extracted = propagate.extract(state['headers'])
                            state['otel_context'] = extracted
                        except Exception:
                            pass
                
                return ServerCallContext(
                    user=user,
                    state=state
                )
        
        return TracePreservingContextBuilder()
    
    def _setup_handlers(self):
        """Setup A2A message and task handlers - handled by RequestHandler"""
        # The CompleteA2ARequestHandler handles all message and task processing
        # through the A2A Protocol standard methods
        pass
    
    def _instrument_fastapi_app(self, fastapi_app=None):
        """Instrument the A2A FastAPI application for distributed tracing"""
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from fastapi import FastAPI
            
            # Use the provided fastapi_app if given
            if fastapi_app:
                # A2AFastAPI inherits from FastAPI, so check for both
                if isinstance(fastapi_app, FastAPI) or str(type(fastapi_app)).find('FastAPI') != -1:
                    FastAPIInstrumentor.instrument_app(fastapi_app)
                    print(f"✅ FastAPI instrumentation added to {self.name}")
                    return
            
            # Fallback: try to build the app if not provided
            if hasattr(self.app, 'build'):
                built_app = self.app.build()
                if isinstance(built_app, FastAPI):
                    # Instrument the built FastAPI app
                    FastAPIInstrumentor.instrument_app(built_app)
                    print(f"✅ FastAPI instrumentation added to {self.name}")
                    return
            
            # Last resort: try direct access patterns
            for attr in ['app', 'fastapi_app', '_app', 'application']:
                if hasattr(self.app, attr):
                    app_instance = getattr(self.app, attr)
                    if isinstance(app_instance, FastAPI):
                        FastAPIInstrumentor.instrument_app(app_instance)
                        print(f"✅ FastAPI instrumentation added via {attr} to {self.name}")
                        return
                        
            print(f"⚠️ Could not find FastAPI app to instrument in {self.name}")
                
        except ImportError:
            print("⚠️ OpenTelemetry FastAPI instrumentation not available")
        except Exception as e:
            print(f"⚠️ Failed to instrument FastAPI app: {e}")
    
    async def start(self):
        """Start the A2A agent"""
        self.print_startup()
        
        # Initialize agent-specific setup
        await self.initialize()
        
        # Start A2A server using uvicorn
        # Build the A2A FastAPI application
        fastapi_app = self.app.build()
        
        config = uvicorn.Config(
            fastapi_app,
            host="localhost",
            port=self.port,
            log_level="warning"
        )
        self.server = uvicorn.Server(config)
        
        # Start server in background
        asyncio.create_task(self.server.serve())
        await asyncio.sleep(1)  # Give server time to start
        
        # Discover other agents
        await self.discover_agents()
        
        self.console.print(f"✅ [green]{self.name} ready on A2A port {self.port}[/green]")
    
    async def stop(self):
        """Stop the A2A agent gracefully"""
        import asyncio
        try:
            # Close HTTP client first to cancel any ongoing requests
            if hasattr(self, 'httpx_client') and self.httpx_client:
                await self.httpx_client.aclose()
            
            # Give a moment for any pending operations to complete
            await asyncio.sleep(0.1)
            
            # Stop the server
            if self.server:
                self.server.should_exit = True
                # Wait a brief moment for graceful shutdown
                await asyncio.sleep(0.1)
                
        except Exception as e:
            # Silently handle any shutdown errors
            pass
            
        self.console.print(f"🛑 [red]{self.name} stopped[/red]")
    
    def print_startup(self):
        """Print agent startup information"""
        # Get capabilities for display
        capabilities = self.get_capabilities()
        
        # Format capabilities list
        if capabilities:
            cap_lines = []
            for cap in capabilities:
                cap_lines.append(f"  • {cap.name}: {cap.description}")
            capabilities_text = f"\n🛠️  Skills & Capabilities:\n" + "\n".join(cap_lines)
        else:
            capabilities_text = ""
        
        startup_info = Panel(
            f"🤖 Agent [bold]{self.name}[/bold] initializing with A2A Protocol\n"
            f"📍 ID: {self.agent_id}\n"
            f"🌐 A2A Port: {self.port}\n"
            f"📋 Description: {self.description}"
            f"{capabilities_text}",
            title="A2A Agent Startup",
            border_style="blue"
        )
        self.console.print(startup_info)
    
    async def discover_agents(self):
        """Discover other A2A agents on the network"""
        self.console.print(f"🔍 [blue]{self.name} discovering A2A peers...[/blue]")
        
        discovered_count = 0
        
        for port in range(8001, 8010):
            if port == self.port:
                continue
            
            try:
                # Try to discover A2A agent at this port
                endpoint = f"http://localhost:{port}"
                
                # Direct HTTP check for A2A agent discovery using instrumented client
                try:
                    # Try A2A agent card endpoint (well-known location)
                    response = await self.httpx_client.get(f"{endpoint}/.well-known/agent-card.json", timeout=2.0)
                    if response.status_code == 200:
                        # Try to get agent info from the response
                        try:
                            agent_data = response.json()
                            agent_name = agent_data.get('name', f'A2A Agent {port}')
                            # Use the agent name to derive a more accurate ID
                            agent_id = f"{agent_name.lower().replace(' ', '_')}_{port}"
                        except:
                            agent_name = f'A2A Agent {port}'
                            agent_id = f"agent_{port}"
                        
                        agent_info = {
                            'id': agent_id,
                            'name': agent_name,
                            'endpoint': endpoint,
                            'port': port
                        }
                        # Store by both the derived ID and by port-based ID for lookup flexibility
                        self.discovered_agents[agent_id] = agent_info
                        self.discovered_agents[f"agent_{port}"] = agent_info
                        discovered_count += 1
                        self.console.print(f"✨ Found: {agent_info['name']} (A2A Protocol)")
                except Exception:
                    # Fallback to check alternate agent card endpoint
                    try:
                        response = await self.httpx_client.get(f"{endpoint}/.well-known/agent.json", timeout=1.0)
                        if response.status_code == 200:
                            try:
                                agent_data = response.json()
                                agent_name = agent_data.get('name', f'A2A Agent {port}')
                                agent_id = f"{agent_name.lower().replace(' ', '_')}_{port}"
                            except:
                                agent_name = f'A2A Agent {port}'
                                agent_id = f"agent_{port}"
                            
                            agent_info = {
                                'id': agent_id,
                                'name': agent_name,
                                'endpoint': endpoint,
                                'port': port
                            }
                            # Store by both the derived ID and by port-based ID  
                            self.discovered_agents[agent_id] = agent_info
                            self.discovered_agents[f"agent_{port}"] = agent_info
                            discovered_count += 1
                            self.console.print(f"✨ Found: {agent_info['name']} (A2A Protocol)")
                    except Exception:
                        pass
            except Exception:
                continue
        
        self.console.print(f"🌐 A2A Discovery complete: {discovered_count} agents found")
    
    async def send_message(self, receiver_id: str, message_content: Dict[str, Any]) -> Optional[Dict]:
        """Send A2A message to another agent"""
        # Try to find the agent by exact ID first, then by name match, then by port
        receiver_info = None
        
        if receiver_id in self.discovered_agents:
            receiver_info = self.discovered_agents[receiver_id]
        else:
            # Try to find by matching agent name pattern
            for agent_id, agent_info in self.discovered_agents.items():
                agent_name_id = agent_info['name'].lower().replace(' ', '_')
                if agent_name_id in receiver_id:
                    receiver_info = agent_info
                    break
        
        if not receiver_info:
            self.logger.warning(f"A2A Agent {receiver_id} not found! Available: {list(self.discovered_agents.keys())}")
            return None
        
        self.console.print(
            f"📤 [green]{self.name}[/green] → [yellow]{receiver_info['name']}[/yellow]: A2A Message"
        )
        
        try:
            # Create A2A message with proper structure
            from a2a.types import TextPart, Role
            import uuid
            
            message = Message(
                message_id=str(uuid.uuid4()),
                role=Role.user,
                parts=[
                    TextPart(
                        text=str(message_content) if not isinstance(message_content, dict) else str(message_content)
                    )
                ]
            )
            
            # Send via A2A JSON-RPC protocol using instrumented client
            # Create A2A JSON-RPC request for message sending
            # Convert the Message object to dict format for JSON-RPC
            message_dict = {
                "message_id": message.message_id,
                "role": message.role.value,
                "parts": [{
                    "kind": "text",
                    "text": getattr(part, 'text', str(part))
                } for part in message.parts]
            }
            
            rpc_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "message/send",
                "params": {
                    "message": message_dict
                }
            }
            
            # Get current trace context and inject it into HTTP headers for propagation
            from opentelemetry import trace, propagate
            
            # Create headers dict for trace context injection
            headers = {}
            
            # Get current span context and inject trace headers
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                # Use OpenTelemetry's propagator to inject trace context into headers
                propagate.inject(headers)
                
                # Add span attributes for better tracing
                current_span.set_attribute("a2a.message.type", "send")
                current_span.set_attribute("a2a.sender.agent", self.name)
                current_span.set_attribute("a2a.receiver.agent", receiver_info['name'])
                current_span.set_attribute("a2a.receiver.endpoint", receiver_info['endpoint'])
                current_span.add_event("a2a_message_sending", {
                    "receiver_id": receiver_id,
                    "message_type": message_content.get("type", "unknown")
                })
            
            # Always inject trace context, even if no current span (for proper propagation)
            if not headers:
                propagate.inject(headers)
            
            # Use the instrumented httpx client with trace context headers
            response = await self.httpx_client.post(
                f"{receiver_info['endpoint']}/",
                json=rpc_request,
                headers=headers,  # Include trace context headers
                timeout=60.0  # Increased timeout for AI operations
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    # A2A JSON-RPC success - result should be a Message object
                    message_result = result["result"]
                    if isinstance(message_result, dict) and "parts" in message_result:
                        # Extract the response from the Message parts
                        parts = message_result["parts"]
                        if parts and isinstance(parts, list):
                            first_part = parts[0]
                            if "text" in first_part:
                                response_text = first_part["text"]
                                # Try to parse the response as JSON (our agent's response)
                                try:
                                    import json
                                    import ast
                                    if response_text.startswith('{') or response_text.startswith("{'"):
                                        # Try parsing as JSON or Python dict
                                        try:
                                            return json.loads(response_text)
                                        except:
                                            try:
                                                return ast.literal_eval(response_text)
                                            except:
                                                response_fixed = response_text.replace("'", '"')
                                                return json.loads(response_fixed)
                                    elif response_text.startswith("Error:"):
                                        return {"status": "failed", "error": response_text}
                                    else:
                                        return {"status": "completed", "message": response_text}
                                except Exception as e:
                                    self.logger.error(f"Failed to parse A2A response: {e}")
                                    return {"status": "completed", "message": response_text}
                        return {"status": "completed", "result": message_result}
                    else:
                        return message_result
                elif "error" in result:
                    return {"status": "failed", "error": result["error"]}
                return result
            else:
                self.logger.error(f"A2A message failed with status {response.status_code}: {response.text}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            self.logger.error(f"Failed to send A2A message: {error_msg}")
            import traceback
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            return {"status": "failed", "error": error_msg}
    
    async def send_task(self, receiver_id: str, task_data: Dict[str, Any]) -> Optional[Dict]:
        """Send A2A task to another agent"""
        if receiver_id not in self.discovered_agents:
            self.logger.warning(f"A2A Agent {receiver_id} not found!")
            return None
        
        receiver_info = self.discovered_agents[receiver_id]
        
        self.console.print(
            f"📋 [green]{self.name}[/green] → [yellow]{receiver_info['name']}[/yellow]: A2A Task"
        )
        
        try:
            # Create A2A task
            task = Task(
                **task_data  # A2A SDK handles task structure
            )
            
            # Send via A2A client
            async with self.client as client:
                response = await client.create_task(
                    receiver_info['endpoint'],
                    task
                )
                return response
                
        except Exception as e:
            self.logger.error(f"Failed to send A2A task: {e}")
            return None
    
    @abstractmethod
    async def initialize(self):
        """Initialize agent-specific setup"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        pass
    
    @abstractmethod
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Process incoming A2A message"""
        pass
    
    @abstractmethod
    async def process_task(self, task: Task) -> TaskResponse:
        """Process incoming A2A task"""
        pass
    
    @abstractmethod
    async def perform_analysis(self, target: str) -> Dict[str, Any]:
        """Perform agent-specific analysis"""
        pass