/**
 * Nyaya-ZTA — Utility Functions
 *
 * Shared utility functions used across the frontend.
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with conflict resolution.
 * Combines clsx for conditional classes with tailwind-merge for deduplication.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a date string to a human-readable format.
 */
export function formatDate(
  dateString: string,
  options?: Intl.DateTimeFormatOptions
): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    ...options,
  });
}

/**
 * Format a date string to include time.
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format a number as a percentage string.
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a number with appropriate suffix (K, M, etc.).
 */
export function formatNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}

/**
 * Truncate text to a maximum length with ellipsis.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

/**
 * Generate initials from a full name.
 */
export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Get a color for a status badge.
 */
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    filed: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    under_review: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    hearing: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    judgment: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    closed: "bg-gray-500/10 text-gray-400 border-gray-500/20",
    appealed: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    pending: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    approved: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    rejected: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    flagged: "bg-orange-500/10 text-orange-400 border-orange-500/20",
    verified: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    tampered: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  };
  return colors[status] || "bg-gray-500/10 text-gray-400 border-gray-500/20";
}

/**
 * Get risk level label and color from a risk score.
 */
export function getRiskLevel(score: number): {
  level: string;
  color: string;
} {
  if (score >= 0.75) return { level: "Critical", color: "text-rose-400" };
  if (score >= 0.5) return { level: "High", color: "text-orange-400" };
  if (score >= 0.25) return { level: "Medium", color: "text-amber-400" };
  return { level: "Low", color: "text-emerald-400" };
}

/**
 * Debounce a function call.
 */
export function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}
