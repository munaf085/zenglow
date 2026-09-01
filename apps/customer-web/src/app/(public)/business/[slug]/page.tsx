"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  MapPin, Phone, Globe, Clock, CheckCircle, ChevronRight, Star, Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Business, Service, ServiceCategory } from "@zenglow/types";
import { formatCurrency, durationLabel } from "@/lib/utils";

const CATEGORY_LABELS: Record<string, string> = {
  SALON: "Salon", SPA: "Spa", BARBER: "Barbershop",
  BEAUTY: "Beauty Studio", WELLNESS: "Wellness", NAIL_STUDIO: "Nail Studio",
  MASSAGE: "Massage", OTHER: "Other",
};

export default function BusinessDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();

  const [business, setBusiness] = useState<Business | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    async function load() {
      try {
        const biz = await api.publicGet<Business>(`/businesses/public/${slug}`);
        setBusiness(biz);
        const [svcs, cats] = await Promise.all([
          api.publicGet<Service[]>(`/businesses/${biz.id}/services?active_only=true`),
          api.publicGet<ServiceCategory[]>(`/businesses/${biz.id}/services/categories`),
        ]);
        setServices(svcs);
        setCategories(cats);
      } catch {
        router.push("/explore");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [slug, router]);

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-64 bg-gray-200 rounded-2xl" />
          <div className="h-8 bg-gray-200 rounded w-1/2" />
          <div className="h-4 bg-gray-200 rounded w-1/3" />
        </div>
      </div>
    );
  }

  if (!business) return null;

  const primaryBranch = business.branches?.find((b) => b.is_primary) ?? business.branches?.[0];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Cover image */}
      <div className="relative h-56 sm:h-72 rounded-2xl overflow-hidden bg-gradient-to-br from-brand-100 to-pink-100 mb-8">
        {business.cover_image_url ? (
          <Image
            src={business.cover_image_url}
            alt={business.name}
            fill
            className="object-cover"
            sizes="(max-width: 1024px) 100vw, 1024px"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center opacity-20 text-8xl">
            ✨
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />

        {/* Business identity overlay */}
        <div className="absolute bottom-6 left-6 flex items-end gap-4">
          <div className="w-16 h-16 rounded-xl border-2 border-white bg-white shadow-lg flex items-center justify-center overflow-hidden flex-shrink-0">
            {business.logo_url ? (
              <Image src={business.logo_url} alt="logo" width={64} height={64} className="object-cover" />
            ) : (
              <span className="text-brand-700 font-bold text-2xl">{business.name[0]}</span>
            )}
          </div>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <h1 className="text-2xl font-bold text-white">{business.name}</h1>
              {business.is_verified && (
                <CheckCircle className="w-5 h-5 text-brand-300 flex-shrink-0" aria-label="Verified" />
              )}
            </div>
            <p className="text-white/80 text-sm">
              {CATEGORY_LABELS[business.category] ?? business.category}
              {primaryBranch?.city ? ` · ${primaryBranch.city}` : ""}
            </p>
          </div>
        </div>

        {business.is_featured && (
          <div className="absolute top-4 right-4 bg-brand-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
            Featured
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Services — main column */}
        <div className="lg:col-span-2">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Services</h2>

          {services.length === 0 ? (
            <p className="text-gray-400 text-sm py-8">No services listed yet.</p>
          ) : categories.length > 0 ? (
            categories.map((cat) => {
              const catServices = services.filter((s) => s.category_id === cat.id);
              if (!catServices.length) return null;
              return (
                <div key={cat.id} className="mb-8">
                  <h3 className="font-semibold text-gray-700 text-sm uppercase tracking-wide mb-3 flex items-center gap-2">
                    {cat.color && (
                      <span
                        className="w-3 h-3 rounded-full inline-block flex-shrink-0"
                        style={{ backgroundColor: cat.color }}
                      />
                    )}
                    {cat.name}
                  </h3>
                  <div className="space-y-2">
                    {catServices.map((svc) => (
                      <ServiceRow
                        key={svc.id}
                        service={svc}
                        businessId={business.id}
                        branchId={primaryBranch?.id}
                      />
                    ))}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="space-y-2">
              {services.map((svc) => (
                <ServiceRow
                  key={svc.id}
                  service={svc}
                  businessId={business.id}
                  branchId={primaryBranch?.id}
                />
              ))}
            </div>
          )}
        </div>

        {/* Sidebar — info + policies */}
        <div className="space-y-5">
          {/* Info card */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            {business.description && (
              <p className="text-sm text-gray-600 leading-relaxed">{business.description}</p>
            )}

            {primaryBranch?.address_line1 && (
              <div className="flex items-start gap-3">
                <MapPin className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-gray-600">
                  <p>{primaryBranch.address_line1}</p>
                  {primaryBranch.city && (
                    <p>
                      {primaryBranch.city}
                      {primaryBranch.state ? `, ${primaryBranch.state}` : ""}
                      {primaryBranch.postal_code ? ` ${primaryBranch.postal_code}` : ""}
                    </p>
                  )}
                </div>
              </div>
            )}

            {business.phone && (
              <div className="flex items-center gap-3">
                <Phone className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <a
                  href={`tel:${business.phone}`}
                  className="text-sm text-gray-600 hover:text-brand-600 transition-colors"
                >
                  {business.phone}
                </a>
              </div>
            )}

            {business.website && (
              <div className="flex items-center gap-3">
                <Globe className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <a
                  href={business.website}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-sm text-brand-600 hover:underline truncate"
                >
                  {business.website.replace(/^https?:\/\//, "")}
                </a>
              </div>
            )}
          </div>

          {/* Booking info */}
          <div className="bg-brand-50 rounded-xl border border-brand-100 p-4 space-y-2">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-brand-600" />
              <span className="text-sm font-semibold text-brand-800">Booking Info</span>
            </div>
            <p className="text-xs text-brand-700">
              Book up to {business.booking_advance_days} days in advance
            </p>
            <p className="text-xs text-brand-700">
              Free cancellation {business.cancellation_hours}h before appointment
            </p>
            {business.deposit_required && business.deposit_percentage && (
              <p className="text-xs text-brand-700">
                {business.deposit_percentage}% deposit required to confirm
              </p>
            )}
          </div>

          {/* Cancellation policy */}
          {business.cancellation_policy && (
            <div className="bg-amber-50 rounded-xl border border-amber-200 p-4">
              <h4 className="text-sm font-semibold text-amber-800 mb-1">Cancellation Policy</h4>
              <p className="text-xs text-amber-700 leading-relaxed">
                {business.cancellation_policy}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Service row component ─────────────────────────────────────────────────── */
function ServiceRow({
  service,
  businessId,
  branchId,
}: {
  service: Service;
  businessId: string;
  branchId?: string;
}) {
  return (
    <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-200 hover:border-brand-200 hover:bg-brand-50/30 transition-all group">
      <div className="flex-1 min-w-0 mr-4">
        <p className="font-medium text-gray-900 text-sm">{service.name}</p>
        {service.description && (
          <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{service.description}</p>
        )}
        <div className="flex items-center gap-1.5 mt-1">
          <Clock className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-xs text-gray-500">{durationLabel(service.duration_minutes)}</span>
        </div>
      </div>
      <div className="flex items-center gap-3 flex-shrink-0">
        <span className="font-semibold text-gray-900 text-sm whitespace-nowrap">
          {formatCurrency(service.price)}
        </span>
        <Link
          href={`/book?business=${businessId}&branch=${branchId ?? ""}&service=${service.id}`}
          className="flex items-center gap-1 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap"
        >
          Book
          <ChevronRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
}
