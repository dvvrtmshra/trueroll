import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import SimulatedChip from "../../components/SimulatedChip";
import LoadingSpinner from "../../components/LoadingSpinner";
import ErrorBanner from "../../components/ErrorBanner";
import EmptyState from "../../components/EmptyState";
import api from "../../lib/api";

const PURPOSES = ["Internship", "Employment", "Background Check", "Other"];
const EXPIRE_OPTIONS = [7, 30, 90];

interface ShareCode {
  id: string;
  employer_name: string;
  purpose: string;
  status: string;
  expires_at: string;
  withdrawn_at: string | null;
  used_count: number;
}

function CodeDisplay({ code }: { code: string }) {
  return (
    <div className="bg-[#0B2545] text-white rounded-xl p-5 text-center mt-4">
      <p className="text-xs uppercase tracking-widest mb-2 opacity-70">Share this code</p>
      <p className="text-3xl font-mono font-bold tracking-widest mb-3">{code}</p>
      <p className="text-xs opacity-60 mb-2">or share the link:</p>
      <p className="text-xs font-mono bg-white/10 rounded px-3 py-1 break-all">
        {window.location.origin}/v/{code.replace("-", "")}
      </p>
    </div>
  );
}

export default function ConsentPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [employerId, setEmployerId] = useState("");
  const [purpose, setPurpose] = useState("Internship");
  const [expDays, setExpDays] = useState(30);
  const [created, setCreated] = useState<{ code: string; qr_url: string } | null>(null);
  const [withdrawId, setWithdrawId] = useState<string | null>(null);

  const { data: codes = [], isLoading: codesLoading, isError: codesError, refetch: refetchCodes } = useQuery<ShareCode[]>({
    queryKey: ["share-codes"],
    queryFn: () => api.get("/consents").then((r) => r.data),
  });

  const { data: employers = [] } = useQuery<{ id: string; name: string }[]>({
    queryKey: ["employers"],
    queryFn: () => api.get("/employers").then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (body: object) => api.post("/consents", body).then((r) => r.data),
    onSuccess: (data) => {
      setCreated({ code: data.code, qr_url: data.qr_url });
      setShowForm(false);
      qc.invalidateQueries({ queryKey: ["share-codes"] });
    },
    onError: () => alert("Could not create share code. Please try again."),
  });

  const withdrawMutation = useMutation({
    mutationFn: (id: string) => api.post(`/consents/${id}/withdraw`, {}).then((r) => r.data),
    onSuccess: () => {
      setWithdrawId(null);
      qc.invalidateQueries({ queryKey: ["share-codes"] });
    },
  });

  const activeCodes = codes.filter((c) => c.status === "active");
  const pastCodes = codes.filter((c) => c.status !== "active");

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-lg font-bold text-[#0B2545]">
              Consent Manager{" "}
              <span className="text-gray-400 font-normal text-base" lang="hi">सहमति प्रबंधक</span>
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Control who can verify you{" "}
              <span lang="hi" className="text-gray-400">· आप कौन को सत्यापित कर सकता है</span>
            </p>
          </div>
          <SimulatedChip />
        </div>

        {codesLoading && <LoadingSpinner message="Loading consents…" />}
        {codesError && <ErrorBanner message="Could not load consents." onRetry={refetchCodes} />}

        {/* Active consents */}
        {!codesLoading && !codesError && (
        <section className="bg-white rounded-xl border border-[#E2E8F0] shadow p-4 mb-4">
          <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide mb-3">
            Who can verify me{" "}
            <span lang="hi" className="text-gray-400 normal-case">· कौन मुझे सत्यापित कर सकता है</span>
          </p>
          {activeCodes.length === 0 && (
            <EmptyState
              title="No active share codes"
              body="Create one below to let an employer verify your enrolment."
            />
          )}
          {activeCodes.map((c) => (
            <div key={c.id} className="flex items-start justify-between py-2 border-b border-gray-100 last:border-0">
              <div>
                <p className="text-sm font-medium text-[#0B2545]">{c.employer_name}</p>
                <p className="text-xs text-gray-500">{c.purpose} · until {new Date(c.expires_at).toLocaleDateString()}</p>
                <p className="text-xs text-gray-400">Used {c.used_count}×</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded font-medium" aria-label="Status: active">ACTIVE</span>
                <button
                  onClick={() => setWithdrawId(c.id)}
                  className="text-xs text-red-600 hover:underline focus:outline-none focus:ring-2 focus:ring-red-400 rounded"
                  aria-label={`Withdraw consent for ${c.employer_name}`}
                >
                  Withdraw
                </button>
              </div>
            </div>
          ))}
        </section>
        )}

        {/* Create form */}
        {!showForm && !created && (
          <button
            onClick={() => setShowForm(true)}
            className="w-full border-2 border-dashed border-[#0B2545]/30 text-[#0B2545] py-3 rounded-xl text-sm font-medium hover:bg-blue-50 mb-4"
          >
            + Create a share code
          </button>
        )}

        {showForm && (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow p-4 mb-4">
            <p className="text-sm font-semibold text-[#0B2545] mb-3">New share code</p>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500 block mb-1">1. Choose verifier</label>
                <select
                  value={employerId}
                  onChange={(e) => setEmployerId(e.target.value)}
                  className="w-full border border-gray-200 rounded px-3 py-1.5 text-sm"
                >
                  <option value="">Select employer…</option>
                  {employers.map((e) => (
                    <option key={e.id} value={e.id}>{e.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">2. Purpose</label>
                <select
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  className="w-full border border-gray-200 rounded px-3 py-1.5 text-sm"
                >
                  {PURPOSES.map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-500 block mb-1">3. Valid for</label>
                <div className="flex gap-2">
                  {EXPIRE_OPTIONS.map((d) => (
                    <button
                      key={d}
                      onClick={() => setExpDays(d)}
                      className={`flex-1 py-1 rounded text-sm border ${
                        expDays === d
                          ? "bg-[#0B2545] text-white border-[#0B2545]"
                          : "border-gray-200 text-gray-600 hover:bg-gray-50"
                      }`}
                    >
                      {d}d
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-blue-50 rounded p-3 text-xs text-gray-600">
                <p className="font-medium mb-1">4. What they will see:</p>
                <p>✓ Enrolled: yes/no, college, programme</p>
                <p className="text-red-600 mt-1">✗ They will NOT see: marks, address, DOB, phone, Aadhaar, other institutions, flags</p>
              </div>
            </div>

            <div className="flex gap-2 mt-4">
              <button
                onClick={() => createMutation.mutate({ employer_id: employerId, purpose, expires_days: expDays })}
                disabled={!employerId || createMutation.isPending}
                className="flex-1 bg-[#1B8A3E] text-white py-2 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {createMutation.isPending ? "Creating…" : "Create"}
              </button>
              <button
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {created && (
          <>
            <CodeDisplay code={created.code} />
            <button
              onClick={() => setCreated(null)}
              className="w-full mt-3 text-sm text-gray-500 hover:underline"
            >
              Done
            </button>
          </>
        )}

        {/* Past consents */}
        {pastCodes.length > 0 && (
          <section className="bg-white rounded-xl border border-[#E2E8F0] p-4 mt-4">
            <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide mb-2">Past</p>
            {pastCodes.map((c) => (
              <div key={c.id} className="flex items-start justify-between py-2 border-b border-gray-100 last:border-0">
                <div>
                  <p className="text-sm text-gray-600">{c.employer_name}</p>
                  <p className="text-xs text-gray-400">{c.purpose}</p>
                </div>
                <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
                  {c.status.toUpperCase()}
                </span>
              </div>
            ))}
          </section>
        )}

        {/* Withdraw confirmation modal */}
        {withdrawId && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-5 max-w-sm w-full shadow-xl">
              <h2 className="text-base font-bold text-[#0B2545] mb-2">Withdraw consent?</h2>
              <p className="text-sm text-gray-600 mb-4">
                This takes effect <strong>immediately</strong>. The next scan will fail with "Consent withdrawn."
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => withdrawMutation.mutate(withdrawId)}
                  className="flex-1 bg-[#D62828] text-white py-2 rounded-lg text-sm font-medium"
                >
                  Withdraw
                </button>
                <button
                  onClick={() => setWithdrawId(null)}
                  className="flex-1 border border-gray-200 py-2 rounded-lg text-sm text-gray-600"
                >
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
