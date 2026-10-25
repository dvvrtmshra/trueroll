import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/auth";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import UploadDropzone from "../../components/UploadDropzone";
import WizardStep from "../../components/WizardStep";
import StatusChip from "../../components/StatusChip";
import TierBadge from "../../components/TierBadge";
import DupClassChip from "../../components/DupClassChip";

interface Course {
  id: string;
  name: string;
  approved_intake: number;
  buckets: { bucket: string; cap: number; used: number }[];
  status: string;
  open_flags: number;
}

interface UploadResult {
  upload_id: string;
  status: string;
  idempotent?: boolean;
  rows_total: number;
  rows_accepted: number;
  rows_warning: number;
  rows_error: number;
  errors_csv?: string;
  identity_tiers?: Record<string, number>;
  duplicates?: Record<string, number>;
  ledger?: { course: string; approved: number; result: string; flags: number }[];
}

const TIER_DESCS: Record<string, string> = {
  T1: "Verified against APAAR registry",
  T2: "APAAR provided; registry check pending or unavailable",
  T3: "No APAAR ID provided — reminder will be sent",
  T4: "Foreign national or opted out — alternative route",
};

const DUP_DESCS: Record<string, string> = {
  D1: "Duplicate within this file (same student_ref) — data error",
  D2: "Same APAAR, different full-time institution — review required",
  D3: "Same APAAR, one online/part-time — possibly permitted",
  D4: "High fuzzy name/DOB match — review required",
  D5: "Moderate fuzzy match — added to watch list",
};

const ERROR_HINTS: Record<string, string> = {
  E101: "Add the missing value in the CSV column",
  E102: "APAAR ID must be exactly 12 digits (numbers only)",
  E103: "Use YYYY-MM-DD format, e.g. 2000-03-15",
  E104: "Check the course_code matches your institution's approved courses",
  E105: "Allowed seat categories: REGULAR, NRI_IN, OCI_FN_EXTRA, CIWGC_EXTRA, EWS, INTL_PG_EXTRA, INTL_MGT_EXTRA, LATERAL",
  E106: "Each student must have a unique student_ref in this file",
  W201: "Add the APAAR ID if available, or leave blank to keep T3 status",
  W203: "Registry was unavailable — student marked T2 and will be retried",
};

const STEPS = ["Choose", "Checking", "Results", "Fix"];

