import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../../store/auth";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import FlagBanner from "../../components/FlagBanner";
import StatusChip from "../../components/StatusChip";
import { useNavigate } from "react-router-dom";

interface FlagRow {
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
  decision_reason: string | null;
}

const TABS = [
  { key: "open", label: "Open" },
  { key: "clarification_requested", label: "Clarification requested" },
  { key: "clarification_replied", label: "Replied" },
  { key: "resolved", label: "Resolved" },
];

export default function CollegeFlagsPage() {
  const user = useAuthStore((s) => s.user) as Record<string, unknown> | null;
  const institutionId = user?.institution_id as string | undefined;
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [activeTab, setActiveTab] = useState("open");
  const [selectedFlag, setSelectedFlag] = useState<FlagRow | null>(null);
  const [replyText, setReplyText] = useState("");
  const [replyMsg, setReplyMsg] = useState<string | null>(null);

  const { data: flags } = useQuery<FlagRow[]>({
    queryKey: ["flags", institutionId, activeTab],
    queryFn: () =>
      api.get("/flags", {
        params: { institution_id: institutionId, status: activeTab },
      }).then((r) => r.data),
    enabled: !!institutionId,
  });

  const replyMut = useMutation({
    mutationFn: ({ id, message }: { id: string; message: string }) =>
      api.post(`/flags/${id}/events`, { action: "reply", message }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["flags"] });
      setReplyMsg("Reply submitted. The officer will be notified.");
      setReplyText("");
    },
    onError: () => setReplyMsg("Failed to submit reply."),
  });

  function ageDays(opened: string) {
    const diff = Date.now() - new Date(opened).getTime();
    return Math.floor(diff / 86400000);
  }

  return (
    <Layout>
      <div className="max-w-4xl">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-4">Flags &amp; Clarifications</h1>
        <FlagBanner />

        <div className="flex border-b border-[#E2E8F0] mb-4">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === t.key
                  ? "border-b-2 border-[#0B2545] text-[#0B2545]"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-2">Flag ID</th>
                <th className="text-left px-4 py-2">Course</th>
                <th className="text-left px-4 py-2">Bucket</th>
                <th className="text-right px-4 py-2">Over-by</th>
                <th className="text-left px-4 py-2">Rule</th>
                <th className="text-right px-4 py-2">Age</th>
                <th className="text-left px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {flags?.map((f) => (
                <tr
                  key={f.id}
                  onClick={() => { setSelectedFlag(f); setReplyMsg(null); setReplyText(""); }}
                  className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-4 py-2 font-mono text-xs text-gray-500">{f.id.slice(0, 8)}</td>
                  <td className="px-4 py-2 text-xs text-gray-600">{f.course_approval_id}</td>
                  <td className="px-4 py-2">{f.bucket}</td>
                  <td className="px-4 py-2 text-right font-medium text-red-700">{f.over_by ?? "—"}</td>
                  <td className="px-4 py-2 text-xs">{f.rule_id ? `${f.rule_id} v${f.rule_version}` : "—"}</td>
                  <td className="px-4 py-2 text-right text-xs text-gray-500">{ageDays(f.opened_at)}d</td>
                  <td className="px-4 py-2"><StatusChip status={f.status} /></td>
                </tr>
              ))}
              {flags?.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-6 text-center text-gray-400">No flags in this category.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Drawer */}
      {selectedFlag && (
        <div className="fixed inset-0 z-40 flex justify-end">
          <div className="absolute inset-0 bg-black/30" onClick={() => setSelectedFlag(null)} />
          <div className="relative w-[480px] bg-white shadow-xl flex flex-col h-full">
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#E2E8F0]">
              <div>
                <h2 className="font-semibold text-[#0B2545]">Flag #{selectedFlag.id.slice(0, 8)}</h2>
                <StatusChip status={selectedFlag.status} />
              </div>
              <button onClick={() => setSelectedFlag(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              <div className="bg-gray-50 rounded p-3 text-sm space-y-1">
                <p><span className="text-gray-500">Course:</span> {selectedFlag.course_approval_id}</p>
                <p><span className="text-gray-500">Bucket:</span> {selectedFlag.bucket}</p>
                {selectedFlag.cap !== null && (
                  <p><span className="text-gray-500">Cap:</span> {selectedFlag.used} / {selectedFlag.cap} ({selectedFlag.over_by} over)</p>
                )}
                {selectedFlag.rule_id && (
                  <p><span className="text-gray-500">Rule:</span> {selectedFlag.rule_id} v{selectedFlag.rule_version} (Illustrative)</p>
                )}
              </div>

              {selectedFlag.decision_reason && (
                <div className="bg-blue-50 border border-blue-100 rounded p-3 text-sm">
                  <p className="text-xs font-semibold text-blue-700 mb-1">Officer message / thread:</p>
                  <p className="text-gray-700 whitespace-pre-wrap">{selectedFlag.decision_reason}</p>
                </div>
              )}

              {replyMsg && (
                <div className="bg-green-50 border border-green-100 rounded p-3 text-sm text-green-800">
                  {replyMsg}
                </div>
              )}

              {selectedFlag.status !== "resolved" && selectedFlag.status !== "escalated" && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Submit explanation
                  </label>
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    rows={4}
                    placeholder="Explain the situation…"
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <div className="flex gap-3 mt-2">
                    <button
                      onClick={() => replyMut.mutate({ id: selectedFlag.id, message: replyText })}
                      disabled={!replyText.trim() || replyMut.isPending}
                      className="px-4 py-2 bg-[#0B2545] text-white text-sm rounded hover:bg-[#0B2545]/90 disabled:opacity-50"
                    >
                      {replyMut.isPending ? "Sending…" : "Submit explanation"}
                    </button>
                    <button
                      onClick={() => navigate("/upload")}
                      className="px-4 py-2 border border-gray-300 text-sm rounded hover:bg-gray-50"
                    >
                      Submit corrected data →
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
