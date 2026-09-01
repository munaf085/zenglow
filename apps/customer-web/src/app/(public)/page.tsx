import Link from "next/link";
import { Search, Star, Calendar, Shield } from "lucide-react";
import { BusinessCard } from "@/components/business/BusinessCard";
import { SearchBar } from "@/components/search/SearchBar";

const CATEGORIES = [
  { label: "Salons", value: "SALON", emoji: "💇" },
  { label: "Spas", value: "SPA", emoji: "💆" },
  { label: "Barbers", value: "BARBER", emoji: "✂️" },
  { label: "Nails", value: "NAIL_STUDIO", emoji: "💅" },
  { label: "Massage", value: "MASSAGE", emoji: "🧖" },
  { label: "Beauty", value: "BEAUTY", emoji: "💄" },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-50 via-white to-pink-50 py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Book your next{" "}
            <span className="text-brand-600">beauty &amp; wellness</span>{" "}
            experience
          </h1>
          <p className="text-lg sm:text-xl text-gray-500 mb-10 max-w-2xl mx-auto">
            Discover and instantly book at thousands of salons, spas, and wellness centres near you.
          </p>
          <SearchBar />
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">Browse by category</h2>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-4">
            {CATEGORIES.map((cat) => (
              <Link
                key={cat.value}
                href={`/explore?category=${cat.value}`}
                className="flex flex-col items-center gap-3 p-4 rounded-xl border border-gray-200 hover:border-brand-300 hover:bg-brand-50 transition-all group"
              >
                <span className="text-3xl">{cat.emoji}</span>
                <span className="text-sm font-medium text-gray-700 group-hover:text-brand-700">
                  {cat.label}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Why Zenglow */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 mb-12 text-center">Why Zenglow?</h2>
          <div className="grid sm:grid-cols-3 gap-8">
            {[
              { icon: <Search className="w-6 h-6 text-brand-600" />, title: "Easy Discovery", desc: "Find top-rated salons and spas near you with real reviews." },
              { icon: <Calendar className="w-6 h-6 text-brand-600" />, title: "Instant Booking", desc: "Book 24/7, get instant confirmations, and manage everything in one place." },
              { icon: <Shield className="w-6 h-6 text-brand-600" />, title: "Secure & Reliable", desc: "Verified businesses, secure payments, and flexible cancellations." },
            ].map((item) => (
              <div key={item.title} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <div className="w-12 h-12 bg-brand-50 rounded-lg flex items-center justify-center mb-4">
                  {item.icon}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA for businesses */}
      <section className="py-16 px-4 bg-brand-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Own a salon or spa?</h2>
          <p className="text-brand-100 mb-8 text-lg">
            Join thousands of businesses using Zenglow to manage bookings, staff, and grow their clientele.
          </p>
          <a
            href={process.env.NEXT_PUBLIC_BUSINESS_APP_URL ?? "#"}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 bg-white text-brand-700 font-semibold px-8 py-3 rounded-lg hover:bg-brand-50 transition-colors"
          >
            Start for free
          </a>
        </div>
      </section>
    </div>
  );
}
