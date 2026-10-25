import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/auth";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import SimulatedChip from "../../components/SimulatedChip";

interface ApiKeyData {
  key_preview: string;
  endpoint: string;
  rate_limit: string;
  simulated: boolean;
  note: string;
}

export default function ApiPage() {
  const user = useAuthStore((s) => s.user) as Record<string, unknown> | null;
  const institutionId = user?.institution_id as string | undefined;
  const [revealed, setRevealed] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  const { data } = useQuery<ApiKeyData>({
    queryKey: ["api-key", institutionId],
    queryFn: () => api.get(`/institutions/${institutionId}/api-key`).then((r) => r.data),
    enabled: !!institutionId,
  });

  async function testConnection() {
    setTesting(true);
    try {
      await api.get("/health");
      setTestResult("Connected ✓ — API is reachable");
    } catch {
      setTestResult("Connection failed ✗");
    } finally {
      setTesting(false);
    }
  }

  const curlExample = `curl -X POST http://localhost:8000/institutions/${institutionId}/uploads \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -F "file=@students.csv" \\
  -F "course_code=YOUR_COURSE_ID" \\
  -F "academic_year=2026-27"`;

  return (
    <Layout>
      <div className="max-w-2xl">
        <div className="flex items-center gap-3 mb-6">
          <h1 className="text-2xl font-bold text-[#0B2545]">API Access</h1>
          <SimulatedChip />
        </div>

        <div className="bg-white border border-[#E2E8F0] rounded-lg p-6 shadow-sm space-y-5">
          <div>
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Your API key</h2>
            <div className="flex items-center gap-3">
              <code className="flex-1 bg-gray-50 border border-gray-200 rounded px-3 py-2 text-sm font-mono">
                {revealed ? `trk_${institutionId?.toLowerCase()}_demo_key_1234` : (data?.key_preview ?? "trk_…****")}
              </code>
              <button
                onClick={() => setRevealed(!revealed)}
                className="px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
              >
                {revealed ? "Hide" : "Reveal"}
              </button>
            </div>
            <p className="text-xs text-[#D9730D] mt-1">{data?.note}</p>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Upload endpoint</h2>
            <code className="block bg-gray-50 border border-gray-200 rounded px-3 py-2 text-xs font-mono break-all">
              POST http://localhost:8000/institutions/{institutionId}/uploads
            </code>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Rate limit</h2>
            <p className="text-sm text-gray-600">{data?.rate_limit ?? "100 uploads/day"}</p>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Example curl command</h2>
            <pre className="bg-gray-900 text-green-400 rounded p-4 text-xs overflow-x-auto whitespace-pre-wrap">
              {curlExample}
            </pre>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Expected response</h2>
            <pre className="bg-gray-50 border border-gray-200 rounded p-3 text-xs font-mono overflow-x-auto">
{`{
  "upload_id": "...",
  "status": "done",
  "rows_total": 1204,
  "rows_accepted": 1188,
  "rows_warning": 9,
  "rows_error": 7,
  "errors_csv": "/institutions/${institutionId}/uploads/.../errors.csv"
}`}
            </pre>
          </div>

          <div>
            <button
              onClick={testConnection}
              disabled={testing}
              className="px-4 py-2 bg-[#1B8A3E] text-white text-sm rounded hover:bg-[#1B8A3E]/90 disabled:opacity-50"
            >
              {testing ? "Testing…" : "Test connection (simulated)"}
            </button>
            {testResult && (
              <p className={`mt-2 text-sm ${testResult.includes("✓") ? "text-green-700" : "text-red-700"}`}>
                {testResult}
              </p>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
