import { useState, useEffect, useCallback } from 'react';
import { queryLogs, parseLogEntries, isReachable as lokiReachable, type LogEntry } from '../api/loki';

const now = () => Math.floor(Date.now() / 1000);
const ago = (s: number) => now() - s;

// Loki label names used by devopsai services.
// Loki 3.x OTLP ingestion promotes resource.service.name → service_name label.
export const LOKI_SERVICE_SELECTOR = '{service_name=~"devopsai.*"}';

export function useLogs(
  serviceSelector = LOKI_SERVICE_SELECTOR,
  windowSec = 1800,
  limit = 200,
  userId = ''
) {
  // Build effective query — filter by service AND optionally by user id in log body
  const effectiveQuery = userId
    ? `{service_name=~"devopsai.*"} |~ "(?i)(user_id|enduser|userId)[=:].*${userId}"`
    : serviceSelector;

  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState<boolean | null>(null);

  // Include effectiveQuery in deps so fetch re-creates when userId changes
  const doFetch = useCallback(async () => {
    const reachable = await lokiReachable();
    setConnected(reachable);
    if (!reachable) { setLoading(false); return; }
    const streams = await queryLogs(effectiveQuery, ago(windowSec), now(), limit);
    setLogs(parseLogEntries(streams));
    setLoading(false);
  }, [effectiveQuery, windowSec, limit]);

  useEffect(() => {
    doFetch();
    const id = setInterval(doFetch, 15_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { logs, loading, connected };
}

export function useLogVolume(windowSec = 3600, userId = '') {
  const [data, setData] = useState<{ time: string; info: number; warn: number; error: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const userFilter = userId
      ? ` |~ "(?i)(user_id|enduser|userId)[=:].*${userId}"`
      : '';
    const streams = await queryLogs(
      `${LOKI_SERVICE_SELECTOR}${userFilter}`,
      ago(windowSec), now(), 1000
    );
    const entries = parseLogEntries(streams);
    const buckets: Record<string, { info: number; warn: number; error: number }> = {};
    for (const e of entries) {
      const key = e.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      if (!buckets[key]) buckets[key] = { info: 0, warn: 0, error: 0 };
      if (e.level === 'error') buckets[key].error++;
      else if (e.level === 'warn') buckets[key].warn++;
      else buckets[key].info++;
    }
    const points = Object.entries(buckets)
      .map(([time, counts]) => ({ time, ...counts }))
      .slice(-24); // last 24 time buckets
    setData(points);
    setLoading(false);
  }, [windowSec, userId]);

  useEffect(() => {
    doFetch();
    const id = setInterval(doFetch, 30_000);
    return () => clearInterval(id);
  }, [doFetch]);

  return { data, loading };
}
