import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import Layout from "../../components/Layout";
import api from "../../lib/api";

interface Reason { code: string; detail: string; }

const LABEL_OPTS = [
  { value: "useful", label: "Useful" },
  { value: "not_useful", label: "Not useful" },
  { value: "need_more_info", label: "Need more information" },
];

function BandChip({ band }: { band: string }) {
  const cls =
    band === "High" ? "bg-red-100 text-red-700" :
    band === "Medium" ? "bg-amber-100 text-amber-700" :
    "bg-green-100 text-green-700";
  return <span className={`px-2 py-0.5 rounded text-xs font-semibold ${cls}`}>{band}</span>;
}

export default function PriorityDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["priority", id],
    queryFn: () => api.get(`/priorities/${id}`).then(r => r.data),
    enabled: !!id,
  });

  const labelMut = useMutation({
    mutationFn: (label: string) => api.post(`/priorities/${id}/label`, { label }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["priority", id] }),
  });

  if (isLoading) return <Layout><div className="p-8 text-gray-400">Loading…</div></Layout>;
  if (!data) return <Layout><div className="p-8 text-gray-400">Not found.</div></Layout>;

  // Build simple bar chart data from features
  const features = data.features ?? {};
  const chartData = [
    { name: "Late share 14d", value: Math.round((features.late_share_14d ?? 0) * 100) },
    { name: "OCI/FN mix", value: Math.round((features.mix_ocifn ?? 0) * 100) },
    { name: "NRI mix", value: Math.round((features.mix_nri ?? 0) * 100) },
    { name: "Withdraw rate", value: Math.round((features.withdraw_rate ?? 0) * 100) },
    { name: "DOB conc.", value: Math.round((features.dob_concentration ?? 0) * 100) },
  ];

  return (
    <Layout>
      <div className="max-w-4xl mx-auto py-6 px-4">
        <button onClick={() => navigate("/priorities")} className="text-sm text-blue-600 hover:underline mb-4">← Priorities</button>

        <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 mb-4">
          <div className="flex items-start justify-between mb-2">
            <div>
              <h1 className="text-xl font-bold text-[#0B2545]">{data.institution_name}</h1>
              <p className="text-sm text-gray-600">{data.course_name} · {data.period}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-[#0B2545]">{data.score}</span>
              <BandChip band={data.band} />
            </div>
          </div>
          <p className="text-xs text-gray-400">{data.peer_group}</p>
        </div>

        {/* Advisory notice */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-4 text-sm text-amber-800 font-medium">
          {data.advisory_notice}
        </div>

        {/* Reasons */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 mb-4">
          <h2 className="font-semibold text-[#0B2545] mb-3">Reason codes</h2>
          {(data.reasons as Reason[]).length === 0 ? (
            <p className="text-sm text-gray-400">No significant reasons detected.</p>
          ) : (
            <div className="space-y-2">
              {(data.reasons as Reason[]).map((r, i) => (
                <div key={i} className="flex items-start gap-3">
                  <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-700 shrink-0">
                    {r.code.replace(/_/g, " ")}
                  </span>
                  <span className="text-sm text-gray-700">{r.detail}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Feature chart */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 mb-4">
          <h2 className="font-semibold text-[#0B2545] mb-3">Feature breakdown (%)</h2>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 80, right: 20 }}>
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={80} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="value" fill="#0B2545" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Officer feedback */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5">
          <h2 className="font-semibold text-[#0B2545] mb-3">Officer feedback</h2>
          <div className="flex gap-2 flex-wrap">
            {LABEL_OPTS.map(opt => (
              <button
                key={opt.value}
                onClick={() => labelMut.mutate(opt.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                  data.officer_label === opt.value
                    ? "bg-[#0B2545] text-white border-[#0B2545]"
                    : "bg-white text-gray-700 border-gray-300 hover:border-[#0B2545]"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-2">Feedback is stored for the future pilot. Not visible to the institution.</p>
          <a href="/model-eval" className="text-xs text-blue-600 hover:underline mt-1 block">→ View model evaluation</a>
        </div>
      </div>
    </Layout>
  );
}
