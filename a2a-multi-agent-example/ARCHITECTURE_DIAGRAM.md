# Multi-Agent System Architecture Diagram

## System Overview
This is an A2A (Agent-to-Agent) Protocol-based multi-agent system for code quality analysis and development workflows, with end-to-end distributed tracing via OpenTelemetry.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           🚀 A2A Multi-Agent Orchestrator                       │
│                                 (a2a_main.py)                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Management Functions                              │ │
│  │ • Agent Initialization & Startup                                           │ │
│  │ • Agent Discovery Coordination                                             │ │
│  │ • Workflow Orchestration                                                   │ │
│  │ • Graceful Shutdown Management                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Initializes & Manages
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              🌐 Agent Network                                   │
│                            (A2A Protocol Communication)                         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
    
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   🔐 Security   │    │   📋 Code       │    │   📚 Documentation │  │   🎯 Dev Lead   │    │   👨‍💻 Developer  │
│   Scanner       │    │   Reviewer      │    │   Agent         │    │   Agent         │    │   Agent         │
│   Port: 8001    │    │   Port: 8002    │    │   Port: 8003    │    │   Port: 8005    │    │   Port: 8006    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Capabilities:   │    │ Capabilities:   │    │ Capabilities:   │    │ Capabilities:   │    │ Capabilities:   │
│ • Bandit Scan   │    │ • Pylint Analysis│   │ • Doc Coverage  │    │ • Task Planning │    │ • Code Generation│
│ • Semgrep Scan  │    │ • MyPy Analysis │    │ • AST Analysis  │    │ • Workflow Mgmt │    │ • AI-Powered    │
│ • Pattern Match │    │ • AST Analysis  │    │ • Quality Score │    │ • Team Coord    │    │ • Template Gen  │
│ • Vuln Report   │    │ • AI Code Review│    │ • Missing Docs  │    │ • Progress Track│    │ • Error Handling│
│                 │    │ • MCP Tools     │    │                 │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Tools:          │    │ Tools:          │    │ Tools:          │    │ Tools:          │    │ Tools:          │
│ • bandit        │    │ • pylint        │    │ • ast module    │    │ • Task Manager  │    │ • OpenAI GPT-4o │
│ • semgrep       │    │ • mypy          │    │ • File analysis │    │ • Rich UI       │    │ • Template Sys  │
│ • Custom Rules  │    │ • openai        │    │ • Report Gen    │    │ • Status Track  │    │ • File I/O      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          📡 Communication Layer                                  │
│                         (A2A Protocol + HTTP/JSON-RPC)                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Transport: HTTP POST with JSON-RPC 2.0                                         │
│ Discovery: /.well-known/agent-card.json endpoints                              │
│ Message Format: A2A Protocol standard (roles, parts, message_id)              │
│ Error Handling: JSON-RPC error responses                                       │
│ Timeout: 60 seconds per request                                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          🔍 Distributed Tracing Layer                           │
│                     (OpenTelemetry + Traceloop Integration)                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ • FastAPI Instrumentation: Automatic HTTP request/response tracing             │
│ • HTTPX Instrumentation: Outbound HTTP call tracing                            │
│ • Custom Context Builder: Preserves trace context across A2A calls             │
│ • Trace Propagation: W3C TraceContext headers (traceparent)                    │
│ • Export: Traceloop.com dashboard integration                                  │
│ • Unified trace_id across all agent communications                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Communication Flow Examples

### 1. Development Workflow
```
User Request
    ↓
🚀 Orchestrator
    ↓
🎯 Dev Lead Agent (Port 8005)
    ├─→ 👨‍💻 Developer Agent (Port 8006) [Code Generation]
    ├─→ 📋 Code Reviewer Agent (Port 8002) [Quality Review]
    ├─→ 🔐 Security Scanner (Port 8001) [Security Scan]
    └─→ 📚 Documentation Agent (Port 8003) [Doc Analysis]
    ↓
Final Report & Generated Code
```

### 2. Code Analysis Workflow
```
Target Code Repository
    ↓
🚀 Orchestrator (Sequential Analysis)
    ├─→ 🔐 Security Scanner (Port 8001)
    │   └─→ Vulnerability Report
    ├─→ 📋 Code Reviewer (Port 8002)
    │   └─→ Code Quality Report
    ├─→ 📚 Documentation Agent (Port 8003)
    │   └─→ Documentation Coverage Report
    └─→ Aggregated Results
```

### 3. A2A Message Flow (with Tracing)
```
Agent A (Sender)                          Agent B (Receiver)
    │                                          │
    │ 1. Create Span in current trace         │
    │ 2. Inject trace headers                 │
    │ 3. HTTP POST /                          │
    │    with traceparent header              │
    │ ─────────────────────────────────────────→
    │                                          │ 4. FastAPI receives request
    │                                          │ 5. FastAPI instrumentation 
    │                                          │    creates child span
    │                                          │ 6. Custom context builder
    │                                          │    preserves trace context
    │                                          │ 7. A2A handler processes
    │                                          │    message in same trace
    │                                          │ 8. Response generated
    │ ←─────────────────────────────────────────
    │ 9. Response processed in                 │
    │    original trace context               │
```

## Key Technical Features

### A2A Protocol Integration
- **Standard Compliance**: Full A2A Protocol v1.0 implementation
- **Agent Discovery**: Automatic peer discovery via well-known endpoints
- **Message Types**: Support for both messages and tasks
- **Error Handling**: JSON-RPC error responses with proper status codes

### Distributed Tracing
- **End-to-End Visibility**: Single trace_id across all agent communications
- **Custom Context Builder**: Preserves OpenTelemetry context in A2A handlers
- **FastAPI Integration**: Automatic HTTP instrumentation
- **Trace Propagation**: W3C TraceContext standard compliance
- **Export Integration**: Real-time trace export to Traceloop dashboard

### Agent Capabilities
- **Security Scanner**: Bandit, Semgrep, pattern matching for vulnerability detection
- **Code Reviewer**: Pylint, MyPy, AST analysis, AI-powered insights
- **Documentation Agent**: Coverage analysis, quality scoring, missing doc detection
- **Dev Lead Agent**: Workflow orchestration, task management, team coordination
- **Developer Agent**: AI-powered code generation using OpenAI GPT-4o-mini

### Infrastructure
- **Async Architecture**: Full asyncio support for concurrent operations
- **Graceful Shutdown**: Signal handling with proper resource cleanup
- **Error Recovery**: Timeout handling and retry mechanisms
- **Rich UI**: Comprehensive console output with progress tracking
- **Configuration**: Environment-based configuration for API keys and settings

## Workflow Patterns

### Development Lifecycle
1. **Task Creation**: Dev Lead creates development tasks
2. **Code Generation**: Developer Agent generates initial code
3. **Quality Gates**: Code Reviewer performs static analysis
4. **Security Validation**: Security Scanner checks for vulnerabilities  
5. **Documentation Check**: Documentation Agent validates coverage
6. **Integration**: Results aggregated and reported

### Trace Context Flow
1. **Orchestrator** creates root span with unique trace_id
2. **HTTP calls** propagate trace context via traceparent headers
3. **FastAPI instrumentation** automatically continues traces
4. **Custom context builder** preserves context for A2A handlers
5. **All operations** share the same trace_id for unified observability
6. **Export** to Traceloop provides end-to-end visibility

This architecture enables a fully distributed, traceable, and scalable multi-agent system for software development workflows.