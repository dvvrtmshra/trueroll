import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../../store/auth";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import TierBadge from "../../components/TierBadge";

interface StudentRow {
  id: string;
  full_name: string;
  apaar_masked: string | null;
  identity_tier: string;
  date_of_birth_year: number | null;
  course_name: string | null;
  seat_category: string | null;
  admission_date: string | null;
  status: string;
}

interface StudentsResponse {
  students: StudentRow[];
  total: number;
  page: number;
}

export default function StudentsPage() {
  const user = useAuthStore((s) => s.user) as Record<string, unknown> | null;
  const institutionId = user?.institution_id as string | undefined;
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<StudentRow | null>(null);
  const [drawerTab, setDrawerTab] = useState<"detail" | "apaar" | "withdraw">("detail");
  const [apaarInput, setApaarInput] = useState("");
  const [withdrawDate, setWithdrawDate] = useState("");
  const [withdrawReason, setWithdrawReason] = useState("");
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const { data, isLoading } = useQuery<StudentsResponse>({
    queryKey: ["students", institutionId, search, page],
    queryFn: () =>
      api.get("/students", {
        params: { institution_id: institutionId, search: search || undefined, page },
      }).then((r) => r.data),
    enabled: !!institutionId,
  });

  const withdrawMut = useMutation({
    mutationFn: ({ id, date, reason }: { id: string; date: string; reason: string }) =>
      api.post(`/students/${id}/withdraw`, { date, reason }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
      setActionMsg("Withdrawal recorded. Seat released.");
      setDrawerTab("detail");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setActionMsg(`Error: ${msg || "Failed to withdraw"}`);
    },
  });

  const apaarMut = useMutation({
    mutationFn: ({ id, apaar_id }: { id: string; apaar_id: string }) =>
      api.patch(`/students/${id}/apaar`, { apaar_id }).then((r) => r.data),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["students"] });
      setActionMsg(`APAAR updated. Identity tier: ${res.identity_tier}. Registry: ${res.registry_result}`);
      setDrawerTab("detail");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setActionMsg(`Error: ${msg || "Failed to update APAAR"}`);
    },
  });

  return (
    <Layout>
      <div className="max-w-5xl">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-6">Students</h1>

        <div className="flex gap-3 mb-4">
          <input
            type="text"
            placeholder="Search by name…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {isLoading && <p className="text-gray-500 text-sm">Loading…</p>}

        <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-2">Name</th>
                <th className="text-left px-4 py-2">APAAR</th>
                <th className="text-left px-4 py-2">Tier</th>
                <th className="text-left px-4 py-2">Course</th>
                <th className="text-left px-4 py-2">Category</th>
                <th className="text-left px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {data?.students.map((s) => (
                <tr
                  key={s.id}
                  onClick={() => { setSelected(s); setDrawerTab("detail"); setActionMsg(null); }}
                  className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-4 py-2 font-medium">{s.full_name}</td>
                  <td className="px-4 py-2 font-mono text-gray-500">{s.apaar_masked ?? "Not linked"}</td>
                  <td className="px-4 py-2"><TierBadge tier={s.identity_tier} /></td>
                  <td className="px-4 py-2 text-gray-600">{s.course_name ?? "—"}</td>
                  <td className="px-4 py-2 text-gray-600">{s.seat_category ?? "—"}</td>
                  <td className="px-4 py-2">
                    <span className={s.status === "withdrawn" ? "text-gray-400" : "text-green-700"}>
                      {s.status === "withdrawn" ? "Withdrawn" : "Enrolled"}
                    </span>
                  </td>
                </tr>
              ))}
              {data?.students.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-6 text-center text-gray-400">No students found.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total > 50 && (
          <div className="flex justify-between items-center mt-3 text-sm">
            <span className="text-gray-500">{data.total} students total</span>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-40">←</button>
              <span>Page {page}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={data.students.length < 50}
                className="px-3 py-1 border rounded disabled:opacity-40">→</button>
            </div>
          </div>
        )}
      </div>

      {/* Slide-over drawer */}
      {selected && (
        <div className="fixed inset-0 z-40 flex justify-end">
          <div className="absolute inset-0 bg-black/30" onClick={() => setSelected(null)} />
          <div className="relative w-96 bg-white shadow-xl flex flex-col h-full">
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#E2E8F0]">
              <h2 className="font-semibold text-[#0B2545]">{selected.full_name}</h2>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-[#E2E8F0]">
              {[["detail", "Details"], ["apaar", "Update APAAR"], ["withdraw", "Withdraw"]] .map(([tab, label]) => (
                <button
                  key={tab}
                  onClick={() => { setDrawerTab(tab as "detail" | "apaar" | "withdraw"); setActionMsg(null); }}
                  className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
                    drawerTab === tab
                      ? "border-b-2 border-[#0B2545] text-[#0B2545]"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {actionMsg && (
                <div className="mb-3 text-sm rounded px-3 py-2 bg-blue-50 text-blue-800">
                  {actionMsg}
                </div>
              )}

              {drawerTab === "detail" && (
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500">APAAR ID</p>
                    <p className="text-sm font-medium">{selected.apaar_masked ?? "Not linked"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Identity tier</p>
                    <TierBadge tier={selected.identity_tier} />
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Year of birth</p>
                    <p className="text-sm">{selected.date_of_birth_year ?? "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Course</p>
                    <p className="text-sm">{selected.course_name ?? "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Seat category</p>
                    <p className="text-sm">{selected.seat_category ?? "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Admission date</p>
                    <p className="text-sm">{selected.admission_date ?? "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Status</p>
                    <p className={`text-sm font-medium ${selected.status === "withdrawn" ? "text-gray-400" : "text-green-700"}`}>
                      {selected.status === "withdrawn" ? "Withdrawn" : "Enrolled"}
                    </p>
                  </div>
                </div>
              )}

              {drawerTab === "apaar" && (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">Enter the 12-digit APAAR ID to link or correct it. The registry will be checked immediately.</p>
                  <input
                    type="text"
                    maxLength={12}
                    placeholder="123456789012"
                    value={apaarInput}
                    onChange={(e) => setApaarInput(e.target.value)}
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => apaarMut.mutate({ id: selected.id, apaar_id: apaarInput })}
                    disabled={apaarInput.length !== 12 || apaarMut.isPending}
                    className="w-full px-4 py-2 bg-[#0B2545] text-white text-sm rounded hover:bg-[#0B2545]/90 disabled:opacity-50"
                  >
                    {apaarMut.isPending ? "Updating…" : "Save APAAR ID"}
                  </button>
                </div>
              )}

              {drawerTab === "withdraw" && (
                <div className="space-y-3">
                  {selected.status === "withdrawn" ? (
                    <p className="text-amber-700 text-sm">This student is already withdrawn.</p>
                  ) : (
                    <>
                      <p className="text-sm text-gray-600">Recording a withdrawal releases the seat immediately.</p>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Withdrawal date</label>
                        <input
                          type="date"
                          value={withdrawDate}
                          onChange={(e) => setWithdrawDate(e.target.value)}
                          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Reason (optional)</label>
                        <textarea
                          value={withdrawReason}
                          onChange={(e) => setWithdrawReason(e.target.value)}
                          rows={3}
                          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                        />
                      </div>
                      <button
                        onClick={() => withdrawMut.mutate({ id: selected.id, date: withdrawDate, reason: withdrawReason })}
                        disabled={!withdrawDate || withdrawMut.isPending}
                        className="w-full px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
                      >
                        {withdrawMut.isPending ? "Recording…" : "Record withdrawal"}
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
