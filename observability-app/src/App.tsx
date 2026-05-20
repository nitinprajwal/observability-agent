import { useState, useEffect } from 'react'
import LoadingScreen from './components/LoadingScreen'
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import {
  LayoutDashboard, Cpu, GitMerge, Brain, Terminal,
  FileText, Settings, HelpCircle, ChevronLeft, ChevronRight,
  RefreshCw, Activity, AlertCircle, CheckCircle, Circle,
  Search, Zap, Server, MemoryStick, Network, ExternalLink
} from 'lucide-react'
import { useRequestRate, useLatency, useTokenUsage, useAgentSteps, useCurrentUser, useAllBackendStatusWithJaeger, useErrorRate, useA2ACalls, useLLMRequestStats, useCPUUsage, useMemoryUsage, useProcessMetrics, useAgentActivitySnapshot } from './hooks/useMetrics'
import { useLogs, useLogVolume, LOKI_SERVICE_SELECTOR } from './hooks/useLogs'
import { useTraces, useServiceTraces } from './hooks/useTraces'
import { useJaegerTraces, useJaegerServices, useServiceDependencies, useJaegerStatus, usePerUserTraceStats, useAgentStepTraces } from './hooks/useJaeger'
import './App.css'

// ── Small helpers ─────────────────────────────────────────────────────────────

function StatusDot({ ok }: { ok: boolean | null }) {
  if (ok === null) return <Circle size={8} className="text-gray-400 animate-pulse" />
  return ok
    ? <CheckCircle size={12} className="text-green-500" />
    : <AlertCircle size={12} className="text-red-400" />
}

interface NitronodeUserStats {
  conversationCount: number
  agentEvents?: {
    total_events: string
    tool_calls: string
    errors: string
    last_activity: string | null
  }
}

function useNitronodeUserStats(userId: string) {
  const [stats, setStats] = useState<NitronodeUserStats | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    fetch('/api/nitronode/api/obs/user-stats', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => setStats(data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }, [userId])

  return { stats, loading }
}

function EmptyState({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-40 gap-2 text-gray-400">
      <Activity size={24} className="opacity-40" />
      <p className="text-sm font-medium">{title}</p>
      {subtitle && <p className="text-xs opacity-70">{subtitle}</p>}
    </div>
  )
}

function ChartCard({ title, children, loading }: { title: string; children: React.ReactNode; loading?: boolean }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        {loading && <RefreshCw size={12} className="text-gray-400 animate-spin" />}
      </div>
      {children}
    </div>
  )
}

const COLORS = { blue: '#3B82F6', purple: '#8B5CF6', green: '#10B981', yellow: '#F59E0B', red: '#EF4444', teal: '#14B8A6' }

const TABS = [
  { id: 'overview',   label: 'Overview',       icon: LayoutDashboard },
  { id: 'pipeline',   label: 'Agent Pipeline', icon: Cpu },
  { id: 'a2a',        label: 'A2A Flows',      icon: GitMerge },
  { id: 'llm',        label: 'LLM Usage',      icon: Brain },
  { id: 'traces',     label: 'Traces (Jaeger)',icon: Zap },
  { id: 'resources',  label: 'Resources',      icon: Server },
  { id: 'sandbox',    label: 'Sandbox',        icon: Terminal },
  { id: 'logs',       label: 'Logs',           icon: FileText },
]

const NAV = [
  { id: 'overview',   label: 'Overview',       icon: LayoutDashboard },
  { id: 'pipeline',   label: 'Agent Pipeline', icon: Cpu },
  { id: 'llm',        label: 'LLM Usage',      icon: Brain, badge: 'Live' },
  { id: 'traces',     label: 'Traces',         icon: Zap, badge: 'New' },
  { id: 'resources',  label: 'Resources',      icon: Server },
  { id: 'a2a',        label: 'A2A Flows',      icon: GitMerge },
  { id: 'sandbox',    label: 'Sandbox',        icon: Terminal },
  { id: 'logs',       label: 'Logs',           icon: FileText },
]

// ── Tab components ─────────────────────────────────────────────────────────────

function BackendStatusCard() {
  const status = useAllBackendStatusWithJaeger()
  const services = [
    { name: 'OTel Collector', ok: status.prometheus, hint: 'collector + prometheus' },
    { name: 'Loki', ok: status.loki, hint: 'log storage' },
    { name: 'Tempo', ok: status.tempo, hint: 'trace storage' },
    { name: 'Jaeger', ok: status.jaeger, hint: 'distributed tracing UI' },
    { name: 'Grafana', ok: status.grafana, hint: 'dashboards' },
  ]
  const allOk = Object.values(status).every(v => v === true)
  const anyNull = Object.values(status).some(v => v === null)
  return (
    <ChartCard title="Backend Status">
      <div className="flex flex-col gap-2 py-1">
        {services.map(svc => (
          <div key={svc.name} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg">
            <div>
              <span className="text-sm font-medium text-gray-700">{svc.name}</span>
              <span className="text-xs text-gray-400 ml-1.5">{svc.hint}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <StatusDot ok={svc.ok} />
              <span className={`text-xs font-medium ${svc.ok === true ? 'text-green-600' : svc.ok === false ? 'text-red-500' : 'text-gray-400'}`}>
                {svc.ok === null ? 'checking…' : svc.ok ? 'online' : 'offline'}
              </span>
            </div>
          </div>
        ))}
        {!anyNull && (
          <div className={`text-xs text-center py-1.5 rounded-lg font-medium ${allOk ? 'text-green-700 bg-green-50' : 'text-yellow-700 bg-yellow-50'}`}>
            {allOk ? '✓ All backends online — run `make obs` to start' : '⚠ Some backends offline — run `make obs`'}
          </div>
        )}
      </div>
    </ChartCard>
  )
}

