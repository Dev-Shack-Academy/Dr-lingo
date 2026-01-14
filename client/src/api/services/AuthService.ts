import httpClient, { API_BASE_URL } from '../HttpClient';
import routes from '../routes';
import type { User, UserRole, RegisterData } from '../../types';

export type { User, UserRole, RegisterData };

export interface LoginResponse {
  user: User;
  requiresOTPSetup?: boolean;
  requiresOTPVerify?: boolean;
}

/**
 * Minimal user data safe to store in localStorage.
 * Does NOT include sensitive fields like tokens, passwords, or PII.
 */
interface StoredUserData {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
}

// In-memory cache of full user data (cleared on page refresh)
let sessionUser: User | null = null;

// Track last server verification time
let lastVerifiedAt: number | null = null;
const VERIFICATION_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Sanitize user data for localStorage storage.
 * Only stores minimal, non-sensitive display data.
 */
function sanitizeUserForStorage(user: User): StoredUserData {
  return {
    id: user.id,
    username: user.username,
    email: user.email,
    first_name: user.first_name,
    last_name: user.last_name,
    role: user.role,
  };
}

/**
 * Convert stored data back to partial user object.
 */
function storedDataToUser(data: StoredUserData): Partial<User> {
  return {
    id: data.id,
    username: data.username,
    email: data.email,
    first_name: data.first_name,
    last_name: data.last_name,
    role: data.role as UserRole,
  };
}

/**
 * Safely write to localStorage with sanitization.
 */
function saveUserToStorage(user: User): void {
  try {
    const sanitized = sanitizeUserForStorage(user);
    localStorage.setItem('user_display', JSON.stringify(sanitized));
    lastVerifiedAt = Date.now();
  } catch (error) {
    console.warn('Failed to save user to localStorage:', error);
  }
}

/**
 * Clear all auth-related localStorage data.
 */
function clearAuthStorage(): void {
  localStorage.removeItem('user_display');
  localStorage.removeItem('user'); // Clean up legacy key
  sessionUser = null;
  lastVerifiedAt = null;
}

