import { create } from "zustand";
import { persist } from "zustand/middleware";
import { loginJson, refreshToken, getMe } from "@/lib/api/auth";
import type { User, LoginRequest } from "@/lib/api/auth";

function setAuthCookie(token: string) {
  document.cookie = `access_token=${token}; path=/; max-age=86400; SameSite=Lax`;
}

function clearAuthCookie() {
  document.cookie = "access_token=; path=/; max-age=0; SameSite=Lax";
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  restore: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await loginJson(credentials);
          localStorage.setItem("access_token", tokens.access_token);
          localStorage.setItem("refresh_token", tokens.refresh_token);
          setAuthCookie(tokens.access_token);
          const user = await getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (err) {
          const message = err instanceof Error ? err.message : "Ошибка входа";
          set({ error: message, isLoading: false, isAuthenticated: false });
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        clearAuthCookie();
        set({ user: null, isAuthenticated: false, error: null });
      },

      restore: async () => {
        const refresh = localStorage.getItem("refresh_token");
        if (!refresh) {
          set({ isAuthenticated: false });
          return;
        }
        set({ isLoading: true });
        try {
          const tokens = await refreshToken(refresh);
          localStorage.setItem("access_token", tokens.access_token);
          localStorage.setItem("refresh_token", tokens.refresh_token);
          const user = await getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },
    }),
    {
      name: "feleti-auth",
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
