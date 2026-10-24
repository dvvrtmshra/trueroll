import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import FlagBanner from "../../components/FlagBanner";
import StatusChip from "../../components/StatusChip";

interface FlagItem {
  id: string;
  institution_id: string;
  course_approval_id: string;
  bucket: string;
  rule_id: string | null;
  rule_version: number | null;
  cap: number | null;
  used: number | null;
  over_by: number | null;
  status: string;
  severity: string;
  opened_at: string;
  assigned_officer: string | null;
}

const TABS = [
  { label: "Open", value: "open" },
  { label: "Under review", value: "under_review" },
  { label: "Clarification requested", value: "clarification_requested" },
  { label: "Resolved", value: "resolved" },
  { label: "Escalated", value: "escalated" },
];

function daysSince(iso: string) {
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 86400_000);
  return d === 0 ? "today" : d === 1 ? "1 day" : `${d} days`;
}

export default function FlagsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const institutionId = searchParams.get("institution_id") || undefined;
  const [activeTab, setActiveTab] = useState("open");

  const { data: flags = [], isLoading } = useQuery<FlagItem[]>({
    queryKey: ["flags", activeTab, institutionId],
    queryFn: () =>
      api
        .get(`/flags?status=${activeTab}${institutionId ? `&institution_id=${institutionId}` : ""}`)
        .then((r) => r.data),
  });

  return (
    <Layout>
      <h1 className="text-xl font-bold text-[#0B2545] mb-4">Flags</h1>
      <FlagBanner />

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.value
                ? "border-b-2 border-[#0B2545] text-[#0B2545]"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-lg border border-[#E2E8F0] overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-600 uppercase tracking-wide">
            <tr>
              <th className="px-4 py-3 text-left">Flag ID</th>
              <th className="px-4 py-3 text-left">Institution</th>
              <th className="px-4 py-3 text-left">Course</th>
              <th className="px-4 py-3 text-left">Bucket</th>
              <th className="px-4 py-3 text-right">Over by</th>
              <th className="px-4 py-3 text-left">Rule</th>
              <th className="px-4 py-3 text-left">Age</th>
              <th className="px-4 py-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Loading…</td></tr>
            )}
            {!isLoading && flags.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">No flags in this category.</td></tr>
            )}
            {flags.map((flag) => (
              <tr
                key={flag.id}
                className="hover:bg-blue-50 cursor-pointer"
                onClick={() => navigate(`/flags/${flag.id}`)}
              >
                <td className="px-4 py-3 font-mono text-xs text-blue-600">
                  #{flag.id.slice(0, 8)}
                </td>
                <td className="px-4 py-3 font-medium text-[#0B2545]">{flag.institution_id}</td>
                <td className="px-4 py-3 text-gray-600 text-xs">{flag.course_approval_id}</td>
                <td className="px-4 py-3 text-gray-700">{flag.bucket}</td>
                <td className="px-4 py-3 text-right font-bold text-red-600">
                  {flag.over_by != null ? `+${flag.over_by}` : "—"}
                </td>
                <td className="px-4 py-3 text-xs text-gray-600">
                  {flag.rule_id ? `${flag.rule_id} v${flag.rule_version}` : "—"}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">{daysSince(flag.opened_at)}</td>
                <td className="px-4 py-3"><StatusChip status={flag.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
