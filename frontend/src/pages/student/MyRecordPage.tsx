import { useQuery } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import TierBadge from "../../components/TierBadge";
import SimulatedChip from "../../components/SimulatedChip";
import LoadingSpinner from "../../components/LoadingSpinner";
import ErrorBanner from "../../components/ErrorBanner";
import api from "../../lib/api";

export default function MyRecordPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["student-me"],
    queryFn: () => api.get("/students/me").then((r) => r.data),
  });

  async function handleDownload() {
    try {
      const r = await api.post("/credentials/certificates", { student_id: data?.id });
      const blob = new Blob([JSON.stringify(r.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `trueroll_credential_${data?.id?.slice(-8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Could not generate credential — please try again.");
    }
  }

  return (
    <Layout>
      <div className="max-w-sm mx-auto mt-4 md:mt-8 px-2 md:px-0">
        <div className="bg-white rounded-xl shadow border border-[#E2E8F0] p-5 md:p-6">
          <SimulatedChip className="mb-4" />

          {isLoading && <LoadingSpinner message="Loading your record…" />}
          {isError && <ErrorBanner message="Could not load your record." onRetry={refetch} />}

          {!isLoading && !isError && data ? (
            <>
              <h1 className="text-xl font-bold text-[#0B2545] mb-0.5">{data.full_name}</h1>
              <p className="text-xs text-gray-400 mb-3" lang="hi">मेरा रिकॉर्ड</p>
              <p className="text-sm text-gray-600 mb-0.5">{data.institution_name}</p>
              <p className="text-sm text-gray-600 mb-3">
                {data.programme}{data.enrolled_period ? `, ${data.enrolled_period}` : ""}
              </p>
              <div className="flex items-center gap-2 mb-3" aria-label="Enrolment status">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  data.status === "enrolled" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-700"
                }`}>
                  {data.status === "enrolled" ? (
                    <>Enrolled <span lang="hi" className="text-green-600">· नामांकित</span></>
                  ) : (
                    <>Withdrawn <span lang="hi" className="text-gray-500">· वापस लिया</span></>
                  )}
                </span>
                <TierBadge tier={data.identity_tier} />
              </div>
              <p className="text-sm text-gray-500 mb-5">
                <span lang="hi" className="text-gray-400 text-xs">APAAR ID · </span>
                {data.apaar_last4
                  ? <span className="font-mono">linked (ends {data.apaar_last4})</span>
                  : <span className="text-amber-600">not linked</span>}
              </p>
              <button
                onClick={handleDownload}
                className="w-full bg-[#0B2545] text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-900 focus:outline-none focus:ring-2 focus:ring-[#0B2545] focus:ring-offset-2"
              >
                Download my verified record
                <span className="block text-xs font-normal opacity-70 mt-0.5" lang="hi">मेरा सत्यापित रिकॉर्ड डाउनलोड करें</span>
              </button>
              <p className="text-xs text-gray-400 mt-2 text-center">
                Produces a signed JSON credential with a QR code.
              </p>
            </>
          ) : !isLoading && !isError && (
            <p className="text-sm text-gray-500">No student record linked to this account.</p>
          )}
        </div>
      </div>
    </Layout>
  );
}
