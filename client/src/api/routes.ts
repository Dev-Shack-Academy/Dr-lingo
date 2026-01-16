/**
 * This file defines all API routes in one place.
 * Avoids hard coding strings throughout the application.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const routes = {
  // Chat routes
  CHAT: '/chat/',
  CHAT_ROOMS: '/chat-rooms/',
  MESSAGES: '/messages/',

  // Item/Resource routes
  ITEMS: '/items/',
  COLLECTIONS: '/collections/',
  COLLECTION_ITEMS: '/collection-items/',

  // System routes
  HEALTH_CHECK: '/health/',
  CONFIG_AI: '/config/ai/',
  TASK_STATUS: '/tasks/',
  CELERY_STATUS: '/celery/status/',

  // Auth routes
  AUTH_LOGIN: '/auth/login/',
  AUTH_REGISTER: '/auth/register/',
  AUTH_LOGOUT: '/auth/logout/',
  AUTH_ME: '/auth/me/',
  AUTH_PROFILE: '/auth/profile/',
  AUTH_CHANGE_PASSWORD: '/auth/change-password/',

  // OTP (Two-Factor) routes
  AUTH_VERIFY_OTP: '/auth/verify-otp/',
  AUTH_SETUP_OTP: '/auth/setup-otp/',
  AUTH_CONFIRM_OTP_SETUP: '/auth/confirm-otp-setup/',

  // User management routes (Admin)
  USERS: '/users/',
};

export default routes;
