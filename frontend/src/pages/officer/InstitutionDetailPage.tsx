import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import BucketBar from "../../components/BucketBar";
import StatusChip from "../../components/StatusChip";

interface InstitutionData {
  id: string;
  name: string;
  region: string;
  state: string;
  city: string;
  type: string;
}

interface CourseLedger {
  course_id: string;
  course_name: string;
  level: string;
  approved_intake: number;
  lawful_max: number;
  admitted: number;
  bucket_counts: Record<string, { cap: number; used: number }>;
  status: string;
  flags_open: number;
}

interface LedgerResponse {
  total: number;
  items: CourseLedger[];
}

const TABS = ["Overview", "Courses & Ledger", "Uploads", "Flags"];

export default function InstitutionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("Overview");
  const [expandedCourse, setExpandedCourse] = useState<string | null>(null);

  const { data: inst } = useQuery<InstitutionData>({
    queryKey: ["institution", id],
    queryFn: () => api.get(`/institutions/${id}`).then((r) => r.data),
  });

  const { data: ledger } = useQuery<LedgerResponse>({
    queryKey: ["ledger", id],
    queryFn: () => api.get(`/ledger?academic_year=2026-27`).then((r) => r.data),
    enabled: activeTab === "Courses & Ledger",
  });

  const courses = ledger?.items.filter((c) => c.course_id.startsWith(id || "")) ?? [];

  return (
    <Layout>
      <button onClick={() => navigate(-1)} className="text-sm text-blue-600 hover:underline mb-4 block">
        ← Back
      </button>

      <h1 className="text-xl font-bold text-[#0B2545] mb-1">{inst?.name ?? id}</h1>
      <p className="text-sm text-gray-500 mb-4">
        {inst?.region} · {inst?.state} · {inst?.type}
      </p>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-200">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? "border-b-2 border-[#0B2545] text-[#0B2545]"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Overview" && inst && (
        <div className="bg-white rounded-lg border border-[#E2E8F0] p-5">
          <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
            <div><dt className="text-gray-500">ID</dt><dd className="font-mono">{inst.id}</dd></div>
            <div><dt className="text-gray-500">Region</dt><dd>{inst.region}</dd></div>
            <div><dt className="text-gray-500">State</dt><dd>{inst.state}</dd></div>
            <div><dt className="text-gray-500">City</dt><dd>{inst.city}</dd></div>
            <div><dt className="text-gray-500">Type</dt><dd>{inst.type}</dd></div>
          </dl>
        </div>
      )}

      {activeTab === "Courses & Ledger" && (
        <div className="space-y-3">
          {courses.length === 0 && (
            <p className="text-gray-400 text-sm">No courses found for this institution.</p>
          )}
          {courses.map((c) => (
            <div key={c.course_id} className="bg-white rounded-lg border border-[#E2E8F0]">
              <button
                className="w-full flex items-center justify-between px-5 py-3 text-left"
                onClick={() => setExpandedCourse(expandedCourse === c.course_id ? null : c.course_id)}
              >
                <div>
                  <span className="font-medium text-[#0B2545]">{c.course_name}</span>
                  <span className="ml-3 text-xs text-gray-500">{c.level}</span>
                </div>
                <div className="flex items-center gap-3">
                  <StatusChip status={c.status} count={c.flags_open} />
                  <span className="text-gray-400 text-sm">{expandedCourse === c.course_id ? "▲" : "▼"}</span>
                </div>
              </button>
              {expandedCourse === c.course_id && (
                <div className="px-5 pb-4 border-t border-gray-100">
                  <div className="grid grid-cols-3 gap-4 text-sm my-3">
                    <div><span className="text-gray-500">Approved</span><br /><strong>{c.approved_intake}</strong></div>
                    <div><span className="text-gray-500">Lawful max</span><br /><strong>{c.lawful_max}</strong></div>
                    <div><span className="text-gray-500">Admitted</span><br /><strong>{c.admitted}</strong></div>
                  </div>
                  {Object.entries(c.bucket_counts).map(([bucket, { cap, used }]) => (
                    <BucketBar key={bucket} label={bucket} used={used} cap={cap} />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === "Flags" && (
        <div className="text-sm text-gray-500">
          <button
            onClick={() => navigate(`/flags?institution_id=${id}`)}
            className="text-blue-600 hover:underline"
          >
            View all flags for this institution →
          </button>
        </div>
      )}

      {activeTab === "Uploads" && (
        <p className="text-sm text-gray-400">Upload history — available in Phase 5.</p>
      )}
    </Layout>
  );
}
