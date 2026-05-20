/**
 * Loki HTTP API client
 * Docs: https://grafana.com/docs/loki/latest/reference/api/
 *
 * Label strategy for DevOps AI OTLP logs:
 * Loki 3.x with otlp_config promotes service.name → service_name stream label.
 * The transform/logs processor in the OTel Collector copies severity_text →
 * attributes["level"], which Loki indexes as the "level" label.
 */

const BASE = '/api/loki';

export interface LokiStream {
  stream: Record<string, string>;
  values: [string, string][]; // [nanosecond_timestamp, log_line]
}

export interface LogEntry {
  timestamp: Date;
  level: string;
  service: string;
  message: string;
  labels: Record<string, string>;
  traceId?: string;
}

export async function queryLogs(
  logQuery: string,
  startSec: number,
  endSec: number,
  limit = 200
): Promise<LokiStream[]> {
  try {
    const params = new URLSearchParams({
      query: logQuery,
      start: String(Math.floor(startSec) * 1e9),
      end: String(Math.floor(endSec) * 1e9),
      limit: String(limit),
      direction: 'backward',
    });
    const res = await fetch(`${BASE}/loki/api/v1/query_range?${params}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data?.data?.result ?? [];
  } catch {
    return [];
  }
}

/**
 * Extract the log severity level from a Loki stream entry.
 *
 * Priority order:
 * 1. Stream labels: "level", "severity", "severity_text" (OTel OTLP promoted labels)
 * 2. Structured metadata / log attributes (OTel transform processor output)
 * 3. Keyword scan in the log body (fallback for unstructured logs)
 */
function extractLevel(stream: Record<string, string>, line: string): string {
  // 1. Check Loki stream labels (set by otlp_config or OTel transform processor)
  const labelLevel =
    stream['level'] ??
    stream['severity'] ??
    stream['severity_text'] ??
    stream['log.level'];

  if (labelLevel) {
    const l = labelLevel.toLowerCase();
    if (l.includes('error') || l.includes('fatal') || l.includes('critical')) return 'error';
    if (l.includes('warn')) return 'warn';
    if (l.includes('debug') || l.includes('trace')) return 'debug';
    return 'info';
  }

  // 2. Try to parse JSON body for structured log level field
  if (line.startsWith('{')) {
    try {
      const obj = JSON.parse(line) as Record<string, unknown>;
      const jsonLevel = (obj['level'] ?? obj['severity'] ?? obj['lvl'] ?? '') as string;
      if (jsonLevel) {
        const l = jsonLevel.toLowerCase();
        if (l.includes('error') || l.includes('fatal')) return 'error';
        if (l.includes('warn')) return 'warn';
        if (l.includes('debug') || l.includes('trace')) return 'debug';
        return 'info';
      }
    } catch { /* not valid JSON */ }
  }

  // 3. Keyword scan — last resort for plain-text logs
  const lower = line.toLowerCase();
  if (lower.includes('error') || lower.includes('exception') || lower.includes('fatal') || lower.includes('panic')) return 'error';
  if (lower.includes('warn')) return 'warn';
  if (lower.includes('debug') || lower.includes('trace')) return 'debug';
  return 'info';
}

/** Extract trace_id from log body or labels (enables Grafana trace→log linking). */
function extractTraceId(stream: Record<string, string>, line: string): string | undefined {
  if (stream['trace_id']) return stream['trace_id'];
  const match = line.match(/"trace_id"\s*:\s*"([0-9a-f]{32})"/i)
    ?? line.match(/trace_id=([0-9a-f]{32})/i)
    ?? line.match(/traceId[=:]([0-9a-f]{32})/i);
  return match?.[1];
}

export function parseLogEntries(streams: LokiStream[]): LogEntry[] {
  const entries: LogEntry[] = [];
  for (const stream of streams) {
    const service =
      stream.stream['service_name'] ??
      stream.stream['service.name'] ??
      stream.stream['job'] ??
      'unknown';

    for (const [ts, line] of stream.values) {
      entries.push({
        timestamp: new Date(Number(ts) / 1e6),
        level: extractLevel(stream.stream, line),
        service,
        message: line.slice(0, 500),
        labels: stream.stream,
        traceId: extractTraceId(stream.stream, line),
      });
    }
  }
  return entries.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
}

export async function isReachable(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/ready`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}
