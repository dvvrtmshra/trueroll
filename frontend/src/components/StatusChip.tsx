interface StatusChipProps {
  status: string;
  count?: number;
}

const map: Record<string, string> = {
  within_limit: "bg-green-100 text-green-800",
  near_cap: "bg-amber-100 text-amber-800",
  flag: "bg-red-100 text-red-800",
  rule_unconfirmed: "bg-gray-100 text-gray-700",
  open: "bg-red-100 text-red-800",
  under_review: "bg-blue-100 text-blue-800",
  clarification_requested: "bg-yellow-100 text-yellow-800",
  resolved: "bg-green-100 text-green-800",
  escalated: "bg-purple-100 text-purple-800",
  auto_cleared: "bg-gray-100 text-gray-600",
  OK: "bg-green-100 text-green-800",
  ALARM: "bg-red-100 text-red-800",
  FLAG: "bg-red-100 text-red-800",
  RULE_NOT_CONFIRMED: "bg-gray-100 text-gray-700",
  NOT_EVALUATED: "bg-gray-100 text-gray-500",
};

const labels: Record<string, string> = {
  within_limit: "Within limit",
  near_cap: "Near cap",
  flag: "FLAG",
  rule_unconfirmed: "Rule unconfirmed",
  OK: "OK",
  ALARM: "ALARM",
  FLAG: "FLAG",
  RULE_NOT_CONFIRMED: "Rule unconfirmed",
  NOT_EVALUATED: "Not evaluated",
};

export default function StatusChip({ status, count }: StatusChipProps) {
  const cls = map[status] || "bg-gray-100 text-gray-600";
  const label = labels[status] || status;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
      {label}{count !== undefined && count > 0 ? ` +${count}` : ""}
    </span>
  );
}
