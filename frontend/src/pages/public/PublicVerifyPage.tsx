import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
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
}

export default function PublicVerifyPage() {
  const { code } = useParams<{ code: string }>();
  const [done, setDone] = useState(false);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const verifyMutation = useMutation({
    mutationFn: (c: string) => api.post("/verify", { code: c }).then((r) => r.data),
    onSuccess: (data) => { setResult(data); setDone(true); },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      setErrorMsg(err?.response?.data?.detail ?? "Verification failed.");
      setDone(true);
    },
  });

  useEffect(() => {
    if (code && !done) {
      verifyMutation.mutate(code.toUpperCase());
    }
  }, [code]);

  if (!done) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <p className="text-gray-500 text-sm">Verifying…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg border border-[#E2E8F0] max-w-sm w-full p-6">
        <div className="text-center mb-5">
          <span className="text-3xl">
            {result?.result === "enrolled" ? "✅" : "⚠️"}
          </span>
          <h1 className="text-xl font-bold text-[#0B2545] mt-2">
            {result?.result === "enrolled" ? "Enrolled" : "Not Enrolled"}
          </h1>
          <p className="text-xs text-gray-400 mt-1">TrueRoll · SAMPLE DATA</p>
        </div>

        {result?.result === "enrolled" ? (
          <div className="space-y-2 text-sm">
            <Row label="Student" value={result.student_display} />
            <Row label="Institution" value={result.institution} />
            <Row label="Programme" value={result.programme} />
            <Row label="Valid as of" value={new Date(result.valid_as_of).toLocaleString()} />
            <Row label="Consent expires" value={new Date(result.consent_expires).toLocaleDateString()} />
            <div className="mt-3">
              <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                result.signature_valid ? "bg-green-100 text-green-800" : "bg-red-100 text-red-700"
              }`}>
                {result.signature_valid ? "Signature valid" : "Signature invalid"}
              </span>
            </div>
          </div>
        ) : (
          <p className="text-sm text-amber-700 text-center">{errorMsg ?? "Consent withdrawn, expired, or invalid."}</p>
        )}

        <p className="text-xs text-gray-400 mt-6 text-center leading-relaxed">
          This response contains no marks, address, DOB, phone, Aadhaar, or flags.
        </p>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-xs text-gray-500 w-32 flex-shrink-0">{label}</span>
      <span className="text-sm font-medium text-[#0B2545]">{value}</span>
    </div>
  );
}
