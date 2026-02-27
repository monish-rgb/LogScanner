interface SeverityBadgeProps {
  severity: string;
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'bg-red-600 text-white',
  high: 'bg-orange-600 text-white',
  medium: 'bg-yellow-600 text-white',
  low: 'bg-blue-600 text-white',
};

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const style = SEVERITY_STYLES[severity] || SEVERITY_STYLES.medium;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase ${style}`}>
      {severity}
    </span>
  );
}
