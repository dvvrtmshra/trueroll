export default function SimulatedChip({ className }: { className?: string }) {
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-orange-100 text-orange-700 border border-orange-300${className ? ` ${className}` : ""}`}>
      SIMULATED
    </span>
  );
}
