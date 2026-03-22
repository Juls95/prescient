"use client";

import Link from "next/link";
import { UserButton } from "@clerk/nextjs";
import { useSync } from "@/lib/useSync";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import {
  LayoutDashboard,
  Settings,
  CreditCard,
  Activity,
  Database,
  Menu,
  X,
  Brain,
  Clock,
  BookOpen,
  UserPlus,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/intelligence", label: "Intelligence", icon: Brain },
  { href: "/history", label: "History", icon: Clock },
  { href: "/info", label: "Methodology", icon: BookOpen },
  { href: "/suggest", label: "Suggest Person", icon: UserPlus },
  { href: "/pipeline", label: "Data Pipeline", icon: Activity },
  { href: "/storage", label: "Filecoin Storage", icon: Database },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoaded } = useSync();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-[#fafafa] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <svg className="animate-spin h-8 w-8 text-[#7c3aed]" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <p className="text-sm text-[#666]">Loading...</p>
        </div>
      </div>
    );
  }

  const displayName = user?.firstName || user?.username || "User";
  const email = user?.primaryEmailAddress?.emailAddress || "";

  return (
    <div className="min-h-screen bg-[#fafafa]">
      {/* Mobile header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-14 bg-white border-b border-[#e5e5e5] flex items-center justify-between px-4 z-50">
        <Link href="/dashboard" className="text-lg font-bold tracking-tighter text-[#0a0a0a]">
          prescient<span className="text-[#7c3aed]">.</span>
        </Link>
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 text-[#666]">
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside className={`fixed top-0 left-0 h-full w-64 bg-white border-r border-[#e5e5e5] z-40 transform transition-transform duration-200 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}>
        <div className="p-6">
          <Link href="/dashboard" className="text-xl font-bold tracking-tighter text-[#0a0a0a]">
            prescient<span className="text-[#7c3aed]">.</span>
          </Link>
        </div>

        <nav className="px-3 space-y-1">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setSidebarOpen(false)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[#666] hover:text-[#0a0a0a] hover:bg-[#f5f5f5] transition"
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[#e5e5e5]">
          <div className="flex items-center gap-3 px-3 py-2">
            <UserButton
              appearance={{
                elements: { avatarBox: "w-8 h-8" },
              }}
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[#0a0a0a] truncate">{displayName}</p>
              <p className="text-xs text-[#999] truncate">{email}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 bg-black/20 z-30" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Main content */}
      <main className="lg:ml-64 pt-14 lg:pt-0 min-h-screen">
        <div className="p-6 lg:p-8 max-w-7xl mx-auto">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
}
