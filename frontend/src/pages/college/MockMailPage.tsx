import Layout from "../../components/Layout";

export default function MockMailPage() {
  return (
    <Layout>
      <div className="max-w-xl">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-4">Mock Mail</h1>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
          <p className="text-sm text-amber-800 font-medium mb-1">Simulated inbox</p>
          <p className="text-sm text-amber-700">
            Messages you would receive (flag notifications, ID reminders, rule changes) appear here.
            Full mock mail is built in Phase 9.
          </p>
        </div>
      </div>
    </Layout>
  );
}
