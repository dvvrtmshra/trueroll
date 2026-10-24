import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import FlagBanner from "../../components/FlagBanner";
import BucketBar from "../../components/BucketBar";
import StatusChip from "../../components/StatusChip";

interface FlagDetail {
  id: string;
  institution_id: string;
  course_approval_id: string;
  bucket: string;
  rule_id: string | null;
  rule_version: number | null;
  cap: number | null;
  used: number | null;
  over_by: number | null;
  record_ids: string;
  status: string;
  severity: string;
  opened_at: string;
  assigned_officer: string | null;
  decision: string | null;
  decision_reason: string | null;
  updated_at: string;
}

interface LedgerDetail {
  bucket_counts: Record<string, { cap: number; used: number }>;
  lawful_max: number;
  admitted: number;
}

function ActionModal({
  action,
  onClose,
  onSubmit,
}: {
  action: string;
  onClose: () => void;
  onSubmit: (reason: string, decision?: string) => void;
}) {
  const [reason, setReason] = useState("");
  const [decision, setDecision] = useState("accepted");

  const labels: Record<string, string> = {
    request_clarification: "Request Clarification",
    resolve: "Accept Explanation",
    escalate: "Escalate",
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h3 className="font-semibold text-[#0B2545] mb-4">{labels[action] || action}</h3>
        {action === "resolve" && (
          <div className="mb-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">Decision</label>
            <select
              value={decision}
              onChange={(e) => setDecision(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              <option value="accepted">Accept explanation</option>
              <option value="monitoring">Continue monitoring</option>
            </select>
          </div>
        )}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reason <span className="text-red-500">*</span>
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="Required…"
          />
        </div>
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            disabled={!reason.trim()}
            onClick={() => onSubmit(reason, action === "resolve" ? decision : undefined)}
            className="px-4 py-2 bg-[#0B2545] text-white text-sm rounded hover:bg-blue-900 disabled:opacity-50"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

export default function FlagDetailPage() {
  const { flagId } = useParams<{ flagId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [modalAction, setModalAction] = useState<string | null>(null);

  const { data: flag, isLoading } = useQuery<FlagDetail>({
    queryKey: ["flag", flagId],
    queryFn: () => api.get(`/flags/${flagId}`).then((r) => r.data),
  });

  const { data: ledger } = useQuery<LedgerDetail>({
    queryKey: ["ledger-course", flag?.course_approval_id],
    queryFn: () => api.get(`/ledger/course/${flag!.course_approval_id}`).then((r) => r.data),
    enabled: !!flag?.course_approval_id,
  });

  const mutation = useMutation({
    mutationFn: ({ action, reason, decision }: { action: string; reason?: string; decision?: string }) =>
      api.post(`/flags/${flagId}/events`, { action, reason, decision }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["flag", flagId] });
      queryClient.invalidateQueries({ queryKey: ["flags"] });
      setModalAction(null);
    },
  });

  if (isLoading || !flag) {
    return <Layout><p className="text-gray-500">Loading…</p></Layout>;
  }

  const recordIds: string[] = (() => {
    try { return JSON.parse(flag.record_ids) as string[]; } catch { return []; }
  })();

  return (
    <Layout>
      {modalAction && (
        <ActionModal
          action={modalAction}
          onClose={() => setModalAction(null)}
          onSubmit={(reason, decision) =>
            mutation.mutate({ action: modalAction, reason, decision })
          }
        />
      )}

      <div className="mb-4 flex items-center gap-2">
        <button onClick={() => navigate("/flags")} className="text-sm text-blue-600 hover:underline">
          ← Flags
        </button>
        <span className="text-gray-400">/</span>
        <span className="text-sm text-gray-600 font-mono">#{flag.id.slice(0, 8)}</span>
        <StatusChip status={flag.status} />
      </div>

      <FlagBanner />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Seat Ledger */}
        <div className="bg-white rounded-lg border border-[#E2E8F0] p-5">
          <h2 className="font-semibold text-[#0B2545] mb-4">Seat Ledger</h2>
          {ledger
            ? Object.entries(ledger.bucket_counts).map(([bucket, { cap, used }]) => (
                <BucketBar key={bucket} label={bucket} used={used} cap={cap} />
              ))
            : <p className="text-xs text-gray-400">Ledger data unavailable.</p>
          }
          {ledger && (
            <div className="mt-3 text-sm text-gray-700">
              <span className="font-medium">Lawful max</span> {ledger.lawful_max} &middot;{" "}
              <span className="font-medium">Admitted</span>{" "}
              <span className={ledger.admitted > ledger.lawful_max ? "text-red-600 font-bold" : ""}>
                {ledger.admitted}
              </span>
            </div>
          )}
        </div>

        {/* Why this flag */}
        <div className="bg-white rounded-lg border border-[#E2E8F0] p-5">
          <h2 className="font-semibold text-[#0B2545] mb-4">Why this flag</h2>
          <dl className="space-y-2 text-sm">
            <div>
              <dt className="text-gray-500">Bucket</dt>
              <dd className="font-medium">{flag.bucket}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Cap</dt>
              <dd>{flag.cap ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Used</dt>
              <dd>{flag.used ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Over by</dt>
              <dd className="text-red-600 font-bold">{flag.over_by != null ? `+${flag.over_by}` : "—"}</dd>
            </div>
            {flag.rule_id && (
              <div>
                <dt className="text-gray-500">Rule</dt>
                <dd>
                  {flag.rule_id} v{flag.rule_version}
                  <span className="ml-2 text-xs text-orange-600 italic">
                    Illustrative: to be confirmed against AICTE rules
                  </span>
                </dd>
              </div>
            )}
          </dl>
        </div>
      </div>

      {/* Evidence */}
      {recordIds.length > 0 && (
        <div className="bg-white rounded-lg border border-[#E2E8F0] p-5 mb-6">
          <h2 className="font-semibold text-[#0B2545] mb-3">
            Evidence: {recordIds.length} record{recordIds.length !== 1 ? "s" : ""}
          </h2>
          <div className="overflow-x-auto">
            <table className="text-xs w-full">
              <thead className="text-gray-500 border-b border-gray-100">
                <tr>
                  <th className="text-left py-2">Student ID</th>
                </tr>
              </thead>
              <tbody>
                {recordIds.slice(0, 20).map((id) => (
                  <tr key={id} className="border-b border-gray-50">
                    <td className="py-1 font-mono text-gray-700">{id}</td>
                  </tr>
                ))}
                {recordIds.length > 20 && (
                  <tr><td className="py-1 text-gray-400">…and {recordIds.length - 20} more</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Actions */}
      {!["resolved", "escalated"].includes(flag.status) && (
        <div className="bg-white rounded-lg border border-[#E2E8F0] p-5">
          <h2 className="font-semibold text-[#0B2545] mb-3">Actions</h2>
          <div className="flex flex-wrap gap-3">
            {flag.status === "open" && (
              <button
                onClick={() => mutation.mutate({ action: "assign" })}
                className="px-4 py-2 bg-[#0B2545] text-white text-sm rounded hover:bg-blue-900"
              >
                Assign to me
              </button>
            )}
            <button
              onClick={() => setModalAction("request_clarification")}
              className="px-4 py-2 bg-white text-[#0B2545] border border-[#0B2545] text-sm rounded hover:bg-blue-50"
            >
              Request clarification
            </button>
            <button
              onClick={() => setModalAction("resolve")}
              className="px-4 py-2 bg-[#1B8A3E] text-white text-sm rounded hover:bg-green-700"
            >
              Accept explanation
            </button>
            <button
              onClick={() => setModalAction("escalate")}
              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
            >
              Escalate
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-3">
            "Escalate" hands this to AICTE's formal process outside this platform. The platform never records a finding.
          </p>
        </div>
      )}
    </Layout>
  );
}
