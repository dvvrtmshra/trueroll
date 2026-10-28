import { useState, useEffect } from "react";
import { Link, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../store/auth";
import { useQuery } from "@tanstack/react-query";
import api from "../lib/api";

interface NavItem {
  label: string;
  to: string;
}

const officerNav: NavItem[] = [
  { label: "Dashboard", to: "/" },
  { label: "Seat-Ledger", to: "/ledger" },
  { label: "Flags", to: "/flags" },
  { label: "Review priorities", to: "/priorities" },
  { label: "Institutions", to: "/institutions" },
  { label: "Identity & Duplicates", to: "/identity" },
  { label: "Reports", to: "/reports" },
  { label: "Rules", to: "/rules" },
  { label: "Model evaluation", to: "/model-eval" },
  { label: "My Activity", to: "/my-activity" },
  { label: "Mock Mail", to: "/mock-mail" },
];

const auditorNav: NavItem[] = [
  { label: "Audit trail", to: "/" },
  { label: "Access log", to: "/access-log" },
  { label: "Rule history", to: "/rule-history" },
  { label: "Exports", to: "/exports" },
];

const adminNav: NavItem[] = [
  { label: "Dashboard", to: "/" },
  { label: "System Admin", to: "/admin" },
  { label: "Audit trail", to: "/audit" },
  { label: "Reports", to: "/reports" },
  { label: "Review priorities", to: "/priorities" },
  { label: "Model evaluation", to: "/model-eval" },
];

const rulesNav: NavItem[] = [
  { label: "Rule book", to: "/rules" },
  { label: "Propose", to: "/propose" },
  { label: "Approvals", to: "/approvals" },
  { label: "Tests & backtest", to: "/tests" },
  { label: "Changelog", to: "/changelog" },
  { label: "Unconfirmed watch", to: "/unconfirmed" },
];

const collegeNav: NavItem[] = [
  { label: "Dashboard", to: "/" },
  { label: "Upload", to: "/upload" },
  { label: "My Seats", to: "/seats" },
  { label: "Students", to: "/students" },
  { label: "Flags", to: "/flags" },
  { label: "Certificates", to: "/certificates" },
  { label: "API", to: "/api" },
  { label: "Mock Mail", to: "/mail" },
  { label: "Help", to: "/help" },
];

const studentNav: NavItem[] = [
  { label: "My Record", to: "/" },
  { label: "Identity", to: "/identity" },
  { label: "Consent", to: "/consent" },
  { label: "Access Log", to: "/access-log" },
  { label: "Certificates", to: "/certificates" },
  { label: "Data & Privacy", to: "/privacy" },
];

const employerNav: NavItem[] = [
  { label: "Verify Student", to: "/" },
  { label: "My Verifications", to: "/my-checks" },
  { label: "Organisation", to: "/organisation" },
];

interface LayoutProps {
  children: React.ReactNode;
  unreadCount?: number;
}

export default function Layout({ children, unreadCount = 0 }: LayoutProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile menu on route change
  useEffect(() => { setMobileMenuOpen(false); }, [location.pathname]);

  const { data: clockData } = useQuery<{ demo_date: string }>({
    queryKey: ["demo-clock"],
    queryFn: () => api.get("/admin/clock").then((r) => r.data),
    staleTime: 30_000,
    retry: false,
  });

  const role = (user as Record<string, unknown>)?.role as string | undefined;
  const region = (user as Record<string, unknown>)?.region as string | undefined;

  const navItems =
    role === "COLLEGE_ADMIN" ? collegeNav
    : (role === "RULES_OWNER" || role === "RULES_APPROVER") ? rulesNav
    : role === "STUDENT" ? studentNav
    : role === "EMPLOYER" ? employerNav
    : role === "AUDITOR" ? auditorNav
    : role === "SYSTEM_ADMIN" ? adminNav
    : officerNav;

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="flex h-screen bg-[#F8FAFC] overflow-hidden">
      {/* Skip to main content (accessibility) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:top-2 focus:left-2 bg-white text-[#0B2545] px-3 py-1 rounded text-sm font-medium border border-[#0B2545]"
      >
        Skip to main content
      </a>

      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar — hidden on mobile unless mobileMenuOpen, always shown on desktop */}
      <aside
        className={`${
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 fixed md:relative z-40 md:z-auto inset-y-0 left-0 ${
          sidebarOpen ? "w-56" : "md:w-14 w-56"
        } flex-shrink-0 bg-[#0B2545] text-white flex flex-col transition-all duration-200`}
        aria-label="Main navigation"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
          {sidebarOpen && (
            <span className="font-bold text-lg tracking-tight">TrueRoll</span>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-white/60 hover:text-white p-1 rounded"
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? "◀" : "▶"}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center px-4 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-white/15 text-white font-medium"
                    : "text-white/70 hover:text-white hover:bg-white/10"
                }`
              }
            >
              {sidebarOpen ? item.label : item.label[0]}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/10 p-3">
          <button
            onClick={handleLogout}
            className="w-full text-left text-xs text-white/50 hover:text-white"
          >
            {sidebarOpen ? "Sign out" : "↩"}
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-white border-b border-[#E2E8F0] px-4 md:px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            {/* Hamburger — mobile only */}
            <button
              className="md:hidden text-[#0B2545] p-1 rounded focus:outline-none focus:ring-2 focus:ring-[#0B2545]"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <span className="text-sm font-semibold text-[#0B2545]">
              {role === "NATIONAL_OFFICER" && "AICTE National Officer"}
              {role === "REGIONAL_OFFICER" && "AICTE Regional Officer"}
              {role === "COLLEGE_ADMIN" && "College Admin"}
              {role === "RULES_OWNER" && "Rules Owner"}
              {role === "RULES_APPROVER" && "Rules Approver"}
              {role === "SYSTEM_ADMIN" && "System Admin"}
              {role === "STUDENT" && "Student Portal"}
              {role === "EMPLOYER" && "Employer Portal"}
              {role === "AUDITOR" && "Auditor"}
            </span>
            {region && (
              <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 text-xs font-medium">
                Region: {region}
              </span>
            )}
            {clockData?.demo_date && (
              <span className="text-xs text-gray-500">
                Demo date: {clockData.demo_date}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {unreadCount > 0 && (
              <span className="relative">
                <span className="text-gray-500 text-lg">🔔</span>
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              </span>
            )}
            <Link to="/login" className="text-xs text-blue-600 hover:underline">
              Switch role
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main id="main-content" className="flex-1 overflow-y-auto p-4 md:p-6" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
