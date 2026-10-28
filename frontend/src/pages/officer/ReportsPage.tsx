import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import api from "../../lib/api";

interface Report {
  id: string;
  title: string;
  description: string;
}

const DETAIL_REPORTS = [
  "national-summary", "seat-utilisation", "flag-ageing", "anomaly-summary",
  "regional-breakdown", "institution-compliance", "student-demographics",
];

export default function ReportsPage() {
  const [activeReport, setActiveReport] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  const { data } = useQuery({
    queryKey: ["reports-list"],
    queryFn: () => api.get("/reports").then(r => r.data),
  });

  const reports: Report[] = data?.reports ?? [];

  async function loadReport(id: string) {
    setActiveReport(id);
    setLoading(true);
    try {
      const r = await api.get(`/reports/${id}`);
      setPreviewData(r.data);
    } catch {
      setPreviewData({ error: "Could not load report." });
    } finally {
      setLoading(false);
    }
  }

  function downloadCsv(id: string) {
    const url = `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/reports/${id}?format=csv`;
    const link = document.createElement("a");
    link.href = url;
    link.download = `${id}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-6 px-4">
        <h1 className="text-xl font-bold text-[#0B2545] mb-1">Reports</h1>
        <p className="text-sm text-gray-500 mb-6">All reports are on synthetic sample data only.</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Report list */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-xl border border-[#E2E8F0] overflow-hidden">
              {reports.map(r => (
                <button
                  key={r.id}
                  onClick={() => loadReport(r.id)}
                  className={`w-full text-left px-4 py-3 border-b border-[#F1F5F9] hover:bg-[#F8FAFC] transition-colors ${
                    activeReport === r.id ? "bg-blue-50 border-l-2 border-l-blue-500" : ""
                  }`}
                >
                  <div className="font-medium text-sm text-[#0B2545]">{r.title}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{r.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Preview pane */}
          <div className="md:col-span-2">
            {!activeReport ? (
              <div className="bg-gray-50 rounded-xl border border-gray-200 h-64 flex items-center justify-center">
                <p className="text-gray-400 text-sm">Select a report to preview</p>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-[#E2E8F0] p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-[#0B2545]">
                    {reports.find(r => r.id === activeReport)?.title ?? activeReport}
                  </h2>
                  <div className="flex gap-2">
                    {DETAIL_REPORTS.includes(activeReport) && (
                      <button
                        onClick={() => downloadCsv(activeReport)}
                        className="px-3 py-1.5 text-xs font-medium rounded border border-gray-300 bg-white hover:border-[#0B2545] text-[#0B2545]"
                      >
                        Export CSV
                      </button>
                    )}
                  </div>
                </div>

                {loading ? (
                  <div className="text-gray-400 text-sm py-8 text-center">Loading…</div>
                ) : previewData ? (
                  <ReportPreview id={activeReport} data={previewData} />
                ) : null}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}

function ReportPreview({ id, data }: { id: string; data: unknown }) {
  if (!data || typeof data !== "object") return null;
  const d = data as Record<string, unknown>;

  if (d.status === "not_run") {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center">
        <p className="text-gray-500 mb-2">{d.message as string}</p>
        <code className="text-xs bg-gray-100 px-2 py-1 rounded">make evaluate</code>
      </div>
    );
  }

  if (id === "national-summary") {
    const tiers = (d.identity_tiers as Record<string, number>) ?? {};
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          {[
            ["Institutions", d.institutions as number],
            ["Courses", d.courses as number],
            ["Students", d.students as number],
            ["Open flags", d.open_flags as number],
            ["Uploads", d.uploads as number],
          ].map(([label, val]) => (
            <div key={label as string} className="bg-[#F8FAFC] rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-[#0B2545]">{val}</div>
              <div className="text-xs text-gray-500">{label as string}</div>
            </div>
          ))}
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-500 mb-2 uppercase">Identity tiers</p>
          <div className="grid grid-cols-4 gap-2">
            {Object.entries(tiers).map(([tier, count]) => (
              <div key={tier} className="bg-blue-50 rounded p-2 text-center">
                <div className="font-bold text-blue-700">{count}</div>
                <div className="text-xs text-blue-500">{tier}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (id === "audit-integrity") {
    const valid = d.valid as boolean;
    return (
      <div className={`rounded-lg p-4 ${valid ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}>
        <p className={`font-semibold ${valid ? "text-green-700" : "text-red-700"}`}>
          Chain: {valid ? "VALID" : "BROKEN"}
        </p>
        <p className="text-sm text-gray-600 mt-1">
          {d.entries_checked as number} entries checked.
          {!valid && ` Broken at entry ${d.broken_at_id}.`}
        </p>
        {!valid && (
          <p className="text-xs text-gray-500 mt-1">
            Expected {d.expected as string}, found {d.found as string}
          </p>
        )}
      </div>
    );
  }

  if (id === "evaluation-summary") {
    const matching = d.matching as Record<string, unknown> | undefined;
    const reconciliation = d.reconciliation as Record<string, unknown> | undefined;
    return (
      <div className="space-y-4 text-sm">
        {matching && (
          <div>
            <p className="font-semibold text-gray-700 mb-2">Matching (fuzzy dedup)</p>
            <div className="grid grid-cols-3 gap-2">
              {["precision", "recall", "f1"].map(m => (
                <div key={m} className="bg-[#F8FAFC] rounded p-2 text-center">
                  <div className="font-bold text-[#0B2545]">{((matching[m] as number) * 100).toFixed(1)}%</div>
                  <div className="text-xs text-gray-500 capitalize">{m}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        {reconciliation && (
          <div className={`rounded-lg p-3 ${(reconciliation.clean as boolean) ? "bg-green-50" : "bg-red-50"}`}>
            <span className={`font-semibold ${(reconciliation.clean as boolean) ? "text-green-700" : "text-red-700"}`}>
              Reconciliation drift: {(reconciliation.clean as boolean) ? "zero (clean)" : `${reconciliation.total_drift} units`}
            </span>
          </div>
        )}
        <p className="text-xs text-gray-400">{d.note as string}</p>
      </div>
    );
  }

  if ((d.items as unknown[])?.length !== undefined) {
    const items = d.items as Record<string, unknown>[];
    if (items.length === 0) return <p className="text-gray-400 text-sm">No data.</p>;
    const keys = Object.keys(items[0]);
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-[#F8FAFC]">
            <tr>
              {keys.slice(0, 6).map(k => (
                <th key={k} className="text-left px-3 py-2 font-semibold text-gray-500 uppercase">{k.replace(/_/g, " ")}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.slice(0, 10).map((row, i) => (
              <tr key={i} className="border-t border-[#F1F5F9]">
                {keys.slice(0, 6).map(k => (
                  <td key={k} className="px-3 py-2 text-gray-700">{String(row[k] ?? "—")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {items.length > 10 && (
          <p className="text-xs text-gray-400 px-3 py-2">Showing 10 of {items.length}. Export CSV for full data.</p>
        )}
      </div>
    );
  }

  // Generic JSON preview
  return (
    <pre className="text-xs bg-gray-50 rounded p-3 overflow-auto max-h-64">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
