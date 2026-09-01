"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, Calendar, Users, Scissors, UserCog,
  CreditCard, Settings, LogOut, ChevronDown, Building2, Menu, X, Clock, Star,
  ShoppingCart, Package, FileText, Award, Boxes, Gift, BarChart3,
} from "lucide-react";
import { useState } from "react";
import { cn, initials } from "@/lib/utils";
import { useAuth } from "@/components/providers/AuthProvider";
import { toast } from "sonner";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/calendar", label: "Calendar", icon: Calendar },
  { href: "/dashboard/pos", label: "POS / Checkout", icon: ShoppingCart },
  { href: "/dashboard/customers", label: "Customers", icon: Users },
  { href: "/dashboard/staff", label: "Staff", icon: UserCog },
  { href: "/dashboard/schedule", label: "Schedules", icon: Clock },
  { href: "/dashboard/services", label: "Services", icon: Scissors },
  { href: "/dashboard/inventory", label: "Inventory", icon: Package },
  { href: "/dashboard/memberships", label: "Memberships", icon: Award },
  { href: "/dashboard/packages", label: "Packages", icon: Boxes },
  { href: "/dashboard/gift-cards", label: "Gift Cards", icon: Gift },
  { href: "/dashboard/invoices", label: "Invoices", icon: FileText },
  { href: "/dashboard/payments", label: "Payments", icon: CreditCard },
  { href: "/dashboard/reports", label: "Reports & Analytics", icon: BarChart3 },
  { href: "/dashboard/reviews", label: "Reviews", icon: Star },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function Sidebar({ mobileOpen, onClose }: { mobileOpen?: boolean; onClose?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, business, businesses, logout, selectBusiness } = useAuth();
  const [bizPickerOpen, setBizPickerOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    toast.success("Logged out");
    router.push("/login");
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-2 px-5 py-5 border-b border-gray-200">
        <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-sm">Z</span>
        </div>
        <span className="font-bold text-gray-900 text-lg">Zenglow</span>
        {onClose && (
          <button onClick={onClose} className="ml-auto lg:hidden p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Business picker */}
      {business && (
        <div className="px-3 py-3 border-b border-gray-200">
          <button
            onClick={() => setBizPickerOpen(!bizPickerOpen)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="w-8 h-8 bg-brand-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Building2 className="w-4 h-4 text-brand-600" />
            </div>
            <div className="flex-1 text-left min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">{business.name}</p>
              <p className="text-xs text-gray-500">{business.branches?.[0]?.city ?? "Business"}</p>
            </div>
            <ChevronDown className={cn("w-4 h-4 text-gray-400 transition-transform", bizPickerOpen && "rotate-180")} />
          </button>
          {bizPickerOpen && businesses.length > 1 && (
            <div className="mt-1 space-y-1">
              {businesses.map((b) => (
                <button
                  key={b.id}
                  onClick={() => { selectBusiness(b); setBizPickerOpen(false); }}
                  className={cn("w-full text-left px-3 py-2 rounded-lg text-sm transition-colors",
                    b.id === business.id ? "bg-brand-50 text-brand-700 font-medium" : "hover:bg-gray-100 text-gray-700"
                  )}
                >
                  {b.name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                active ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <Icon className={cn("w-5 h-5", active ? "text-brand-600" : "text-gray-400")} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      {user && (
        <div className="px-3 py-4 border-t border-gray-200">
          <div className="flex items-center gap-3 px-3 py-2 mb-1">
            <div className="w-8 h-8 bg-brand-600 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs font-semibold">{initials(user.first_name, user.last_name)}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user.first_name} {user.last_name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-red-50 hover:text-red-700 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 min-h-screen bg-white border-r border-gray-200 fixed top-0 left-0 z-30">
        <SidebarContent />
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <>
          <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={onClose} />
          <aside className="fixed top-0 left-0 w-72 h-full bg-white z-50 lg:hidden shadow-xl overflow-y-auto">
            <SidebarContent />
          </aside>
        </>
      )}
    </>
  );
}
