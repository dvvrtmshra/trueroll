import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
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
  { label: "Institutions", to: "/institutions" },
  { label: "Identity & Duplicates", to: "/identity" },
  { label: "Reports", to: "/reports" },
  { label: "Rules", to: "/rules" },
  { label: "My Activity", to: "/my-activity" },
  { label: "Mock Mail", to: "/mock-mail" },
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

interface LayoutProps {
  children: React.ReactNode;
  unreadCount?: number;
}

export default function Layout({ children, unreadCount = 0 }: LayoutProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const { data: clockData } = useQuery<{ demo_date: string }>({
    queryKey: ["demo-clock"],
    queryFn: () => api.get("/admin/clock").then((r) => r.data),
    staleTime: 30_000,
    retry: false,
  });

  const role = (user as Record<string, unknown>)?.role as string | undefined;
  const region = (user as Record<string, unknown>)?.region as string | undefined;

  const navItems =
    role === "COLLEGE_ADMIN" ? collegeNav : officerNav;

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="flex h-screen bg-[#F8FAFC] overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`${sidebarOpen ? "w-56" : "w-14"} flex-shrink-0 bg-[#0B2545] text-white flex flex-col transition-all duration-200`}
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
        <header className="bg-white border-b border-[#E2E8F0] px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-[#0B2545]">
              {role === "NATIONAL_OFFICER" && "AICTE National Officer"}
              {role === "REGIONAL_OFFICER" && "AICTE Regional Officer"}
              {role === "COLLEGE_ADMIN" && "College Admin"}
              {role === "RULES_OWNER" && "Rules Owner"}
              {role === "SYSTEM_ADMIN" && "System Admin"}
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
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
