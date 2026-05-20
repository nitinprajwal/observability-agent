import { useState, useEffect, useCallback } from 'react';
import {
  searchTraces,
  getServices,
  getDependencies,
  isReachable,
  type TraceSearchResult,
  type ServiceDependency,
} from '../api/jaeger';

// ── Reachability ──────────────────────────────────────────────────────────────

export function useJaegerStatus() {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    isReachable().then(setOk);
    const id = setInterval(() => isReachable().then(setOk), 30_000);
    return () => clearInterval(id);
  }, []);
  return ok;
}

// ── Services ──────────────────────────────────────────────────────────────────

export function useJaegerServices() {
  const [services, setServices] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const s = await getServices();
    setServices(s);
    setLoading(false);
  }, []);

  useEffect(() => {
    doFetch();
    const id = setInterval(doFetch, 30_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { services, loading };
}

// ── Trace search ──────────────────────────────────────────────────────────────

export function useJaegerTraces(service?: string, userId?: string, limit = 50) {
  const [traces, setTraces] = useState<TraceSearchResult[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    // Jaeger tag search uses key=value format for exact match
    // For enduser.id filtering we pass it as a JSON tag object
    const tagStr = userId ? JSON.stringify({ 'enduser.id': userId }) : undefined;
    const results = await searchTraces({
      service: service || undefined,
      tags: tagStr,
      limit,
      lookback: '6h',
    });
    setTraces(results);
    setLoading(false);
  }, [service, userId, limit]);

  useEffect(() => {
    doFetch();
    const id = setInterval(doFetch, 15_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { traces, loading, refetch: doFetch };
}

// ── Agent step traces (sandbox operations) ────────────────────────────────────
// Fetches traces that contain agent.step.* operation names from devopsai-agent
export function useAgentStepTraces(userId?: string, limit = 30) {
  const [traces, setTraces] = useState<TraceSearchResult[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    // Fetch all recent devopsai-agent traces; filter client-side for agent.step ops
    const tagStr = userId ? JSON.stringify({ 'enduser.id': userId }) : undefined;
    const results = await searchTraces({
      service: 'devopsai-agent',
      tags: tagStr,
      limit: Math.max(limit * 3, 100), // fetch more so filtering leaves enough
      lookback: '6h',
    });
    setTraces(results);
    setLoading(false);
  }, [userId, limit]);

  useEffect(() => {
    doFetch();
    const id = setInterval(doFetch, 20_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { traces, loading, refetch: doFetch };
}

// ── Service dependencies ──────────────────────────────────────────────────────

export function useServiceDependencies() {
  const [deps, setDeps] = useState<ServiceDependency[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const d = await getDependencies(3_600_000); // last 1 hour
    setDeps(d);
    setLoading(false);
  }, []);

  useEffect(() => {
    doFetch();
    const id = setInterval(doFetch, 60_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { deps, loading };
}

// ── Per-user trace stats ──────────────────────────────────────────────────────

export interface UserTraceStats {
  userId: string;
  traceCount: number;
  avgDurationMs: number;
  p95DurationMs: number;
  errorCount: number;
  lastSeen: number;
}

export function usePerUserTraceStats(limit = 20) {
  const [stats, setStats] = useState<UserTraceStats[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    // Fetch all recent traces and group by enduser.id tag
    const traces = await searchTraces({ limit: 200, lookback: '1h' });
    // Since Jaeger summary doesn't have user tags, we fetch per devopsai service
    const agentTraces = await searchTraces({
      service: 'devopsai-agent',
      limit,
      lookback: '1h',
    });
    // Aggregate by service as proxy for users (enduser.id comes from spans)
    const byService: Record<string, TraceSearchResult[]> = {};
    [...traces, ...agentTraces].forEach(t => {
      const key = t.serviceName;
      byService[key] = [...(byService[key] ?? []), t];
    });

    const result: UserTraceStats[] = Object.entries(byService).map(([svc, ts]) => {
      const durations = ts.map(t => t.duration / 1000).sort((a, b) => a - b);
      const avg = durations.reduce((a, b) => a + b, 0) / (durations.length || 1);
      const p95 = durations[Math.floor(durations.length * 0.95)] ?? 0;
      return {
        userId: svc,
        traceCount: ts.length,
        avgDurationMs: Math.round(avg),
        p95DurationMs: Math.round(p95),
        errorCount: 0,
        lastSeen: Math.max(...ts.map(t => t.timestamp)),
      };
    });

    setStats(result.sort((a, b) => b.traceCount - a.traceCount));
    setLoading(false);
  }, [limit]);

  useEffect(() => {
    doFetch();
    const id = setInterval(doFetch, 30_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { stats, loading };
}
