import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import api from "../../lib/api";

interface VerifyResult {
  verification_id: string;
  result: string;
  student_display: string;
  institution: string;
  programme: string;
  status: string;
  valid_as_of: string;
  consent_expires: string;
  signature_valid: boolean;
  shared_by: string;
}

const RESULT_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  enrolled: { bg: "bg-green-50 border-green-300", text: "text-green-800", label: "ENROLLED" },
  not_enrolled: { bg: "bg-red-50 border-red-300", text: "text-red-800", label: "NOT ENROLLED" },
  withdrawn: { bg: "bg-amber-50 border-amber-300", text: "text-amber-800", label: "CONSENT WITHDRAWN" },
  expired: { bg: "bg-gray-50 border-gray-300", text: "text-gray-600", label: "CODE EXPIRED" },
  not_for_this_verifier: { bg: "bg-red-50 border-red-300", text: "text-red-800", label: "NOT FOR THIS VERIFIER" },
};

export default function VerifyPage() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const verifyMutation = useMutation({
    mutationFn: (body: { code: string }) =>
      api.post("/verify", body).then((r) => r.data),
    onSuccess: (data: VerifyResult) => {
      setResult(data);
      setError(null);
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      const detail = err?.response?.data?.detail;
      if (detail?.includes("withdrawn")) {
        setResult({ result: "withdrawn" } as VerifyResult);
      } else if (detail?.includes("expired")) {
        setResult({ result: "expired" } as VerifyResult);
      } else if (detail?.includes("not for this")) {
        setResult({ result: "not_for_this_verifier" } as VerifyResult);
      } else {
        setError(detail ?? "Verification failed. Check the code and try again.");
        setResult(null);
      }
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const cleaned = code.trim().toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (cleaned.length < 8) { setError("Enter the full 8-character code."); return; }
    setError(null);
    setResult(null);
    verifyMutation.mutate({ code: cleaned });
  }

  const style = result ? (RESULT_STYLE[result.result] ?? RESULT_STYLE.not_enrolled) : null;

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-6 md:mt-10 px-2 md:px-0">
        <h1 className="text-lg font-bold text-[#0B2545] mb-1">Verify a student</h1>
        <p className="text-sm text-gray-500 mb-6">
          Enter the 8-character code the student shared with you.
        </p>

        <form onSubmit={handleSubmit} className="mb-6" aria-label="Student verification form">
          <label htmlFor="share-code-input" className="block text-xs text-gray-500 mb-1 font-medium">Share code</label>
          <div className="flex gap-2">
            <input
              id="share-code-input"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="XXXX-XXXX"
              className="flex-1 border border-gray-200 rounded-lg px-4 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[#0B2545]/20"
              maxLength={9}
              autoFocus
              autoCapitalize="characters"
              aria-describedby={error ? "verify-error" : undefined}
            />
            <button
              type="submit"
              disabled={verifyMutation.isPending}
              className="bg-[#0B2545] text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-900 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[#0B2545] focus:ring-offset-2"
            >
              {verifyMutation.isPending ? "Checking…" : "Verify"}
            </button>
          </div>
          {error && <p id="verify-error" className="text-xs text-red-600 mt-2" role="alert">{error}</p>}
        </form>

        {result && style && (
          <div className={`rounded-xl border-2 p-5 ${style.bg}`}>
            <div className={`text-xl font-bold mb-3 ${style.text}`}>
              {style.label}
            </div>

            {result.result === "enrolled" && (
              <div className="space-y-1">
                <Row label="Student" value={result.student_display} />
                <Row label="Institution" value={result.institution} />
                <Row label="Programme" value={result.programme} />
                <Row label="Status" value={result.status} />
                <Row label="Valid as of" value={new Date(result.valid_as_of).toLocaleString()} />
                <Row label="Consent expires" value={new Date(result.consent_expires).toLocaleDateString()} />
                <div className="mt-3 flex items-center gap-2">
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-medium ${
                      result.signature_valid
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {result.signature_valid ? "Signature valid" : "Signature invalid"}
                  </span>
                  <span className="text-xs text-gray-500">ID: {result.verification_id?.slice(-8)}</span>
                </div>
              </div>
            )}

            {result.result === "withdrawn" && (
              <p className="text-sm text-amber-700">
                The student has withdrawn consent. This code is no longer valid.
              </p>
            )}
            {result.result === "expired" && (
              <p className="text-sm text-gray-600">
                This share code has expired. Ask the student to create a new one.
              </p>
            )}
            {result.result === "not_for_this_verifier" && (
              <p className="text-sm text-red-700">
                This code was not created for your organisation. Ask the student to share a code addressed to you.
              </p>
            )}
          </div>
        )}

        <div className="mt-8 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-4">
          <p className="text-xs font-semibold text-gray-500 mb-2">IMPORTANT — what you are NOT told</p>
          <p className="text-xs text-gray-500 leading-relaxed">
            This response never contains marks, address, date of birth, phone, Aadhaar, records at other institutions, or any conduct flag.
            It confirms enrolment only. All fields comply with the minimal-disclosure requirement of the spec.
          </p>
        </div>
      </div>
    </Layout>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-xs text-gray-500 w-32 flex-shrink-0">{label}</span>
      <span className="text-sm text-[#0B2545] font-medium">{value}</span>
    </div>
  );
}
