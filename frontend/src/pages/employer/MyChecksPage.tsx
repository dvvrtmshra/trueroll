import { useQuery } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import api from "../../lib/api";

interface Check {
  id: string;
  result: string;
  student_display: string;
  institution: string;
  programme: string;
  verified_at: string;
  share_code_id: string;
}

export default function MyChecksPage() {
  const { data = [], isLoading } = useQuery<Check[]>({
    queryKey: ["verify-history"],
    queryFn: () => api.get("/verify/history").then((r) => r.data),
  });

  return (
    <Layout>
      <div className="max-w-2xl mx-auto mt-6">
        <h1 className="text-lg font-bold text-[#0B2545] mb-4">My verifications</h1>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow overflow-hidden">
          {isLoading ? (
            <p className="p-4 text-sm text-gray-400">Loading…</p>
          ) : data.length === 0 ? (
            <p className="p-4 text-sm text-gray-400">No verifications yet. Use the Verify tab to check a student.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-4 py-2 text-xs text-gray-500 font-medium">Time</th>
                  <th className="text-left px-4 py-2 text-xs text-gray-500 font-medium">Student</th>
                  <th className="text-left px-4 py-2 text-xs text-gray-500 font-medium">Institution</th>
                  <th className="text-left px-4 py-2 text-xs text-gray-500 font-medium">Result</th>
                </tr>
              </thead>
              <tbody>
                {data.map((c) => (
                  <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-2 text-xs text-gray-500 whitespace-nowrap">
                      {new Date(c.verified_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-gray-700">{c.student_display}</td>
                    <td className="px-4 py-2 text-gray-600 text-xs">{c.institution}</td>
                    <td className="px-4 py-2">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                        c.result === "enrolled"
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-600"
                      }`}>
                        {c.result.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </Layout>
  );
}
