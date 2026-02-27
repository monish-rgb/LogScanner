interface ProgressBarProps {
  percent: number;
  label?: string;
}

export default function ProgressBar({ percent, label }: ProgressBarProps) {
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-sm text-slate-300">{label}</span>
          <span className="text-sm text-slate-400">{percent}%</span>
        </div>
      )}
      <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
        <div
          className="bg-blue-500 h-3 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
