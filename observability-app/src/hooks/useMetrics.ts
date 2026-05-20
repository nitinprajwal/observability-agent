import { useState, useEffect, useCallback } from 'react';
import { rangeQuery, instantQuery, isReachable as promReachable, type PrometheusResult } from '../api/prometheus';

// Read userId from URL param (passed by DevOps AI sidebar when opening obs dashboard)
export function useCurrentUser(): string {
  return new URLSearchParams(window.location.search).get('userId') || '';
}

const now = () => Math.floor(Date.now() / 1000);
const ago = (seconds: number) => now() - seconds;

function labelValue(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function userMatcher(userId = ''): string {
  return userId ? `,enduser_id="${labelValue(userId)}"` : '';
}

export interface TimeSeriesPoint { time: string; value: number }

function parseTimeSeries(results: PrometheusResult[], labelKey?: string): Record<string, TimeSeriesPoint[]> {
  const out: Record<string, TimeSeriesPoint[]> = {};
  for (const r of results) {
    const key = labelKey ? (r.metric[labelKey] ?? 'unknown') : 'value';
    const points: TimeSeriesPoint[] = (r.values ?? (r.value ? [r.value] : [])).map(([ts, val]) => ({
      time: new Date(Number(ts) * 1000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      value: parseFloat(parseFloat(val).toFixed(3)),
    }));
    out[key] = points;
  }
  return out;
}

// ── HTTP request rate ──────────────────────────────────────────────────────────
// OTel Node.js HTTP instrumentation emits http.server.request.duration (histogram).
// With resource_to_telemetry_conversion=true and no Prometheus namespace, the
// metric becomes: http_server_request_duration_seconds_count
export function useRequestRate(windowSec = 3600) {
  const [data, setData] = useState<TimeSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    // Query both old and new OTel HTTP semconv metric names
    const results = await rangeQuery(
      // OTel Next.js uses old semconv: http_server_duration_milliseconds_count
      // Fall back to broad query without service_name filter if app hasn't connected yet
      `sum(rate(http_server_duration_milliseconds_count{service_name=~"devopsai.*"}[2m])) * 60
       or sum(rate(http_server_request_duration_seconds_count{service_name=~"devopsai.*"}[2m])) * 60
       or sum(rate(http_server_duration_milliseconds_count[2m])) * 60`,
      ago(windowSec), now(), '120'
    );
    const series = parseTimeSeries(results);
    setData(Object.values(series)[0] ?? []);
    setLoading(false);
  }, [windowSec]);

  useEffect(() => {doFetch(); const id = setInterval(doFetch, 30_000); return () => clearInterval(id); }, [doFetch]);
  return { data, loading };
}

// ── HTTP latency p50 / p95 / p99 ─────────────────────────────────────────────
export function useLatency(windowSec = 3600) {
  const [data, setData] = useState<{ time: string; p50: number; p95: number; p99: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    // Use old OTel semconv metric (actually present in Prometheus)
    const bucketMetric = 'http_server_duration_milliseconds_bucket{service_name=~"devopsai.*"}';
    const [p50r, p95r, p99r] = await Promise.all([
      rangeQuery(`histogram_quantile(0.50, sum(rate(${bucketMetric}[5m])) by (le)) * 1000`, ago(windowSec), now(), '120'),
      rangeQuery(`histogram_quantile(0.95, sum(rate(${bucketMetric}[5m])) by (le)) * 1000`, ago(windowSec), now(), '120'),
      rangeQuery(`histogram_quantile(0.99, sum(rate(${bucketMetric}[5m])) by (le)) * 1000`, ago(windowSec), now(), '120'),
    ]);
    const s50 = parseTimeSeries(p50r);
    const s95 = parseTimeSeries(p95r);
    const s99 = parseTimeSeries(p99r);
    const times = Object.values(s50)[0]?.map(p => p.time) ?? [];
    setData(times.map((time, i) => ({
      time,
      p50: Object.values(s50)[0]?.[i]?.value ?? 0,
      p95: Object.values(s95)[0]?.[i]?.value ?? 0,
      p99: Object.values(s99)[0]?.[i]?.value ?? 0,
    })));
    setLoading(false);
  }, [windowSec]);

  useEffect(() => {doFetch(); const id = setInterval(doFetch, 30_000); return () => clearInterval(id); }, [doFetch]);
  return { data, loading };
}

