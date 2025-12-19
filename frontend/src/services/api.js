import axios from 'axios';
import { API_BASE_URL, APP_CONFIG } from '../config/config';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // Try to get token from sessionStorage first (where Zustand persist stores it)
    const authStorage = sessionStorage.getItem('auth-storage');
    let token = null;
    
    if (authStorage) {
      try {
        const parsed = JSON.parse(authStorage);
        token = parsed.state?.token;
      } catch (e) {
        console.error('Failed to parse auth storage:', e);
      }
    }
    
    // Fallback to direct sessionStorage key
    if (!token) {
      token = sessionStorage.getItem(APP_CONFIG.tokenKey);
    }
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only redirect to login if user is authenticated and token is expired
    // Don't redirect on login page or during initial login attempt
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      const authStorage = sessionStorage.getItem('auth-storage');
      let hasToken = false;
      
      if (authStorage) {
        try {
          const parsed = JSON.parse(authStorage);
          hasToken = !!parsed.state?.token;
        } catch (e) {
          hasToken = false;
        }
      }
      
      // Only redirect if there was a token (authenticated user session expired)
      if (hasToken) {
        sessionStorage.removeItem('auth-storage');
        sessionStorage.removeItem(APP_CONFIG.tokenKey);
        sessionStorage.removeItem(APP_CONFIG.userKey);
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
