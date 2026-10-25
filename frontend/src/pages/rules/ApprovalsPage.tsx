import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import IllustrativeLabel from "../../components/IllustrativeLabel";
import { useAuthStore } from "../../store/auth";

interface RuleVersion {
  id: string;
  rule_id: string;
  version: number;
  academic_year: string;
  bucket: string;
  cap_percent: number | null;
  cap_fixed: number | null;
  cap_basis: string;
  source_document: string;
  source_clause: string;
  status: string;
  approvals: string;
}

export default function ApprovalsPage() {
  const qc = useQueryClient();
  const user = useAuthStore((s) => s.user) as Record<string, unknown> | null;
  const myEmail = user?.email as string | undefined;

  const [rejectTarget, setRejectTarget] = useState<{ rule_id: string; version: number } | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const { data: rules = [], isLoading } = useQuery<RuleVersion[]>({
    queryKey: ["rules", "pending_review"],
    queryFn: () => api.get("/rules?status=pending_review").then((r) => r.data),
  });

  const approveMutation = useMutation({
    mutationFn: ({ rule_id, version }: { rule_id: string; version: number }) =>
      api.post(`/rules/${rule_id}/versions/${version}/approve`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ rule_id, version, reason }: { rule_id: string; version: number; reason: string }) =>
      api.post(`/rules/${rule_id}/versions/${version}/reject`, { reason }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["rules"] });
      setRejectTarget(null);
      setRejectReason("");
    },
  });

  function isProposer(rv: RuleVersion): boolean {
    try {
      const approvals = JSON.parse(rv.approvals);
      return approvals.some(
        (a: { by: string; role: string }) => a.role === "proposer" && a.by === myEmail
      );
    } catch {
      return false;
    }
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-6">Approval queue</h1>

        {isLoading ? (
          <div className="text-gray-500 text-sm">Loading…</div>
        ) : rules.length === 0 ? (
          <div className="bg-white rounded-lg border border-[#E2E8F0] p-8 text-center text-gray-500">
            No rules pending approval.
          </div>
        ) : (
          <div className="space-y-4">
            {rules.map((rv) => {
              const approvals = JSON.parse(rv.approvals || "[]");
              const proposerEntry = approvals.find((a: { role: string }) => a.role === "proposer");
              const proposedBy = proposerEntry?.by ?? "unknown";
              const iAmProposer = isProposer(rv);

              return (
                <div key={rv.id} className="bg-white rounded-lg border border-[#E2E8F0] p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono font-semibold text-[#0B2545]">
                          {rv.rule_id} v{rv.version}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-700">
                          Pending approval
                        </span>
                        <IllustrativeLabel />
                      </div>
                      <p className="text-sm text-gray-600">
                        Bucket: <strong>{rv.bucket}</strong> · Cap:{" "}
                        {rv.cap_basis === "PERCENT_OF_INTAKE"
                          ? `${rv.cap_percent}% of intake`
                          : `${rv.cap_fixed} fixed`}{" "}
                        · Year: {rv.academic_year}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        Source: {rv.source_document} — {rv.source_clause}
                      </p>
                      <p className="text-sm text-gray-400 mt-1">Proposed by: {proposedBy}</p>
                    </div>

                    <div className="flex gap-2 flex-shrink-0 ml-4">
                      {iAmProposer ? (
                        <button
                          disabled
                          title="A different person must approve this rule."
                          className="bg-gray-100 text-gray-400 px-4 py-2 rounded text-sm cursor-not-allowed"
                        >
                          Approve (you proposed this)
                        </button>
                      ) : (
                        <>
                          <button
                            onClick={() => approveMutation.mutate({ rule_id: rv.rule_id, version: rv.version })}
                            disabled={approveMutation.isPending}
                            className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 disabled:opacity-50"
                          >
                            ✓ Approve
                          </button>
                          <button
                            onClick={() => setRejectTarget({ rule_id: rv.rule_id, version: rv.version })}
                            className="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded text-sm hover:bg-red-100"
                          >
                            ✗ Reject
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Reject modal */}
        {rejectTarget && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg">
              <h2 className="font-bold text-[#0B2545] mb-3">
                Reject {rejectTarget.rule_id} v{rejectTarget.version}
              </h2>
              <textarea
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm h-24"
                placeholder="Reason for rejection (required)…"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
              <div className="flex gap-3 mt-4">
                <button
                  disabled={!rejectReason.trim() || rejectMutation.isPending}
                  onClick={() =>
                    rejectMutation.mutate({ ...rejectTarget, reason: rejectReason })
                  }
                  className="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700 disabled:opacity-50"
                >
                  Confirm rejection
                </button>
                <button onClick={() => setRejectTarget(null)} className="text-gray-600 text-sm hover:underline">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
