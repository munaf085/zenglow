import { Header } from "@/components/layout/Header";
import Link from "next/link";

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">{children}</main>
      <footer className="bg-gray-50 border-t border-gray-200 py-12 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between gap-8">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xs">Z</span>
                </div>
                <span className="font-bold text-gray-900">Zenglow</span>
              </div>
              <p className="text-sm text-gray-500 max-w-xs">
                Discover and book at the best salons, spas, and wellness centres near you.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  Quick Links
                </h3>

                <ul className="space-y-2 text-sm text-gray-500">
                  <li>
                    <Link href="/about" className="hover:text-gray-700">
                      About Us
                    </Link>
                  </li>
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Discover</h3>
                <ul className="space-y-2 text-sm text-gray-500">
                  <li><a href="/explore" className="hover:text-gray-700">Explore</a></li>
                  <li><a href="/explore?category=SALON" className="hover:text-gray-700">Salons</a></li>
                  <li><a href="/explore?category=SPA" className="hover:text-gray-700">Spas</a></li>
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Account</h3>
                <ul className="space-y-2 text-sm text-gray-500">
                  <li><a href="/login" className="hover:text-gray-700">Log in</a></li>
                  <li><a href="/register" className="hover:text-gray-700">Sign up</a></li>
                  <li><a href="/bookings" className="hover:text-gray-700">My Bookings</a></li>
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Business</h3>
                <ul className="space-y-2 text-sm text-gray-500">
                  <li><a href={process.env.NEXT_PUBLIC_BUSINESS_APP_URL ?? "#"} className="hover:text-gray-700" target="_blank" rel="noreferrer">For Businesses</a></li>
                </ul>
              </div>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-200 text-sm text-gray-400">
            © {new Date().getFullYear()} Zenglow. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
