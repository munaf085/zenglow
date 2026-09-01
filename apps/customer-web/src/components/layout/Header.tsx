"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, User, Calendar, Heart, Menu, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/providers/AuthProvider";
import { toast } from "sonner";

export function Header() {
  const { user, isAuthenticated, logout } = useAuth();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    toast.success("Logged out");
    router.push("/");
    setMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">Z</span>
            </div>
            <span className="text-xl font-bold text-gray-900">Zenglow</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/explore" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
              Explore
            </Link>
            {isAuthenticated && (
              <>
                <Link href="/bookings" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                  My Bookings
                </Link>
                <Link href="/favourites" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                  Favourites
                </Link>
              </>
            )}
          </nav>

          {/* Desktop Auth */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <Link
                  href="/profile"
                  className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  <div className="w-8 h-8 bg-brand-100 rounded-full flex items-center justify-center">
                    <span className="text-brand-700 text-xs font-semibold">
                      {user?.first_name?.[0]}{user?.last_name?.[0]}
                    </span>
                  </div>
                  <span>{user?.first_name}</span>
                </Link>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-500 hover:text-gray-700 p-2 rounded-md hover:bg-gray-100 transition-colors"
                  aria-label="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm font-medium text-gray-600 hover:text-gray-900 px-4 py-2 rounded-md hover:bg-gray-100 transition-colors"
                >
                  Log in
                </Link>
                <Link
                  href="/register"
                  className="text-sm font-medium text-white bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-md transition-colors"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu toggle */}
          <button
            className="md:hidden p-2 rounded-md text-gray-500 hover:bg-gray-100"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white px-4 py-4 space-y-3">
          <Link href="/explore" className="block text-sm font-medium text-gray-700 py-2" onClick={() => setMenuOpen(false)}>Explore</Link>
          {isAuthenticated ? (
            <>
              <Link href="/bookings" className="block text-sm font-medium text-gray-700 py-2" onClick={() => setMenuOpen(false)}>My Bookings</Link>
              <Link href="/profile" className="block text-sm font-medium text-gray-700 py-2" onClick={() => setMenuOpen(false)}>Profile</Link>
              <button onClick={handleLogout} className="block text-sm font-medium text-red-600 py-2 w-full text-left">Log out</button>
            </>
          ) : (
            <>
              <Link href="/login" className="block text-sm font-medium text-gray-700 py-2" onClick={() => setMenuOpen(false)}>Log in</Link>
              <Link href="/register" className="block text-sm font-medium text-brand-600 py-2" onClick={() => setMenuOpen(false)}>Sign up</Link>
            </>
          )}
        </div>
      )}
    </header>
  );
}
