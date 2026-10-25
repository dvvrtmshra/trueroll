import Layout from "../../components/Layout";

const SECTIONS = [
  {
    title: "What we store about you",
    body: "Your name, course, enrolment status, and APAAR ID tier. Your phone number and guardian name are never stored — only a keyed token that cannot be reversed.",
  },
  {
    title: "Who can see your record",
    body: "National and Regional Officers see aggregated counts. College Admins see your name, course, and status within their institution. No one can see your full APAAR ID — not even officers.",
  },
  {
    title: "When an employer verifies you",
    body: "They see only: enrolled yes/no, college name, programme, and an expiry date. They never see marks, address, date of birth, phone, other institutions, or any flag against your record.",
  },
  {
    title: "You control employer access",
    body: "Each share code is single-employer and time-limited. You can withdraw it instantly at any time. Withdrawal takes effect on the next scan — there is no delay.",
  },
  {
    title: "Your access log",
    body: "Every time your record is read by an employer, officer, or admin, an entry appears in your access log. You can review it at any time.",
  },
  {
    title: "Data retention",
    body: "Your record is retained for the period required under AICTE regulations. After that period, your record will be anonymised. This is a simulated system — no real data is retained.",
  },
];

export default function DataPrivacyPage() {
  return (
    <Layout>
      <div className="max-w-sm mx-auto mt-6">
        <h1 className="text-lg font-bold text-[#0B2545] mb-1">Data &amp; Privacy</h1>
        <p className="text-xs text-gray-500 mb-5">How TrueRoll handles your information</p>

        <div className="space-y-4">
          {SECTIONS.map((s) => (
            <div key={s.title} className="bg-white rounded-xl border border-[#E2E8F0] p-4">
              <p className="text-sm font-semibold text-[#0B2545] mb-1">{s.title}</p>
              <p className="text-sm text-gray-600 leading-relaxed">{s.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 bg-amber-50 border border-amber-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-amber-800 mb-1">SAMPLE DATA</p>
          <p className="text-xs text-amber-700">
            This is a prototype. No real student data is collected or stored. All names, IDs, and institutions are fictional.
          </p>
        </div>
      </div>
    </Layout>
  );
}
