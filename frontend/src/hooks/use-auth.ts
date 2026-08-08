/**
 * VADP — Auth Custom Hook
 *
 * Provides authentication actions (login, register, logout) and state.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth-store";
import type { AuthResponse, LoginRequest, RegisterRequest } from "@/types/auth";

export function useAuth() {
  const router = useRouter();
  const { user, isAuthenticated, setAuth, logout: clearAuthStore } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.post<AuthResponse>("/auth/login", credentials);
      setAuth(data.user, data.access_token, data.refresh_token);

      // Redirect based on role
      const redirectMap: Record<string, string> = {
        citizen: "/citizen",
        lawyer: "/lawyer",
        judge: "/judge",
        admin: "/admin",
        court_clerk: "/judge",
        registrar: "/admin",
      };
      const dest = redirectMap[data.user.role] || "/citizen";
      router.push(dest);
    } catch (err: any) {
      setError(err.message || "Failed to log in. Please check your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.post<AuthResponse>("/auth/register", payload);
      setAuth(data.user, data.access_token, data.refresh_token);

      const redirectMap: Record<string, string> = {
        citizen: "/citizen",
        lawyer: "/lawyer",
        judge: "/judge",
        admin: "/admin",
      };
      router.push(redirectMap[data.user.role] || "/citizen");
    } catch (err: any) {
      setError(err.message || "Failed to register account.");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearAuthStore();
    router.push("/login");
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
  };
}
