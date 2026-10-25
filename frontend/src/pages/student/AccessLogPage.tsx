import { useQuery } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import api from "../../lib/api";

export default function AccessLogPage() {
  const { data = [], isLoading } = useQuery<Record<string, unknown>[]>({
    queryKey: ["student-access-log"],
    queryFn: () => api.get("/students/me/access-log").then((r) => r.data),
  });

  return (
    <Layout>
      <div className="max-w-2xl mx-auto mt-6">
        <h1 className="text-lg font-bold text-[#0B2545] mb-4">Access log</h1>
        <p className="text-sm text-gray-500 mb-4">
          Every verification of your record, and every time an officer or college admin read your details.
        </p>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow overflow-hidden">
          {isLoading ? (
            <p className="p-4 text-sm text-gray-400">Loading…</p>
          ) : data.length === 0 ? (
            <p className="p-4 text-sm text-gray-400">No access events yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-4 py-2 text-xs text-gray-500 font-medium">Time</th>
                  <th className="text-left px-4 py-2 text-xs text-gray-500 font-medium">Who</th>
                  <th className="text-left px-4 py-2 text-xs text-gray-500 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {data.map((e, i) => (
                  <tr key={String(e.id ?? i)} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-4 py-2 text-gray-500 text-xs whitespace-nowrap">
                      {e.time ? new Date(String(e.time)).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-2 text-gray-700">{String(e.actor ?? "—")}</td>
                    <td className="px-4 py-2 text-gray-600">{String(e.action ?? "—")}</td>
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
