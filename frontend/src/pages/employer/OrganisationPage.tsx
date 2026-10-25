import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/auth";
import Layout from "../../components/Layout";
import api from "../../lib/api";

export default function OrganisationPage() {
  const user = useAuthStore((s) => s.user) as Record<string, unknown> | null;
  const employerId = user?.employer_id as string | undefined;

  const { data, isLoading } = useQuery({
    queryKey: ["employer", employerId],
    queryFn: () => api.get(`/employers/${employerId}`).then((r) => r.data),
    enabled: !!employerId,
  });

  return (
    <Layout>
      <div className="max-w-sm mx-auto mt-8">
        <h1 className="text-lg font-bold text-[#0B2545] mb-4">My organisation</h1>
        {isLoading ? (
          <p className="text-sm text-gray-400">Loading…</p>
        ) : data ? (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow p-5 space-y-3">
            <Row label="Name" value={data.name} />
            <Row label="CIN / Reg no." value={data.registration_number ?? "—"} />
            <Row label="Industry" value={data.industry ?? "—"} />
            <Row label="Status" value={data.status ?? "active"} />
          </div>
        ) : (
          <p className="text-sm text-gray-500">No organisation record found.</p>
        )}

        <div className="mt-6 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-4">
          <p className="text-xs text-gray-500 leading-relaxed">
            Your organisation details are set by the AICTE system administrator. Contact support to update them.
          </p>
        </div>
      </div>
    </Layout>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className="text-sm font-medium text-[#0B2545]">{value}</p>
    </div>
  );
}
