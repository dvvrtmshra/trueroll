import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import api from "../../lib/api";

interface AuditEntry {
  id: number;
  actor: string;
  actor_role: string;
  action: string;
  object_type: string;
  object_id: string | null;
  time: string;
  hash_prefix: string;
  extra: string | null;
}

interface ChainResult {
  valid: boolean;
  entries_checked: number;
  broken_at_id?: number;
  expected?: string;
  found?: string;
}

export default function AuditTrailPage() {
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");
  const [objectType, setObjectType] = useState("");
  const [chainResult, setChainResult] = useState<ChainResult | null>(null);
  const [verifying, setVerifying] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["audit-entries", actor, action, objectType],
    queryFn: () => api.get("/audit/entries", {
      params: {
        actor: actor || undefined,
        action: action || undefined,
        object_type: objectType || undefined,
        limit: 100,
      },
    }).then(r => r.data),
  });

  const entries: AuditEntry[] = data?.items ?? [];
  const total: number = data?.total ?? 0;

  async function verifyChain() {
    setVerifying(true);
    try {
      const r = await api.get("/audit/chain/verify");
      setChainResult(r.data);
    } finally {
      setVerifying(false);
    }
  }

  function downloadCsv() {
    const params = new URLSearchParams({ format: "csv", limit: "500" });
    if (actor) params.set("actor", actor);
    if (action) params.set("action", action);
    if (objectType) params.set("object_type", objectType);
    const url = `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/audit/entries?${params}`;
    window.open(url, "_blank");
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-6 px-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-[#0B2545]">Audit trail</h1>
            <p className="text-sm text-gray-500">{total} entries. Student details are masked for this role.</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={verifyChain}
              disabled={verifying}
              className="px-4 py-2 text-sm font-semibold bg-[#0B2545] text-white rounded-lg hover:bg-[#0B2545]/90 disabled:opacity-50"
            >
              {verifying ? "Verifying…" : "Verify chain now"}
            </button>
            <button
              onClick={downloadCsv}
              className="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-lg hover:border-[#0B2545] text-[#0B2545]"
            >
              Export CSV
            </button>
          </div>
        </div>

        {/* Chain result */}
        {chainResult && (
          <div className={`rounded-xl px-5 py-4 mb-4 border ${chainResult.valid ? "bg-green-50 border-green-200" : "bg-red-50 border-red-300"}`}>
            <p className={`font-semibold ${chainResult.valid ? "text-green-800" : "text-red-800"}`}>
              Chain: {chainResult.valid ? "VALID — No entry changed or removed." : `BROKEN at entry ${chainResult.broken_at_id}`}
            </p>
            <p className="text-sm mt-1 text-gray-600">
              {chainResult.entries_checked} entries checked.
              {!chainResult.valid && ` Expected ${chainResult.expected?.slice(0, 8)}, found ${chainResult.found?.slice(0, 8)}.`}
            </p>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-3 mb-4 flex-wrap">
          {[
            { label: "Actor", value: actor, set: setActor },
            { label: "Action", value: action, set: setAction },
            { label: "Object type", value: objectType, set: setObjectType },
          ].map(({ label, value, set }) => (
            <input
              key={label}
              value={value}
              onChange={e => set(e.target.value)}
              placeholder={label}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm w-44"
            />
          ))}
          <button onClick={() => { setActor(""); setAction(""); setObjectType(""); }}
            className="text-xs text-gray-500 hover:text-gray-700">
            Clear
          </button>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0]">
              <tr>
                {["Time", "Actor", "Role", "Action", "Object", "Object ID", "Hash (8)", "Link"].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={8} className="text-center text-gray-400 py-8">Loading…</td></tr>
              ) : entries.length === 0 ? (
                <tr><td colSpan={8} className="text-center text-gray-400 py-8">No entries found.</td></tr>
              ) : entries.map(e => (
                <tr
                  key={e.id}
                  className={`border-b border-[#F1F5F9] ${chainResult && !chainResult.valid && e.id === chainResult.broken_at_id ? "bg-red-50" : ""}`}
                >
                  <td className="px-4 py-2 text-xs text-gray-500">{e.time ? new Date(e.time).toLocaleString() : "—"}</td>
                  <td className="px-4 py-2 font-medium text-[#0B2545] max-w-[120px] truncate">{e.actor}</td>
                  <td className="px-4 py-2 text-xs text-gray-500">{e.actor_role}</td>
                  <td className="px-4 py-2 text-gray-700">{e.action}</td>
                  <td className="px-4 py-2 text-xs text-gray-500">{e.object_type}</td>
                  <td className="px-4 py-2 text-xs font-mono text-gray-500">{e.object_id ?? "—"}</td>
                  <td className="px-4 py-2 text-xs font-mono text-gray-400">{e.hash_prefix}</td>
                  <td className="px-4 py-2 text-xs">
                    {chainResult && !chainResult.valid && e.id === chainResult.broken_at_id ? (
                      <span className="text-red-600 font-semibold">BREAK</span>
                    ) : (
                      <span className="text-green-600">OK</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
