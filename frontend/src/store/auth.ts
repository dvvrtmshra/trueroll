import { create } from "zustand";

interface AuthState {
  token: string | null;
  user: Record<string, unknown> | null;
  setToken: (token: string) => void;
  setUser: (user: Record<string, unknown>) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: sessionStorage.getItem("tr_token"),
  user: null,
  setToken: (token) => {
    sessionStorage.setItem("tr_token", token);
    set({ token });
  },
  setUser: (user) => set({ user }),
  logout: () => {
    sessionStorage.removeItem("tr_token");
    set({ token: null, user: null });
  },
}));
