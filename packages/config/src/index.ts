export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const CUSTOMER_APP_URL =
  process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export const BUSINESS_APP_URL =
  process.env.NEXT_PUBLIC_BUSINESS_APP_URL ?? "http://localhost:3001";

export const ADMIN_APP_URL =
  process.env.NEXT_PUBLIC_ADMIN_APP_URL ?? "http://localhost:3002";

export const DAYS_OF_WEEK = [
  "Monday", "Tuesday", "Wednesday",
  "Thursday", "Friday", "Saturday", "Sunday",
];

export const BUSINESS_CATEGORIES = [
  { value: "SALON", label: "Salon" },
  { value: "SPA", label: "Spa" },
  { value: "BARBER", label: "Barbershop" },
  { value: "BEAUTY", label: "Beauty Studio" },
  { value: "WELLNESS", label: "Wellness Center" },
  { value: "NAIL_STUDIO", label: "Nail Studio" },
  { value: "MASSAGE", label: "Massage Center" },
  { value: "OTHER", label: "Other" },
] as const;

export const APPOINTMENT_STATUS_LABELS: Record<string, string> = {
  PENDING: "Pending",
  CONFIRMED: "Confirmed",
  IN_PROGRESS: "In Progress",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
  NO_SHOW: "No Show",
  RESCHEDULED: "Rescheduled",
};

export const APPOINTMENT_STATUS_COLORS: Record<string, string> = {
  PENDING: "yellow",
  CONFIRMED: "green",
  IN_PROGRESS: "blue",
  COMPLETED: "gray",
  CANCELLED: "red",
  NO_SHOW: "orange",
  RESCHEDULED: "purple",
};
