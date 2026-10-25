import Layout from "../../components/Layout";

const SECTIONS = [
  {
    title: "Identity tiers",
    body: "T1: APAAR ID verified against the national registry. T2: APAAR provided but registry check pending. T3: No APAAR ID yet — a reminder will be sent before the deadline. T4: Foreign national or student who opted out — counted but not penalised.",
  },
  {
    title: "Seat rules",
    body: "Rules define how many extra seats are allowed beyond the approved intake. Rules are marked 'Illustrative: to be confirmed against AICTE rules' until officially approved by two different people.",
  },
  {
    title: "Flags",
    body: "A flag is raised when the seat-ledger detects a potential issue. A flag is not a finding — an officer reviews it. You can reply with an explanation or upload corrected data.",
  },
  {
    title: "Fixing upload errors",
    body: "Download the error report from the Upload wizard. Fix the rows and re-upload. Re-uploading the same file (same content) is safe — it changes nothing.",
  },
  {
    title: "Duplicate cases",
    body: "D1: same student in the same file — data error. D2: same APAAR at two different full-time colleges — needs review. D3: same APAAR in a physical and an online programme — may be permitted. D4/D5: fuzzy name/DOB match — advisory, nobody is rejected automatically.",
  },
];

export default function HelpPage() {
  return (
    <Layout>
      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-6">Help</h1>
        <div className="space-y-4">
          {SECTIONS.map((s) => (
            <div key={s.title} className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm">
              <h2 className="font-semibold text-[#0B2545] mb-2">{s.title}</h2>
              <p className="text-sm text-gray-600">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
