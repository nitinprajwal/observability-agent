/**
 * Jaeger Query API client
 * Docs: https://www.jaegertracing.io/docs/latest/apis/
 *
 * Jaeger runs with QUERY_BASE_PATH=/api/jaeger, so:
 *   UI  →  /api/jaeger/
 *   API →  /api/jaeger/api/services, /api/jaeger/api/traces, etc.
 *
 * nginx proxies /api/jaeger/* to Jaeger:16686 without stripping the prefix.
 */

const BASE = '/api/jaeger';
const API  = `${BASE}/api`;

export interface JaegerTrace {
  traceID: string;
  spans: JaegerSpan[];
  processes: Record<string, JaegerProcess>;
  warnings: string[] | null;
}

export interface JaegerSpan {
  traceID: string;
  spanID: string;
  operationName: string;
  references: Array<{ refType: string; traceID: string; spanID: string }>;
  startTime: number;   // microseconds
  duration: number;    // microseconds
  tags: JaegerTag[];
  logs: Array<{ timestamp: number; fields: JaegerTag[] }>;
  processID: string;
  warnings: string[] | null;
}

export interface JaegerProcess {
  serviceName: string;
  tags: JaegerTag[];
}

export interface JaegerTag {
  key: string;
  type: 'string' | 'bool' | 'int64' | 'float64';
  value: string | boolean | number;
}

export interface JaegerService {
  name: string;
}

export interface JaegerOperation {
  name: string;
  spanKind: string;
}

// ── Services ──────────────────────────────────────────────────────────────────

export async function getServices(): Promise<string[]> {
  try {
    const res = await fetch(`${API}/services`);
    if (!res.ok) return [];
    const data = await res.json();
    return data?.data ?? [];
  } catch {
    return [];
  }
}

// ── Trace search ──────────────────────────────────────────────────────────────

export interface TraceSearchParams {
  service?: string;
  operation?: string;
  tags?: string;          // e.g. 'enduser.id="user123"'
  start?: number;         // microseconds
  end?: number;           // microseconds
  minDuration?: string;   // e.g. '1ms'
  maxDuration?: string;
  limit?: number;
  lookback?: string;      // e.g. '1h', '24h'
}

export interface TraceSearchResult {
  traceID: string;
  spans: number;
  services: number;
  duration: number;       // microseconds
  timestamp: number;      // microseconds
  serviceName: string;
  operationName: string;
}

export async function searchTraces(params: TraceSearchParams = {}): Promise<TraceSearchResult[]> {
  try {
    const p = new URLSearchParams();
    if (params.service) p.set('service', params.service);
    if (params.operation) p.set('operation', params.operation);
    if (params.tags) p.set('tags', params.tags);
    if (params.limit) p.set('limit', String(params.limit));
    if (params.lookback) p.set('lookback', params.lookback);
    if (params.minDuration) p.set('minDuration', params.minDuration);
    if (params.start) p.set('start', String(params.start));
    if (params.end) p.set('end', String(params.end));

    const res = await fetch(`${API}/traces?${p}`);
    if (!res.ok) return [];
    const data = await res.json();

    // Flatten the nested trace format into a summary list
    const traces: JaegerTrace[] = data?.data ?? [];
    return traces.map(t => {
      const rootSpan = t.spans.find(s => s.references.length === 0) ?? t.spans[0];
      const process = t.processes?.[rootSpan?.processID ?? ''];
      return {
        traceID: t.traceID,
        spans: t.spans.length,
        services: Object.keys(t.processes ?? {}).length,
        duration: rootSpan?.duration ?? 0,
        timestamp: rootSpan?.startTime ?? 0,
        serviceName: process?.serviceName ?? 'unknown',
        operationName: rootSpan?.operationName ?? 'unknown',
      };
    });
  } catch {
    return [];
  }
}

// ── Single trace ──────────────────────────────────────────────────────────────

export async function getTrace(traceId: string): Promise<JaegerTrace | null> {
  try {
    const res = await fetch(`${API}/traces/${traceId}`);
    if (!res.ok) return null;
    const data = await res.json();
    return data?.data?.[0] ?? null;
  } catch {
    return null;
  }
}

// ── Service dependencies (service map) ───────────────────────────────────────

export interface ServiceDependency {
  parent: string;
  child: string;
  callCount: number;
}

export async function getDependencies(lookback = 3600000): Promise<ServiceDependency[]> {
  try {
    const endTs = Date.now();
    const p = new URLSearchParams({ endTs: String(endTs), lookback: String(lookback) });
    const res = await fetch(`${API}/dependencies?${p}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data?.data ?? [];
  } catch {
    return [];
  }
}

// ── Health check ──────────────────────────────────────────────────────────────

export async function isReachable(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/`, { signal: AbortSignal.timeout(3000) });
    return res.ok || res.status === 404; // 404 = Jaeger is up but path not found under QUERY_BASE_PATH
  } catch {
    return false;
  }
}
