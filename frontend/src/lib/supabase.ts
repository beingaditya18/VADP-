/**
 * VADP — Supabase Client
 *
 * Provides Supabase client instances for both browser and server contexts.
 * Uses @supabase/ssr for proper cookie-based session management.
 *
 * Usage:
 *   // In client components:
 *   import { createBrowserClient } from "@/lib/supabase";
 *   const supabase = createBrowserClient();
 *
 *   // In server components/actions:
 *   import { createServerClient } from "@/lib/supabase";
 *   const supabase = createServerClient();
 */

import { createBrowserClient as createSupabaseBrowserClient } from "@supabase/ssr";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

/**
 * Create a Supabase client for browser/client-side usage.
 *
 * This client uses the anon key and manages sessions via cookies.
 * It should be used in client components and hooks.
 */
export function createBrowserClient() {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    console.warn(
      "[VADP] Supabase URL or anon key not configured. " +
        "Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local"
    );
  }

  return createSupabaseBrowserClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}
