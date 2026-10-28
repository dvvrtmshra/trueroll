import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth";
import api from "../lib/api";

type Step = "choose" | "email" | "otp";

interface QuickRole {
  label: string;
  email: string;
  color: string;
}

const QUICK_ROLES: QuickRole[] = [
  { label: "AICTE National Officer", email: "officer.national@trueroll.demo", color: "bg-[#0B2545] hover:bg-blue-900" },
  { label: "AICTE Regional Officer (North)", email: "officer.north@trueroll.demo", color: "bg-[#0B2545] hover:bg-blue-900" },
  { label: "AICTE Regional Officer (South)", email: "officer.south@trueroll.demo", color: "bg-[#0B2545] hover:bg-blue-900" },
  { label: "College Admin (INST-0001)", email: "admin.inst0001@trueroll.demo", color: "bg-teal-700 hover:bg-teal-800" },
  { label: "Rules Owner", email: "rules.owner@trueroll.demo", color: "bg-indigo-700 hover:bg-indigo-800" },
  { label: "Rules Approver", email: "rules.approver@trueroll.demo", color: "bg-indigo-600 hover:bg-indigo-700" },
  { label: "Student (verified)", email: "student.verified@trueroll.demo", color: "bg-green-700 hover:bg-green-800" },
  { label: "Employer (DemoTech)", email: "employer.demotech@trueroll.demo", color: "bg-amber-700 hover:bg-amber-800" },
  { label: "Auditor", email: "auditor@trueroll.demo", color: "bg-gray-700 hover:bg-gray-800" },
  { label: "System Admin", email: "sysadmin@trueroll.demo", color: "bg-red-700 hover:bg-red-800" },
];

export default function LoginPage() {
  const [step, setStep] = useState<Step>("choose");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { setToken, setUser } = useAuthStore();
  const navigate = useNavigate();

  async function requestOtp(emailAddr: string) {
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/request-otp", { email: emailAddr });
      setEmail(emailAddr);
      setStep("otp");
    } catch {
      setError("Could not send OTP. Check the email address.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.post<{ access_token: string }>("/auth/verify-otp", { email, otp });
      setToken(res.data.access_token);
      const me = await api.get("/auth/me");
      setUser(me.data);
      navigate("/");
    } catch {
      setError("Invalid OTP. Demo OTP is always 123456.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] px-4">
      <div className="bg-white shadow-lg rounded-xl p-8 w-full max-w-lg">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-[#0B2545]">TrueRoll</h1>
          <p className="text-xs text-gray-400 mt-1">SAMPLE DATA prototype — SIH 2026 PS SIH26263</p>
          <div className="mt-2 inline-block bg-amber-100 text-amber-800 text-xs px-3 py-1 rounded-full font-medium">
            All records are synthetic. No real student or institutional data.
          </div>
        </div>

        {step === "choose" && (
          <div>
            <p className="text-sm text-gray-600 text-center mb-4 font-medium">Sign in as…</p>
            <div className="grid grid-cols-1 gap-2">
              {QUICK_ROLES.map((role) => (
                <button
                  key={role.email}
                  disabled={loading}
                  onClick={() => requestOtp(role.email)}
                  className={`w-full text-white rounded-lg py-2.5 px-4 text-sm font-medium text-left transition-colors disabled:opacity-50 ${role.color}`}
                >
                  {role.label}
                </button>
              ))}
            </div>
            <div className="mt-4 border-t border-gray-100 pt-4">
              <button
                className="w-full text-sm text-gray-500 hover:text-gray-700 underline"
                onClick={() => setStep("email")}
              >
                Enter a custom email instead
              </button>
            </div>
            {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
          </div>
        )}

        {step === "email" && (
          <form
            onSubmit={(e) => { e.preventDefault(); requestOtp(email); }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="you@trueroll.demo"
                data-testid="email-input"
              />
            </div>
            {error && <p className="text-red-600 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#0B2545] text-white rounded py-2 text-sm font-medium hover:bg-blue-900 disabled:opacity-50"
              data-testid="request-otp"
            >
              {loading ? "Sending…" : "Send OTP"}
            </button>
            <button
              type="button"
              className="w-full text-sm text-gray-500 underline"
              onClick={() => setStep("choose")}
            >
              Back to role selection
            </button>
          </form>
        )}

        {step === "otp" && (
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
              OTP sent to <strong>{email}</strong>.
              <br />
              Demo OTP is always <code className="bg-blue-100 px-1 rounded">123456</code>.
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">OTP</label>
              <input
                type="text"
                required
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                maxLength={6}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 tracking-widest text-center text-lg"
                placeholder="123456"
                autoFocus
                data-testid="otp-input"
              />
            </div>
            {error && <p className="text-red-600 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#0B2545] text-white rounded py-2 text-sm font-medium hover:bg-blue-900 disabled:opacity-50"
              data-testid="verify-otp"
            >
              {loading ? "Verifying…" : "Sign in"}
            </button>
            <button
              type="button"
              className="w-full text-sm text-gray-500 underline"
              onClick={() => { setStep("choose"); setError(""); setOtp(""); }}
            >
              Use a different account
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
