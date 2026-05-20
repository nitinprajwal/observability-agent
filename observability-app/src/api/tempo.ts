/**
 * Grafana Tempo HTTP API client
 * Docs: https://grafana.com/docs/tempo/latest/api_docs/
 *
 * DevOps AI services:
 *   devopsai-agent  — Python LangGraph agent (Bedrock + A2A)
 *   devopsai-app    — Next.js frontend API routes
 */

const BASE = '/api/tempo';

export interface TraceResult {
  traceID: string;
  rootServiceName: string;
  rootTraceName: string;
  startTimeUnixNano: string;
  durationMs: number;
  spanSet?: { spans: Span[] };
}

export interface Span {
  spanID: string;
  name: string;
  durationNanos: number;
  attributes?: Array<{ key: string; value: { stringValue?: string; intValue?: number } }>;
}

export async function searchTraces(
  service?: string,
  limit = 20,
  userId = ''
): Promise<TraceResult[]> {
  try {
    const params = new URLSearchParams({ limit: String(limit) });

    // Build a TraceQL query that filters by service and optionally user id.
    // Use =~ for service to support both old and new service naming.
    if (userId && service) {
      params.set('q', `{resource.service.name=~"${service}" && span.enduser.id="${userId}"}`);
    } else if (userId) {
      params.set('q', `{span.enduser.id="${userId}"}`);
    } else if (service) {
      // Match exact or prefix (devopsai-agent, devopsai-app)
      params.set('q', `{resource.service.name=~"${service}"}`);
    } else {
      // All devopsai services
      params.set('q', `{resource.service.namespace="devopsai"}`);
    }

    const res = await fetch(`${BASE}/api/v2/search?${params}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data?.traces ?? [];
  } catch {
    return [];
  }
}

export async function getTrace(traceId: string): Promise<unknown> {
  try {
    const res = await fetch(`${BASE}/api/traces/${traceId}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function isReachable(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/ready`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

