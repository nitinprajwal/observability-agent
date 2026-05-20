"""
Custom waterfall trace exporter for visualizing agent interactions
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace import ReadableSpan

@dataclass
class WaterfallSpan:
    """Span data for waterfall visualization"""
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    name: str
    start_time: int
    end_time: int
    duration_ms: float
    attributes: Dict[str, str]
    agent_name: str = ""
    
    def __post_init__(self):
        # Extract agent name from attributes
        self.agent_name = (
            self.attributes.get("agent.sender", "") or 
            self.attributes.get("agent.receiver", "") or
            "Unknown"
        )

class WaterfallTraceExporter(SpanExporter):
    """Export spans and create waterfall visualization"""
    
    def __init__(self):
        self.console = Console()
        self.spans_by_trace: Dict[str, List[WaterfallSpan]] = {}
        self.completed_traces: set = set()
    
    def export(self, spans: List[ReadableSpan]) -> SpanExportResult:
        """Process and collect spans for waterfall display"""
        
        for span in spans:
            # Convert to waterfall span
            waterfall_span = WaterfallSpan(
                trace_id=format(span.context.trace_id, '032x'),
                span_id=format(span.context.span_id, '016x'),
                parent_id=format(span.parent.span_id, '016x') if span.parent else None,
                name=span.name,
                start_time=span.start_time,
                end_time=span.end_time,
                duration_ms=(span.end_time - span.start_time) / 1_000_000,  # Convert to ms
                attributes={k: str(v) for k, v in (span.attributes or {}).items()}
            )
            
            # Group by trace ID
            trace_id = waterfall_span.trace_id
            if trace_id not in self.spans_by_trace:
                self.spans_by_trace[trace_id] = []
            
            self.spans_by_trace[trace_id].append(waterfall_span)
            
            # Check if trace is complete (heuristic: has root span and multiple spans)
            trace_spans = self.spans_by_trace[trace_id]
            has_root = any(s.parent_id is None for s in trace_spans)
            has_multiple_spans = len(trace_spans) >= 3
            
            if has_root and has_multiple_spans and trace_id not in self.completed_traces:
                self.completed_traces.add(trace_id)
                self._print_waterfall(trace_id, trace_spans)
        
        return SpanExportResult.SUCCESS
    
    def _print_waterfall(self, trace_id: str, spans: List[WaterfallSpan]):
        """Print waterfall visualization for a complete trace"""
        
        # Sort spans by start time
        spans.sort(key=lambda s: s.start_time)
        
        # Find trace boundaries
        min_start = min(s.start_time for s in spans)
        max_end = max(s.end_time for s in spans)
        total_duration = (max_end - min_start) / 1_000_000  # Convert to ms
        
        self.console.print()
        self.console.print("=" * 100)
        self.console.print(f"🌊 [bold cyan]WATERFALL TRACE VIEW[/bold cyan] - Trace ID: {trace_id[:16]}...")
        self.console.print(f"📊 Total Duration: {total_duration:.2f}ms | Spans: {len(spans)}")
        self.console.print("=" * 100)
        
        # Create waterfall table
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Timeline", style="cyan", width=40)
        table.add_column("Agent", style="green", width=15)
        table.add_column("Operation", style="yellow", width=20)
        table.add_column("Duration", style="magenta", width=10)
        table.add_column("Details", style="dim", width=15)
        
        # Create visual timeline
        TIMELINE_WIDTH = 35
        
        for span in spans:
            # Calculate position and width in timeline
            start_offset = (span.start_time - min_start) / 1_000_000
            start_pos = int((start_offset / total_duration) * TIMELINE_WIDTH)
            duration_width = max(1, int((span.duration_ms / total_duration) * TIMELINE_WIDTH))
            
            # Create visual bar
            timeline_bar = " " * start_pos + "█" * duration_width
            timeline_bar = timeline_bar[:TIMELINE_WIDTH].ljust(TIMELINE_WIDTH)
            
            # Get operation type
            operation = self._get_operation_type(span)
            
            # Get additional details
            details = self._get_span_details(span)
            
            table.add_row(
                f"[cyan]{timeline_bar}[/cyan]",
                f"[green]{span.agent_name[:14]}[/green]",
                f"[yellow]{operation}[/yellow]",
                f"[magenta]{span.duration_ms:.1f}ms[/magenta]",
                f"[dim]{details}[/dim]"
            )
        
        self.console.print(table)
        
        # Create tree view showing span relationships
        self._print_span_tree(spans)
        
        self.console.print("=" * 100)
    
    def _get_operation_type(self, span: WaterfallSpan) -> str:
        """Extract operation type from span name and attributes"""
        name = span.name.lower()
        
        if "send_message" in name:
            return "📤 Send Msg"
        elif "handle_message" in name:
            return "📥 Handle Msg"  
        elif "post" in name and "/message" in span.attributes.get("http.target", ""):
            return "🌐 HTTP POST"
        elif "fastapi" in name:
            return "🚀 FastAPI"
        elif "openai" in name or "chat" in name:
            return "🤖 AI Call"
        elif "development" in name:
            return "👨‍💻 Develop"
        elif "review" in name:
            return "🔍 Review"
        else:
            return span.name[:15]
    
    def _get_span_details(self, span: WaterfallSpan) -> str:
        """Extract relevant details from span attributes"""
        details = []
        
        if "message.type" in span.attributes:
            details.append(span.attributes["message.type"][:8])
        
        if "http.status_code" in span.attributes:
            details.append(f"HTTP {span.attributes['http.status_code']}")
            
        if "agent.receiver" in span.attributes and span.attributes["agent.receiver"] != span.agent_name:
            details.append(f"→{span.attributes['agent.receiver'][:6]}")
        
        return " ".join(details)[:14]
    
    def _print_span_tree(self, spans: List[WaterfallSpan]):
        """Print tree view of span relationships"""
        
        # Build parent-child mapping
        children: Dict[Optional[str], List[WaterfallSpan]] = {}
        for span in spans:
            parent_id = span.parent_id
            if parent_id not in children:
                children[parent_id] = []
            children[parent_id].append(span)
        
        # Find root spans
        root_spans = children.get(None, [])
        if not root_spans:
            return
        
        self.console.print()
        self.console.print("🌳 [bold blue]Span Relationship Tree:[/bold blue]")
        
        tree = Tree("🔄 [bold]Multi-Agent Trace[/bold]")
        
        for root in root_spans:
            self._add_span_to_tree(tree, root, children, spans)
        
        self.console.print(tree)
    
    def _add_span_to_tree(self, parent_node, span: WaterfallSpan, children: Dict[Optional[str], List[WaterfallSpan]], all_spans: List[WaterfallSpan]):
        """Recursively add span and its children to tree"""
        
        operation = self._get_operation_type(span)
        node_text = f"[cyan]{span.agent_name}[/cyan] - {operation} ([magenta]{span.duration_ms:.1f}ms[/magenta])"
        
        if span.attributes.get("message.type"):
            node_text += f" - [yellow]{span.attributes['message.type']}[/yellow]"
        
        node = parent_node.add(node_text)
        
        # Add children
        span_children = children.get(span.span_id, [])
        for child in sorted(span_children, key=lambda s: s.start_time):
            self._add_span_to_tree(node, child, children, all_spans)
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any remaining spans"""
        return True
    
    def shutdown(self) -> None:
        """Shutdown the exporter"""
        pass