// ── LLM token usage ──────────────────────────────────────────────────────────
// OpenLLMetry (traceloop-sdk) emits gen_ai_client_token_usage with label
//   gen_ai_token_type="input"|"output"  (confirmed from Prometheus label inspection)
export function useTokenUsage(windowSec = 3600) {
  const [data, setData] = useState<{ time: string; input: number; output: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const [inputR, outputR] = await Promise.all([
      rangeQuery(
        `sum(increase(gen_ai_client_token_usage_sum{gen_ai_token_type="input"}[5m]))
         or sum(increase(gen_ai_client_token_usage_count{gen_ai_token_type="input"}[5m]))`,
        ago(windowSec), now(), '300'
      ),
      rangeQuery(
        `sum(increase(gen_ai_client_token_usage_sum{gen_ai_token_type="output"}[5m]))
         or sum(increase(gen_ai_client_token_usage_count{gen_ai_token_type="output"}[5m]))`,
        ago(windowSec), now(), '300'
      ),
    ]);
    const sIn = parseTimeSeries(inputR);
    const sOut = parseTimeSeries(outputR);
    const times = Object.values(sIn)[0]?.map(p => p.time) ?? Object.values(sOut)[0]?.map(p => p.time) ?? [];
    setData(times.map((time, i) => ({
      time,
      input: Object.values(sIn)[0]?.[i]?.value ?? 0,
      output: Object.values(sOut)[0]?.[i]?.value ?? 0,
    })));
    setLoading(false);
  }, [windowSec]);

  useEffect(() => {doFetch(); const id = setInterval(doFetch, 30_000); return () => clearInterval(id); }, [doFetch]);
  return { data, loading };
}

// ── LLM request count and duration ───────────────────────────────────────────
export function useLLMRequestStats(windowSec = 3600) {
  const [data, setData] = useState<{ time: string; count: number; durationMs: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const [countR, durR] = await Promise.all([
      rangeQuery(
        `sum(rate(gen_ai_client_operation_duration_seconds_count[5m])) * 300
         or sum(rate(llm_request_total[5m])) * 300`,
        ago(windowSec), now(), '300'
      ),
      rangeQuery(
        `histogram_quantile(0.95, sum(rate(gen_ai_client_operation_duration_seconds_bucket[5m])) by (le)) * 1000`,
        ago(windowSec), now(), '300'
      ),
    ]);
    const sCount = parseTimeSeries(countR);
    const sDur = parseTimeSeries(durR);
    const times = Object.values(sCount)[0]?.map(p => p.time) ?? [];
    setData(times.map((time, i) => ({
      time,
      count: Object.values(sCount)[0]?.[i]?.value ?? 0,
      durationMs: Object.values(sDur)[0]?.[i]?.value ?? 0,
    })));
    setLoading(false);
  }, [windowSec]);

  useEffect(() => {doFetch(); const id = setInterval(doFetch, 30_000); return () => clearInterval(id); }, [doFetch]);
  return { data, loading };
}

// ── Agent pipeline step counts ────────────────────────────────────────────────
// Python telemetry.py emits "agent_step_count" counter (no namespace prefix)
export function useAgentSteps(userId = '') {
  const [data, setData] = useState<{ step: string; count: number }[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const labels = `service_name="devopsai-agent"${userMatcher(userId)}`;
    const results = await instantQuery(
      `sort_desc(sum by (agent_step) (agent_step_count_total{${labels}}))`
    );
    const points = results.map(r => ({
      step: r.metric['agent_step'] ?? 'unknown',
      count: parseFloat(r.value?.[1] ?? '0'),
    }));
    setData(points);
    setLoading(false);
  }, [userId]);

  useEffect(() => {doFetch(); const id = setInterval(doFetch, 30_000); return () => clearInterval(id); }, [doFetch]);
  return { data, loading };
}

