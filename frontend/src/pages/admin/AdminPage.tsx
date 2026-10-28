import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import api from "../../lib/api";

type Tab = "health" | "simulators" | "scenarios" | "clock" | "keys" | "jobs" | "tamper" | "backups";
const TABS: { id: Tab; label: string }[] = [
  { id: "health", label: "Health" },
  { id: "simulators", label: "Simulators" },
  { id: "scenarios", label: "Scenarios" },
  { id: "clock", label: "Clock" },
  { id: "keys", label: "Keys" },
  { id: "jobs", label: "Jobs" },
  { id: "tamper", label: "Tamper demo" },
  { id: "backups", label: "Backups" },
];

const SCENARIOS = ["S1", "S2", "S3", "S4", "S5"];
const REGISTRY_MODES = ["up", "slow", "flaky", "down"];

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("health");

  return (
    <Layout>
      <div className="max-w-5xl mx-auto py-6 px-4">
        <h1 className="text-xl font-bold text-[#0B2545] mb-4">System Admin</h1>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-[#E2E8F0] overflow-x-auto">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                tab === t.id
                  ? "border-[#0B2545] text-[#0B2545]"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "health" && <HealthTab />}
        {tab === "simulators" && <SimulatorsTab />}
        {tab === "scenarios" && <ScenariosTab />}
        {tab === "clock" && <ClockTab />}
        {tab === "keys" && <KeysTab />}
        {tab === "jobs" && <JobsTab />}
        {tab === "tamper" && <TamperTab />}
        {tab === "backups" && <BackupsTab />}
      </div>
    </Layout>
  );
}

// ── Health ────────────────────────────────────────────────────────────────────

