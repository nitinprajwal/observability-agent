# A2A Protocol Multi-Agent System

A comprehensive multi-agent system demonstrating **Agent-to-Agent (A2A) Protocol**, **OpenLLMetry tracing**, and **MCP integration** through realistic AI-powered development workflows. Built for conference demonstrations and production-ready distributed agent systems.

## 🎯 What This System Does

This system features **two powerful workflows** with specialized agents:

### 🔍 **Code Quality Analysis Workflow**
Three review agents collaborate to analyze existing code:
1. **Security Scanner Agent** - Scans for security vulnerabilities using tools like Bandit and Semgrep
2. **Code Reviewer Agent** - Analyzes code quality, complexity, and style using MCP tools and linters
3. **Documentation Agent** - Evaluates documentation coverage and quality

### 🚀 **A2A Development Workflow** (Featured!)
Five agents collaborate using **A2A Protocol** in a complete AI-powered development lifecycle:
1. **Dev Lead Agent** - Orchestrates development tasks and coordinates A2A communication
2. **Developer Agent** - 🤖 **Uses GPT-4o-mini** to generate high-quality Python code based on requirements
3. **Security Scanner Agent** - Reviews generated code for security vulnerabilities
4. **Code Reviewer Agent** - 🤖 **Uses GPT-4o-mini** to analyze code quality with MCP tools
5. **Documentation Agent** - Evaluates documentation coverage and quality

The agents use **authentic A2A Protocol** for discovery, authentication, and message passing, with full **cross-agent trace propagation** via OpenTelemetry.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- uv package manager (recommended) or pip

### Installation & Setup

```bash
# Clone or download this project
cd multi-agent-example

# Install with uv (recommended)
uv sync --dev

# OR install with pip
pip install -e .
```

### 🔑 API Keys Setup

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual API keys
# Required keys:
# - OPENAI_API_KEY=sk-your-openai-api-key-here  
# - TRACELOOP_API_KEY=tl_your-traceloop-api-key-here

# Get your keys from:
# - OpenAI: https://platform.openai.com/account/api-keys
# - Traceloop: https://app.traceloop.com/settings/api-keys
```

**Alternative: Export directly (temporary)**
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export TRACELOOP_API_KEY="your_traceloop_api_key_here"
```

### 🔧 Optional Tools

```bash
# Enhanced security scanning (optional)
uv add bandit semgrep

# Or with pip
pip install bandit semgrep
```

## 🚀 Running the A2A System

### Complete A2A Development Workflow

```bash
# Run the complete A2A multi-agent development demo
uv run python test_a2a_complete.py

# Or test with specific requirements
uv run python -c "
import asyncio
from multi_agent_example.a2a_main import A2AMultiAgentOrchestrator

async def main():
    orchestrator = A2AMultiAgentOrchestrator()
    await orchestrator.initialize()
    
    # Run development workflow
    result = await orchestrator.run_development_workflow(
        task_description='Create a secure authentication system',
        requirements=[
            'Implement JWT token authentication',
            'Add password hashing with bcrypt', 
            'Include rate limiting protection',
            'Add comprehensive error handling'
        ]
    )
    
    await orchestrator.shutdown()

asyncio.run(main())
"
```

### Test Traceloop Integration

```bash
# Set your Traceloop API key first
export TRACELOOP_API_KEY="your_key_here"

# Run with Traceloop export
uv run python test_traceloop_export.py

# Check dashboard at: https://app.traceloop.com
```

### Quick Development Test

```bash
# Test A2A system without Traceloop (uses demo key)
uv run python test_a2a_complete.py
```

## 🏗️ Architecture

### 🔗 A2A Protocol Architecture
- **Authentic A2A Protocol**: Uses official `a2a-sdk` for genuine agent-to-agent communication
- **Agent Discovery**: Automatic discovery via A2A endpoints (`/.well-known/agent-card.json`)
- **Message Passing**: JSON-RPC message format with proper A2A validation
- **RequestHandler**: Complete A2A RequestHandler implementation with proper method signatures
- **Agent Cards**: Full A2A AgentCard, AgentSkill, and AgentCapability definitions
- **Port Management**: Each agent runs on dedicated ports (8001-8006)