// ── API error rate ────────────────────────────────────────────────────────────
export function useErrorRate(windowSec = 3600) {
  const [data, setData] = useState<TimeSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const results = await rangeQuery(
      `sum(rate(http_server_duration_milliseconds_count{http_response_status_code=~"5..",service_name=~"devopsai.*"}[2m])) * 60
       or sum(rate(http_server_request_duration_seconds_count{http_response_status_code=~"5..",service_name=~"devopsai.*"}[2m])) * 60
       or vector(0)`,
      ago(windowSec), now(), '120'
    );
    const series = parseTimeSeries(results);
    setData(Object.values(series)[0] ?? []);
    setLoading(false);
  }, [windowSec]);

  useEffect(() => {doFetch(); const id = setInterval(doFetch, 30_000); return () => clearInterval(id); }, [doFetch]);
  return { data, loading };
}

// ── A2A delegation call count ─────────────────────────────────────────────────
export function useA2ACalls(windowSec = 3600, userId = '') {
  const [data, setData] = useState<TimeSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const labels = `service_name="devopsai-agent"${userMatcher(userId)}`;
    const results = await rangeQuery(
      `sum(increase(http_client_request_duration_seconds_count{url=~".*/a2a.*",${labels}}[5m]))
       or sum(increase(agent_step_count_total{agent_step="delegate_to_agent",${labels}}[5m]))
       or vector(0)`,
      ago(windowSec), now(), '300'
    );
    const series = parseTimeSeries(results);
    setData(Object.values(series)[0] ?? []);
    setLoading(false);
  }, [windowSec, userId]);

  useEffect(() => {doFetch(); const id = setInterval(doFetch, 30_000); return () => clearInterval(id); }, [doFetch]);
  return { data, loading };
}

// ── Backend connectivity ──────────────────────────────────────────────────────
export function useConnectionStatus() {
  const [connected, setConnected] = useState<boolean | null>(null);
  useEffect(() => {
    promReachable().then(setConnected);
    const id = setInterval(() => promReachable().then(setConnected), 15_000);
    return () => clearInterval(id);
  }, []);
  return connected;
}

export interface BackendStatus {
  prometheus: boolean | null;
  loki: boolean | null;
  tempo: boolean | null;
  grafana: boolean | null;
}

export function useAllBackendStatus(): BackendStatus {
  const [status, setStatus] = useState<BackendStatus>({
    prometheus: null, loki: null, tempo: null, grafana: null,
  });

  const check = useCallback(async () => {
    const [prom, loki, tempo, grafana] = await Promise.all([
      fetch('/api/prometheus/-/healthy', { signal: AbortSignal.timeout(3000) })
        .then(r => r.ok).catch(() => false),
      fetch('/api/loki/ready', { signal: AbortSignal.timeout(3000) })
        .then(r => r.ok).catch(() => false),
      fetch('/api/tempo/ready', { signal: AbortSignal.timeout(3000) })
        .then(r => r.ok).catch(() => false),
      // Grafana 200 or 401 (NitroNode auth required) both mean Grafana is up
      fetch('/api/grafana/api/health', { signal: AbortSignal.timeout(3000) })
        .then(r => r.ok || r.status === 401).catch(() => false),
    ]);
    setStatus({ prometheus: prom, loki, tempo, grafana });
  }, []);

  useEffect(() => {
    check();
    const id = setInterval(check, 15_000);
    return () => clearInterval(id);
  }, [check]);

  return status;
}

