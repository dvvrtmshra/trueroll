interface BucketBarProps {
  label: string;
  used: number;
  cap: number;
}

export default function BucketBar({ label, used, cap }: BucketBarProps) {
  const pct = cap > 0 ? Math.min(100, (used / cap) * 100) : 0;
  const over = used > cap;
  const near = pct >= 95;
  const barColor = over ? "bg-red-500" : near ? "bg-amber-500" : "bg-blue-500";

  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span className="font-medium">{label}</span>
        <span className={over ? "text-red-600 font-bold" : ""}>{used} / {cap}</span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-2 rounded-full transition-all ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
