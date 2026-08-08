/**
 * VADP — Application Constants
 *
 * Centralized constants used throughout the frontend.
 * Jurisdiction-specific data is loaded from the backend,
 * but UI-level constants are defined here.
 */

export const APP_NAME = "VADP";
export const APP_DESCRIPTION =
  "Zero Trust Explainable AI Framework for Secure Judicial Decision Support";

/**
 * Navigation items for each user role.
 */
export const NAV_ITEMS = {
  citizen: [
    { label: "Dashboard", href: "/citizen", icon: "LayoutDashboard" },
    { label: "My Cases", href: "/citizen/cases", icon: "Briefcase" },
    { label: "File New Case", href: "/citizen/cases/new", icon: "FilePlus" },
    { label: "Documents", href: "/citizen/documents", icon: "FileText" },
    { label: "Notifications", href: "/citizen/notifications", icon: "Bell" },
  ],
  lawyer: [
    { label: "Dashboard", href: "/lawyer", icon: "LayoutDashboard" },
    { label: "Cases", href: "/lawyer/cases", icon: "Briefcase" },
    { label: "Legal Research", href: "/lawyer/research", icon: "Search" },
    { label: "Documents", href: "/lawyer/documents", icon: "FileText" },
    { label: "Notifications", href: "/lawyer/notifications", icon: "Bell" },
  ],
  judge: [
    { label: "Dashboard", href: "/judge", icon: "LayoutDashboard" },
    { label: "Case Queue", href: "/judge/cases", icon: "Briefcase" },
    { label: "AI Assistance", href: "/judge/ai-assist", icon: "Brain" },
    { label: "Explainability", href: "/judge/explainability", icon: "BarChart3" },
    { label: "Notifications", href: "/judge/notifications", icon: "Bell" },
  ],
  admin: [
    { label: "Dashboard", href: "/admin", icon: "LayoutDashboard" },
    { label: "Users", href: "/admin/users", icon: "Users" },
    { label: "Policies", href: "/admin/policies", icon: "Shield" },
    { label: "Audit Ledger", href: "/admin/audit", icon: "Link" },
    { label: "Analytics", href: "/admin/analytics", icon: "BarChart3" },
    { label: "Settings", href: "/admin/settings", icon: "Settings" },
  ],
} as const;

/**
 * Case type options (jurisdiction-agnostic defaults).
 * These will be overridden by jurisdiction configuration from the backend.
 */
export const DEFAULT_CASE_TYPES = [
  "Civil",
  "Criminal",
  "Constitutional",
  "Consumer",
  "Family",
  "Cybercrime",
  "Public Interest Litigation",
  "Commercial",
  "Labour",
  "Tax",
] as const;

/**
 * Case status flow for the timeline visualization.
 */
export const CASE_STATUS_FLOW = [
  { status: "filed", label: "Filed", description: "Case has been filed" },
  { status: "under_review", label: "Under Review", description: "Being reviewed by the court" },
  { status: "hearing", label: "Hearing", description: "Case is in hearing phase" },
  { status: "judgment", label: "Judgment", description: "Judgment is being prepared" },
  { status: "closed", label: "Closed", description: "Case has been closed" },
] as const;

/**
 * AI recommendation types.
 */
export const RECOMMENDATION_TYPES = [
  { value: "case_summary", label: "Case Summary" },
  { value: "judgment_assistance", label: "Judgment Assistance" },
  { value: "risk_assessment", label: "Risk Assessment" },
  { value: "legal_research", label: "Legal Research" },
  { value: "bias_check", label: "Bias Detection" },
] as const;
