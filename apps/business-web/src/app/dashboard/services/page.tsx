"use client";

import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Clock, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Service, ServiceCategory } from "@zenglow/types";
import { formatCurrency, durationLabel, cn } from "@/lib/utils";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const serviceSchema = z.object({
  name: z.string().min(1, "Required"),
  description: z.string().optional(),
  price: z.number({ coerce: true }).min(0, "Must be ≥ 0"),
  duration_minutes: z.number({ coerce: true }).int().min(5).max(480),
  tax_rate: z.number({ coerce: true }).min(0).max(100).default(18),
  buffer_after_minutes: z.number({ coerce: true }).int().min(0).default(0),
  is_active: z.boolean().default(true),
  online_booking_enabled: z.boolean().default(true),
});
type ServiceForm = z.infer<typeof serviceSchema>;

export default function ServicesPage() {
  const { business } = useAuth();
  const [services, setServices] = useState<Service[]>([]);
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSvc, setEditingSvc] = useState<Service | null>(null);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<ServiceForm>({
    resolver: zodResolver(serviceSchema),
    defaultValues: { tax_rate: 18, buffer_after_minutes: 0, is_active: true, online_booking_enabled: true },
  });

  const load = async () => {
    if (!business) return;
    setIsLoading(true);
    try {
      const [svcs, cats] = await Promise.all([
        api.get<Service[]>(`/businesses/${business.id}/services?active_only=false`),
        api.get<ServiceCategory[]>(`/businesses/${business.id}/services/categories`),
      ]);
      setServices(svcs);
      setCategories(cats);
    } catch { /* ignore */ }
    finally { setIsLoading(false); }
  };

  useEffect(() => { load(); }, [business]);

  const openCreate = () => { setEditingSvc(null); reset({ tax_rate: 18, duration_minutes: 60, is_active: true, online_booking_enabled: true }); setShowModal(true); };
  const openEdit = (s: Service) => {
    setEditingSvc(s);
    reset({ name: s.name, description: s.description ?? "", price: s.price, duration_minutes: s.duration_minutes, tax_rate: s.tax_rate, buffer_after_minutes: s.buffer_after_minutes, is_active: s.is_active, online_booking_enabled: s.online_booking_enabled });
    setShowModal(true);
  };

  const onSubmit = async (data: ServiceForm) => {
    if (!business) return;
    try {
      if (editingSvc) {
        await api.patch(`/businesses/${business.id}/services/${editingSvc.id}`, data);
        toast.success("Service updated");
      } else {
        await api.post(`/businesses/${business.id}/services`, data);
        toast.success("Service created");
      }
      setShowModal(false);
      load();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleDelete = async (s: Service) => {
    if (!confirm(`Delete "${s.name}"?`)) return;
    try {
      await api.delete(`/businesses/${business!.id}/services/${s.id}`);
      toast.success("Service deleted");
      load();
    } catch (err: any) { toast.error(err.message); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Services</h1>
          <p className="text-gray-500 text-sm mt-1">{services.length} services</p>
        </div>
        <button onClick={openCreate} className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors">
          <Plus className="w-4 h-4" /> Add service
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-brand-600" /></div>
      ) : services.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-4xl mb-3">✂️</p>
          <h3 className="font-semibold text-gray-900 mb-1">No services yet</h3>
          <p className="text-gray-500 text-sm mb-4">Add your services to start accepting bookings.</p>
          <button onClick={openCreate} className="bg-brand-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-700">Add first service</button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
          {services.map((svc) => (
            <div key={svc.id} className="flex items-center gap-4 px-5 py-4 hover:bg-gray-50 transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-gray-900 truncate">{svc.name}</p>
                  {!svc.is_active && <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Inactive</span>}
                  {!svc.online_booking_enabled && <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">No online booking</span>}
                </div>
                <div className="flex items-center gap-3 mt-1">
                  <div className="flex items-center gap-1 text-xs text-gray-500">
                    <Clock className="w-3.5 h-3.5" /> {durationLabel(svc.duration_minutes)}
                  </div>
                  {svc.description && <p className="text-xs text-gray-400 truncate hidden sm:block">{svc.description}</p>}
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="font-semibold text-gray-900">{formatCurrency(svc.price)}</span>
                <div className="flex gap-1">
                  <button onClick={() => openEdit(svc)} className="p-1.5 text-gray-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors" aria-label="Edit">
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button onClick={() => handleDelete(svc)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" aria-label="Delete">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Service modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-start justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg my-8">
            <div className="px-6 py-5 border-b border-gray-200">
              <h2 className="text-lg font-bold text-gray-900">{editingSvc ? "Edit Service" : "Add Service"}</h2>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Service name *</label>
                <input {...register("name")} className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea {...register("description")} rows={2} className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price (₹) *</label>
                  <input {...register("price")} type="number" min="0" step="0.01" className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                  {errors.price && <p className="mt-1 text-xs text-red-600">{errors.price.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Duration (min) *</label>
                  <input {...register("duration_minutes")} type="number" min="5" step="5" className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                  {errors.duration_minutes && <p className="mt-1 text-xs text-red-600">{errors.duration_minutes.message}</p>}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tax rate (%)</label>
                  <input {...register("tax_rate")} type="number" min="0" max="100" step="0.1" className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Buffer after (min)</label>
                  <input {...register("buffer_after_minutes")} type="number" min="0" step="5" className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
              </div>
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input {...register("is_active")} type="checkbox" className="w-4 h-4 text-brand-600 rounded" />
                  <span className="text-sm text-gray-700">Active</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input {...register("online_booking_enabled")} type="checkbox" className="w-4 h-4 text-brand-600 rounded" />
                  <span className="text-sm text-gray-700">Online booking</span>
                </label>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2.5 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
                <button type="submit" disabled={isSubmitting} className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-sm font-semibold text-white">
                  {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                  {editingSvc ? "Save changes" : "Create service"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
