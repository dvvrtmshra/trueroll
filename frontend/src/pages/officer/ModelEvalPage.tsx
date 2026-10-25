import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import Layout from "../../components/Layout";
import KpiCard from "../../components/KpiCard";
import SimulatedChip from "../../components/SimulatedChip";
import api from "../../lib/api";

const ANOMALY_TYPES = [
  "LATE_SURGE", "CATEGORY_MIX", "SHARED_ATTRIBUTE_CLUSTER",
  "FULL_STREAK", "POST_AUDIT_WITHDRAWALS",
];

function pct(v: number) { return `${(v * 100).toFixed(1)}%`; }

export default function ModelEvalPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["anomaly-eval"],
    queryFn: () => api.get("/anomaly/evaluation").then(r => r.data),
  });

  // PR curve: synthesize from by_type metrics
  const prCurveData = data?.by_type
    ? Object.entries(data.by_type as Record<string, { precision: number; recall: number }>).map(([type, m]) => ({
        name: type.replace(/_/g, " "),
        precision: m.precision,
        recall: m.recall,
      }))
    : [];

  const overall = data?.overall;
  const conf = overall ? { tp: overall.tp, fp: overall.fp, fn: overall.fn, tn: overall.tn } : null;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto py-6 px-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-[#0B2545]">Model evaluation</h1>
          <SimulatedChip />
        </div>

        {/* Honesty notice — prominent */}
        <div className="bg-amber-50 border-2 border-amber-300 rounded-xl px-5 py-4 mb-6">
          <p className="text-sm font-semibold text-amber-800">
            {data?.honesty_notice ?? "Evaluated on synthetic labelled data. Real accuracy requires an AICTE pilot with officer-labelled outcomes."}
          </p>
        </div>

        {isLoading ? (
          <div className="text-gray-400 py-8 text-center">Loading…</div>
        ) : data?.status === "not_run" ? (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
            <p className="text-gray-500 mb-2">{data.message}</p>
            <code className="text-xs bg-gray-100 px-2 py-1 rounded">cd backend && python -m scripts.evaluate_anomaly</code>
          </div>
        ) : (
          <>
            {/* KPI cards */}
            {overall && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <KpiCard label="Precision" value={pct(overall.precision)} />
                <KpiCard label="Recall" value={pct(overall.recall)} />
                <KpiCard label="F1" value={pct(overall.f1)} />
                <KpiCard label="PR-AUC" value={pct(overall.pr_auc)} />
              </div>
            )}

            {/* By-type table */}
            <div className="bg-white rounded-xl border border-[#E2E8F0] overflow-hidden mb-6">
              <h2 className="font-semibold text-[#0B2545] px-5 py-3 border-b border-[#E2E8F0]">By anomaly type</h2>
              <table className="w-full text-sm">
                <thead className="bg-[#F8FAFC]">
                  <tr>
                    {["Type", "Precision", "Recall", "FPR", "PR-AUC", "Beats baseline"].map(h => (
                      <th key={h} className="text-left px-4 py-2 text-xs text-gray-500 uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ANOMALY_TYPES.map(atype => {
                    const m = data?.by_type?.[atype] ?? {};
                    return (
                      <tr key={atype} className="border-t border-[#F1F5F9]">
                        <td className="px-4 py-2 font-medium text-[#0B2545]">{atype.replace(/_/g, " ")}</td>
                        <td className="px-4 py-2">{pct(m.precision ?? 0)}</td>
                        <td className="px-4 py-2">{pct(m.recall ?? 0)}</td>
                        <td className="px-4 py-2">{pct(m.fpr ?? 0)}</td>
                        <td className="px-4 py-2">{pct(m.pr_auc ?? 0)}</td>
                        <td className="px-4 py-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${m.beats_baseline ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                            {m.beats_baseline ? "Yes" : "No"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* PR curve */}
            {prCurveData.length > 0 && (
              <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 mb-6">
                <h2 className="font-semibold text-[#0B2545] mb-4">Precision–Recall by type</h2>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={prCurveData}>
                    <XAxis dataKey="recall" label={{ value: "Recall", position: "insideBottom", offset: -2 }} tick={{ fontSize: 11 }} />
                    <YAxis label={{ value: "Precision", angle: -90, position: "insideLeft" }} tick={{ fontSize: 11 }} domain={[0, 1]} />
                    <Tooltip formatter={(v) => pct(Number(v))} />
                    <Line type="monotone" dataKey="precision" stroke="#0B2545" dot={{ r: 4 }} name="Precision" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Confusion matrix */}
            {conf && (
              <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 mb-6">
                <h2 className="font-semibold text-[#0B2545] mb-4">Confusion matrix (overall)</h2>
                <div className="grid grid-cols-2 gap-2 max-w-xs">
                  <div className="bg-green-50 border border-green-200 rounded p-3 text-center">
                    <div className="text-2xl font-bold text-green-700">{conf.tp}</div>
                    <div className="text-xs text-green-600">True positive</div>
                  </div>
                  <div className="bg-red-50 border border-red-200 rounded p-3 text-center">
                    <div className="text-2xl font-bold text-red-700">{conf.fp}</div>
                    <div className="text-xs text-red-600">False positive</div>
                  </div>
                  <div className="bg-amber-50 border border-amber-200 rounded p-3 text-center">
                    <div className="text-2xl font-bold text-amber-700">{conf.fn}</div>
                    <div className="text-xs text-amber-600">False negative</div>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded p-3 text-center">
                    <div className="text-2xl font-bold text-gray-700">{conf.tn}</div>
                    <div className="text-xs text-gray-600">True negative</div>
                  </div>
                </div>
              </div>
            )}

            {/* Baseline comparison */}
            {data?.baseline && (
              <div className="bg-white rounded-xl border border-[#E2E8F0] p-5">
                <h2 className="font-semibold text-[#0B2545] mb-3">Model vs baseline (random at 8% contamination)</h2>
                <table className="text-sm">
                  <thead>
                    <tr className="text-gray-500 text-xs uppercase">
                      <th className="text-left pr-8 py-1">Metric</th>
                      <th className="text-left pr-8">Model</th>
                      <th className="text-left">Baseline</th>
                    </tr>
                  </thead>
                  <tbody>
                    {["precision", "recall", "pr_auc"].map(m => (
                      <tr key={m} className="border-t border-[#F1F5F9]">
                        <td className="pr-8 py-1.5 capitalize">{m.replace("_", " ")}</td>
                        <td className="pr-8 font-semibold">{pct(overall?.[m] ?? 0)}</td>
                        <td>{pct(data.baseline[m] ?? 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
