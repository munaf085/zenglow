"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { Filter, Search } from "lucide-react";
import { api } from "@/lib/api";
import type { Business, PaginatedResponse } from "@zenglow/types";
import { BusinessCard } from "@/components/business/BusinessCard";
import { cn } from "@/lib/utils";

const CATEGORIES = [
  { label: "All", value: "" },
  { label: "Salons", value: "SALON" },
  { label: "Spas", value: "SPA" },
  { label: "Barbers", value: "BARBER" },
  { label: "Nails", value: "NAIL_STUDIO" },
  { label: "Massage", value: "MASSAGE" },
  { label: "Beauty", value: "BEAUTY" },
  { label: "Wellness", value: "WELLNESS" },
];

export default function ExplorePage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const [city, setCity] = useState(searchParams.get("city") ?? "");
  const [category, setCategory] = useState(searchParams.get("category") ?? "");

  const fetchBusinesses = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ page: "1", page_size: "24" });
      if (query) params.set("q", query);
      if (city) params.set("city", city);
      if (category) params.set("category", category);
      const res = await api.publicGet<PaginatedResponse<Business>>(`/businesses/search?${params}`);
      setBusinesses(res.items);
      setTotal(res.total);
    } catch {
      setBusinesses([]);
    } finally {
      setIsLoading(false);
    }
  }, [query, city, category]);

  useEffect(() => { fetchBusinesses(); }, [fetchBusinesses]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchBusinesses();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3 mb-8">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search businesses or services..."
            className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            aria-label="Search"
          />
        </div>
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="City"
          className="sm:w-40 px-4 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          aria-label="City"
        />
        <button type="submit" className="bg-brand-600 text-white px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-brand-700 transition-colors">
          Search
        </button>
      </form>

      {/* Category pills */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-8">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.value}
            onClick={() => setCategory(cat.value)}
            className={cn(
              "px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors border",
              category === cat.value
                ? "bg-brand-600 text-white border-brand-600"
                : "bg-white text-gray-600 border-gray-300 hover:border-brand-300 hover:text-brand-700"
            )}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Results header */}
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-gray-500">
          {isLoading ? "Searching..." : `${total} businesses found`}
        </p>
      </div>

      {/* Business grid */}
      {isLoading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-gray-200 overflow-hidden animate-pulse">
              <div className="h-44 bg-gray-200" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : businesses.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-5xl mb-4">🔍</p>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No businesses found</h3>
          <p className="text-gray-500 text-sm">Try adjusting your search or browsing a different category.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {businesses.map((business) => (
            <BusinessCard key={business.id} business={business} />
          ))}
        </div>
      )}
    </div>
  );
}
