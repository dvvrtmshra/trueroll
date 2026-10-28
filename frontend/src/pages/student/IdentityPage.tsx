import { useQuery } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import TierBadge from "../../components/TierBadge";
import LoadingSpinner from "../../components/LoadingSpinner";
import api from "../../lib/api";

const tierInfo: Record<string, { title: string; titleHi: string; body: string; colour: string }> = {
  T1: { title: "Your APAAR ID is verified.", titleHi: "आपकी APAAR ID सत्यापित है।", body: "Your identity is confirmed with the national registry.", colour: "text-green-700" },
  T2: { title: "Your APAAR number was entered but not verified yet.", titleHi: "APAAR नंबर दर्ज है लेकिन सत्यापित नहीं।", body: "Tap 'Verify now' to confirm with the registry. This opens a simulated consent screen.", colour: "text-amber-700" },
  T3: { title: "You have no APAAR ID yet.", titleHi: "आपके पास अभी APAAR ID नहीं है।", body: "You are still counted and nothing is held against you. You can add your APAAR ID at any time.", colour: "text-gray-700" },
  T4: { title: "You opted out or have no route to an APAAR ID.", titleHi: "आपने APAAR से बाहर निकलने का विकल्प चुना।", body: "You are counted. No penalty.", colour: "text-blue-700" },
};

export default function IdentityPage() {
  const { data, isLoading } = useQuery({
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
      <div className="max-w-sm mx-auto mt-4 md:mt-8 px-2 md:px-0">
        <h1 className="text-lg font-bold text-[#0B2545] mb-1">
          Identity{" "}
          <span className="text-gray-400 font-normal text-base" lang="hi">पहचान</span>
        </h1>

        {isLoading ? (
          <LoadingSpinner message="Loading identity status…" />
        ) : (
          <>
            <div className="bg-white rounded-xl border border-[#E2E8F0] shadow p-5 mb-4">
              <div className="flex items-start gap-2 mb-3">
                <TierBadge tier={tier} />
                <div>
                  <p className={`text-sm font-medium ${info.colour}`}>{info.title}</p>
                  <p className={`text-xs mt-0.5 ${info.colour} opacity-70`} lang="hi">{info.titleHi}</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-4">{info.body}</p>

              {tier === "T2" && (
                <button
                  onClick={handleVerifyNow}
                  className="w-full bg-amber-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-amber-700 mb-2 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
                >
                  Verify now{" "}
                  <span lang="hi" className="text-xs font-normal opacity-80">· अभी सत्यापित करें</span>
                </button>
              )}
              {tier === "T3" && (
                <button
                  className="w-full bg-[#0B2545] text-white py-2.5 rounded-lg text-sm font-medium hover:bg-blue-900 mb-2 focus:outline-none focus:ring-2 focus:ring-[#0B2545] focus:ring-offset-2"
                  onClick={() => alert("Add your APAAR ID on the Students page via your college.")}
                >
                  How to get one{" "}
                  <span lang="hi" className="text-xs font-normal opacity-80">· कैसे प्राप्त करें</span>
                </button>
              )}
            </div>

            <div className="bg-white rounded-xl border border-[#E2E8F0] p-4 space-y-1">
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-2">
                Options <span lang="hi" className="normal-case">· विकल्प</span>
              </p>
              {[
                { en: "Link my APAAR ID", hi: "APAAR ID जोड़ें" },
                { en: "I do not have one", hi: "मेरे पास नहीं है" },
                { en: "I want to opt out", hi: "बाहर निकलना चाहता/चाहती हूँ" },
                { en: "I am a foreign national", hi: "मैं विदेशी नागरिक हूँ" },
              ].map(({ en, hi }) => (
                <button
                  key={en}
                  className="w-full text-left text-sm text-[#0B2545] py-2 px-3 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#0B2545] rounded"
                >
                  {en} →{" "}
                  <span lang="hi" className="text-gray-400 text-xs">{hi}</span>
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