### 📊 OpenTelemetry Tracing & Observability
- **Cross-Agent Trace Propagation**: W3C Trace Context headers across HTTP requests
- **Traceloop Export**: Professional dashboard for trace visualization and analysis
- **FastAPI Instrumentation**: Automatic tracing of HTTP server requests/responses  
- **HTTPX Instrumentation**: Client-side HTTP request tracing
- **Custom Spans**: Business logic spans with agent names, operations, and metadata
- **Dashboard Waterfall**: Complete cross-agent request flow visualization

### MCP Integration
- Code Reviewer agent uses MCP tools for advanced analysis:
  - AST analyzer for code structure analysis  
  - Complexity calculator for cyclomatic complexity
  - Style checker for code formatting compliance
- Demonstrates protocol-based tool integration

## 🔧 Features

### 🤖 AI-Powered Development
- **GPT-4o-mini Code Generation**: Fast, cost-effective, high-quality Python code generation
- **AI Code Review**: Intelligent feedback on code quality, security, and best practices  
- **Smart Requirements Analysis**: AI understands and implements complex requirements
- **Contextual Suggestions**: AI provides specific, actionable improvement recommendations
- **Cost-Effective**: Uses GPT-4o-mini for optimal performance/cost balance

### Real-World Problem Solving
- **Security Analysis**: Detects SQL injection, XSS, hardcoded secrets, etc.
- **Code Quality**: Measures complexity, style compliance, maintainability
- **Documentation**: Analyzes docstring coverage and quality
- **Actionable Reports**: Prioritized improvement recommendations

### Agent Collaboration
- Agents share results and coordinate analysis phases
- Cross-referencing findings for comprehensive assessment
- Distributed decision making and result aggregation

### Observability
- Rich console output with progress indicators
- Detailed tracing of agent interactions
- Performance metrics and operation timings
- Visual result displays with tables and panels

## 📊 Sample Output

```
🧪 Testing Complete A2A Protocol Multi-Agent System
🌟 Demonstrating authentic Agent-to-Agent Protocol communication
================================================================================

🚀 A2A Multi-Agent System
🎯 Initializing Agent-to-Agent Protocol Communication

Traceloop exporting traces to https://api.traceloop.com authenticating with bearer token
✅ Traceloop SDK initialized
🚀 FastAPI instrumentation enabled
📡 HTTPX client instrumentation enabled
🔗 Cross-agent trace propagation activated
📊 Traces will be exported to Traceloop: https://api.traceloop.com
🔍 View traces at: https://app.traceloop.com

🤖 Initializing agents...
╭───────────────────────────── A2A Agent Startup ──────────────────────────────╮
│ 🤖 Agent Security Scanner initializing with A2A Protocol                     │
│ 📍 ID: security_scanner_2587bd69                                             │
│ 🌐 A2A Port: 8001                                                            │
│ 📋 Description: A2A-based security vulnerability scanner                     │
╰──────────────────────────────────────────────────────────────────────────────╯

                         🎭 A2A Agent Network Overview                          
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Agent               ┃ Port ┃ Capabilities                         ┃  Status  ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Security Scanner    │ 8001 │ vulnerability_scan, security_report  │ ● Active │
│ Code Reviewer Agent │ 8002 │ code_quality_review, ai_insights     │ ● Active │
│ Documentation Agent │ 8003 │ documentation_analysis               │ ● Active │
│ Dev Lead Agent      │ 8005 │ orchestrate_development_workflow     │ ● Active │
│ Developer Agent     │ 8006 │ generate_code, refactor_code         │ ● Active │
└─────────────────────┴──────┴──────────────────────────────────────┴──────────┘

🚀 Starting A2A Development Workflow...
╭──────────────────────── 🆕 Development Task task_185 ────────────────────────╮
│ 📋 Create a calculator function for A2A demo                                 │
│ ⚡ Priority: HIGH                                                            │
│ Requirements:                                                                │
│   • Create a function that can add, subtract, multiply, and divide           │
│   • Include proper error handling for division by zero                       │
│   • Add comprehensive docstring with examples                                │
│   • Use type hints for better code quality                                   │
╰──────────────────────────────────────────────────────────────────────────────╯

⚡ Phase 2: Code Generation
📤 Dev Lead Agent → Developer Agent: A2A Message
🧠 Sending request to GPT-4o-mini...
✅ Code generation completed successfully!

🔍 Phase 3: Multi-Agent Review
📤 Dev Lead Agent → Security Scanner: A2A Message
📤 Dev Lead Agent → Code Reviewer Agent: A2A Message
📤 Dev Lead Agent → Documentation Agent: A2A Message

================================================================================
🎉 A2A PROTOCOL MULTI-AGENT SYSTEM TEST SUCCESSFUL!
🚀 Ready for conference demonstration!
================================================================================

📊 A2A Workflow Results:
  ✅ Status: completed
  🔧 Workflow Phases: 4/4
  💻 Code Generated: ✅
  🔍 Agent Reviews: 3
  🎯 Final Assessment: GOOD

🌐 A2A Agent Network Status:
  • Active Agents: 5
  • A2A Protocol: ✅ Operational
  • Cross-Agent Tracing: ✅ Active
  • AI Integration: ✅ Available
```

