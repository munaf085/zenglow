import Link from "next/link";
import Image from "next/image";
import { MapPin, Star, CheckCircle } from "lucide-react";
import type { Business } from "@zenglow/types";

interface BusinessCardProps {
  business: Business;
}

const CATEGORY_LABELS: Record<string, string> = {
  SALON: "Salon", SPA: "Spa", BARBER: "Barbershop",
  BEAUTY: "Beauty Studio", WELLNESS: "Wellness", NAIL_STUDIO: "Nail Studio",
  MASSAGE: "Massage", OTHER: "Other",
};

export function BusinessCard({ business }: BusinessCardProps) {
  const primaryBranch = business.branches?.find((b) => b.is_primary) ?? business.branches?.[0];
  const city = primaryBranch?.city;

  return (
    <Link
      href={`/business/${business.slug}`}
      className="group block bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md hover:border-brand-200 transition-all"
    >
      {/* Image */}
      <div className="relative h-44 bg-gradient-to-br from-brand-100 to-pink-100 overflow-hidden">
        {business.cover_image_url ? (
          <Image
            src={business.cover_image_url}
            alt={business.name}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-5xl opacity-30">✨</span>
          </div>
        )}
        {business.is_featured && (
          <span className="absolute top-3 left-3 bg-brand-600 text-white text-xs font-semibold px-2 py-0.5 rounded-full">
            Featured
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="font-semibold text-gray-900 text-base leading-tight group-hover:text-brand-700 transition-colors line-clamp-1">
            {business.name}
          </h3>
          {business.is_verified && (
            <CheckCircle className="w-4 h-4 text-brand-500 flex-shrink-0 mt-0.5" aria-label="Verified" />
          )}
        </div>

        <p className="text-xs text-gray-500 mb-2">
          {CATEGORY_LABELS[business.category] ?? business.category}
        </p>

        {city && (
          <div className="flex items-center gap-1 text-sm text-gray-500">
            <MapPin className="w-3.5 h-3.5" />
            <span>{city}</span>
          </div>
        )}

        {business.description && (
          <p className="text-sm text-gray-500 mt-2 line-clamp-2 leading-relaxed">
            {business.description}
          </p>
        )}
      </div>
    </Link>
  );
}
