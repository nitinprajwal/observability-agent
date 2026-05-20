import { useState, useEffect, useCallback } from 'react';
import { searchTraces, isReachable as tempoReachable, type TraceResult } from '../api/tempo';

export function useTraces(service?: string, limit = 20, userId = '') {
  const [traces, setTraces] = useState<TraceResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState<boolean | null>(null);

  // Include userId in deps so the query re-fires when user context changes
  const doFetch = useCallback(async () => {
    const reachable = await tempoReachable();
    setConnected(reachable);
    if (!reachable) { setLoading(false); return; }
    const results = await searchTraces(service, limit, userId);
    setTraces(results);
    setLoading(false);
  }, [service, limit, userId]);

  useEffect(() => {
    doFetch();
    const id = setInterval(doFetch, 20_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { traces, loading, connected };
}

export function useServiceTraces(userId = '') {
  // Both queries include userId so they refresh when user context changes
  const { traces: appTraces, loading: appLoading } = useTraces('devopsai-app', 10, userId);
  const { traces: agentTraces, loading: agentLoading } = useTraces('devopsai-agent', 10, userId);
  return {
    traces: [...appTraces, ...agentTraces]
      .sort((a, b) => Number(b.startTimeUnixNano) - Number(a.startTimeUnixNano))
      .slice(0, 20),
    loading: appLoading && agentLoading,
  };
}
