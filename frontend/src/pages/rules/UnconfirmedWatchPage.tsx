import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import api from "../../lib/api";
import Layout from "../../components/Layout";

export default function UnconfirmedWatchPage() {
  const { data: items = [], isLoading } = useQuery({
    queryKey: ["rules-unconfirmed"],
    queryFn: () => api.get("/rules/unconfirmed").then((r) => r.data),
  });

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-2">Unconfirmed-rule watch</h1>
        <p className="text-sm text-gray-500 mb-6">
          Courses whose most recent Seat-Ledger evaluation depends on a Draft, Pending or missing rule.
          No automatic action is taken. Human review required.
        </p>

        {isLoading ? (
          <div className="text-gray-500 text-sm">Loading…</div>
        ) : items.length === 0 ? (
          <div className="bg-white rounded-lg border border-[#E2E8F0] p-8 text-center text-gray-500">
            No courses with unconfirmed rules.
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-[#E2E8F0] overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Institution</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Course</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Evaluated at</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Missing rule</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {items.map((item: {
                  course_id: string;
                  institution_id: string;
                  institution_name: string;
                  course_name: string;
                  evaluated_at: string;
                  missing_rule_buckets: string;
                }) => (
                  <tr key={item.course_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-700">{item.institution_name}</td>
                    <td className="px-4 py-3">
                      <Link to={`/ledger`} className="text-blue-600 hover:underline">
                        {item.course_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {item.evaluated_at?.slice(0, 16).replace("T", " ")}
                    </td>
                    <td className="px-4 py-3 text-amber-700 text-xs font-mono">
                      {item.missing_rule_buckets}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                        Rule not confirmed: human review
                      </span>
                    </td>
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
