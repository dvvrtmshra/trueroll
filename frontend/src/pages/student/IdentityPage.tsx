import { useQuery } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import TierBadge from "../../components/TierBadge";
import api from "../../lib/api";

const tierInfo: Record<string, { title: string; body: string; colour: string }> = {
  T1: { title: "Your APAAR ID is verified.", body: "Your identity is confirmed with the national registry.", colour: "text-green-700" },
  T2: { title: "Your APAAR number was entered but not verified yet.", body: "Tap 'Verify now' to confirm with the registry. This opens a simulated consent screen.", colour: "text-amber-700" },
  T3: { title: "You have no APAAR ID yet.", body: "You are still counted and nothing is held against you. You can add your APAAR ID at any time.", colour: "text-gray-700" },
  T4: { title: "You opted out or have no route to an APAAR ID.", body: "You are counted. No penalty.", colour: "text-blue-700" },
};

export default function IdentityPage() {
  const { data } = useQuery({
    queryKey: ["student-me"],
    queryFn: () => api.get("/students/me").then((r) => r.data),
  });

  const tier = data?.identity_tier ?? "T3";
  const info = tierInfo[tier] ?? tierInfo.T3;

  function handleVerifyNow() {
    window.open(`/api/sim/registry/consent?apaar=${data?.apaar_last4 ?? ""}`, "_blank", "width=480,height=420");
  }

  return (
    <Layout>
      <div className="max-w-sm mx-auto mt-8">
        <h1 className="text-lg font-bold text-[#0B2545] mb-4">Identity</h1>
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow p-5 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <TierBadge tier={tier} />
            <span className={`text-sm font-medium ${info.colour}`}>{info.title}</span>
          </div>
          <p className="text-sm text-gray-600 mb-4">{info.body}</p>

          {tier === "T2" && (
            <button
              onClick={handleVerifyNow}
              className="w-full bg-amber-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-amber-700 mb-2"
            >
              Verify now
            </button>
          )}
          {tier === "T3" && (
            <button
              className="w-full bg-[#0B2545] text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-900 mb-2"
              onClick={() => alert("Add your APAAR ID on the Students page via your college.")}
            >
              How to get one
            </button>
          )}
        </div>

        <div className="bg-white rounded-xl border border-[#E2E8F0] p-4 space-y-2">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-2">Options</p>
          <button className="w-full text-left text-sm text-[#0B2545] py-1.5 px-3 rounded hover:bg-gray-50">
            Link my APAAR ID →
          </button>
          <button className="w-full text-left text-sm text-gray-500 py-1.5 px-3 rounded hover:bg-gray-50">
            I do not have one →
          </button>
          <button className="w-full text-left text-sm text-gray-500 py-1.5 px-3 rounded hover:bg-gray-50">
            I want to opt out →
          </button>
          <button className="w-full text-left text-sm text-gray-500 py-1.5 px-3 rounded hover:bg-gray-50">
            I am a foreign national →
          </button>
        </div>
      </div>
    </Layout>
  );
}
