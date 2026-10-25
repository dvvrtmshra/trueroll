import { useQuery } from "@tanstack/react-query";
import api from "../../lib/api";
import Layout from "../../components/Layout";

export default function ChangelogPage() {
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ["audit-rules"],
    queryFn: () => api.get("/audit/entries?object_type=rule_version&limit=100").then((r) => r.data),
  });

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-6">Rule changelog</h1>
        {isLoading ? (
          <div className="text-gray-500 text-sm">Loading…</div>
        ) : entries.length === 0 ? (
          <div className="bg-white rounded-lg border border-[#E2E8F0] p-8 text-center text-gray-500">
            No rule audit entries yet.
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-[#E2E8F0] overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Time</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Actor</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Action</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Rule</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {entries.map((e: { id: number; time: string; actor: string; action: string; object_id: string }) => (
                  <tr key={e.id}>
                    <td className="px-4 py-3 text-gray-500 text-xs">{e.time?.slice(0, 19).replace("T", " ")}</td>
                    <td className="px-4 py-3 text-gray-700">{e.actor}</td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">{e.action}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-blue-600">{e.object_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
