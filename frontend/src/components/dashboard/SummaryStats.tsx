import type { AnalysisSummary } from '../../types/analysis';

interface SummaryStatsProps {
  summary: AnalysisSummary;
}

export default function SummaryStats({ summary }: SummaryStatsProps) {
  const stats = [
    { label: 'Total Entries', value: summary.total_entries, color: 'text-blue-400' },
    { label: 'Anomalies Found', value: summary.total_anomalies, color: 'text-red-400' },
    { label: 'Critical', value: summary.severity_breakdown.critical || 0, color: 'text-red-500' },
    { label: 'High', value: summary.severity_breakdown.high || 0, color: 'text-orange-400' },
    { label: 'Medium', value: summary.severity_breakdown.medium || 0, color: 'text-yellow-400' },
    { label: 'Low', value: summary.severity_breakdown.low || 0, color: 'text-blue-300' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((stat) => (
        <div key={stat.label} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <p className="text-sm text-slate-400">{stat.label}</p>
          <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
        </div>
      ))}
    </div>
  );
}
