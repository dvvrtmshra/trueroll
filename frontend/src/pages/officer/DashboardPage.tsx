import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import KpiCard from "../../components/KpiCard";
import SimulatedChip from "../../components/SimulatedChip";
import { useStream, StreamEvent } from "../../lib/useStream";

interface Stats {
  colleges_total: number;
  colleges_reported: number;
  students_total: number;
  flags_open: number;
  identity_coverage_pct: number;
  identity_mix: Record<string, number>;
  flag_ageing: Record<string, number>;
  seat_usage_by_region: { region: string; used: number; capacity: number; pct: number }[];
}

interface ActivityItem {
  id: number;
  time: string;
  message: string;
  action: string;
  institution_name: string;
}

const TIER_COLORS = ["#1B8A3E", "#0B2545", "#D9730D", "#9CA3AF"];
const TIER_LABELS = ["T1", "T2", "T3", "T4"];

function timeAgo(iso: string) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function DashboardPage() {
  const [unread, setUnread] = useState(0);
  const [liveItems, setLiveItems] = useState<ActivityItem[]>([]);

  const { data: stats } = useQuery<Stats>({
    queryKey: ["dashboard-stats"],
    queryFn: () => api.get("/dashboard/stats").then((r) => r.data),
    refetchInterval: 30_000,
  });

  const { data: activity = [] } = useQuery<ActivityItem[]>({
    queryKey: ["activity"],
    queryFn: () => api.get("/activity?limit=20").then((r) => r.data),
    staleTime: 10_000,
  });

  const handleEvent = useCallback((e: StreamEvent) => {
    if (e.type === "upload_finished" || e.type === "flag_created") {
      setUnread((n) => n + 1);
      setLiveItems((prev) => [
        {
          id: Date.now(),
          time: (e.timestamp as string) || new Date().toISOString(),
          message: e.type === "upload_finished"
            ? `${e.institution_name} uploaded ${e.rows_accepted} students`
            : `Flag raised for ${e.institution_name}`,
          action: e.type,
          institution_name: (e.institution_name as string) || "",
        },
        ...prev.slice(0, 19),
      ]);
    }
  }, []);

  useStream(handleEvent);

  const allActivity: ActivityItem[] = [
    ...liveItems,
    ...activity.filter((a) => !liveItems.some((l) => l.id === a.id)),
  ].slice(0, 20);

  const regionData = stats?.seat_usage_by_region ?? [];

  const identityPieData = stats
    ? TIER_LABELS.map((t, i) => ({
        name: t,
        value: stats.identity_mix[t] ?? 0,
        color: TIER_COLORS[i],
      }))
    : [];

  const flagAgeData = stats
    ? [
        { name: "0-3d", value: stats.flag_ageing.d0_3 ?? 0 },
        { name: "4-7d", value: stats.flag_ageing.d4_7 ?? 0 },
        { name: "8-14d", value: stats.flag_ageing.d8_14 ?? 0 },
        { name: ">14d", value: stats.flag_ageing.gt14 ?? 0 },
      ]
    : [];

  return (
    <Layout unreadCount={unread}>
      <h1 className="text-xl font-bold text-[#0B2545] mb-4">Dashboard</h1>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="Colleges Reported"
          value={`${stats?.colleges_reported ?? "—"} / ${stats?.colleges_total ?? "—"}`}
          color="blue"
        />
        <KpiCard
          label="Students"
          value={stats?.students_total?.toLocaleString() ?? "—"}
          color="blue"
        />
        <KpiCard
          label="Open Flags"
          value={stats?.flags_open ?? "—"}
          color={stats?.flags_open ? "red" : "green"}
        />
        <KpiCard
          label="Identity Coverage"
          value={`${stats?.identity_coverage_pct ?? "—"}%`}
          sub="T1 + T2"
          color={
            (stats?.identity_coverage_pct ?? 0) >= 70 ? "green"
            : (stats?.identity_coverage_pct ?? 0) >= 50 ? "amber"
            : "red"
          }
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Region bar chart */}
        <div className="bg-white rounded-lg border border-[#E2E8F0] p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Seat Usage by Region</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={regionData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="region" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} unit="%" domain={[0, 100]} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="pct" fill="#0B2545" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Live activity */}
        <div className="bg-white rounded-lg border border-[#E2E8F0] p-4">
          <div className="flex items-center gap-2 mb-3">
            <h2 className="text-sm font-semibold text-gray-700">Live Activity</h2>
            <SimulatedChip />
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {allActivity.length === 0 && (
              <p className="text-xs text-gray-400">No recent activity.</p>
            )}
            {allActivity.map((item, i) => (
              <div key={`${item.id}-${i}`} className="flex gap-2 text-xs">
                <span className="text-gray-400 whitespace-nowrap flex-shrink-0">
                  {timeAgo(item.time)}
                </span>
                <span className="text-gray-700 truncate">{item.message}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Identity mix + flag ageing */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-[#E2E8F0] p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Identity Mix</h2>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={identityPieData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={70}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
                labelLine={false}
              >
                {identityPieData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg border border-[#E2E8F0] p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Flag Ageing</h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={flagAgeData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#D62828" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Layout>
  );
}
