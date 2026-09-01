import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, parseISO } from "date-fns";
export function cn(...i: ClassValue[]) { return twMerge(clsx(i)); }
export function formatCurrency(n: number) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(n); }
export function formatDate(s: string) { return format(parseISO(s), "MMM d, yyyy"); }
