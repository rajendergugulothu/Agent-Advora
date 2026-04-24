"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";
import {
  IconHome, IconDocument, IconChart,
  IconInstagram, IconSettings, IconMenu, IconX, IconLogout,
} from "@/components/NavIcons";

const NAV_ITEMS = [
  { href: "/dashboard",           label: "Overview",          Icon: IconHome },
  { href: "/dashboard/drafts",    label: "Drafts",            Icon: IconDocument },
  { href: "/dashboard/analytics", label: "Analytics",         Icon: IconChart },
  { href: "/dashboard/connect",   label: "Connect Instagram", Icon: IconInstagram },
  { href: "/dashboard/settings",  label: "Settings",          Icon: IconSettings },
];

interface DashboardNavProps {
  userEmail: string;
}

export function DashboardNav({ userEmail }: DashboardNavProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close sidebar on route change
  useEffect(() => { setMobileOpen(false); }, [pathname]);

  // Lock scroll when mobile menu is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [mobileOpen]);

  const isActive = (href: string) =>
    href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(href);

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-100">
        <Logo size="sm" />
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, Icon }) => (
          <Link
            key={href}
            href={href}
            className={isActive(href) ? "nav-link-active" : "nav-link"}
          >
            <Icon className="w-[18px] h-[18px] shrink-0" />
            <span>{label}</span>
            {isActive(href) && (
              <span className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-600" />
            )}
          </Link>
        ))}
      </nav>

      {/* User footer */}
      <div className="px-3 py-4 border-t border-gray-100">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-gray-50">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-brand-500 to-advora-teal flex items-center justify-center shrink-0">
            <span className="text-xs font-bold text-white">
              {userEmail[0]?.toUpperCase() ?? "U"}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-gray-700 truncate">{userEmail}</p>
          </div>
        </div>
        <form action="/auth/signout" method="post" className="mt-1">
          <button className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm text-gray-500 hover:text-red-500 hover:bg-red-50 transition-colors">
            <IconLogout className="w-4 h-4" />
            <span>Sign out</span>
          </button>
        </form>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-60 shrink-0 bg-white border-r border-gray-100 flex-col h-screen sticky top-0">
        <SidebarContent />
      </aside>

      {/* Mobile top bar */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-gray-100 px-4 h-14 flex items-center justify-between">
        <Logo size="sm" />
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
          aria-label="Open menu"
        >
          <IconMenu />
        </button>
      </header>

      {/* Mobile drawer overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={`lg:hidden fixed top-0 left-0 bottom-0 z-50 w-72 bg-white shadow-2xl transform transition-transform duration-300 ease-out ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Close button */}
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors"
          aria-label="Close menu"
        >
          <IconX />
        </button>
        <SidebarContent />
      </aside>

      {/* Mobile bottom nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-100 px-2 pb-safe">
        <div className="flex items-center justify-around">
          {NAV_ITEMS.slice(0, 4).map(({ href, label, Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-colors min-w-[3.5rem] ${
                isActive(href)
                  ? "text-brand-600"
                  : "text-gray-400 hover:text-gray-600"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{label.split(" ")[0]}</span>
            </Link>
          ))}
          <Link
            href="/dashboard/settings"
            className={`flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-colors min-w-[3.5rem] ${
              isActive("/dashboard/settings") ? "text-brand-600" : "text-gray-400 hover:text-gray-600"
            }`}
          >
            <IconSettings className="w-5 h-5" />
            <span className="text-[10px] font-medium">Settings</span>
          </Link>
        </div>
      </nav>
    </>
  );
}
