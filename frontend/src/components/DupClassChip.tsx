interface DupClassChipProps {
  cls: string;
}

const config: Record<string, { label: string; style: string; desc: string }> = {
  D1: {
    label: "D1",
    style: "bg-red-100 text-red-800",
    desc: "Same ref in same file — likely data error",
  },
  D2: {
    label: "D2",
    style: "bg-orange-100 text-orange-800",
    desc: "Same APAAR, different full-time institutions — review required",
  },
  D3: {
    label: "D3",
    style: "bg-amber-100 text-amber-800",
    desc: "Same APAAR, one online / part-time — possibly permitted (UGC dual-programme)",
  },
  D4: {
    label: "D4",
    style: "bg-orange-100 text-orange-800",
    desc: "High fuzzy match (no APAAR) — review required",
  },
  D5: {
    label: "D5",
    style: "bg-yellow-100 text-yellow-800",
    desc: "Moderate fuzzy match — watch list",
  },
};

export default function DupClassChip({ cls }: DupClassChipProps) {
  const c = config[cls] ?? { label: cls, style: "bg-gray-100 text-gray-600", desc: "" };
  return (
    <span
      title={c.desc}
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold cursor-help ${c.style}`}
    >
      {c.label}
    </span>
  );
}