export default function UploadWizardPage() {
  const user = useAuthStore((s) => s.user) as Record<string, unknown> | null;
  const institutionId = user?.institution_id as string | undefined;

  const [step, setStep] = useState(0);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [mode, setMode] = useState<"full_list" | "round">("full_list");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [activeTab, setActiveTab] = useState("errors");
  const [_uploading, setUploading] = useState(false);
  const [progressLabel, setProgressLabel] = useState("Reading rows…");

  const { data: courses } = useQuery<Course[]>({
    queryKey: ["college-courses", institutionId],
    queryFn: () => api.get(`/institutions/${institutionId}/courses`).then((r) => r.data),
    enabled: !!institutionId,
  });

  const { data: uploadErrors } = useQuery<unknown[]>({
    queryKey: ["upload-errors", result?.upload_id],
    queryFn: () =>
      api.get(`/institutions/${institutionId}/uploads/${result!.upload_id}`).then((r) => r.data),
    enabled: !!result?.upload_id && !result?.idempotent,
  });

  async function handleUpload() {
    if (!file || !selectedCourse || !institutionId) return;
    setStep(1);
    setUploading(true);

    const labels = ["Reading rows…", "Checking identities…", "Duplicate check…", "Seat-Ledger evaluation…"];
    let li = 0;
    const interval = setInterval(() => {
      li = (li + 1) % labels.length;
      setProgressLabel(labels[li]);
    }, 800);

    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("course_code", selectedCourse);
      fd.append("academic_year", "2026-27");
      const res = await api.post(`/institutions/${institutionId}/uploads`, fd);
      setResult(res.data);
      setStep(2);
    } catch {
      setStep(0);
    } finally {
      clearInterval(interval);
      setUploading(false);
    }
  }

  const canUpload = !!file && !!selectedCourse;

  return (
    <Layout>
      <div className="max-w-3xl">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-6">Upload Students</h1>
        <WizardStep steps={STEPS} current={step} />

        {/* Step 1 — Choose */}
        {step === 0 && (
          <div className="bg-white border border-[#E2E8F0] rounded-lg p-6 shadow-sm space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Course</label>
              <select
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a course…</option>
                {courses?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} (intake {c.approved_intake})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Mode</label>
              <div className="flex gap-4">
                {(["full_list", "round"] as const).map((m) => (
                  <label key={m} className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="radio"
                      name="mode"
                      value={m}
                      checked={mode === m}
                      onChange={() => setMode(m)}
                    />
                    {m === "full_list" ? "Full list" : "Round update"}
                  </label>
                ))}
              </div>
            </div>

            <UploadDropzone onFile={setFile} />

            <div className="flex items-center justify-between">
              <a
                href="#"
                className="text-xs text-blue-600 hover:underline"
                onClick={(e) => {
                  e.preventDefault();
                  // Template download: just inform the user
                  alert("Template: student_ref,full_name,date_of_birth,apaar_id,nationality_status,seat_category,course_code,admission_date,mode");
                }}
              >
                Download template
              </a>
              <button
                onClick={handleUpload}
                disabled={!canUpload}
                className="px-5 py-2 bg-[#0B2545] text-white text-sm rounded hover:bg-[#0B2545]/90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Upload →
              </button>
            </div>
          </div>
        )}

        {/* Step 2 — Checking */}
        {step === 1 && (
          <div className="bg-white border border-[#E2E8F0] rounded-lg p-8 shadow-sm text-center">
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
              <div className="h-2 bg-blue-500 rounded-full animate-pulse" style={{ width: "70%" }} />
            </div>
            <p className="text-sm text-gray-600">{progressLabel}</p>
            <p className="text-xs text-gray-400 mt-2">Processing {file?.name}</p>
          </div>
        )}

        {/* Step 2 — Results */}
        {step === 2 && result && (
          <div className="space-y-4">
            {/* Summary bar */}
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-4 shadow-sm">
              <p className="text-sm font-medium text-[#0B2545]">
                {result.rows_total} rows read
                {" · "}
                <span className="text-green-700">{result.rows_accepted} accepted</span>
                {result.rows_warning > 0 && (
                  <span className="text-amber-700"> · {result.rows_warning} warnings</span>
                )}
                {result.rows_error > 0 && (
                  <span className="text-red-700"> · {result.rows_error} errors</span>
                )}
              </p>
              {result.idempotent && (
                <p className="text-xs text-blue-700 mt-1 bg-blue-50 px-3 py-1 rounded">
                  Re-uploading the same file changes nothing — already processed (upload ID: {result.upload_id})
                </p>
              )}
            </div>

            {/* Tabs */}
            <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm overflow-hidden">
              <div className="flex border-b border-[#E2E8F0]">
                {["errors", "warnings", "tiers", "duplicates", "seat_check"].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 text-sm font-medium transition-colors ${
                      activeTab === tab
                        ? "border-b-2 border-[#0B2545] text-[#0B2545]"
                        : "text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    {tab === "errors" && `Errors (${result.rows_error})`}
                    {tab === "warnings" && `Warnings (${result.rows_warning})`}
                    {tab === "tiers" && "Identity Tiers"}
                    {tab === "duplicates" && "Duplicates"}
                    {tab === "seat_check" && "Seat Check"}
                  </button>
                ))}
              </div>

              <div className="p-4">
                {activeTab === "errors" && (
                  <div>
                    {result.rows_error === 0 ? (
                      <p className="text-green-700 text-sm">No errors — all rows are valid.</p>
                    ) : (
                      <>
                        <p className="text-sm text-gray-600 mb-3">
                          Valid rows are kept even when some rows fail.
                        </p>
                        {result.errors_csv && (
                          <a
                            href={`/api${result.errors_csv}`}
                            className="inline-block mb-3 text-xs text-blue-600 hover:underline border border-blue-200 rounded px-3 py-1"
                          >
                            Download error report CSV
                          </a>
                        )}
                        <table className="w-full text-xs border-collapse">
                          <thead>
                            <tr className="bg-gray-50">
                              <th className="text-left px-2 py-1 border-b">Row</th>
                              <th className="text-left px-2 py-1 border-b">Field</th>
                              <th className="text-left px-2 py-1 border-b">Code</th>
                              <th className="text-left px-2 py-1 border-b">Fix hint</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(uploadErrors as Record<string, unknown>[] | undefined)?.filter((e) =>
                              String(e.error_code).startsWith("E")
                            ).slice(0, 20).map((e, i) => (
                              <tr key={i} className="border-b border-gray-100">
                                <td className="px-2 py-1">{String(e.row_number ?? "")}</td>
                                <td className="px-2 py-1">{String(e.field ?? "")}</td>
                                <td className="px-2 py-1 font-mono text-red-700">{String(e.error_code)}</td>
                                <td className="px-2 py-1 text-gray-600">
                                  {ERROR_HINTS[String(e.error_code)] || String(e.message)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </>
                    )}
                  </div>
                )}

                {activeTab === "warnings" && (
                  <div>
                    {result.rows_warning === 0 ? (
                      <p className="text-green-700 text-sm">No warnings.</p>
                    ) : (
                      <ul className="space-y-2">
                        {(uploadErrors as Record<string, unknown>[] | undefined)?.filter((e) =>
                          String(e.error_code).startsWith("W")
                        ).map((w, i) => (
                          <li key={i} className="text-sm text-amber-800 bg-amber-50 rounded px-3 py-2">
                            <span className="font-mono font-medium">{String(w.error_code)}</span>
                            {" — "}
                            {ERROR_HINTS[String(w.error_code)] || String(w.message)}
                            {w.error_code === "W203" && (
                              <span className="block text-xs mt-1 text-amber-600">
                                Registry unavailable: students shown as unverified and retried. Nobody was rejected.
                              </span>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {activeTab === "tiers" && (
                  <div>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="text-left px-3 py-2">Tier</th>
                          <th className="text-right px-3 py-2">Count</th>
                          <th className="text-left px-3 py-2">Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(result.identity_tiers ?? {}).map(([t, n]) => (
                          <tr key={t} className="border-t border-gray-100">
                            <td className="px-3 py-2"><TierBadge tier={t} /></td>
                            <td className="px-3 py-2 text-right font-medium">{n as number}</td>
                            <td className="px-3 py-2 text-gray-500 text-xs">{TIER_DESCS[t]}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {activeTab === "duplicates" && (
                  <div>
                    {Object.values(result.duplicates ?? {}).every((v) => v === 0) ? (
                      <p className="text-green-700 text-sm">No duplicate cases found.</p>
                    ) : (
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="text-left px-3 py-2">Class</th>
                            <th className="text-right px-3 py-2">Count</th>
                            <th className="text-left px-3 py-2">Meaning</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(result.duplicates ?? {}).filter(([, n]) => (n as number) > 0).map(([cls, n]) => (
                            <tr key={cls} className="border-t border-gray-100">
                              <td className="px-3 py-2"><DupClassChip cls={cls} /></td>
                              <td className="px-3 py-2 text-right font-medium">{n as number}</td>
                              <td className="px-3 py-2 text-gray-500 text-xs">{DUP_DESCS[cls]}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}

                {activeTab === "seat_check" && (
                  <div>
                    {result.ledger?.map((row, i) => (
                      <div key={i} className="mb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-sm">{row.course}</span>
                          <StatusChip status={row.result} count={row.flags} />
                        </div>
                        <p className="text-xs text-gray-500">
                          Approved intake: {row.approved} · Seat-Ledger result: {row.result}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              {result.rows_error > 0 && (
                <button
                  onClick={() => setStep(3)}
                  className="px-4 py-2 bg-[#D9730D] text-white text-sm rounded hover:bg-[#D9730D]/90"
                >
                  Fix errors →
                </button>
              )}
              <button
                onClick={() => { setStep(0); setFile(null); setResult(null); }}
                className="px-4 py-2 border border-gray-300 text-sm rounded hover:bg-gray-50"
              >
                Upload another file
              </button>
            </div>
          </div>
        )}

        {/* Step 3 — Fix */}
        {step === 3 && result && (
          <div className="bg-white border border-[#E2E8F0] rounded-lg p-6 shadow-sm space-y-4">
            <h2 className="font-semibold text-[#0B2545]">Fix and resubmit</h2>
            {result.errors_csv && (
              <a
                href={`/api${result.errors_csv}`}
                className="inline-block text-sm text-blue-600 hover:underline border border-blue-200 rounded px-4 py-2"
              >
                Download error report CSV
              </a>
            )}
            <p className="text-sm text-gray-600">
              Fix the errors in your spreadsheet, then re-upload the corrected file below.
            </p>
            <UploadDropzone onFile={setFile} label="Drop your corrected CSV here" />
            <p className="text-xs text-gray-400 italic">
              Re-uploading the same file (identical content) changes nothing.
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleUpload}
                disabled={!file}
                className="px-5 py-2 bg-[#0B2545] text-white text-sm rounded hover:bg-[#0B2545]/90 disabled:opacity-50"
              >
                Upload corrected file
              </button>
              <button
                onClick={() => setStep(0)}
                className="px-4 py-2 border border-gray-300 text-sm rounded hover:bg-gray-50"
              >
                Start over
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