function HealthTab() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["admin-health"],
    queryFn: () => api.get("/admin/health").then(r => r.data),
    refetchInterval: 30_000,
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-[#0B2545]">Service health</h2>
        <button onClick={() => refetch()} className="text-xs text-blue-600 hover:underline">Refresh</button>
      </div>
      {isLoading ? <p className="text-gray-400 text-sm">Checking…</p> : (
        <div className="space-y-2">
          {data && Object.entries(data.services as Record<string, Record<string, unknown>>).map(([name, svc]) => (
            <div key={name} className="flex items-center justify-between bg-white border border-[#E2E8F0] rounded-lg px-4 py-3">
              <span className="font-medium text-[#0B2545] capitalize">{name.replace(/_/g, " ")}</span>
              <div className="flex items-center gap-2">
                {svc.mode != null && <span className="text-xs text-gray-500">Mode: {String(svc.mode)}</span>}
                {svc.entries !== undefined && <span className="text-xs text-gray-500">{svc.entries as number} entries</span>}
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  svc.status === "ok" ? "bg-green-100 text-green-700" :
                  svc.status === "degraded" ? "bg-amber-100 text-amber-700" :
                  "bg-red-100 text-red-700"
                }`}>
                  {svc.status as string}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Simulators ────────────────────────────────────────────────────────────────

function SimulatorsTab() {
  const [registryMode, setRegistryMode] = useState("up");
  const [msg, setMsg] = useState("");

  const setMode = useMutation({
    mutationFn: (mode: string) => api.post("/sim/mode", { mode }),
    onSuccess: (_, mode) => {
      setMsg(`Registry mode set to "${mode}"`);
      setRegistryMode(mode);
    },
  });

  const { data: regData } = useQuery({
    queryKey: ["registry-integration"],
    queryFn: () => api.get("/admin/integration-register").then(r => r.data),
  });

  return (
    <div className="space-y-4">
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
        {regData?.note ?? "Live APAAR and DigiLocker access needs registered approval (API Setu requester onboarding). This prototype uses a simulator behind the same adapter."}
      </div>

      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5">
        <h3 className="font-semibold text-[#0B2545] mb-3">Registry simulator mode</h3>
        <div className="flex gap-2 flex-wrap mb-2">
          {REGISTRY_MODES.map(mode => (
            <button
              key={mode}
              onClick={() => setMode.mutate(mode)}
              className={`px-4 py-2 text-sm font-medium rounded-lg border transition-colors capitalize ${
                registryMode === mode
                  ? "bg-[#0B2545] text-white border-[#0B2545]"
                  : "bg-white text-gray-700 border-gray-300 hover:border-[#0B2545]"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
        {msg && <p className="text-xs text-green-600">{msg}</p>}
      </div>

      {/* Integration register */}
      {regData?.integrations && (
        <div className="bg-white border border-[#E2E8F0] rounded-xl overflow-hidden">
          <h3 className="font-semibold text-[#0B2545] px-5 py-3 border-b border-[#E2E8F0]">Integration register</h3>
          <table className="w-full text-sm">
            <thead className="bg-[#F8FAFC]">
              <tr>
                {["Integration", "Purpose", "Status"].map(h => (
                  <th key={h} className="text-left px-4 py-2 text-xs text-gray-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(regData.integrations as Array<Record<string, string>>).map((integ, i) => (
                <tr key={i} className="border-t border-[#F1F5F9]">
                  <td className="px-4 py-2 font-medium text-[#0B2545]">{integ.name}</td>
                  <td className="px-4 py-2 text-gray-600">{integ.purpose}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      integ.status === "SIMULATED" ? "bg-orange-100 text-orange-700 border border-orange-300" :
                      integ.status === "FUTURE" ? "bg-gray-100 text-gray-500" :
                      "bg-green-100 text-green-700"
                    }`}>{integ.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Scenarios ─────────────────────────────────────────────────────────────────

function ScenariosTab() {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  async function loadScenario(id: string) {
    setLoading(id);
    try {
      const r = await api.post(`/admin/scenarios/${id}`);
      setResult(r.data);
    } catch (e: unknown) {
      setResult({ error: (e as Error).message ?? "Error" });
    } finally {
      setLoading(null);
    }
  }

  async function resetDemo() {
    setLoading("reset");
    try {
      const r = await api.post("/admin/reset-demo");
      setResult(r.data);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5">
        <h3 className="font-semibold text-[#0B2545] mb-3">Load a scenario</h3>
        <div className="flex gap-2 flex-wrap mb-4">
          {SCENARIOS.map(s => (
            <button
              key={s}
              onClick={() => loadScenario(s)}
              disabled={loading === s}
              className="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-lg hover:border-[#0B2545] text-[#0B2545] disabled:opacity-50"
            >
              {loading === s ? "Loading…" : `Load ${s}`}
            </button>
          ))}
        </div>
        <button
          onClick={resetDemo}
          disabled={loading === "reset"}
          className="px-4 py-2 text-sm font-semibold bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
        >
          {loading === "reset" ? "Resetting…" : "Reset demo"}
        </button>
      </div>
      {result && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <pre className="text-xs overflow-auto">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

// ── Clock ─────────────────────────────────────────────────────────────────────

function ClockTab() {
  const qc = useQueryClient();
  const [toDate, setToDate] = useState("");
  const [msg, setMsg] = useState("");

  const { data: clockData } = useQuery({
    queryKey: ["demo-clock"],
    queryFn: () => api.get("/admin/clock").then(r => r.data),
  });

  const advanceMut = useMutation({
    mutationFn: (d: string) => api.post("/admin/clock/advance", { to_date: d }),
    onSuccess: (r) => {
      setMsg(`Clock advanced to ${r.data.new_date}. ${r.data.rules_activated?.length ?? 0} rules activated.`);
      qc.invalidateQueries({ queryKey: ["demo-clock"] });
    },
  });

  function advanceOneDay() {
    if (!clockData?.demo_date) return;
    const d = new Date(clockData.demo_date);
    d.setDate(d.getDate() + 1);
    advanceMut.mutate(d.toISOString().slice(0, 10));
  }

  return (
    <div className="space-y-4">
      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5">
        <h3 className="font-semibold text-[#0B2545] mb-2">Demo clock</h3>
        <p className="text-sm text-gray-600 mb-4">
          Current demo date: <span className="font-mono font-semibold">{clockData?.demo_date ?? "…"}</span>
        </p>
        <div className="flex gap-3 items-end flex-wrap">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Set to date</label>
            <input
              type="date"
              value={toDate}
              onChange={e => setToDate(e.target.value)}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm"
            />
          </div>
          <button
            onClick={() => toDate && advanceMut.mutate(toDate)}
            disabled={!toDate || advanceMut.isPending}
            className="px-4 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#0B2545]/90 disabled:opacity-50"
          >
            Set date
          </button>
          <button
            onClick={advanceOneDay}
            disabled={advanceMut.isPending}
            className="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-lg hover:border-[#0B2545] text-[#0B2545] disabled:opacity-50"
          >
            Advance one day
          </button>
        </div>
        {msg && <p className="text-xs text-green-600 mt-2">{msg}</p>}
      </div>
    </div>
  );
}

// ── Keys ──────────────────────────────────────────────────────────────────────

function KeysTab() {
  const { data } = useQuery({
    queryKey: ["admin-keys"],
    queryFn: () => api.get("/admin/keys").then(r => r.data),
  });
  const [msg, setMsg] = useState("");

  async function rotate() {
    const r = await api.post("/admin/keys/rotate");
    setMsg(`Key rotated. New key: ${r.data.new_key_id}`);
  }

  return (
    <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 space-y-3">
      <h3 className="font-semibold text-[#0B2545]">Signing keys</h3>
      <p className="text-sm text-gray-600">Active key: <span className="font-mono">{data?.active_key_id ?? "…"}</span></p>
      <p className="text-xs text-gray-400">{data?.note}</p>
      <button
        onClick={rotate}
        className="px-4 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#0B2545]/90"
      >
        Rotate key
      </button>
      {msg && <p className="text-xs text-green-600">{msg}</p>}
    </div>
  );
}

// ── Jobs ──────────────────────────────────────────────────────────────────────

function JobsTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-jobs"],
    queryFn: () => api.get("/admin/jobs").then(r => r.data),
    refetchInterval: 10_000,
  });

  const jobs = data?.items ?? [];

  return (
    <div>
      <h3 className="font-semibold text-[#0B2545] mb-3">Upload jobs</h3>
      <div className="bg-white rounded-xl border border-[#E2E8F0] overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[#F8FAFC] border-b border-[#E2E8F0]">
            <tr>
              {["ID", "Institution", "Year", "Status", "Rows", "Accepted", "Errors", "Created"].map(h => (
                <th key={h} className="text-left px-3 py-2 text-xs font-semibold text-gray-500 uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={8} className="text-center text-gray-400 py-8">Loading…</td></tr>
            ) : jobs.length === 0 ? (
              <tr><td colSpan={8} className="text-center text-gray-400 py-8">No jobs.</td></tr>
            ) : jobs.map((j: Record<string, unknown>, i: number) => (
              <tr key={i} className="border-b border-[#F1F5F9]">
                <td className="px-3 py-2 text-xs font-mono text-gray-500">{String(j.id).slice(-8)}</td>
                <td className="px-3 py-2 text-gray-700">{j.institution_id as string}</td>
                <td className="px-3 py-2 text-gray-600">{j.academic_year as string}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                    j.status === "completed" ? "bg-green-100 text-green-700" :
                    j.status === "failed" ? "bg-red-100 text-red-700" :
                    j.status === "processing" ? "bg-blue-100 text-blue-700" :
                    "bg-gray-100 text-gray-500"
                  }`}>{j.status as string}</span>
                </td>
                <td className="px-3 py-2">{j.rows_total as number ?? "—"}</td>
                <td className="px-3 py-2 text-green-700">{j.rows_accepted as number ?? "—"}</td>
                <td className="px-3 py-2 text-red-700">{j.rows_error as number ?? "—"}</td>
                <td className="px-3 py-2 text-xs text-gray-400">
                  {j.created_at ? new Date(j.created_at as string).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Tamper demo ───────────────────────────────────────────────────────────────

function TamperTab() {
  const [entryId, setEntryId] = useState("");
  const [tamperResult, setTamperResult] = useState<Record<string, unknown> | null>(null);
  const [restoreResult, setRestoreResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  async function doTamper() {
    if (!entryId) return;
    setLoading(true);
    try {
      const r = await api.post("/admin/tamper", { entry_id: parseInt(entryId) });
      setTamperResult(r.data);
      setRestoreResult(null);
    } finally {
      setLoading(false);
    }
  }

  async function doRestore() {
    setLoading(true);
    try {
      const r = await api.post("/admin/restore");
      setRestoreResult(r.data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-amber-50 border-2 border-amber-300 rounded-xl px-5 py-4">
        <p className="font-semibold text-amber-800">Prototype demonstration only</p>
        <p className="text-sm text-amber-700 mt-1">
          This directly edits one audit entry in the database to demonstrate that the Auditor's
          chain verify will detect any such edit. Use "Restore" to repair it. Never do this in production.
        </p>
      </div>

      <div className="bg-white border border-[#E2E8F0] rounded-xl p-5 space-y-3">
        <h3 className="font-semibold text-[#0B2545]">Edit an old audit entry</h3>
        <div className="flex gap-3 items-end">
          <div>
            <label className="text-xs text-gray-500 block mb-1">Audit entry ID</label>
            <input
              type="number"
              value={entryId}
              onChange={e => setEntryId(e.target.value)}
              placeholder="e.g. 1"
              className="border border-gray-300 rounded px-3 py-1.5 text-sm w-32"
            />
          </div>
          <button
            onClick={doTamper}
            disabled={!entryId || loading}
            className="px-4 py-2 text-sm font-semibold bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            Tamper entry
          </button>
          <button
            onClick={doRestore}
            disabled={loading || !tamperResult}
            className="px-4 py-2 text-sm font-semibold bg-[#0B2545] text-white rounded-lg hover:bg-[#0B2545]/90 disabled:opacity-50"
          >
            Restore
          </button>
        </div>

        {tamperResult && !restoreResult && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-800">
            Entry tampered. Now go to the Audit trail screen and click "Verify chain now" — the chain will show as broken.
          </div>
        )}
        {restoreResult && (
          <div className="bg-green-50 border border-green-200 rounded p-3 text-sm text-green-800">
            Entry restored. Verify chain again — it will show as valid.
          </div>
        )}
      </div>
    </div>
  );
}

// ── Backups ───────────────────────────────────────────────────────────────────

function BackupsTab() {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl px-5 py-4">
      <p className="font-semibold text-amber-800">Backups are planned for production and not yet tested.</p>
      <p className="text-sm text-amber-700 mt-1">
        In production, automated daily backups of the database and vault keys would be configured here.
        For the prototype, use <code className="bg-amber-100 px-1 rounded">make seed</code> to rebuild the demo state.
      </p>
    </div>
  );
}