const AuthService = {
  /**
   * Login user with session/cookie auth.
   * Auth token is stored in httpOnly cookie by the server.
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await httpClient.post<{
      user: User;
      requires_otp_setup?: boolean;
      requires_otp_verify?: boolean;
    }>(`${API_BASE_URL}${routes.AUTH_LOGIN}`, { username, password });

    const { user, requires_otp_setup, requires_otp_verify } = response.data;

    // Only set as authenticated if no OTP required
    if (!requires_otp_setup && !requires_otp_verify) {
      sessionUser = user;
      saveUserToStorage(user);
    }

    return {
      user,
      requiresOTPSetup: requires_otp_setup,
      requiresOTPVerify: requires_otp_verify,
    };
  },

  /**
   * Verify OTP code for two-factor authentication.
   */
  async verifyOTP(code: string): Promise<{ user: User }> {
    const response = await httpClient.post<{ user: User }>(
      `${API_BASE_URL}${routes.AUTH_VERIFY_OTP}`,
      {
        otp_token: code,
      }
    );

    sessionUser = response.data.user;
    saveUserToStorage(response.data.user);

    return response.data;
  },

  /**
   * Setup OTP for user - returns QR code for authenticator app.
   */
  async setupOTP(): Promise<{ qr_code: string; secret: string }> {
    const response = await httpClient.post<{ qr_code: string; secret: string }>(
      `${API_BASE_URL}${routes.AUTH_SETUP_OTP}`
    );
    return response.data;
  },

  /**
   * Confirm OTP setup with verification code.
   */
  async confirmOTPSetup(code: string): Promise<{ success: boolean; user: User }> {
    const response = await httpClient.post<{ success: boolean; user: User }>(
      `${API_BASE_URL}${routes.AUTH_CONFIRM_OTP_SETUP}`,
      { otp_token: code }
    );

    // After confirming OTP setup, user is fully authenticated
    sessionUser = response.data.user;
    saveUserToStorage(response.data.user);

    return response.data;
  },

  /**
   * Register a new user.
   */
  async register(data: RegisterData): Promise<{ user: User }> {
    const response = await httpClient.post(`${API_BASE_URL}${routes.AUTH_REGISTER}`, data);
    return response.data;
  },

  /**
   * Logout user and clear session.
   */
  async logout(): Promise<void> {
    try {
      await httpClient.post(`${API_BASE_URL}${routes.AUTH_LOGOUT}`);
    } catch (error) {
      console.debug('Server logout failed, proceeding with client-side logout');
    }
    clearAuthStorage();
  },

  /**
   * Get current user profile from server.
   * This verifies the session is still valid.
   */
  async getCurrentUser(): Promise<User> {
    const response = await httpClient.get<User>(`${API_BASE_URL}${routes.AUTH_ME}`);
    sessionUser = response.data;
    saveUserToStorage(response.data);
    return response.data;
  },

  /**
   * Update user profile.
   */
  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await httpClient.patch<User>(`${API_BASE_URL}${routes.AUTH_PROFILE}`, data);
    sessionUser = response.data;
    saveUserToStorage(response.data);
    return response.data;
  },

  /**
   * Change password.
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await httpClient.post(`${API_BASE_URL}${routes.AUTH_CHANGE_PASSWORD}`, {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  /**
   * Check if user appears to be authenticated (has stored session data).
   * NOTE: This only checks for presence of stored data, not actual session validity.
   * For security-critical operations, use verifySession() instead.
   */
  hasStoredSession(): boolean {
    return !!localStorage.getItem('user_display');
  },

  /**
   * Verify session is still valid with the server.
   * Use this for security-critical operations.
   * Returns the user if valid, null if session is invalid/expired.
   */
  async verifySession(): Promise<User | null> {
    try {
      const user = await this.getCurrentUser();
      return user;
    } catch {
      clearAuthStorage();
      return null;
    }
  },

  /**
   * Check if session needs re-verification based on time elapsed.
   */
  needsVerification(): boolean {
    if (!lastVerifiedAt) return true;
    return Date.now() - lastVerifiedAt > VERIFICATION_INTERVAL_MS;
  },

  /**
   * Get stored user display data from localStorage.
   * Returns in-memory cached user if available, otherwise minimal stored data.
   * NOTE: This may be stale - use getCurrentUser() for fresh data.
   */
  getStoredUser(): User | null {
    // Return in-memory cache if available (most up-to-date)
    if (sessionUser) return sessionUser;

    // Fall back to localStorage display data
    const storedStr = localStorage.getItem('user_display');
    if (storedStr) {
      try {
        const stored = JSON.parse(storedStr) as StoredUserData;
        // Return partial user data (enough for display purposes)
        return storedDataToUser(stored) as User;
      } catch {
        clearAuthStorage();
        return null;
      }
    }

    // Check for legacy 'user' key and migrate
    const legacyStr = localStorage.getItem('user');
    if (legacyStr) {
      try {
        const legacyUser = JSON.parse(legacyStr) as User;
        // Migrate to new sanitized storage
        saveUserToStorage(legacyUser);
        localStorage.removeItem('user');
        return legacyUser;
      } catch {
        localStorage.removeItem('user');
        return null;
      }
    }

    return null;
  },

  /**
   * Check if user has specific role.
   */
  hasRole(role: UserRole): boolean {
    const user = this.getStoredUser();
    return user?.role === role;
  },

  /**
   * Check if user is admin.
   */
  isAdmin(): boolean {
    const user = this.getStoredUser();
    return user?.role === 'admin';
  },

  /**
   * Check if user is doctor or admin.
   */
  canAccessDoctorFeatures(): boolean {
    const user = this.getStoredUser();
    return user?.role === 'doctor' || user?.role === 'admin';
  },

  /**
   * @deprecated Use hasStoredSession() for quick checks or verifySession() for security-critical operations.
   */
  isAuthenticated(): boolean {
    return this.hasStoredSession();
  },
};

export default AuthService;
