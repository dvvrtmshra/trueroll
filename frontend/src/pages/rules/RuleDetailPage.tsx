import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import IllustrativeLabel from "../../components/IllustrativeLabel";

export default function RuleDetailPage() {
  const { ruleId, version } = useParams<{ ruleId: string; version: string }>();

  const { data: rv, isLoading } = useQuery({
    queryKey: ["rule-version", ruleId, version],
    queryFn: () => api.get(`/rules/${ruleId}/versions/${version}`).then((r) => r.data),
    enabled: !!ruleId && !!version,
  });

  const { data: allVersions = [] } = useQuery({
    queryKey: ["rule-versions", ruleId],
    queryFn: () => api.get(`/rules/${ruleId}/versions`).then((r) => r.data),
    enabled: !!ruleId,
  });

  if (isLoading) return <Layout><div className="text-gray-500 text-sm p-6">Loading…</div></Layout>;
  if (!rv) return <Layout><div className="text-red-500 p-6">Rule version not found.</div></Layout>;

  const approvals: Array<{ by: string; role: string; at: string; reason?: string }> =
    JSON.parse(rv.approvals || "[]");
  const levels: string[] = JSON.parse(rv.programme_level || "[]");
  const categories: string[] = JSON.parse(rv.eligible_categories || "[]");

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <h1 className="text-2xl font-bold text-[#0B2545]">
            Rule {rv.rule_id} — Version {rv.version}
          </h1>
          <span className="px-2 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-700 text-xs font-medium capitalize">
            {rv.status.replace("_", " ")}
          </span>
        </div>

        <div className="mb-4">
          <IllustrativeLabel />
        </div>

        {/* Two-column provenance */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg border border-[#E2E8F0] p-5">
            <h2 className="font-semibold text-[#0B2545] mb-3">What it says</h2>
            <dl className="space-y-2 text-sm">
              <div><dt className="text-gray-500">Bucket</dt><dd className="font-mono">{rv.bucket}</dd></div>
              <div><dt className="text-gray-500">Cap</dt>
                <dd>{rv.cap_basis === "PERCENT_OF_INTAKE" ? `${rv.cap_percent}% of approved intake` : `${rv.cap_fixed} fixed seats`}</dd>
              </div>
              <div><dt className="text-gray-500">Eligible categories</dt>
                <dd>{categories.length > 0 ? categories.join(", ") : "All"}</dd>
              </div>
              <div><dt className="text-gray-500">Scope</dt>
                <dd>{levels.join(", ")} · {rv.domain} · {rv.state} · {rv.institution_type}</dd>
              </div>
              <div><dt className="text-gray-500">Academic year</dt><dd>{rv.academic_year}</dd></div>
              <div><dt className="text-gray-500">Effective from</dt><dd>{rv.effective_from ?? "Open"}</dd></div>
              <div><dt className="text-gray-500">Effective to</dt><dd>{rv.effective_to ?? "Open-ended"}</dd></div>
            </dl>
          </div>

          <div className="bg-white rounded-lg border border-[#E2E8F0] p-5">
            <h2 className="font-semibold text-[#0B2545] mb-3">Where it comes from</h2>
            <dl className="space-y-2 text-sm">
              <div><dt className="text-gray-500">Document</dt><dd>{rv.source_document}</dd></div>
              <div><dt className="text-gray-500">Clause</dt><dd>{rv.source_clause}</dd></div>
              {rv.source_url && (
                <div><dt className="text-gray-500">URL</dt>
                  <dd><a href={rv.source_url} className="text-blue-600 hover:underline text-xs">{rv.source_url}</a></dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {/* Approvals trail */}
        {approvals.length > 0 && (
          <div className="bg-white rounded-lg border border-[#E2E8F0] p-5 mb-6">
            <h2 className="font-semibold text-[#0B2545] mb-3">Approvals</h2>
            <div className="flex items-center gap-2 flex-wrap text-sm">
              {approvals.map((a, i) => (
                <span key={i} className="flex items-center gap-1">
                  {i > 0 && <span className="text-gray-400">→</span>}
                  <span className="bg-gray-100 px-2 py-1 rounded">
                    {a.role === "proposer" ? "Proposed by" : a.role === "rejector" ? "Rejected by" : "Approved by"}{" "}
                    <strong>{a.by}</strong>
                    {a.at && <span className="text-gray-400 text-xs ml-1">({a.at.slice(0, 10)})</span>}
                    {a.reason && <span className="text-red-600 ml-1">: {a.reason}</span>}
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Used by */}
        <div className="bg-white rounded-lg border border-[#E2E8F0] p-5 mb-6">
          <h2 className="font-semibold text-[#0B2545] mb-1">Used by</h2>
          <p className="text-sm text-gray-600">{rv.evaluation_count ?? 0} evaluations (rule version stored with each one)</p>
        </div>

        {/* Version history */}
        {allVersions.length > 1 && (
          <div className="bg-white rounded-lg border border-[#E2E8F0] p-5 mb-6">
            <h2 className="font-semibold text-[#0B2545] mb-3">Version history</h2>
            <div className="flex items-center gap-2 flex-wrap text-sm">
              {allVersions.map((v: { version: number; status: string; academic_year: string }, i: number) => (
                <span key={v.version} className="flex items-center gap-1">
                  {i > 0 && <span className="text-gray-400">→</span>}
                  <a
                    href={`/rules/${ruleId}/versions/${v.version}`}
                    className={`px-2 py-1 rounded ${v.version === rv.version ? "bg-[#0B2545] text-white" : "bg-gray-100 text-blue-600 hover:underline"}`}
                  >
                    v{v.version} <span className="text-xs opacity-70">{v.status} ({v.academic_year})</span>
                  </a>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
