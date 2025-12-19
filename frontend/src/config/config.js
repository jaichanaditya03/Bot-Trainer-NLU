export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const APP_CONFIG = {
  name: 'Bot Trainer Application',
  logo: 'https://cdn-icons-png.flaticon.com/512/4712/4712027.png',
  version: '1.0.0',
  tokenKey: 'bot_trainer_token',
  userKey: 'bot_trainer_user',
};

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  DASHBOARD: '/dashboard',
  ADMIN_PANEL: '/admin',
};
