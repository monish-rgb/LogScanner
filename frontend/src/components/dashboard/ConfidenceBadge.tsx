interface ConfidenceBadgeProps {
  score: number;
}

export default function ConfidenceBadge({ score }: ConfidenceBadgeProps) {
  const percent = Math.round(score * 100);

  let colorClass: string;
  if (percent >= 80) {
    colorClass = 'bg-red-900/50 text-red-300 border-red-700';
  } else if (percent >= 50) {
    colorClass = 'bg-yellow-900/50 text-yellow-300 border-yellow-700';
  } else {
    colorClass = 'bg-green-900/50 text-green-300 border-green-700';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colorClass}`}>
      {percent}% confidence
    </span>
  );
}
