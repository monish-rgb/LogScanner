import type { LogEntry } from '../../types/logEntry';

interface LogTableProps {
  entries: LogEntry[];
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function LogTable({ entries, page, totalPages, onPageChange }: LogTableProps) {
  if (entries.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        No log entries to display
      </div>
    );
  }

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-slate-400 uppercase bg-slate-800/50">
            <tr>
              <th className="px-3 py-3">#</th>
              <th className="px-3 py-3">Timestamp</th>
              <th className="px-3 py-3">Source IP</th>
              <th className="px-3 py-3">User</th>
              <th className="px-3 py-3">Action</th>
              <th className="px-3 py-3">Category</th>
              <th className="px-3 py-3">Risk</th>
              <th className="px-3 py-3">Bytes</th>
              <th className="px-3 py-3">URL</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr
                key={entry.id}
                className={`border-b border-slate-700/50 ${
                  entry.is_anomalous
                    ? 'bg-red-900/20 hover:bg-red-900/30'
                    : 'hover:bg-slate-800/50'
                }`}
              >
                <td className="px-3 py-2 text-slate-500">{entry.line_number}</td>
                <td className="px-3 py-2 text-slate-300 whitespace-nowrap">
                  {entry.timestamp
                    ? new Date(entry.timestamp).toLocaleString()
                    : '-'}
                </td>
                <td className="px-3 py-2 text-slate-300 font-mono text-xs">
                  {entry.source_ip || '-'}
                </td>
                <td className="px-3 py-2 text-slate-300">{entry.user || '-'}</td>
                <td className="px-3 py-2">
                  <span
                    className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                      entry.action?.toLowerCase() === 'blocked'
                        ? 'bg-red-900/50 text-red-300'
                        : entry.action?.toLowerCase() === 'allowed'
                        ? 'bg-green-900/50 text-green-300'
                        : 'bg-slate-700 text-slate-300'
                    }`}
                  >
                    {entry.action || '-'}
                  </span>
                </td>
                <td className="px-3 py-2 text-slate-400 text-xs">{entry.category || '-'}</td>
                <td className="px-3 py-2">
                  {entry.risk_score != null ? (
                    <span
                      className={`text-xs font-medium ${
                        entry.risk_score >= 70
                          ? 'text-red-400'
                          : entry.risk_score >= 40
                          ? 'text-yellow-400'
                          : 'text-green-400'
                      }`}
                    >
                      {entry.risk_score}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
                <td className="px-3 py-2 text-slate-400 text-xs">
                  {entry.bytes_transferred != null
                    ? entry.bytes_transferred.toLocaleString()
                    : '-'}
                </td>
                <td className="px-3 py-2 text-slate-500 text-xs max-w-xs truncate">
                  {entry.destination_url || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 px-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-slate-300 rounded transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-slate-400">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-slate-300 rounded transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
