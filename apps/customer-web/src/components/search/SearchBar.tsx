"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, MapPin } from "lucide-react";

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [city, setCity] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (city) params.set("city", city);
    router.push(`/explore?${params.toString()}`);
  };

  return (
    <form
      onSubmit={handleSearch}
      className="flex flex-col sm:flex-row gap-3 max-w-2xl mx-auto"
      role="search"
    >
      <div className="flex-1 relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search salons, services..."
          className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent text-base shadow-sm"
          aria-label="Search businesses or services"
        />
      </div>
      <div className="relative sm:w-48">
        <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="City"
          className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent text-base shadow-sm"
          aria-label="City"
        />
      </div>
      <button
        type="submit"
        className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-8 py-3.5 rounded-xl transition-colors shadow-sm whitespace-nowrap"
      >
        Search
      </button>
    </form>
  );
}
