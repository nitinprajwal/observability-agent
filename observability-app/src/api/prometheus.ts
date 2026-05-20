/**
 * Prometheus HTTP API client
 * Docs: https://prometheus.io/docs/prometheus/latest/querying/api/
 */

const BASE = '/api/prometheus';

export interface PrometheusResult {
  metric: Record<string, string>;
  value?: [number, string];
  values?: [number, string][];
}

export async function instantQuery(query: string): Promise<PrometheusResult[]> {
  try {
    const res = await fetch(
      `${BASE}/api/v1/query?query=${encodeURIComponent(query)}&time=${Math.floor(Date.now() / 1000)}`
    );
    if (!res.ok) return [];
    const data = await res.json();
    return data?.data?.result ?? [];
  } catch {
    return [];
  }
}

export async function rangeQuery(
  query: string,
  startSec: number,
  endSec: number,
  step = '60'
): Promise<PrometheusResult[]> {
  try {
    const params = new URLSearchParams({
      query,
      start: String(startSec),
      end: String(endSec),
      step,
    });
    const res = await fetch(`${BASE}/api/v1/query_range?${params}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data?.data?.result ?? [];
  } catch {
    return [];
  }
}

export async function getMetricNames(): Promise<string[]> {
  try {
    const res = await fetch(`${BASE}/api/v1/label/__name__/values`);
    if (!res.ok) return [];
    const data = await res.json();
    return data?.data ?? [];
  } catch {
    return [];
  }
}

// Check if Prometheus is reachable
export async function isReachable(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/-/healthy`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}
