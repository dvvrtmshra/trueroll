import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/auth";
import SampleDataRibbon from "./components/SampleDataRibbon";
import LoginPage from "./pages/LoginPage";

// Officer pages
import OfficerDashboardPage from "./pages/officer/DashboardPage";
import LedgerPage from "./pages/officer/LedgerPage";
import OfficerFlagsPage from "./pages/officer/FlagsPage";
import FlagDetailPage from "./pages/officer/FlagDetailPage";
import InstitutionDetailPage from "./pages/officer/InstitutionDetailPage";

// College pages
import CollegeDashboardPage from "./pages/college/DashboardPage";
import UploadWizardPage from "./pages/college/UploadWizardPage";
import MySeatsPage from "./pages/college/MySeatsPage";
import StudentsPage from "./pages/college/StudentsPage";
import CollegeFlagsPage from "./pages/college/FlagsPage";
import ApiPage from "./pages/college/ApiPage";
import MockMailPage from "./pages/college/MockMailPage";
import HelpPage from "./pages/college/HelpPage";

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
        <Route index element={<OfficerDashboardPage />} />
        <Route path="ledger" element={<LedgerPage />} />
        <Route path="flags" element={<OfficerFlagsPage />} />
        <Route path="flags/:flagId" element={<FlagDetailPage />} />
        <Route path="institutions/:id" element={<InstitutionDetailPage />} />
        <Route path="*" element={<PlaceholderPage title="Coming soon" />} />
      </Routes>
    );
  }

  if (role === "COLLEGE_ADMIN") {
    return (
      <Routes>
        <Route index element={<CollegeDashboardPage />} />
        <Route path="upload" element={<UploadWizardPage />} />
        <Route path="seats" element={<MySeatsPage />} />
        <Route path="students" element={<StudentsPage />} />
        <Route path="flags" element={<CollegeFlagsPage />} />
        <Route path="api" element={<ApiPage />} />
        <Route path="mail" element={<MockMailPage />} />
        <Route path="help" element={<HelpPage />} />
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
