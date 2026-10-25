import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import api from "../../lib/api";
import Layout from "../../components/Layout";

const BUCKETS = [
  "OCI_FN_EXTRA", "CIWGC_EXTRA", "EWS", "INTL_PG_EXTRA",
  "INTL_MGT_EXTRA", "LATERAL", "REGULAR",
];

const LEVELS = ["UG", "PG", "Diploma", "MBA/PGDM", "MCA"];

export default function ProposePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    rule_id: "",
    version: 1,
    academic_year: "2026-27",
    programme_level: ["UG"],
    domain: "ALL",
    state: "ALL",
    institution_type: "ALL",
    bucket: "OCI_FN_EXTRA",
    cap_basis: "PERCENT_OF_INTAKE",
    cap_percent: 10,
    cap_fixed: null as number | null,
    eligible_categories: [] as string[],
    source_document: "",
    source_clause: "",
    source_url: "",
    effective_from: "",
    effective_to: "",
  });
  const [proposed, setProposed] = useState<{ rule_id: string; version: number } | null>(null);
  const [error, setError] = useState("");

  const proposeMutation = useMutation({
    mutationFn: (data: typeof form) =>
      api.post("/rules", {
        ...data,
        cap_percent: data.cap_basis === "PERCENT_OF_INTAKE" ? data.cap_percent : null,
        cap_fixed: data.cap_basis === "FIXED" ? data.cap_fixed : null,
        source_url: data.source_url || null,
        effective_from: data.effective_from || null,
        effective_to: data.effective_to || null,
      }).then((r) => r.data),
    onSuccess: (rv) => {
      setProposed({ rule_id: rv.rule_id, version: rv.version });
      setError("");
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to propose rule.");
    },
  });

  const submitMutation = useMutation({
    mutationFn: ({ rule_id, version }: { rule_id: string; version: number }) =>
      api.post(`/rules/${rule_id}/versions/${version}/submit`).then((r) => r.data),
    onSuccess: () => navigate("/approvals"),
  });

  function toggleLevel(l: string) {
    setForm((f) => ({
      ...f,
      programme_level: f.programme_level.includes(l)
        ? f.programme_level.filter((x) => x !== l)
        : [...f.programme_level, l],
    }));
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-6">Propose a rule</h1>

        {!proposed ? (
          <form
            className="bg-white rounded-lg border border-[#E2E8F0] p-6 space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              proposeMutation.mutate(form);
            }}
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rule ID</label>
                <input
                  required
                  value={form.rule_id}
                  onChange={(e) => setForm({ ...form, rule_id: e.target.value })}
                  className="w-full border border-gray-200 rounded px-3 py-2 text-sm font-mono"
                  placeholder="e.g. SN-A"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
                <input
                  type="number" min={1}
                  value={form.version}
                  onChange={(e) => setForm({ ...form, version: parseInt(e.target.value) })}
                  className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Academic year</label>
                <select
                  value={form.academic_year}
                  onChange={(e) => setForm({ ...form, academic_year: e.target.value })}
                  className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                >
                  <option>2026-27</option>
                  <option>2025-26</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bucket</label>
                <select
                  value={form.bucket}
                  onChange={(e) => setForm({ ...form, bucket: e.target.value })}
                  className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                >
                  {BUCKETS.map((b) => <option key={b}>{b}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Programme level</label>
              <div className="flex gap-2 flex-wrap">
                {LEVELS.map((l) => (
                  <button
                    key={l} type="button"
                    onClick={() => toggleLevel(l)}
                    className={`px-3 py-1 rounded text-sm border ${form.programme_level.includes(l) ? "bg-[#0B2545] text-white border-[#0B2545]" : "border-gray-200 text-gray-600"}`}
                  >
                    {l}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cap basis</label>
                <select
                  value={form.cap_basis}
                  onChange={(e) => setForm({ ...form, cap_basis: e.target.value })}
                  className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                >
                  <option value="PERCENT_OF_INTAKE">Percent of intake</option>
                  <option value="FIXED">Fixed number</option>
                </select>
              </div>
              {form.cap_basis === "PERCENT_OF_INTAKE" ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Percentage (%)</label>
                  <input
                    type="number" min={0} max={100} step={0.5}
                    value={form.cap_percent ?? ""}
                    onChange={(e) => setForm({ ...form, cap_percent: parseFloat(e.target.value) })}
                    className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Fixed seats</label>
                  <input
                    type="number" min={0}
                    value={form.cap_fixed ?? ""}
                    onChange={(e) => setForm({ ...form, cap_fixed: parseInt(e.target.value) })}
                    className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                  />
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Domain</label>
                <input
                  value={form.domain}
                  onChange={(e) => setForm({ ...form, domain: e.target.value })}
                  className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                  placeholder="ALL or Engineering"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                <input
                  value={form.state}
                  onChange={(e) => setForm({ ...form, state: e.target.value })}
                  className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                  placeholder="ALL"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source document <span className="text-red-500">*</span>
              </label>
              <input
                required
                value={form.source_document}
                onChange={(e) => setForm({ ...form, source_document: e.target.value })}
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                placeholder="e.g. AICTE Handbook Addendum 2026-27 (Illustrative)"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source clause <span className="text-red-500">*</span>
              </label>
              <input
                required
                value={form.source_clause}
                onChange={(e) => setForm({ ...form, source_clause: e.target.value })}
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                placeholder="e.g. Para 3.1 (Illustrative: to be confirmed against AICTE rules)"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Source URL (optional)</label>
              <input
                value={form.source_url}
                onChange={(e) => setForm({ ...form, source_url: e.target.value })}
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                placeholder="https://..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Effective from</label>
                <input
                  type="date"
                  value={form.effective_from}
                  onChange={(e) => setForm({ ...form, effective_from: e.target.value })}
                  className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Effective to (leave blank = open-ended)</label>
                <input
                  type="date"
                  value={form.effective_to}
                  onChange={(e) => setForm({ ...form, effective_to: e.target.value })}
                  className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                />
              </div>
            </div>

            {error && <p className="text-red-600 text-sm">{error}</p>}

            <button
              type="submit"
              disabled={proposeMutation.isPending}
              className="bg-[#0B2545] text-white px-6 py-2 rounded hover:bg-[#1a3a6b] disabled:opacity-50"
            >
              {proposeMutation.isPending ? "Saving draft…" : "Save as draft"}
            </button>
          </form>
        ) : (
          <div className="bg-white rounded-lg border border-[#E2E8F0] p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-green-600 text-lg">✓</span>
              <span className="font-semibold text-[#0B2545]">
                Rule {proposed.rule_id} v{proposed.version} saved as draft.
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Review the draft, then submit it for approval. A different person must approve before it can be activated.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => submitMutation.mutate(proposed)}
                disabled={submitMutation.isPending}
                className="bg-[#D9730D] text-white px-4 py-2 rounded text-sm hover:bg-[#b85f0a] disabled:opacity-50"
              >
                {submitMutation.isPending ? "Submitting…" : "Submit for review →"}
              </button>
              <button
                onClick={() => setProposed(null)}
                className="text-gray-600 text-sm hover:underline"
              >
                Propose another
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
