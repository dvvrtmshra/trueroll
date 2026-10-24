import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/auth";
import SampleDataRibbon from "./components/SampleDataRibbon";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/officer/DashboardPage";
import LedgerPage from "./pages/officer/LedgerPage";
import FlagsPage from "./pages/officer/FlagsPage";
import FlagDetailPage from "./pages/officer/FlagDetailPage";
import InstitutionDetailPage from "./pages/officer/InstitutionDetailPage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
      <div className="text-center">
        <h1 className="text-xl font-bold text-[#0B2545] mb-2">{title}</h1>
        <p className="text-gray-500 text-sm">Coming in a future phase.</p>
        <a href="/" className="mt-4 inline-block text-blue-600 hover:underline text-sm">← Dashboard</a>
      </div>
    </div>
  );
}

function RoleRouter() {
  const user = useAuthStore((s) => s.user) as Record<string, unknown> | null;
  const role = user?.role as string | undefined;

  if (role === "NATIONAL_OFFICER" || role === "REGIONAL_OFFICER" || role === "SYSTEM_ADMIN") {
    return (
      <Routes>
        <Route index element={<DashboardPage />} />
        <Route path="ledger" element={<LedgerPage />} />
        <Route path="flags" element={<FlagsPage />} />
        <Route path="flags/:flagId" element={<FlagDetailPage />} />
        <Route path="institutions/:id" element={<InstitutionDetailPage />} />
        <Route path="*" element={<PlaceholderPage title="Coming soon" />} />
      </Routes>
    );
  }

  return <PlaceholderPage title={`${role ?? "User"} screens coming soon`} />;
}

export default function App() {
  return (
    <>
      <SampleDataRibbon />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <RoleRouter />
            </RequireAuth>
          }
        />
      </Routes>
    </>
  );
}
