import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import IllustrativeLabel from "../../components/IllustrativeLabel";

interface RuleVersion {
  id: string;
  rule_id: string;
  version: number;
  academic_year: string;
  programme_level: string;
  domain: string;
  bucket: string;
  cap_basis: string;
  cap_percent: number | null;
  cap_fixed: number | null;
  effective_from: string | null;
  status: string;
  enabled: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-600",
  pending_review: "bg-amber-100 text-amber-700",
  approved: "bg-blue-100 text-blue-700",
  active: "bg-green-100 text-green-700",
  retired: "bg-slate-100 text-slate-500",
  rejected: "bg-red-100 text-red-600",
};

function StatusChip({ status }: { status: string }) {
  const cls = STATUS_COLORS[status] ?? "bg-gray-100 text-gray-600";
  const label = status.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{label}</span>;
}

export default function RuleBookPage() {
  const qc = useQueryClient();
  const [filterStatus, setFilterStatus] = useState("");
  const [filterYear, setFilterYear] = useState("2026-27");

  const { data: rules = [], isLoading } = useQuery<RuleVersion[]>({
    queryKey: ["rules", filterStatus, filterYear],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filterStatus) params.set("status", filterStatus);
      if (filterYear) params.set("academic_year", filterYear);
      return api.get(`/rules?${params}`).then((r) => r.data);
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ rule_id, version }: { rule_id: string; version: number }) => {
      return api.post(`/rules/${rule_id}/versions/${version}/activate`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-[#0B2545]">Rule Book</h1>
          <Link
            to="/propose"
            className="bg-[#0B2545] text-white px-4 py-2 rounded text-sm hover:bg-[#1a3a6b]"
          >
            + Propose new rule
          </Link>
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-4">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gray-200 rounded px-3 py-1.5 text-sm"
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="pending_review">Pending approval</option>
            <option value="approved">Approved</option>
            <option value="active">Active</option>
            <option value="retired">Retired</option>
          </select>
          <select
            value={filterYear}
            onChange={(e) => setFilterYear(e.target.value)}
            className="border border-gray-200 rounded px-3 py-1.5 text-sm"
          >
            <option value="2026-27">2026-27</option>
            <option value="2025-26">2025-26</option>
          </select>
        </div>

        {isLoading ? (
          <div className="text-gray-500 text-sm">Loading rules…</div>
        ) : (
          <div className="bg-white rounded-lg border border-[#E2E8F0] overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-[#E2E8F0]">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Rule ID</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Ver.</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Year</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Bucket</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Cap</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Effective from</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {rules.map((rv) => (
                  <tr key={rv.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link
                        to={`/rules/${rv.rule_id}/versions/${rv.version}`}
                        className="font-mono text-blue-600 hover:underline"
                      >
                        {rv.rule_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-500">v{rv.version}</td>
                    <td className="px-4 py-3 text-gray-500">{rv.academic_year}</td>
                    <td className="px-4 py-3 font-mono text-xs">{rv.bucket}</td>
                    <td className="px-4 py-3 text-gray-700">
                      {rv.cap_basis === "PERCENT_OF_INTAKE" && rv.cap_percent != null
                        ? `${rv.cap_percent}% of intake`
                        : rv.cap_fixed != null
                        ? `${rv.cap_fixed} fixed`
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{rv.effective_from ?? "—"}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <StatusChip status={rv.status} />
                        {rv.status === "active" && <IllustrativeLabel />}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {rv.status === "approved" && (
                        <button
                          onClick={() => toggleMutation.mutate({ rule_id: rv.rule_id, version: rv.version })}
                          className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                        >
                          Activate
                        </button>
                      )}
                      {rv.status === "pending_review" && (
                        <Link
                          to="/approvals"
                          className="text-xs text-amber-600 hover:underline"
                        >
                          Review →
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
                {rules.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-gray-400">
                      No rules found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
