interface TierBadgeProps {
  tier: string;
}

const config: Record<string, { label: string; cls: string }> = {
  T1: { label: "T1 Verified", cls: "bg-green-100 text-green-800" },
  T2: { label: "T2 Pending", cls: "bg-amber-100 text-amber-800" },
  T3: { label: "T3 No ID", cls: "bg-gray-100 text-gray-700" },
  T4: { label: "T4 Foreign/Opt-out", cls: "bg-blue-100 text-blue-800" },
};

export default function TierBadge({ tier }: TierBadgeProps) {
  const c = config[tier] ?? { label: tier, cls: "bg-gray-100 text-gray-600" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${c.cls}`}>
      {c.label}
    </span>
  );
}
