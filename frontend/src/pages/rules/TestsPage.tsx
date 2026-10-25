import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import api from "../../lib/api";
import Layout from "../../components/Layout";

interface TestResult {
  scenario: string;
  expected: string;
  actual: string;
  pass: boolean;
}

interface BacktestResult {
  changes: Array<{
    institution_id: string;
    institution_name: string;
    course_id: string;
    course_name: string;
    old_status: string;
    new_status: string;
  }>;
  total_courses: number;
  changed: number;
}

export default function TestsPage() {
  const [tab, setTab] = useState<"regression" | "backtest">("regression");
  const [testResults, setTestResults] = useState<TestResult[] | null>(null);
  const [backtestRuleId, setBacktestRuleId] = useState("");
  const [backtestVersion, setBacktestVersion] = useState(1);
  const [backtestYear, setBacktestYear] = useState("2026-27");
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);

  const { data: rules = [] } = useQuery({
    queryKey: ["rules-for-backtest"],
    queryFn: () => api.get("/rules").then((r) => r.data),
  });

  const runTestsMutation = useMutation({
    mutationFn: () => api.post("/rules/tests/run").then((r) => r.data),
    onSuccess: (data) => setTestResults(data),
  });

  const backtestMutation = useMutation({
    mutationFn: () =>
      api.post(`/rules/${backtestRuleId}/backtest`, {
        version: backtestVersion,
        academic_year: backtestYear,
      }).then((r) => r.data),
    onSuccess: (data) => setBacktestResult(data),
  });

  const allPass = testResults?.every((t) => t.pass) ?? false;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-6">Tests and backtest</h1>

        {/* Tab bar */}
        <div className="flex border-b border-[#E2E8F0] mb-6">
          {(["regression", "backtest"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm capitalize ${
                tab === t
                  ? "border-b-2 border-[#0B2545] text-[#0B2545] font-medium"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {t === "regression" ? "Regression suite" : "Backtest"}
            </button>
          ))}
        </div>

        {tab === "regression" && (
          <div>
            <div className="flex items-center gap-4 mb-4">
              <button
                onClick={() => runTestsMutation.mutate()}
                disabled={runTestsMutation.isPending}
                className="bg-[#0B2545] text-white px-4 py-2 rounded text-sm hover:bg-[#1a3a6b] disabled:opacity-50"
              >
                {runTestsMutation.isPending ? "Running…" : "▶ Run tests"}
              </button>
              {testResults && (
                <span className={`text-sm font-medium ${allPass ? "text-green-600" : "text-red-600"}`}>
                  {testResults.filter((t) => t.pass).length}/{testResults.length} passed
                </span>
              )}
            </div>

            {testResults ? (
              <div className="bg-white rounded-lg border border-[#E2E8F0] overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Scenario</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Expected</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Actual</th>
                      <th className="text-left px-4 py-3 font-medium text-gray-600">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {testResults.map((t, i) => (
                      <tr key={i} className={t.pass ? "" : "bg-red-50"}>
                        <td className="px-4 py-3 text-gray-700">{t.scenario}</td>
                        <td className="px-4 py-3 font-mono text-xs text-gray-600">{t.expected}</td>
                        <td className="px-4 py-3 font-mono text-xs">{t.actual}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${t.pass ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                            {t.pass ? "PASS" : "FAIL"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-gray-50 rounded border border-dashed border-gray-200 p-8 text-center text-gray-400 text-sm">
                Click "Run tests" to run the regression suite (S1–S5, S14, S18).
              </div>
            )}
          </div>
        )}

        {tab === "backtest" && (
          <div>
            <div className="bg-white rounded-lg border border-[#E2E8F0] p-5 mb-4">
              <h2 className="font-semibold text-[#0B2545] mb-4">Configure backtest</h2>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rule</label>
                  <select
                    value={`${backtestRuleId}|${backtestVersion}`}
                    onChange={(e) => {
                      const [rid, v] = e.target.value.split("|");
                      setBacktestRuleId(rid);
                      setBacktestVersion(parseInt(v));
                    }}
                    className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                  >
                    <option value="|">Select a rule…</option>
                    {rules.map((rv: { rule_id: string; version: number; status: string }) => (
                      <option key={`${rv.rule_id}|${rv.version}`} value={`${rv.rule_id}|${rv.version}`}>
                        {rv.rule_id} v{rv.version} ({rv.status})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Academic year</label>
                  <select
                    value={backtestYear}
                    onChange={(e) => setBacktestYear(e.target.value)}
                    className="w-full border border-gray-200 rounded px-3 py-2 text-sm"
                  >
                    <option>2026-27</option>
                    <option>2025-26</option>
                  </select>
                </div>
                <div className="flex items-end">
                  <button
                    onClick={() => backtestMutation.mutate()}
                    disabled={!backtestRuleId || backtestMutation.isPending}
                    className="bg-[#0B2545] text-white px-4 py-2 rounded text-sm hover:bg-[#1a3a6b] disabled:opacity-50"
                  >
                    {backtestMutation.isPending ? "Running…" : "Run backtest"}
                  </button>
                </div>
              </div>
            </div>

            {backtestResult && (
              <div>
                <p className="text-sm text-gray-600 mb-3">
                  {backtestResult.changed} of {backtestResult.total_courses} courses would change status.
                </p>
                {backtestResult.changes.length === 0 ? (
                  <div className="bg-green-50 border border-green-200 rounded p-4 text-sm text-green-700">
                    No institutions would change status under this rule.
                  </div>
                ) : (
                  <div className="bg-white rounded-lg border border-[#E2E8F0] overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="text-left px-4 py-3 font-medium text-gray-600">Institution</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-600">Course</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-600">Before</th>
                          <th className="text-left px-4 py-3 font-medium text-gray-600">After</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E2E8F0]">
                        {backtestResult.changes.map((c, i) => (
                          <tr key={i}>
                            <td className="px-4 py-3 text-gray-700">{c.institution_name}</td>
                            <td className="px-4 py-3 text-gray-600">{c.course_name}</td>
                            <td className="px-4 py-3">
                              <span className="text-xs font-mono">{c.old_status}</span>
                            </td>
                            <td className="px-4 py-3">
                              <span className={`text-xs font-mono font-semibold ${c.new_status === "FLAG" ? "text-red-600" : c.new_status === "OK" ? "text-green-600" : "text-amber-600"}`}>
                                {c.new_status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
