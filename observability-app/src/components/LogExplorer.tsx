import React, { useState } from 'react';
import { Search, Filter, RefreshCw } from 'lucide-react';
import { useLogs, LOKI_SERVICE_SELECTOR } from '../hooks/useLogs';
import { useCurrentUser } from '../hooks/useMetrics';

const LEVEL_COLORS: Record<string, string> = {
  error:   'bg-red-100 text-red-700',
  warn:    'bg-yellow-100 text-yellow-800',
  warning: 'bg-yellow-100 text-yellow-800',
  info:    'bg-blue-100 text-blue-700',
  debug:   'bg-gray-100 text-gray-600',
};

export const LogExplorer: React.FC = () => {
  const userId = useCurrentUser();
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('all');

  // Pull last 2 hours of logs from real Loki — 500 entries max
  const { logs, loading, connected } = useLogs(LOKI_SERVICE_SELECTOR, 7200, 500, userId);

  const filtered = logs.filter(l => {
    if (levelFilter !== 'all' && l.level !== levelFilter) return false;
    if (search && !l.message.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col h-[500px]">
      {/* Toolbar */}
      <div className="p-3 border-b border-gray-200 flex gap-3 bg-gray-50/50 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
          <input
            type="text"
            placeholder="Search logs…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <select
          value={levelFilter}
          onChange={e => setLevelFilter(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All levels</option>
          <option value="error">Error</option>
          <option value="warn">Warn</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
        </select>
        <button className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-2">
          <Filter size={16} />
          Filters
        </button>
        {loading && <RefreshCw size={14} className="text-gray-400 animate-spin" />}
        {/* Connection indicator */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className={`w-2 h-2 rounded-full ${
            connected === null ? 'bg-gray-300 animate-pulse' :
            connected ? 'bg-green-500' : 'bg-red-400'
          }`} />
          <span className="text-gray-500">
            {connected === null ? 'Checking…' : connected ? 'Loki live' : 'Loki offline'}
          </span>
        </div>
      </div>

      {/* Log table */}
      <div className="flex-1 overflow-auto">
        {filtered.length > 0 ? (
          <table className="w-full text-xs text-left font-mono">
            <thead className="sticky top-0 bg-gray-100 text-gray-600 shadow-sm z-10 uppercase tracking-wider">
              <tr>
                <th className="px-4 py-2 font-medium w-28">Time</th>
                <th className="px-4 py-2 font-medium w-16">Level</th>
                <th className="px-4 py-2 font-medium w-32">Service</th>
                <th className="px-4 py-2 font-medium">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.slice(0, 200).map((log, i) => (
                <tr key={i} className="hover:bg-blue-50/50">
                  <td className="px-4 py-2 text-gray-500 whitespace-nowrap">
                    {log.timestamp.toLocaleTimeString()}
                  </td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      LEVEL_COLORS[log.level] ?? 'bg-gray-100 text-gray-600'
                    }`}>
                      {log.level.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-600 truncate max-w-[8rem]">{log.service}</td>
                  <td className="px-4 py-2 text-gray-900 truncate max-w-md">{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-gray-400">
            <p className="text-sm font-medium">
              {loading ? 'Loading logs…' :
               connected === false ? 'Loki is offline — run `make obs`' :
               logs.length > 0 ? 'No logs match filter' :
               'No logs yet — start the DevOps AI agent to generate logs'}
            </p>
          </div>
        )}
      </div>

      {/* Footer count */}
      {!loading && filtered.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-100 text-xs text-gray-400 bg-gray-50">
          {filtered.length} log{filtered.length !== 1 ? 's' : ''} shown
          {logs.length > filtered.length && ` (${logs.length} total)`}
        </div>
      )}
    </div>
  );
};
