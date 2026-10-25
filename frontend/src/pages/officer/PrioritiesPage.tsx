import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import Layout from "../../components/Layout";
import SimulatedChip from "../../components/SimulatedChip";
import api from "../../lib/api";

interface Reason { code: string; detail: string; }
interface Priority {
  id: string;
  institution_name: string;
  course_name: string | null;
  period: string;
  score: number;
  band: string;
  reasons: Reason[];
  peer_group: string | null;
  model_version: string;
  status: string;
  officer_label: string | null;
}

function BandChip({ band }: { band: string }) {
  const cls =
    band === "High" ? "bg-red-100 text-red-700 border-red-300" :
    band === "Medium" ? "bg-amber-100 text-amber-700 border-amber-300" :
    "bg-green-100 text-green-700 border-green-300";
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${cls}`}>{band}</span>;
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? "#D62828" : score >= 40 ? "#D9730D" : "#1B8A3E";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 bg-gray-200 rounded-full h-2">
        <div className="h-2 rounded-full" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="text-xs font-mono text-gray-700">{score}</span>
    </div>
  );
}

function ReasonChip({ code }: { code: string }) {
  return (
    <span className="inline-block px-1.5 py-0.5 rounded text-xs bg-[#EFF6FF] text-[#1e40af] border border-blue-200 mr-1">
      {code.replace(/_/g, " ")}
    </span>
  );
}

export default function PrioritiesPage() {
  const navigate = useNavigate();
  const [band, setBand] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["priorities", band],
    queryFn: () => api.get("/priorities", { params: { band: band || undefined } }).then(r => r.data),
  });

  const items: Priority[] = data?.items ?? [];
  const message: string | undefined = data?.message;

  return (
    <Layout>
      <div className="max-w-6xl mx-auto py-6 px-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-[#0B2545]">Review priorities</h1>
            <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-1.5 mt-1">
              Advisory only. Not a flag. Not a finding. An officer decides.
            </p>
          </div>
          <SimulatedChip />
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-4">
          <select
            value={band}
            onChange={e => setBand(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm"
          >
            <option value="">All bands</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>

        {isLoading ? (
          <div className="text-gray-400 text-sm py-8 text-center">Loading…</div>
        ) : message && items.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-500">{message}</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-[#E2E8F0] overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0]">
                <tr>
                  {["Institution", "Course", "Score", "Band", "Top reasons", "Model", "Officer note"].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <tr
                    key={item.id}
                    onClick={() => navigate(`/priorities/${item.id}`)}
                    className="border-b border-[#F1F5F9] hover:bg-[#F8FAFC] cursor-pointer"
                  >
                    <td className="px-4 py-3 font-medium text-[#0B2545]">{item.institution_name}</td>
                    <td className="px-4 py-3 text-gray-600">{item.course_name ?? "—"}</td>
                    <td className="px-4 py-3"><ScoreBar score={item.score} /></td>
                    <td className="px-4 py-3"><BandChip band={item.band} /></td>
                    <td className="px-4 py-3">
                      {item.reasons.slice(0, 2).map(r => <ReasonChip key={r.code} code={r.code} />)}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">{item.model_version}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">{item.officer_label?.replace(/_/g, " ") ?? "—"}</td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr><td colSpan={7} className="text-center text-gray-400 py-8">No priorities found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
