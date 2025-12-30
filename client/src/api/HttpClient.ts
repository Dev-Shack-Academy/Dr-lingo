import axios, { AxiosError, AxiosResponse } from 'axios';

/**
 * Get CSRF token from cookies
 */
function getCSRFToken(): string | null {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.trim().split('=');
    if (cookieName === name) {
      return cookieValue;
    }
  }
  return null;
}

/**
 * Wrapper for axios library.
 * Uses session/cookie-based authentication with OTP.
 */
const httpClient = axios.create({
  timeout: 600000, // 10 minutes for AI operations
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Send cookies with requests
});

/**
 * Attach request interceptor to add CSRF token
 */
httpClient.interceptors.request.use(
  (config) => {
    // Add CSRF token for non-GET requests
    if (config.method && !['get', 'head', 'options'].includes(config.method.toLowerCase())) {
      const csrfToken = getCSRFToken();
      if (csrfToken && config.headers) {
        config.headers.set('X-CSRFToken', csrfToken);
      }
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
  requiresOTP?: boolean;

  constructor(message: string, status?: number, data?: unknown, requiresOTP?: boolean) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.requiresOTP = requiresOTP;
  }
}

/**
 * Attach response interceptor to handle errors
 */
httpClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    // Check if OTP verification is required
    if (error.response?.status === 403) {
      const data = error.response.data as any;
      if (data?.detail?.includes('OTP') || data?.detail?.includes('two-factor')) {
        return Promise.reject(new ApiError('Two-factor authentication required', 403, data, true));
      }
    }

    // Handle 401 Unauthorized - session expired
    if (error.response?.status === 401) {
      window.location.href = '/login';
      return Promise.reject(new ApiError('Session expired. Please log in again.', 401));
    }

    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
      const apiError = new ApiError(
        'API request failed',
        error.response.status,
        error.response.data
      );
      return Promise.reject(apiError);
    }

    if (error.request) {
      console.error('Network Error:', error.message);
      return Promise.reject(
        new ApiError('Unable to connect to server. Please check your connection.')
      );
    }

    return Promise.reject(new ApiError(error.message || 'An unexpected error occurred.'));
  }
);

export default httpClient;
