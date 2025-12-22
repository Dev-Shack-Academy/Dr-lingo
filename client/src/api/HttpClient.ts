import axios, { AxiosError, AxiosResponse } from 'axios';

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * Token management utilities
 */
export const TokenManager = {
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),

  setTokens: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  },

  clearTokens: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  isAuthenticated: () => !!localStorage.getItem(ACCESS_TOKEN_KEY),
};

/**
 * Wrapper for axios library.
 * Use httpClient instance to configure axios http instance.
 */
const httpClient = axios.create({
  timeout: 60000, // 60 seconds for AI operations
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});

/**
 * Attach request interceptor to add JWT auth token
 */
httpClient.interceptors.request.use(
  (config) => {
    const token = TokenManager.getAccessToken();
    if (token && config.headers) {
      config.headers.set('Authorization', `Bearer ${token}`);
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

/**
 * Custom API Error class that preserves error details
 */
export class ApiError extends Error {
  status?: number;
  data?: unknown;

  constructor(message: string, status?: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Attach response interceptor to handle errors and token refresh
 */
httpClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Handle 401 Unauthorized - try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = TokenManager.getRefreshToken();
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/token/refresh/', {
            refresh: refreshToken,
          });

          const { access } = response.data;
          TokenManager.setTokens(access, refreshToken);

          // Retry original request with new token
          originalRequest.headers['Authorization'] = `Bearer ${access}`;
          return httpClient(originalRequest);
        } catch (refreshError) {
          // Refresh failed - clear tokens and redirect to login
          TokenManager.clearTokens();
          window.location.href = '/login';
          return Promise.reject(new ApiError('Session expired. Please log in again.', 401));
        }
      }
    }

    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.status, error.response.data);

      // Create ApiError with the response data preserved
      const apiError = new ApiError(
        'API request failed',
        error.response.status,
        error.response.data
      );
      return Promise.reject(apiError);
    }

    if (error.request) {
      // Request made but no response received
      console.error('Network Error:', error.message);
      return Promise.reject(
        new ApiError('Unable to connect to server. Please check your connection.')
      );
    }

    // Something else happened
    return Promise.reject(new ApiError(error.message || 'An unexpected error occurred.'));
  }
);

export default httpClient;