// ── Host metrics: CPU utilization (from hostmetrics receiver) ─────────────────
// system.cpu.utilization is a gauge exported by OTel hostmetrics scraper.
// With resource_to_telemetry_conversion=true it gets service.name labels.
export function useCPUUsage(windowSec = 1800) {
  const [data, setData] = useState<TimeSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const results = await rangeQuery(
      // Average CPU across all cores, exclude idle
      // OTel hostmetrics uses _ratio suffix (0-1 scale) not _utilization (0-100)
      `(1 - avg(system_cpu_utilization_ratio{state="idle"})) * 100
       or (1 - avg(system_cpu_time_seconds_total{state="idle"} / on() group_left sum(system_cpu_time_seconds_total))) * 100`,
      ago(windowSec), now(), '60'
    );
    const series = parseTimeSeries(results);
    setData(Object.values(series)[0] ?? []);
    setLoading(false);
  }, [windowSec]);

  useEffect(() => { doFetch(); const id = setInterval(doFetch, 15_000); return () => clearInterval(id); }, [doFetch]);
  return { data, loading };
}

// ── Host metrics: Memory utilization ─────────────────────────────────────────
export function useMemoryUsage(windowSec = 1800) {
  const [data, setData] = useState<TimeSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const results = await rangeQuery(
      // system.memory.utilization{state="used"} from hostmetrics
      // OTel hostmetrics: ratio metric, states are free/buffered/cached/slab_*
      // Approximate used = 1 - free - buffered - cached - slab_reclaimable
      `(1 - sum(system_memory_utilization_ratio{state=~"free|buffered|cached|slab_reclaimable"})) * 100
       or (1 - avg(system_memory_utilization_ratio{state="free"})) * 100`,
      ago(windowSec), now(), '60'
    );
    const series = parseTimeSeries(results);
    setData(Object.values(series)[0] ?? []);
    setLoading(false);
  }, [windowSec]);

  useEffect(() => { doFetch(); const id = setInterval(doFetch, 15_000); return () => clearInterval(id); }, [doFetch]);
  return { data, loading };
}

// ── Process metrics ───────────────────────────────────────────────────────────
// The OTel hostmetrics receiver runs inside the obs container and only sees the
// obs container's own processes (supervisord, otelcol-contrib, nginx).
// The devopsai-agent and devopsai-app run on the host machine and do NOT push
// their own process metrics via OTLP.
//
// Strategy: expose the otelcol-contrib process (the collector that receives all
// OTLP telemetry) as a proxy for "infrastructure CPU/mem", and derive agent
// activity from the agent_step_count and gen_ai metrics that the agent DOES emit.
export function useProcessMetrics(windowSec = 1800) {
  const [cpuData, setCpuData] = useState<Record<string, TimeSeriesPoint[]>>({});
  const [memData, setMemData] = useState<Record<string, TimeSeriesPoint[]>>({});
  // Agent activity derived from instrumentation metrics (not host process scraping)
  const [agentCallRate, setAgentCallRate] = useState<TimeSeriesPoint[]>([]);
  const [agentTokenRate, setAgentTokenRate] = useState<TimeSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const [cpuResults, memResults, callResults, tokenResults] = await Promise.all([
      // Collector process CPU (the only process visible from obs container)
      rangeQuery(
        `sum by (process_executable_name) (process_cpu_utilization_ratio{process_executable_name=~"otelcol.*|supervisord"}) * 100`,
        ago(windowSec), now(), '60'
      ),
      // Collector process memory in MB
      rangeQuery(
        `sum by (process_executable_name) (process_memory_usage_bytes{process_executable_name=~"otelcol.*|supervisord"}) / 1048576`,
        ago(windowSec), now(), '60'
      ),
      // Agent LLM call rate — real agent activity indicator
      rangeQuery(
        `sum(rate(gen_ai_client_operation_duration_seconds_count{service_name="devopsai-agent"}[5m])) * 300 or vector(0)`,
        ago(windowSec), now(), '300'
      ),
      // Agent token throughput (input + output tokens per 5m window)
      rangeQuery(
        `sum(increase(gen_ai_client_token_usage_sum{service_name="devopsai-agent"}[5m])) or vector(0)`,
        ago(windowSec), now(), '300'
      ),
    ]);
    setCpuData(parseTimeSeries(cpuResults, 'process_executable_name'));
    setMemData(parseTimeSeries(memResults, 'process_executable_name'));
    setAgentCallRate(Object.values(parseTimeSeries(callResults))[0] ?? []);
    setAgentTokenRate(Object.values(parseTimeSeries(tokenResults))[0] ?? []);
    setLoading(false);
  }, [windowSec]);

  useEffect(() => { doFetch(); const id = setInterval(doFetch, 15_000); return () => clearInterval(id); }, [doFetch]);
  return { cpuData, memData, agentCallRate, agentTokenRate, loading };
}

