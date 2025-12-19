import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { APP_CONFIG } from '../config/config';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      loginTimestamp: null,

      login: (token, user) => {
        // Prevent crashing on undefined token
        if (!token) {
          console.warn("Login called without token");
          return;
        }

        try {
          const loginTime = Date.now();

          set({
            token,
            user,
            isAuthenticated: true,
            loginTimestamp: loginTime,
          });

          console.log('✅ Login successful - Session expires in 12 hours');
        } catch (err) {
          console.error("Auth store login error:", err);
        }
      },

      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          loginTimestamp: null,
        });
        console.log('🔒 Logged out successfully');
      },

      checkSession: () => {
        const state = get();
        if (!state.isAuthenticated || !state.loginTimestamp) {
          return true; // No active session
        }

        const now = Date.now();
        const sessionDuration = now - state.loginTimestamp;
        const twelveHoursInMs = 12 * 60 * 60 * 1000; // 12 hours in milliseconds

        if (sessionDuration >= twelveHoursInMs) {
          console.log('⏰ Session expired after 12 hours - Auto logout');
          get().logout();
          return false;
        }

        return true;
      },

      updateUser: (userData) => {
        set((state) => ({
          user: { ...state.user, ...userData },
        }));
      },
    }),
    {
      name: 'auth-storage',
      storage: {
        getItem: (name) => {
          const value = sessionStorage.getItem(name);
          return value ? JSON.parse(value) : null;
        },
        setItem: (name, value) => {
          sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => {
          sessionStorage.removeItem(name);
        },
      },
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        loginTimestamp: state.loginTimestamp,
      }),
    }
  )
);