## 🛠️ Configuration

### Environment Variables

**Recommended: Use .env file (automatically loaded)**
```bash
# Copy and edit the environment file
cp .env.example .env

# The .env file contains:
OPENAI_API_KEY=sk-your-openai-api-key-here
TRACELOOP_API_KEY=tl_your-traceloop-api-key-here
TRACELOOP_BASE_URL=https://api.traceloop.com
ENVIRONMENT=development
DEBUG=false
```

**Alternative: Export directly**
```bash
export OPENAI_API_KEY="your_openai_api_key"
export TRACELOOP_API_KEY="your_traceloop_api_key"
```

### A2A Agent Ports

- **Security Scanner**: 8001
- **Code Reviewer**: 8002  
- **Documentation Agent**: 8003
- **Dev Lead Agent**: 8005
- **Developer Agent**: 8006

### 📊 Traceloop Dashboard

Once running with `TRACELOOP_API_KEY`, visit **https://app.traceloop.com** to see:

- 🌊 **Trace Waterfall**: Complete cross-agent request flow visualization
- 📊 **Performance Metrics**: Request timing, duration, and throughput  
- 🔍 **Error Analysis**: Failed requests and exception tracking
- 📈 **Service Map**: Agent relationships and communication patterns
- 🎯 **Business Metrics**: Code generation success rates, review scores

### 🎯 What You'll See in Traceloop

With your API key configured, the dashboard will show:

- **📊 Service Map**: Visual network of your 5 A2A agents and their connections
- **🌊 Trace Waterfall**: Complete request flow from Dev Lead → Developer → Reviewers  
- **📈 Performance Metrics**: Request timing, spans per trace, success rates
- **🔍 Span Details**: Agent names, message types, business context attributes
- **🚨 Error Tracking**: Failed requests with stack traces and retry attempts

## 🎪 Conference Demo Features

This system was designed for conference presentations and includes:

### 🎯 **Authentic A2A Protocol Implementation**
- **Real A2A SDK**: Uses official `a2a-sdk`, not custom HTTP APIs
- **Complete Protocol**: Agent discovery, capability exchange, message validation
- **Production Ready**: Full RequestHandler implementation with proper error handling

### 🔍 **Comprehensive Tracing & Observability**
- **Cross-Agent Propagation**: W3C Trace Context headers across all agent communication
- **Traceloop Dashboard**: Professional waterfall visualization and service map
- **Real-time Monitoring**: See traces as they happen during demo
- **Business Context**: Spans include agent names, operations, and workflow stages

### 🤖 **AI-Powered Workflows**
- **GPT-4o-mini Integration**: Cost-effective, high-quality code generation and review
- **Realistic Use Cases**: Security scanning, code review, documentation analysis
- **Multi-Agent Collaboration**: Agents coordinate to solve complex development tasks
- **MCP Tool Integration**: Advanced code analysis with protocol-based tools

### 🎨 **Engaging Presentation Features**
- **Rich Visual Output**: Colorful tables, panels, and progress indicators
- **Live Agent Network**: Real-time display of active agents and their capabilities  
- **Interactive Workflows**: Watch AI agents collaborate in real-time
- **Conference Ready**: Professional output suitable for large screen projection

