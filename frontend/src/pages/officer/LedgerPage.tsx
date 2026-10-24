import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import StatusChip from "../../components/StatusChip";
import BucketBar from "../../components/BucketBar";

interface LedgerRow {
  course_id: string;
  institution_id: string;
  institution_name: string;
  course_name: string;
  level: string;
  domain: string;
  region: string;
  approved_intake: number;
  lawful_max: number;
  admitted: number;
  bucket_counts: Record<string, { cap: number; used: number }>;
  status: string;
  flags_open: number;
  rule_chips: string[];
}

interface CompareRow {
  course_id: string;
  institution_name: string;
  course_name: string;
  admitted: number;
  approved_intake: number;
  lawful_max: number;
  simple_counter_status: string;
  seat_ledger_status: string;
  seat_ledger_detail: string;
  flags_open: number;
}

interface LedgerResponse {
  total: number;
  items: LedgerRow[];
}

interface CompareResponse {
  items: CompareRow[];
  note: string;
}

export default function LedgerPage() {
  const navigate = useNavigate();
  const [compareMode, setCompareMode] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState<LedgerRow | null>(null);
  const [regionFilter, setRegionFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const params = new URLSearchParams();
  if (regionFilter) params.set("region", regionFilter);
  if (statusFilter && statusFilter !== "all") params.set("status", statusFilter);

  const { data: ledger, isLoading } = useQuery<LedgerResponse>({
    queryKey: ["ledger", regionFilter, statusFilter],
    queryFn: () => api.get(`/ledger?${params.toString()}`).then((r) => r.data),
    enabled: !compareMode,
  });

  const { data: compareData, isLoading: compareLoading } = useQuery<CompareResponse>({
    queryKey: ["ledger-compare"],
    queryFn: () => api.get("/ledger/compare").then((r) => r.data),
    enabled: compareMode,
  });

  return (
    <Layout>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-[#0B2545]">Seat-Ledger Monitor</h1>
        <button
          onClick={() => { setCompareMode(!compareMode); setSelectedCourse(null); }}
          className={`px-4 py-1.5 rounded text-sm font-medium border transition-colors ${
            compareMode
              ? "bg-[#0B2545] text-white border-[#0B2545]"
              : "bg-white text-[#0B2545] border-[#0B2545] hover:bg-blue-50"
          }`}
        >
          Compare mode: {compareMode ? "ON" : "OFF"}
        </button>
      </div>

      {!compareMode && (
        <>
          {/* Filters */}
          <div className="flex gap-3 mb-4 flex-wrap">
            <input
              type="text"
              placeholder="Filter by region…"
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm w-40 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="all">All statuses</option>
              <option value="within_limit">Within limit</option>
              <option value="near_cap">Near cap</option>
              <option value="flag">Flag</option>
              <option value="rule_unconfirmed">Rule unconfirmed</option>
            </select>
            {ledger && (
              <span className="text-sm text-gray-500 self-center">{ledger.total} courses</span>
            )}
          </div>

          {/* Table */}
          <div className="bg-white rounded-lg border border-[#E2E8F0] overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-600 uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-3 text-left">Institution</th>
                  <th className="px-4 py-3 text-left">Course</th>
                  <th className="px-4 py-3 text-left">Level</th>
                  <th className="px-4 py-3 text-right">Approved</th>
                  <th className="px-4 py-3 text-right">Lawful Max</th>
                  <th className="px-4 py-3 text-right">Admitted</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Rules</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {isLoading && (
                  <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Loading…</td></tr>
                )}
                {ledger?.items.map((row) => (
                  <tr
                    key={row.course_id}
                    className="hover:bg-blue-50 cursor-pointer"
                    onClick={() => setSelectedCourse(selectedCourse?.course_id === row.course_id ? null : row)}
                  >
                    <td className="px-4 py-3 font-medium text-[#0B2545]">{row.institution_name}</td>
                    <td className="px-4 py-3 text-gray-700">{row.course_name}</td>
                    <td className="px-4 py-3 text-gray-500">{row.level}</td>
                    <td className="px-4 py-3 text-right">{row.approved_intake}</td>
                    <td className="px-4 py-3 text-right">{row.lawful_max}</td>
                    <td className="px-4 py-3 text-right font-medium">{row.admitted}</td>
                    <td className="px-4 py-3">
                      <StatusChip status={row.status} count={row.flags_open} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {row.rule_chips.map((chip) => (
                          <span key={chip} className="px-1.5 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">
                            {chip}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Side drawer */}
          {selectedCourse && (
            <div className="fixed right-0 top-0 h-full w-80 bg-white shadow-xl border-l border-gray-200 z-40 overflow-y-auto p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-[#0B2545]">{selectedCourse.course_name}</h3>
                <button onClick={() => setSelectedCourse(null)} className="text-gray-400 hover:text-gray-600">✕</button>
              </div>
              <p className="text-xs text-gray-500 mb-4">{selectedCourse.institution_name}</p>
              <div>
                {Object.entries(selectedCourse.bucket_counts).map(([bucket, { cap, used }]) => (
                  <BucketBar key={bucket} label={bucket} used={used} cap={cap} />
                ))}
                {Object.keys(selectedCourse.bucket_counts).length === 0 && (
                  <p className="text-xs text-gray-400">No bucket data yet.</p>
                )}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100">
                <button
                  onClick={() => navigate(`/flags?institution_id=${selectedCourse.institution_id}`)}
                  className="text-sm text-blue-600 hover:underline"
                >
                  View flags for this institution →
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {compareMode && (
        <div>
          <div className="bg-amber-50 border border-amber-200 rounded p-3 mb-4 text-sm text-amber-800">
            <strong>Compare mode</strong> — why a simple counter fails vs the Seat-Ledger.
          </div>

          <div className="bg-white rounded-lg border border-[#E2E8F0] overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-600 uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-3 text-left">Course / Admitted</th>
                  <th className="px-4 py-3 text-center">Simple Counter (&gt;approved)</th>
                  <th className="px-4 py-3 text-center">Seat-Ledger</th>
                  <th className="px-4 py-3 text-left">Explanation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {compareLoading && (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">Loading…</td></tr>
                )}
                {compareData?.items.map((row) => (
                  <tr key={row.course_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-[#0B2545]">{row.institution_name}</p>
                      <p className="text-xs text-gray-500">{row.course_name}</p>
                      <p className="text-xs text-gray-400">
                        {row.admitted} admitted / {row.approved_intake} approved
                      </p>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusChip status={row.simple_counter_status} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <StatusChip
                        status={row.flags_open > 0 ? "flag" : row.seat_ledger_status === "OK" ? "within_limit" : row.seat_ledger_status}
                        count={row.flags_open > 0 ? row.flags_open : undefined}
                      />
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">{row.seat_ledger_detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {compareData?.note && (
            <p className="text-xs text-gray-500 mt-3 italic">{compareData.note}</p>
          )}
        </div>
      )}
    </Layout>
  );
}
