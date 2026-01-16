import axios, { AxiosError, AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * HTTP client configured for session-based authentication.
 */
const httpClient = axios.create({
  timeout: 600000, // 10 minutes for AI operations
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookies for session auth (required for cross-origin)
});

// Store CSRF token in memory (for cross-origin requests where cookie isn't readable)
let csrfToken: string | null = null;

/**
 * Fetch CSRF token from the server.
 * Call this on app initialization.
 */
export async function fetchCsrfToken(): Promise<string | null> {
  try {
    const response = await axios.get(`${API_BASE_URL}/auth/csrf/`, {
      withCredentials: true,
    });
    csrfToken = response.data.csrfToken;
    return csrfToken;
  } catch (error) {
    console.error('Failed to fetch CSRF token:', error);
    return null;
  }
}

/**
 * Request interceptor for CSRF token handling
 */
httpClient.interceptors.request.use(
  (config) => {
    // First try to get CSRF token from cookie
    let token = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrftoken='))
      ?.split('=')[1];

    if (token) {
      token = decodeURIComponent(token);
    } else {
      // Fall back to in-memory token (for cross-origin)
      token = csrfToken || undefined;
    }

    if (token && config.headers) {
      config.headers['X-CSRFToken'] = token;
    }

    // Special handling for FormData (file uploads)
    if (config.data instanceof FormData) {
      config.headers.setContentType(null);
    }

    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

/**
 * Response interceptor for error handling
 */
httpClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as Record<string, unknown>;

      // Handle authentication errors
      if (status === 401) {
        // Clear local storage and redirect to login
        localStorage.removeItem('user_display');
        localStorage.removeItem('user'); // Legacy cleanup
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }

      const message = data?.error || data?.detail || 'Unknown error';
      return Promise.reject(new Error(String(message)));
    }

    if (error.request) {
      return Promise.reject(new Error('No response received from server.'));
    }

    return Promise.reject(new Error(error.message));
  }
);

export default httpClient;
export { API_BASE_URL };
