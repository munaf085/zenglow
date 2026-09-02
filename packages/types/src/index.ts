// ── Auth ──────────────────────────────────────────────────────────────────────
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

// ── Business ──────────────────────────────────────────────────────────────────
export type BusinessCategory =
  | "SALON" | "SPA" | "BARBER" | "BEAUTY"
  | "WELLNESS" | "NAIL_STUDIO" | "MASSAGE" | "OTHER";

export type BusinessStatus = "PENDING" | "ACTIVE" | "SUSPENDED" | "DEACTIVATED";

export interface Branch {
  id: string;
  business_id: string;
  name: string;
  is_primary: boolean;
  is_active: boolean;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  country: string;
  postal_code?: string;
  latitude?: number;
  longitude?: number;
  phone?: string;
  email?: string;
  created_at: string;
}

export interface Business {
  id: string;
  slug: string;
  owner_id: string;
  name: string;
  category: BusinessCategory;
  description?: string;
  logo_url?: string;
  cover_image_url?: string;
  email?: string;
  phone?: string;
  website?: string;
  instagram_url?: string;
  facebook_url?: string;
  tiktok_url?: string;
  status: BusinessStatus;
  is_verified: boolean;
  is_featured: boolean;
  booking_advance_days: number;
  cancellation_hours: number;
  cancellation_policy?: string;
  deposit_required: boolean;
  deposit_percentage?: number;
  subscription_plan_id?: string;
  branches: Branch[];
  created_at: string;
}

// ── Staff ─────────────────────────────────────────────────────────────────────
export type StaffStatus = "ACTIVE" | "INACTIVE" | "ON_LEAVE";

export interface Staff {
  id: string;
  business_id: string;
  branch_id?: string;
  user_id?: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  title?: string;
  bio?: string;
  avatar_url?: string;
  status: StaffStatus;
  bookable: boolean;
  sort_order: number;
  service_ids: string[];
  created_at: string;
}

export interface WorkingHours {
  id: string;
  entity_type: string;
  entity_id: string;
  business_id: string;
  day_of_week: number;
  is_open: boolean;
  open_time?: string;
  close_time?: string;
  break_start?: string;
  break_end?: string;
}

// ── Service ───────────────────────────────────────────────────────────────────
export interface ServiceCategory {
  id: string;
  business_id: string;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
}

export interface Service {
  id: string;
  business_id: string;
  category_id?: string;
  name: string;
  description?: string;
  price: number;
  tax_rate: number;
  duration_minutes: number;
  buffer_before_minutes: number;
  buffer_after_minutes: number;
  is_active: boolean;
  online_booking_enabled: boolean;
  image_url?: string;
  sort_order: number;
  created_at: string;
}

// ── Booking ───────────────────────────────────────────────────────────────────
export type AppointmentStatus =
  | "PENDING" | "CONFIRMED" | "IN_PROGRESS"
  | "COMPLETED" | "CANCELLED" | "NO_SHOW" | "RESCHEDULED";

export interface TimeSlot {
  start_time: string;
  end_time: string;
  staff_id: string;
  staff_name: string;
  available: boolean;
}

export interface AvailabilityResponse {
  date: string;
  service_id: string;
  service_name: string;
  duration_minutes: number;
  slots: TimeSlot[];
}

export interface AppointmentItem {
  id: string;
  service_id: string;
  service_name: string;
  staff_id: string;
  duration_minutes: number;
  price: number;
  tax_rate: number;
  start_time: string;
  end_time: string;
}

export interface Appointment {
  id: string;
  business_id: string;
  branch_id: string;
  customer_id: string;
  start_time: string;
  end_time: string;
  status: AppointmentStatus;
  source: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  deposit_amount: number;
  customer_notes?: string;
  items: AppointmentItem[];
  created_at: string;
}

// ── Payment ───────────────────────────────────────────────────────────────────
export type PaymentStatus =
  | "PENDING" | "PROCESSING" | "CAPTURED"
  | "FAILED" | "REFUNDED" | "PARTIALLY_REFUNDED" | "CANCELLED";

export interface Payment {
  id: string;
  business_id: string;
  appointment_id?: string;
  customer_id: string;
  amount: number;
  currency: string;
  provider: string;
  status: PaymentStatus;
  provider_order_id?: string;
  provider_payment_id?: string;
  paid_at?: string;
  created_at: string;
}

export interface PaymentOrder {
  payment_id: string;
  provider_order_id: string;
  amount: number;
  currency: string;
  provider: string;
  status: PaymentStatus;
  provider_key?: string;
}

// ── Pagination ────────────────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ── Error ─────────────────────────────────────────────────────────────────────
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

// ── Admin ─────────────────────────────────────────────────────────────────────
export interface DashboardStats {
  total_businesses: number;
  active_businesses: number;
  total_users: number;
  total_bookings: number;
  total_revenue: number;
  bookings_today: number;
  new_businesses_this_month: number;
  new_users_this_month: number;
}

export interface SubscriptionPlan {
  id: string;
  tier: "FREE" | "STARTER" | "PROFESSIONAL" | "ENTERPRISE";
  name: string;
  description?: string;
  monthly_price: number;
  yearly_price: number;
  currency: string;
  max_branches: number;
  max_staff: number;
  max_services: number;
  max_bookings_per_month: number;
  is_active: boolean;
}
