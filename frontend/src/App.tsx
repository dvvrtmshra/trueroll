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

// Rules Owner pages
import RuleBookPage from "./pages/rules/RuleBookPage";
import RuleDetailPage from "./pages/rules/RuleDetailPage";
import ProposePage from "./pages/rules/ProposePage";
import ApprovalsPage from "./pages/rules/ApprovalsPage";
import TestsPage from "./pages/rules/TestsPage";
import ChangelogPage from "./pages/rules/ChangelogPage";
import UnconfirmedWatchPage from "./pages/rules/UnconfirmedWatchPage";

// Student pages
import MyRecordPage from "./pages/student/MyRecordPage";
import IdentityPage from "./pages/student/IdentityPage";
import ConsentPage from "./pages/student/ConsentPage";
import AccessLogPage from "./pages/student/AccessLogPage";
import CertificatesPage from "./pages/student/CertificatesPage";
import DataPrivacyPage from "./pages/student/DataPrivacyPage";

// Employer pages
import VerifyPage from "./pages/employer/VerifyPage";
import MyChecksPage from "./pages/employer/MyChecksPage";
import OrganisationPage from "./pages/employer/OrganisationPage";

// Public pages
import PublicVerifyPage from "./pages/public/PublicVerifyPage";

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

  if (role === "RULES_OWNER" || role === "RULES_APPROVER") {
    return (
      <Routes>
        <Route index element={<RuleBookPage />} />
        <Route path="rules" element={<RuleBookPage />} />
        <Route path="rules/:ruleId/versions/:version" element={<RuleDetailPage />} />
        <Route path="propose" element={<ProposePage />} />
        <Route path="approvals" element={<ApprovalsPage />} />
        <Route path="tests" element={<TestsPage />} />
        <Route path="changelog" element={<ChangelogPage />} />
        <Route path="unconfirmed" element={<UnconfirmedWatchPage />} />
        <Route path="*" element={<PlaceholderPage title="Coming soon" />} />
      </Routes>
    );
  }

  if (role === "STUDENT") {
    return (
      <Routes>
        <Route index element={<MyRecordPage />} />
        <Route path="identity" element={<IdentityPage />} />
        <Route path="consent" element={<ConsentPage />} />
        <Route path="access-log" element={<AccessLogPage />} />
        <Route path="certificates" element={<CertificatesPage />} />
        <Route path="privacy" element={<DataPrivacyPage />} />
        <Route path="*" element={<PlaceholderPage title="Coming soon" />} />
      </Routes>
    );
  }

  if (role === "EMPLOYER") {
    return (
      <Routes>
        <Route index element={<VerifyPage />} />
        <Route path="verify" element={<VerifyPage />} />
        <Route path="my-checks" element={<MyChecksPage />} />
        <Route path="organisation" element={<OrganisationPage />} />
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
        <Route path="/v/:code" element={<PublicVerifyPage />} />
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