function OverviewTab() {
  const { data: reqData, loading: reqLoading } = useRequestRate()
  const { data: latData, loading: latLoading } = useLatency()
  const { data: errData, loading: errLoading } = useErrorRate()
  const userId = useCurrentUser()
  const { stats: userStats, loading: userStatsLoading } = useNitronodeUserStats(userId)

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-4">
        <ChartCard title="Requests per Minute" loading={reqLoading}>
          {reqData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={reqData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="value" fill={COLORS.blue} name="req/min" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No request data yet" subtitle="Make API requests to see metrics" />}
        </ChartCard>

        <ChartCard title="Response Latency (ms)" loading={latLoading}>
          {latData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={latData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Line type="monotone" dataKey="p50" stroke={COLORS.blue} dot={false} name="p50" />
                <Line type="monotone" dataKey="p95" stroke={COLORS.yellow} dot={false} name="p95" />
                <Line type="monotone" dataKey="p99" stroke={COLORS.red} dot={false} name="p99" />
              </LineChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No latency data yet" subtitle="Latency metrics appear after first requests" />}
        </ChartCard>

        <BackendStatusCard />
      </div>

      {userId && (
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Persisted Conversations', value: userStats?.conversationCount ?? 0 },
            { label: 'Persisted AG-UI Events', value: userStats?.agentEvents?.total_events ?? '0' },
            { label: 'Persisted Tool Calls', value: userStats?.agentEvents?.tool_calls ?? '0' },
            { label: 'Persisted Errors', value: userStats?.agentEvents?.errors ?? '0' },
          ].map(item => (
            <div key={item.label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <p className="text-xs text-gray-500">{item.label}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{userStatsLoading ? '…' : item.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Error rate */}
      <div className="grid grid-cols-2 gap-4">
        <ChartCard title="5xx Error Rate (errors/min)" loading={errLoading}>
          {errData.length > 0 ? (
            <ResponsiveContainer width="100%" height={120}>
              <AreaChart data={errData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 9 }} tickLine={false} />
                <YAxis tick={{ fontSize: 9 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ fontSize: 11 }} />
                <Area type="monotone" dataKey="value" stroke={COLORS.red} fill={COLORS.red} fillOpacity={0.2} name="errors/min" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No errors" subtitle="5xx HTTP errors appear here" />}
        </ChartCard>

        {/* Quick Grafana embed link */}
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex flex-col justify-between">
          <div>
            <p className="text-sm font-semibold text-blue-800">Full Grafana Dashboard</p>
            <p className="text-xs text-blue-600 mt-0.5">
              {userId ? `Viewing as user ${userId.slice(0, 8)}… — your traces, logs, and metrics` : 'Explore traces, metrics, and logs with full Grafana power'}
            </p>
          </div>
          <a
            href={`/api/grafana/d/nitronode-user-obs${userId ? `?var-user_id=${encodeURIComponent(userId)}&kiosk` : '/'}`}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors text-center"
          >
            Open Grafana →
          </a>
        </div>
      </div>

      {/* Observability Stack — clickable backend cards */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Observability Stack</p>
        <div className="grid grid-cols-4 gap-3">
          {[
            {
              name: 'Grafana',
              emoji: '📊',
              desc: 'Dashboards · service maps · user-level view',
              url: `/api/grafana/d/nitronode-user-obs${userId ? `?var-user_id=${encodeURIComponent(userId)}` : '/'}`,
              urlLabel: 'Open Dashboard',
              bg: 'bg-orange-50',
              border: 'border-orange-100',
              badge: 'bg-orange-100 text-orange-700',
            },
            {
              name: 'Prometheus',
              emoji: '⚡',
              desc: 'Metrics · scrape :8889 · PromQL queries',
              url: '/api/prometheus/-/healthy',
              urlLabel: 'Health check',
              bg: 'bg-red-50',
              border: 'border-red-100',
              badge: 'bg-red-100 text-red-700',
            },
            {
              name: 'Loki',
              emoji: '📋',
              desc: 'OTLP logs · service_name labels · LogQL',
              url: '/api/loki/ready',
              urlLabel: 'Health check',
              bg: 'bg-yellow-50',
              border: 'border-yellow-100',
              badge: 'bg-yellow-100 text-yellow-700',
            },
            {
              name: 'Tempo',
              emoji: '🔍',
              desc: 'Distributed traces · TraceQL · spans',
              url: '/api/tempo/ready',
              urlLabel: 'Health check',
              bg: 'bg-purple-50',
              border: 'border-purple-100',
              badge: 'bg-purple-100 text-purple-700',
            },
          ].map(svc => (
            <div
              key={svc.name}
              className={`${svc.bg} border ${svc.border} rounded-xl p-4 flex flex-col gap-2`}
            >
              <div className="flex items-center justify-between">
                <span className="text-base">{svc.emoji}</span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${svc.badge}`}>
                  {svc.name}
                </span>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{svc.desc}</p>
              <a
                href={svc.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-medium text-blue-600 hover:underline mt-auto"
              >
                {svc.urlLabel} →
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function PipelineTab() {
  const userId = useCurrentUser()
  const { data: steps, loading } = useAgentSteps(userId)
  const { traces, loading: tracesLoading } = useTraces('devopsai-agent', 15, userId)

  const stepData = steps.map(step => ({
    step: step.step.replace(/_/g, ' '),
    count: step.count,
  }))

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        <ChartCard title="Pipeline Step Executions" loading={loading}>
          {steps.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={stepData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="step" tick={{ fontSize: 10 }} width={110} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="count" fill={COLORS.purple} radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No pipeline executions yet" subtitle="Run the agent to see pipeline steps" />}
        </ChartCard>

        <ChartCard title="Recent Agent Traces" loading={tracesLoading}>
          {traces.length > 0 ? (
            <div className="flex flex-col divide-y divide-gray-50 overflow-y-auto max-h-52">
              {traces.slice(0, 8).map(t => (
                <div key={t.traceID} className="flex items-center justify-between py-2 text-xs">
                  <div className="flex flex-col gap-0.5">
                    <span className="font-medium text-gray-700 truncate max-w-48">{t.rootTraceName || 'agent run'}</span>
                    <span className="text-gray-400">{t.rootServiceName}</span>
                  </div>
                  <span className={`font-mono px-2 py-0.5 rounded ${t.durationMs > 5000 ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                    {t.durationMs?.toFixed(0) ?? '?'}ms
                  </span>
                </div>
              ))}
            </div>
          ) : <EmptyState title="No traces yet" subtitle="Agent executions appear here" />}
        </ChartCard>
      </div>
    </div>
  )
}

function LLMTab() {
  const { data: tokenData, loading } = useTokenUsage()
  const { data: llmStats, loading: statsLoading } = useLLMRequestStats()
  const userId = useCurrentUser()
  const { traces, loading: tracesLoading } = useTraces('devopsai-agent', 20, userId)

  const bedrock = traces.filter(t => t.rootTraceName?.toLowerCase().includes('bedrock') || t.rootServiceName === 'devopsai-agent')

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        <ChartCard title="Token Usage — 5 min windows" loading={loading}>
          {tokenData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={tokenData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Area type="monotone" dataKey="input" stackId="1" stroke={COLORS.blue} fill={COLORS.blue} fillOpacity={0.2} name="Input tokens" />
                <Area type="monotone" dataKey="output" stackId="1" stroke={COLORS.purple} fill={COLORS.purple} fillOpacity={0.2} name="Output tokens" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No LLM token data yet" subtitle="Token counts appear after Bedrock calls complete" />}
        </ChartCard>

        <ChartCard title="LLM Request Rate + p95 Latency" loading={statsLoading}>
          {llmStats.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={llmStats}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis yAxisId="left" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} unit="ms" />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Line yAxisId="left" type="monotone" dataKey="count" stroke={COLORS.blue} dot={false} name="Calls/5min" />
                <Line yAxisId="right" type="monotone" dataKey="durationMs" stroke={COLORS.purple} dot={false} name="p95 latency" />
              </LineChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No LLM request data yet" subtitle="Bedrock call latency + rate appear here" />}
        </ChartCard>
      </div>

      <ChartCard title="Recent Bedrock Call Traces" loading={tracesLoading}>
        {bedrock.length > 0 ? (
          <div className="flex flex-col divide-y divide-gray-50 overflow-y-auto max-h-48">
            {bedrock.slice(0, 8).map(t => (
              <div key={t.traceID} className="flex items-center justify-between py-2 text-xs">
                <div className="flex flex-col gap-0.5">
                  <span className="font-medium text-gray-700 truncate max-w-56">{t.rootTraceName || 'bedrock call'}</span>
                  <span className="text-gray-400">{new Date(Number(t.startTimeUnixNano) / 1e6).toLocaleTimeString()}</span>
                </div>
                <span className={`font-mono px-2 py-0.5 rounded ${(t.durationMs ?? 0) > 10000 ? 'bg-red-50 text-red-600' : 'bg-purple-50 text-purple-600'}`}>
                  {t.durationMs?.toFixed(0) ?? '?'}ms
                </span>
              </div>
            ))}
          </div>
        ) : <EmptyState title="No Bedrock traces yet" subtitle="LLM calls will appear here once OpenLLMetry instruments them" />}
      </ChartCard>

      <div className="bg-purple-50 border border-purple-100 rounded-xl p-4">
        <p className="text-sm font-semibold text-purple-800 mb-1">💡 LLM Intelligence</p>
        {tokenData.some(d => d.input > 5000) ? (
          <p className="text-xs text-purple-700">High input token usage detected. Consider prompt compression in the planning step to reduce costs.</p>
        ) : (
          <p className="text-xs text-purple-600">
            Token usage is tracked via OpenLLMetry (traceloop-sdk). Metric: <code className="font-mono bg-purple-100 px-1 rounded">gen_ai_client_token_usage_total</code>.
            Send agent requests to see LLM usage insights.
          </p>
        )}
      </div>
    </div>
  )
}

function A2ATab() {
  const userId = useCurrentUser()
  const { traces: allTraces, loading } = useServiceTraces(userId)
  const { data: a2aCalls, loading: a2aLoading } = useA2ACalls(3600, userId)
  const a2aTraces = allTraces.filter(t =>
    t.rootTraceName?.toLowerCase().includes('a2a') ||
    t.rootTraceName?.toLowerCase().includes('delegate') ||
    t.rootTraceName?.toLowerCase().includes('agent')
  )

  return (
    <div className="flex flex-col gap-4">
      {/* A2A call rate chart */}
      <ChartCard title="A2A Delegation Calls (5 min windows)" loading={a2aLoading}>
        {a2aCalls.length > 0 ? (
          <ResponsiveContainer width="100%" height={140}>
            <AreaChart data={a2aCalls.map((d, i) => ({ time: String(i), value: d.value }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="time" tick={{ fontSize: 9 }} tickLine={false} />
              <YAxis tick={{ fontSize: 9 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ fontSize: 11 }} />
              <Area type="monotone" dataKey="value" stroke={COLORS.teal} fill={COLORS.teal} fillOpacity={0.2} name="A2A calls" />
            </AreaChart>
          </ResponsiveContainer>
        ) : <EmptyState title="No A2A calls recorded yet" subtitle="Register agents and make delegations to see call patterns" />}
      </ChartCard>

      <ChartCard title="All Service Traces" loading={loading}>
        {allTraces.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-500 border-b border-gray-100">
                  <th className="text-left py-2 font-medium">Trace</th>
                  <th className="text-left py-2 font-medium">Service</th>
                  <th className="text-left py-2 font-medium">Started</th>
                  <th className="text-right py-2 font-medium">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {allTraces.slice(0, 12).map(t => (
                  <tr key={t.traceID} className="hover:bg-gray-50">
                    <td className="py-2 font-medium text-blue-600 truncate max-w-48">{t.rootTraceName || t.traceID.slice(0, 12)}</td>
                    <td className="py-2 text-gray-600">{t.rootServiceName}</td>
                    <td className="py-2 text-gray-500">{new Date(Number(t.startTimeUnixNano) / 1e6).toLocaleTimeString()}</td>
                    <td className="py-2 text-right font-mono">
                      <span className={`px-1.5 py-0.5 rounded ${(t.durationMs ?? 0) > 3000 ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                        {t.durationMs?.toFixed(0) ?? '?'}ms
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <EmptyState title="No traces yet" subtitle="devopsai-agent and devopsai-app traces appear here" />}
      </ChartCard>

      {a2aTraces.length === 0 && (
        <div className="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-6 text-center">
          <GitMerge size={24} className="mx-auto text-gray-300 mb-2" />
          <p className="text-sm text-gray-500">Register A2A agents and make inter-agent calls to see flow visualizations here.</p>
          <p className="text-xs text-gray-400 mt-1">A2A HTTP calls are auto-instrumented via HTTPXClientInstrumentor.</p>
        </div>
      )}
    </div>
  )
}

function SandboxTab() {
  const userId = useCurrentUser()
  // Use Jaeger (not Tempo) — all agent traces go to Jaeger
  const { traces, loading, refetch } = useAgentStepTraces(userId || undefined, 50)

  // Categorise traces by operation type
  const fileOps = traces.filter(t => {
    const n = t.operationName.toLowerCase()
    return n.includes('write_file') || n.includes('read_file') || n.includes('edit_file') ||
           n.includes('list_files') || n.includes('delete_file') || n.includes('find_files')
  })
  const shellOps = traces.filter(t => {
    const n = t.operationName.toLowerCase()
    return n.includes('execute_command') || n.includes('execute_tool execute_command')
  })
  const agentStepOps = traces.filter(t =>
    t.operationName.toLowerCase().includes('agent.step')
  )

  // Group by operation name for the bar chart
  const opCounts: Record<string, number> = {}
  traces.forEach(t => {
    const key = t.operationName.replace('execute_tool ', '').replace('agent.step.', '')
    opCounts[key] = (opCounts[key] ?? 0) + 1
  })
  const opChartData = Object.entries(opCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([op, count]) => ({ op: op.replace(/_/g, ' '), count }))

  const JAEGER_BASE = '/api/jaeger'

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-3">
        {[
          {
            label: 'Traced Operations',
            value: String(traces.length),
            sub: userId ? `user ${userId.slice(0, 8)}… (last 6h)` : 'all users · last 6h',
            color: 'blue',
          },
          {
            label: 'Shell Commands',
            value: String(shellOps.length),
            sub: 'execute_command traced',
            color: 'green',
          },
          {
            label: 'File Operations',
            value: String(fileOps.length),
            sub: 'read/write/edit traced',
            color: 'purple',
          },
        ].map(s => (
          <div key={s.label} className={`bg-${s.color}-50 border border-${s.color}-100 rounded-xl p-4`}>
            <p className={`text-xs text-${s.color}-600 font-medium`}>{s.label}</p>
            <p className={`text-2xl font-bold text-${s.color}-700 mt-1`}>{loading ? '…' : s.value}</p>
            <p className={`text-xs text-${s.color}-500 mt-0.5`}>{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Operation frequency bar chart */}
      {opChartData.length > 0 && (
        <ChartCard title="Operation Frequency (last 6h)" loading={loading}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={opChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="op" tick={{ fontSize: 10 }} width={130} />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" fill={COLORS.teal} radius={[0, 3, 3, 0]} name="executions" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {/* Detailed trace table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-50">
          <h3 className="text-sm font-semibold text-gray-700">Sandbox Operation Traces</h3>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">{traces.length} traces · via Jaeger</span>
            <button onClick={refetch} className="p-1 hover:bg-gray-50 rounded">
              <RefreshCw size={12} className={loading ? 'animate-spin text-gray-400' : 'text-gray-500'} />
            </button>
          </div>
        </div>
        {traces.length > 0 ? (
          <div className="overflow-x-auto max-h-72 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-white border-b border-gray-100">
                <tr className="text-gray-500">
                  <th className="text-left px-4 py-2 font-medium">Operation</th>
                  <th className="text-right px-4 py-2 font-medium">Spans</th>
                  <th className="text-right px-4 py-2 font-medium">Duration</th>
                  <th className="text-left px-4 py-2 font-medium">Time</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {traces.slice(0, 30).map(t => {
                  const isShell = t.operationName.toLowerCase().includes('execute_command')
                  const isFile = t.operationName.toLowerCase().includes('file')
                  const badge = isShell ? 'bg-green-50 text-green-700' : isFile ? 'bg-blue-50 text-blue-700' : 'bg-gray-50 text-gray-600'
                  return (
                    <tr key={t.traceID} className="hover:bg-gray-50">
                      <td className="px-4 py-2">
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${badge}`}>
                          {t.operationName.replace('execute_tool ', '').replace('agent.step.', '')}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-right text-gray-500">{t.spans}</td>
                      <td className="px-4 py-2 text-right font-mono">
                        <span className={`px-1.5 py-0.5 rounded ${t.duration > 5_000_000 ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                          {t.duration > 1_000_000 ? `${(t.duration / 1_000_000).toFixed(1)}s` : `${(t.duration / 1000).toFixed(0)}ms`}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-gray-400">{t.timestamp ? new Date(t.timestamp / 1000).toLocaleTimeString() : '—'}</td>
                      <td className="px-4 py-2">
                        <a href={`${JAEGER_BASE}/trace/${t.traceID}`} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-700">
                          <ExternalLink size={11} />
                        </a>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title={loading ? 'Loading traces…' : 'No sandbox operations traced yet'}
            subtitle="Run the agent to execute commands (write_file, execute_command, etc.) and see traces here"
          />
        )}
      </div>

      {agentStepOps.length === 0 && !loading && traces.length === 0 && (
        <div className="bg-amber-50 border border-amber-100 rounded-xl p-4">
          <p className="text-sm font-semibold text-amber-800 mb-1">💡 How to populate this tab</p>
          <p className="text-xs text-amber-700">
            Ask the DevOps AI agent to run a command or edit a file. Each tool call creates an
            <code className="font-mono bg-amber-100 px-1 rounded mx-1">agent.step.*</code> span
            that appears here in real-time.
          </p>
        </div>
      )}
    </div>
  )
}

function LogsTab() {
  const [search, setSearch] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const userId = useCurrentUser()
  const { logs, loading, connected } = useLogs(LOKI_SERVICE_SELECTOR, 3600, 300, userId)
  const { data: volumeData, loading: volLoading } = useLogVolume(3600, userId)

  const filtered = logs.filter(l => {
    if (levelFilter !== 'all' && l.level !== levelFilter) return false
    if (search && !l.message.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const LEVEL_COLORS: Record<string, string> = {
    error: 'bg-red-100 text-red-700',
    warn: 'bg-yellow-100 text-yellow-700',
    info: 'bg-blue-100 text-blue-700',
    debug: 'bg-gray-100 text-gray-600',
  }

  return (
    <div className="flex flex-col gap-4">
      <ChartCard title="Log Volume" loading={volLoading}>
        {volumeData.length > 0 ? (
          <ResponsiveContainer width="100%" height={120}>
            <AreaChart data={volumeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="time" tick={{ fontSize: 9 }} tickLine={false} />
              <YAxis tick={{ fontSize: 9 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ fontSize: 11 }} />
              <Area type="monotone" dataKey="info" stackId="1" stroke={COLORS.blue} fill={COLORS.blue} fillOpacity={0.3} name="Info" />
              <Area type="monotone" dataKey="warn" stackId="1" stroke={COLORS.yellow} fill={COLORS.yellow} fillOpacity={0.4} name="Warn" />
              <Area type="monotone" dataKey="error" stackId="1" stroke={COLORS.red} fill={COLORS.red} fillOpacity={0.5} name="Error" />
            </AreaChart>
          </ResponsiveContainer>
        ) : <EmptyState title="No log data" subtitle={connected === false ? "Loki unreachable — start make obs" : "Logs appear after services send telemetry"} />}
      </ChartCard>

      <div className="flex gap-2 items-center">
        <input
          type="text" placeholder="Search logs…" value={search} onChange={e => setSearch(e.target.value)}
          className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200"
        />
        <select
          value={levelFilter} onChange={e => setLevelFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 bg-white"
        >
          <option value="all">All levels</option>
          <option value="error">Error</option>
          <option value="warn">Warn</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
        </select>
        {loading && <RefreshCw size={14} className="text-gray-400 animate-spin" />}
        {connected !== null && (
          <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-gray-50 text-xs">
            <StatusDot ok={connected} />
            <span className="text-gray-500">{connected ? 'Loki connected' : 'Loki offline'}</span>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        {filtered.length > 0 ? (
          <div className="overflow-x-auto max-h-80 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-white border-b border-gray-100">
                <tr className="text-gray-500">
                  <th className="text-left px-3 py-2 font-medium">Time</th>
                  <th className="text-left px-3 py-2 font-medium">Level</th>
                  <th className="text-left px-3 py-2 font-medium">Service</th>
                  <th className="text-left px-3 py-2 font-medium">Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.slice(0, 100).map((log, i) => (
                  <tr key={i} className="hover:bg-gray-50 font-mono">
                    <td className="px-3 py-1.5 text-gray-400 whitespace-nowrap">{log.timestamp.toLocaleTimeString()}</td>
                    <td className="px-3 py-1.5">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-semibold ${LEVEL_COLORS[log.level] ?? 'bg-gray-100 text-gray-600'}`}>
                        {log.level.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-3 py-1.5 text-blue-600 whitespace-nowrap">{log.service}</td>
                    <td className="px-3 py-1.5 text-gray-700 max-w-md truncate">{log.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title={logs.length > 0 ? 'No logs match filter' : 'No logs yet'}
            subtitle={logs.length > 0 ? 'Clear search or change level filter' : 'Start make obs and run NitroNode to see logs'}
          />
        )}
      </div>
    </div>
  )
}

// ── TracesTab (Jaeger) ────────────────────────────────────────────────────────

function TracesTab() {
  const userId = useCurrentUser()
  const [selectedService, setSelectedService] = useState('devopsai-agent')
  const [searchQuery, setSearchQuery] = useState('')
  const jaegerOk = useJaegerStatus()
  const { services } = useJaegerServices()
  const { traces, loading, refetch } = useJaegerTraces(selectedService, userId || undefined, 50)
  const { deps, loading: depsLoading } = useServiceDependencies()
  const { stats: userStats } = usePerUserTraceStats(20)

  const filtered = traces.filter(t =>
    !searchQuery ||
    t.operationName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.traceID.includes(searchQuery)
  )

  // Build service dependency graph data for recharts
  const depData = deps.map(d => ({ name: `${d.parent} → ${d.child}`, calls: d.callCount }))
    .sort((a, b) => b.calls - a.calls).slice(0, 10)

  const JAEGER_BASE = '/api/jaeger'

  return (
    <div className="flex flex-col gap-4">

      {/* Jaeger status + open link */}
      <div className={`flex items-center justify-between p-3 rounded-xl border ${jaegerOk ? 'bg-green-50 border-green-100' : jaegerOk === false ? 'bg-red-50 border-red-100' : 'bg-gray-50 border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <StatusDot ok={jaegerOk} />
          <span className="text-sm font-medium text-gray-700">Jaeger Tracing</span>
          {jaegerOk && <span className="text-xs text-green-600">Connected</span>}
          {jaegerOk === false && <span className="text-xs text-red-600">Unavailable — run <code>make obs</code></span>}
        </div>
        {jaegerOk && (
          <a href={`${JAEGER_BASE}/`} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 font-medium">
            <ExternalLink size={12} /> Open Full Jaeger UI
          </a>
        )}
      </div>

      {/* Service filter + search */}
      <div className="flex gap-3">
        <select
          value={selectedService}
          onChange={e => setSelectedService(e.target.value)}
          className="flex-shrink-0 text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-200"
        >
          <option value="">All services</option>
          {services.map(s => <option key={s} value={s}>{s}</option>)}
          {!services.length && (
            <>
              <option value="devopsai-agent">devopsai-agent</option>
              <option value="devopsai-app">devopsai-app</option>
            </>
          )}
        </select>
        <div className="flex-1 flex items-center gap-2 border border-gray-200 rounded-lg px-3 py-2 bg-white">
          <Search size={14} className="text-gray-400" />
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search operation name or trace ID…"
            className="flex-1 text-sm outline-none"
          />
        </div>
        <button onClick={refetch} className="px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50">
          <RefreshCw size={14} className={loading ? 'animate-spin text-gray-400' : 'text-gray-600'} />
        </button>
      </div>

      {/* Traces table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-50">
          <h3 className="text-sm font-semibold text-gray-700">Recent Traces</h3>
          <span className="text-xs text-gray-400">{filtered.length} traces</span>
        </div>
        {filtered.length === 0 ? (
          <EmptyState title={loading ? 'Loading traces…' : 'No traces found'} subtitle={jaegerOk ? 'Run the agent to generate traces' : 'Start the observability stack first'} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-500 bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-4 py-2 font-medium">Trace ID</th>
                  <th className="text-left px-4 py-2 font-medium">Service</th>
                  <th className="text-left px-4 py-2 font-medium">Operation</th>
                  <th className="text-right px-4 py-2 font-medium">Spans</th>
                  <th className="text-right px-4 py-2 font-medium">Duration</th>
                  <th className="text-left px-4 py-2 font-medium">Time</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.slice(0, 30).map(t => (
                  <tr key={t.traceID} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-blue-600">{t.traceID.slice(0, 12)}…</td>
                    <td className="px-4 py-2 text-gray-600">{t.serviceName}</td>
                    <td className="px-4 py-2 text-gray-700 max-w-48 truncate">{t.operationName}</td>
                    <td className="px-4 py-2 text-right text-gray-600">{t.spans}</td>
                    <td className="px-4 py-2 text-right font-mono">
                      <span className={`px-1.5 py-0.5 rounded ${t.duration > 5_000_000 ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                        {t.duration > 1_000_000 ? `${(t.duration / 1_000_000).toFixed(1)}s` : `${(t.duration / 1000).toFixed(0)}ms`}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-400">
                      {t.timestamp ? new Date(t.timestamp / 1000).toLocaleTimeString() : '—'}
                    </td>
                    <td className="px-4 py-2">
                      <a href={`${JAEGER_BASE}/trace/${t.traceID}`} target="_blank" rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800">
                        <ExternalLink size={12} />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Service dependency chart */}
      <div className="grid grid-cols-2 gap-4">
        <ChartCard title="Service Call Counts (last 1h)" loading={depsLoading}>
          {depData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={depData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 9 }} width={120} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="calls" fill={COLORS.purple} radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No dependency data yet" subtitle="Traces will populate this chart" />}
        </ChartCard>

        {/* Per-user trace count */}
        <ChartCard title="Traces per Service">
          {userStats.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={userStats.slice(0, 8)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="userId" tick={{ fontSize: 9 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="traceCount" fill={COLORS.teal} radius={[3, 3, 0, 0]} name="Traces" />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No per-service data yet" />}
        </ChartCard>
      </div>
    </div>
  )
}

// ── ResourcesTab ──────────────────────────────────────────────────────────────

function ResourcesTab() {
  const { data: cpuData, loading: cpuLoading } = useCPUUsage()
  const { data: memData, loading: memLoading } = useMemoryUsage()
  const { cpuData: procCpu, memData: procMem, agentCallRate, agentTokenRate, loading: procLoading } = useProcessMetrics()
  const userId = useCurrentUser()
  const { llmCalls, tokensIn, tokensOut, stepCount, loading: activityLoading } = useAgentActivitySnapshot(userId)

  // Collector process series (otelcol-contrib is the only meaningful one)
  const collectorCpuSeries = Object.entries(procCpu).filter(([k]) => k.includes('otelcol'))
  const collectorMemSeries = Object.entries(procMem).filter(([k]) => k.includes('otelcol'))

  const mergedCollectorCpu = (() => {
    if (!collectorCpuSeries.length) return []
    const pts = collectorCpuSeries[0][1]
    return pts.map(p => ({ time: p.time, 'OTel Collector': p.value }))
  })()

  const mergedCollectorMem = (() => {
    if (!collectorMemSeries.length) return []
    const pts = collectorMemSeries[0][1]
    return pts.map(p => ({ time: p.time, 'OTel Collector': p.value }))
  })()

  return (
    <div className="flex flex-col gap-4">

      {/* Per-user agent activity — derived from instrumentation, not process scraping */}
      {userId && (
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
          <p className="text-sm font-semibold text-blue-800 mb-1 flex items-center gap-2">
            <Network size={14} /> User Context
          </p>
          <p className="text-xs text-blue-600">
            Showing activity for user <code className="bg-blue-100 px-1 rounded">{userId.slice(0, 12)}…</code>.
            CPU and memory are reported at the process level for the OTel Collector (the obs container).
            Agent activity is derived from Bedrock call metrics and agent step counters emitted by devopsai-agent.
          </p>
        </div>
      )}

      {/* Agent activity stat cards — real data from Prometheus */}
      <div className="grid grid-cols-4 gap-3">
        {[
          {
            label: 'CPU Series',
            value: cpuData.length > 0 ? `${cpuData[cpuData.length-1]?.value?.toFixed(1) ?? 0}%` : '—',
            icon: Cpu, color: 'red',
            sub: 'Host system CPU',
          },
          {
            label: 'Memory',
            value: memData.length > 0 ? `${memData[memData.length-1]?.value?.toFixed(1) ?? 0}%` : '—',
            icon: MemoryStick, color: 'blue',
            sub: 'Host system memory',
          },
          {
            label: 'Agent LLM Calls',
            value: activityLoading ? '…' : llmCalls != null ? String(Math.round(llmCalls)) : '—',
            icon: Server, color: 'purple',
            sub: userId ? `user ${userId.slice(0,8)}…` : 'all users (total)',
          },
          {
            label: 'Agent Tool Steps',
            value: activityLoading ? '…' : stepCount != null ? String(Math.round(stepCount)) : '—',
            icon: Zap, color: 'teal',
            sub: userId ? `user ${userId.slice(0,8)}…` : 'all users (total)',
          },
        ].map(s => (
          <div key={s.label} className={`bg-${s.color}-50 border border-${s.color}-100 rounded-xl p-4`}>
            <div className="flex items-center gap-2 mb-2">
              <s.icon size={14} className={`text-${s.color}-600`} />
              <p className={`text-xs text-${s.color}-600 font-medium`}>{s.label}</p>
            </div>
            <p className={`text-2xl font-bold text-${s.color}-700`}>{s.value}</p>
            <p className={`text-xs text-${s.color}-400 mt-1`}>{s.sub}</p>
          </div>
        ))}
      </div>

      {/* Token throughput */}
      {(tokensIn != null || tokensOut != null) && (
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
            <p className="text-xs text-indigo-600 font-medium mb-1">Total Input Tokens</p>
            <p className="text-2xl font-bold text-indigo-700">{activityLoading ? '…' : tokensIn != null ? Math.round(tokensIn).toLocaleString() : '—'}</p>
            <p className="text-xs text-indigo-400 mt-1">Bedrock input token sum</p>
          </div>
          <div className="bg-violet-50 border border-violet-100 rounded-xl p-4">
            <p className="text-xs text-violet-600 font-medium mb-1">Total Output Tokens</p>
            <p className="text-2xl font-bold text-violet-700">{activityLoading ? '…' : tokensOut != null ? Math.round(tokensOut).toLocaleString() : '—'}</p>
            <p className="text-xs text-violet-400 mt-1">Bedrock output token sum</p>
          </div>
        </div>
      )}

      {/* Host-level CPU and memory charts */}
      <div className="grid grid-cols-2 gap-4">
        <ChartCard title="Host CPU Utilization (%)" loading={cpuLoading}>
          {cpuData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={cpuData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} domain={[0, 100]} unit="%" />
                <Tooltip contentStyle={{ fontSize: 12 }} formatter={(v) => [`${Number(v).toFixed(1)}%`, 'CPU']} />
                <Area type="monotone" dataKey="value" stroke={COLORS.red} fill={COLORS.red} fillOpacity={0.2} name="CPU %" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No CPU data yet" subtitle="Hostmetrics collector populates this after startup" />}
        </ChartCard>

        <ChartCard title="Host Memory Utilization (%)" loading={memLoading}>
          {memData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={memData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} domain={[0, 100]} unit="%" />
                <Tooltip contentStyle={{ fontSize: 12 }} formatter={(v) => [`${Number(v).toFixed(1)}%`, 'Memory']} />
                <Area type="monotone" dataKey="value" stroke={COLORS.blue} fill={COLORS.blue} fillOpacity={0.2} name="Memory %" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No memory data yet" subtitle="OTel hostmetrics populates this after startup" />}
        </ChartCard>
      </div>

      {/* Agent LLM call rate + token rate over time */}
      <div className="grid grid-cols-2 gap-4">
        <ChartCard title="Agent LLM Calls (5 min windows)" loading={procLoading}>
          {agentCallRate.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={agentCallRate}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="value" fill={COLORS.purple} radius={[3,3,0,0]} name="Bedrock calls" />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No agent call data" subtitle="Agent LLM call rate appears here after requests" />}
        </ChartCard>

        <ChartCard title="Agent Token Throughput (5 min)" loading={procLoading}>
          {agentTokenRate.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={agentTokenRate}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="value" stroke={COLORS.teal} fill={COLORS.teal} fillOpacity={0.2} name="Tokens" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No token data" subtitle="Token throughput appears after Bedrock calls" />}
        </ChartCard>
      </div>

      {/* OTel Collector process metrics (the only host-visible process from obs container) */}
      <div className="grid grid-cols-2 gap-4">
        <ChartCard title="OTel Collector CPU (%)" loading={procLoading}>
          {mergedCollectorCpu.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={mergedCollectorCpu}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} unit="%" />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="OTel Collector" stroke={COLORS.yellow} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No collector CPU data" subtitle="OTel Collector process metrics appear after startup" />}
        </ChartCard>

        <ChartCard title="OTel Collector Memory (MB)" loading={procLoading}>
          {mergedCollectorMem.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={mergedCollectorMem}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} unit="MB" />
                <Tooltip contentStyle={{ fontSize: 12 }} formatter={(v) => [`${Number(v).toFixed(0)} MB`, 'Memory']} />
                <Area type="monotone" dataKey="OTel Collector" stroke={COLORS.green} fill={COLORS.green} fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No collector memory data" subtitle="OTel Collector process metrics appear after startup" />}
        </ChartCard>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-xl p-3">
        <p className="text-xs text-gray-500">
          <strong>Note:</strong> devopsai-agent and devopsai-app run on the host machine and do not expose
          process-level CPU/memory via OTLP. Agent activity is measured via Bedrock instrumentation metrics
          (LLM calls, token counts, step counters). Host metrics are from the OTel hostmetrics receiver
          inside the observability container.
        </p>
      </div>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  const currentUserId = useCurrentUser()
  const [initializing, setInitializing] = useState(true)
  useEffect(() => {
    // 3.5s loading screen — enough time for backends to connect and for UX
    const t = setTimeout(() => setInitializing(false), 3500)
    return () => clearTimeout(t)
  }, [])

  const [activeTab, setActiveTab] = useState('overview')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  // Global refresh ticker for display
  useEffect(() => {
    const id = setInterval(() => setLastRefresh(new Date()), 30000)
    return () => clearInterval(id)
  }, [])

  const TAB_COMPONENTS: Record<string, React.ReactNode> = {
    overview:  <OverviewTab />,
    pipeline:  <PipelineTab />,
    a2a:       <A2ATab />,
    llm:       <LLMTab />,
    traces:    <TracesTab />,
    resources: <ResourcesTab />,
    sandbox:   <SandboxTab />,
    logs:      <LogsTab />,
  }

  const activeNav = NAV.find(n => n.id === activeTab)

  if (initializing) {
    return (
      <LoadingScreen
        message="Starting Devops AI Observability"
        subtitle="Connecting to Prometheus · Loki · Tempo · Grafana…"
      />
    )
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans">
      {/* ── Sidebar ─────────────────────────────────────────────────────────── */}
      <aside className={`flex flex-col bg-gray-900 text-white transition-all duration-200 ${sidebarOpen ? 'w-56' : 'w-14'} flex-shrink-0`}>
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-4 py-4 border-b border-gray-800">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Activity size={14} className="text-white" />
          </div>
          {sidebarOpen && <span className="font-bold text-sm tracking-tight">Devops AI Observability</span>}
        </div>

        {/* Nav items */}
        <nav className="flex-1 py-3 flex flex-col gap-0.5 px-2">
          {NAV.map(item => {
            const Icon = item.icon
            const active = activeTab === item.id
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition-colors w-full text-left ${
                  active ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <Icon size={16} className="flex-shrink-0" />
                {sidebarOpen && (
                  <span className="flex-1 truncate">{item.label}</span>
                )}
                {sidebarOpen && 'badge' in item && (
                  <span className="text-xs bg-blue-500 text-white px-1.5 py-0.5 rounded-full">{item.badge}</span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Bottom */}
        <div className="border-t border-gray-800 py-3 px-2 flex flex-col gap-0.5">
          {[{ id: 'settings', label: 'Settings', icon: Settings }, { id: 'support', label: 'Support', icon: HelpCircle }].map(item => {
            const Icon = item.icon
            return (
              <button key={item.id} className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm text-gray-500 hover:text-white hover:bg-gray-800 transition-colors w-full text-left">
                <Icon size={15} className="flex-shrink-0" />
                {sidebarOpen && <span className="truncate">{item.label}</span>}
              </button>
            )
          })}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm text-gray-600 hover:text-white hover:bg-gray-800 transition-colors w-full"
          >
            {sidebarOpen ? <ChevronLeft size={15} /> : <ChevronRight size={15} />}
            {sidebarOpen && <span className="text-xs">Collapse</span>}
          </button>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-100 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div>
            <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-0.5">
              <span>Observability</span>
              <span>›</span>
              <span className="text-gray-600 font-medium">{activeNav?.label ?? 'Overview'}</span>
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-bold text-gray-900">{activeNav?.label ?? 'Overview'}</h1>
              {currentUserId && (
                <span className="text-xs bg-blue-50 text-blue-600 border border-blue-100 px-2.5 py-1 rounded-full font-medium">
                  👤 User: {currentUserId.slice(0, 8)}…
                </span>
              )}
              {!currentUserId && (
                <span className="text-xs bg-gray-50 text-gray-400 border border-gray-200 px-2.5 py-1 rounded-full">
                  All users
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400">
              Refreshed {lastRefresh.toLocaleTimeString()}
            </span>
            <button
              onClick={() => setLastRefresh(new Date())}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <RefreshCw size={12} />
              Refresh
            </button>
          </div>
        </header>

        {/* Tab bar */}
        <div className="bg-white border-b border-gray-100 px-6 flex gap-0 flex-shrink-0">
          {TABS.map(tab => {
            const Icon = tab.icon
            const active = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  active
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon size={14} />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto p-6">
          {TAB_COMPONENTS[activeTab]}
        </div>
      </main>
    </div>
  )
}
