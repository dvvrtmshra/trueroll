import { useAuthStore } from "../store/auth";
import { useNavigate } from "react-router-dom";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm px-6 py-4 flex items-center justify-between">
        <span className="font-bold text-gray-800">TrueRoll</span>
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-gray-600">
              {String(user.email)} · <span className="font-medium">{String(user.role)}</span>
            </span>
          )}
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-gray-800 underline"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-6 py-12">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Phase 0 scaffold — full features arrive in Phase 1+
        </h2>
        <p className="text-gray-500 text-sm">
          You are signed in as <strong>{user ? String(user.role) : "—"}</strong>. Role-specific
          dashboards are implemented from Phase 2 onward.
        </p>
      </main>
    </div>
  );
}
