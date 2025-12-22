/**
 * This file defines all API routes in one place.
 * Avoids hard coding strings throughout the application.
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const routes = {
  CHAT: '/chat',
  ITEMS: '/items/',
  HEALTH_CHECK: '/health/',
  // Auth routes
  AUTH_LOGIN: '/auth/login/',
  AUTH_REGISTER: '/auth/register/',
  AUTH_ME: '/auth/me/',
  AUTH_PROFILE: '/auth/profile/',
  AUTH_CHANGE_PASSWORD: '/auth/change-password/',
};

export default routes;