## 🔍 Technical Stack

- **A2A Protocol**: Official `a2a-sdk` for authentic agent communication
- **OpenTelemetry**: Industry standard distributed tracing
- **FastAPI**: Modern async HTTP framework for agent servers
- **Traceloop**: Professional trace visualization and analysis
- **Rich**: Beautiful terminal output with colors and formatting
- **OpenAI GPT-4o-mini**: Cost-effective AI for code generation and review
- **AsyncIO**: Concurrent agent operations and HTTP communication
- **Pydantic**: Data validation and serialization
- **MCP**: Model Context Protocol for advanced tool integration

## 🤝 Agent Capabilities

Each agent exposes its capabilities via REST API:

```bash
# List agent capabilities
curl http://localhost:8001/capabilities
curl http://localhost:8002/capabilities  
curl http://localhost:8003/capabilities

# Check agent health
curl http://localhost:8001/health
```

## 🚧 Extending the System

To add new agents:

1. Inherit from `BaseAgent`
2. Implement required abstract methods
3. Add to `CodeQualityOrchestrator.agent_classes`
4. Define capabilities and message handlers

Example agent skeleton:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("My Agent", 8004, "Does something useful")
    
    async def initialize(self):
        # Setup agent-specific resources
        pass
    
    def get_capabilities(self):
        return [AgentCapability(...)]
    
    async def process_message(self, message):
        # Handle incoming messages
        pass
    
    async def perform_analysis(self, target):
        # Main agent logic
        return {}
```

## 📝 License

MIT License - feel free to use this in your own projects and presentations!

## 🚀 Complete Setup Guide

### 1️⃣ **Installation**
```bash
git clone <this-repo>
cd multi-agent-example
uv sync --dev
```

### 2️⃣ **API Keys** 
```bash
# Copy and configure environment file
cp .env.example .env

# Edit .env file with your actual API keys:
# OPENAI_API_KEY=sk-your-key-here
# TRACELOOP_API_KEY=tl_your-key-here

# Get your keys from:
# - OpenAI: https://platform.openai.com/account/api-keys  
# - Traceloop: https://app.traceloop.com/settings/api-keys
```

### 3️⃣ **Run Complete Demo**
```bash
# Full A2A system with AI-powered development workflow
uv run python test_a2a_complete.py

# OR test Traceloop dashboard integration
uv run python test_traceloop_export.py
```

### 4️⃣ **View Results**
- **Console**: Rich visual output with A2A agent communication
- **Dashboard**: https://app.traceloop.com (shows cross-agent waterfall)

> **💡 Note**: The `.env` file is git-ignored for security. Each developer needs to create their own `.env` file with their API keys.

## 🎯 Perfect For

### 📚 **Conference Presentations**
- **Live Demo**: Watch AI agents collaborate in real-time
- **Visual Appeal**: Rich console output + professional dashboard
- **Technical Depth**: Real A2A Protocol + OpenTelemetry tracing
- **Audience Engagement**: Relatable AI-powered development workflow

### 🎓 **Educational Use**
- **Distributed Systems**: Agent communication patterns and discovery
- **Observability**: Cross-service tracing and monitoring  
- **AI Integration**: Practical GPT-4o-mini usage in multi-agent systems
- **Modern Protocols**: A2A, OpenTelemetry, MCP integration

### 🏢 **Production Insights**
- **Agent Architecture**: Scalable multi-agent system design
- **Trace Propagation**: W3C standards implementation
- **Error Handling**: Robust failure modes and recovery
- **Performance Monitoring**: Real-time observability patterns

---

## 🙋‍♂️ Questions?

This system demonstrates cutting-edge multi-agent architecture with:

✅ **Authentic A2A Protocol** (not toy HTTP APIs)  
✅ **Production-grade tracing** (OpenTelemetry + Traceloop)  
✅ **Real AI integration** (GPT-4o-mini for development workflows)  
✅ **Professional presentation** (Rich visuals + dashboard)

Perfect for **conference demonstrations**, **educational workshops**, and **production architecture examples**!