// ── Agent activity snapshot (current values for stat cards) ──────────────────
export function useAgentActivitySnapshot(userId = '') {
  const [llmCalls, setLlmCalls] = useState<number | null>(null);
  const [tokensIn, setTokensIn] = useState<number | null>(null);
  const [tokensOut, setTokensOut] = useState<number | null>(null);
  const [stepCount, setStepCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const doFetch = useCallback(async () => {
    const um = userMatcher(userId);
    const [llmR, inR, outR, stepsR] = await Promise.all([
      instantQuery(`sum(gen_ai_client_operation_duration_seconds_count{service_name="devopsai-agent"${um}}) or vector(0)`),
      instantQuery(`sum(gen_ai_client_token_usage_sum{gen_ai_token_type="input",service_name="devopsai-agent"${um}}) or vector(0)`),
      instantQuery(`sum(gen_ai_client_token_usage_sum{gen_ai_token_type="output",service_name="devopsai-agent"${um}}) or vector(0)`),
      instantQuery(`sum(agent_step_count_total{service_name="devopsai-agent"${um}}) or vector(0)`),
    ]);
    setLlmCalls(parseFloat(llmR[0]?.value?.[1] ?? '0'));
    setTokensIn(parseFloat(inR[0]?.value?.[1] ?? '0'));
    setTokensOut(parseFloat(outR[0]?.value?.[1] ?? '0'));
    setStepCount(parseFloat(stepsR[0]?.value?.[1] ?? '0'));
    setLoading(false);
  }, [userId]);

  useEffect(() => { doFetch(); const id = setInterval(doFetch, 15_000); return () => clearInterval(id); }, [doFetch]);
  return { llmCalls, tokensIn, tokensOut, stepCount, loading };
}

// ── Backend status including Jaeger ──────────────────────────────────────────
export function useAllBackendStatusWithJaeger() {
  const [status, setStatus] = useState<{
    prometheus: boolean | null;
    loki: boolean | null;
    tempo: boolean | null;
    grafana: boolean | null;
    jaeger: boolean | null;
  }>({ prometheus: null, loki: null, tempo: null, grafana: null, jaeger: null });

  const check = useCallback(async () => {
    const [prom, loki, tempo, grafana, jaeger] = await Promise.all([
      fetch('/api/prometheus/-/healthy', { signal: AbortSignal.timeout(3000) })
        .then(r => r.ok).catch(() => false),
      fetch('/api/loki/ready', { signal: AbortSignal.timeout(3000) })
        .then(r => r.ok).catch(() => false),
      fetch('/api/tempo/ready', { signal: AbortSignal.timeout(3000) })
        .then(r => r.ok).catch(() => false),
      fetch('/api/grafana/api/health', { signal: AbortSignal.timeout(3000) })
        .then(r => r.ok || r.status === 401).catch(() => false),
      fetch('/api/jaeger/', { signal: AbortSignal.timeout(3000) })
        .then(r => r.ok || r.status === 302 || r.status === 404).catch(() => false),
    ]);
    setStatus({ prometheus: prom, loki, tempo, grafana, jaeger });
  }, []);

  useEffect(() => { check(); const id = setInterval(check, 15_000); return () => clearInterval(id); }, [check]);
  return status;
}
