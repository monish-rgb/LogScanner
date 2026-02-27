import type { Anomaly } from '../../types/analysis';
import ConfidenceBadge from './ConfidenceBadge';
import SeverityBadge from './SeverityBadge';

interface AnomalyCardProps {
  anomaly: Anomaly;
}

function formatAnomalyType(type: string): string {
  return type
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export default function AnomalyCard({ anomaly }: AnomalyCardProps) {
  const entry = anomaly.log_entry;

  return (
    <div className="bg-slate-800 border border-red-900/50 rounded-lg p-4 hover:border-red-700/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <SeverityBadge severity={anomaly.severity} />
          <span className="text-sm font-medium text-slate-200">
            {formatAnomalyType(anomaly.anomaly_type)}
          </span>
        </div>
        <ConfidenceBadge score={anomaly.confidence_score} />
      </div>

      <p className="text-sm text-slate-300 mb-3">{anomaly.explanation}</p>

      {entry && (
        <div className="bg-slate-900/50 rounded p-3 text-xs font-mono text-slate-400 space-y-1">
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            <span>Line: {entry.line_number}</span>
            {entry.source_ip && <span>IP: {entry.source_ip}</span>}
            {entry.user && <span>User: {entry.user}</span>}
            {entry.action && <span>Action: {entry.action}</span>}
            {entry.category && <span>Category: {entry.category}</span>}
            {entry.risk_score != null && <span>Risk: {entry.risk_score}</span>}
            {entry.bytes_transferred != null && (
              <span>Bytes: {entry.bytes_transferred.toLocaleString()}</span>
            )}
          </div>
          {entry.destination_url && (
            <div className="truncate text-slate-500 pt-1">
              URL: {entry.destination_url}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
