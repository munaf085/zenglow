"use client";

import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, UserCheck, UserX, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/providers/AuthProvider";
import type { Staff } from "@zenglow/types";
import { cn, initials } from "@/lib/utils";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const staffSchema = z.object({
  first_name: z.string().min(1, "Required").max(100),
  last_name: z.string().min(1, "Required").max(100),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  phone: z.string().optional(),
  title: z.string().optional(),
});
type StaffForm = z.infer<typeof staffSchema>;

export default function StaffPage() {
  const { business } = useAuth();
  const [staffList, setStaffList] = useState<Staff[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingStaff, setEditingStaff] = useState<Staff | null>(null);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<StaffForm>({
    resolver: zodResolver(staffSchema),
  });

  const loadStaff = async () => {
    if (!business) return;
    setIsLoading(true);
    try {
      const res = await api.get<Staff[]>(`/businesses/${business.id}/staff`);
      setStaffList(res);
    } catch { /* ignore */ }
    finally { setIsLoading(false); }
  };

  useEffect(() => { loadStaff(); }, [business]);

  const openCreate = () => { setEditingStaff(null); reset({}); setShowModal(true); };
  const openEdit = (s: Staff) => { setEditingStaff(s); reset({ first_name: s.first_name, last_name: s.last_name, email: s.email ?? "", phone: s.phone ?? "", title: s.title ?? "" }); setShowModal(true); };

  const onSubmit = async (data: StaffForm) => {
    if (!business) return;
    try {
      if (editingStaff) {
        await api.patch(`/businesses/${business.id}/staff/${editingStaff.id}`, data);
        toast.success("Staff updated");
      } else {
        await api.post(`/businesses/${business.id}/staff`, data);
        toast.success("Staff member added");
      }
      setShowModal(false);
      loadStaff();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleDelete = async (s: Staff) => {
    if (!confirm(`Remove ${s.first_name} ${s.last_name}?`)) return;
    try {
      await api.delete(`/businesses/${business!.id}/staff/${s.id}`);
      toast.success("Staff member removed");
      loadStaff();
    } catch (err: any) { toast.error(err.message); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Staff</h1>
          <p className="text-gray-500 text-sm mt-1">{staffList.length} team members</p>
        </div>
        <button onClick={openCreate} className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors">
          <Plus className="w-4 h-4" /> Add staff
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-brand-600" /></div>
      ) : staffList.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-4xl mb-3">👥</p>
          <h3 className="font-semibold text-gray-900 mb-1">No staff added yet</h3>
          <p className="text-gray-500 text-sm mb-4">Add your team members to enable bookings.</p>
          <button onClick={openCreate} className="bg-brand-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors">Add first staff member</button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {staffList.map((s) => (
            <div key={s.id} className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 bg-brand-100 rounded-full flex items-center justify-center flex-shrink-0">
                    {s.avatar_url ? <img src={s.avatar_url} className="w-full h-full rounded-full object-cover" alt="" /> :
                      <span className="text-brand-700 font-semibold text-sm">{initials(s.first_name, s.last_name)}</span>}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{s.first_name} {s.last_name}</p>
                    {s.title && <p className="text-xs text-gray-500">{s.title}</p>}
                  </div>
                </div>
                <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full",
                  s.status === "ACTIVE" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600")}>
                  {s.status}
                </span>
              </div>
              {s.email && <p className="text-xs text-gray-500 mb-3 truncate">{s.email}</p>}
              <div className="flex gap-2 pt-3 border-t border-gray-100">
                <button onClick={() => openEdit(s)} className="flex-1 flex items-center justify-center gap-1.5 text-xs font-medium text-gray-600 hover:text-brand-600 py-1.5 rounded-lg hover:bg-brand-50 transition-colors">
                  <Pencil className="w-3.5 h-3.5" /> Edit
                </button>
                <button onClick={() => handleDelete(s)} className="flex-1 flex items-center justify-center gap-1.5 text-xs font-medium text-gray-600 hover:text-red-600 py-1.5 rounded-lg hover:bg-red-50 transition-colors">
                  <Trash2 className="w-3.5 h-3.5" /> Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
            <div className="px-6 py-5 border-b border-gray-200">
              <h2 className="text-lg font-bold text-gray-900">{editingStaff ? "Edit Staff" : "Add Staff Member"}</h2>
            </div>
            <form onSubmit={handleSubmit(onSubmit)} className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First name *</label>
                  <input {...register("first_name")} className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                  {errors.first_name && <p className="mt-1 text-xs text-red-600">{errors.first_name.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last name *</label>
                  <input {...register("last_name")} className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                  {errors.last_name && <p className="mt-1 text-xs text-red-600">{errors.last_name.message}</p>}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Job title</label>
                <input {...register("title")} placeholder="e.g. Senior Stylist" className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input {...register("email")} type="email" className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input {...register("phone")} type="tel" className="w-full px-3 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2.5 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-sm font-semibold text-white transition-colors">
                  {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  {editingStaff ? "Save changes" : "Add staff"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
