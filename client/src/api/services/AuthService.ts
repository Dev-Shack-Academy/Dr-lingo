import httpClient from '../HttpClient';
import { API_BASE_URL } from '../routes';
import type { User, UserRole, RegisterData } from '../../types';

export type { User, UserRole, RegisterData };

export interface LoginResponse {
  user: User;
  requiresOTPSetup?: boolean;
  requiresOTPVerify?: boolean;
}

// Session auth state
let sessionUser: User | null = null;

const AuthService = {
  /**
   * Login user with session/cookie auth
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await httpClient.post<{
      user: User;
      requires_otp_setup?: boolean;
      requires_otp_verify?: boolean;
    }>(`${API_BASE_URL}/auth/login/`, { username, password });

    const { user, requires_otp_setup, requires_otp_verify } = response.data;

    // Only set as authenticated if no OTP required
    if (!requires_otp_setup && !requires_otp_verify) {
      sessionUser = user;
      localStorage.setItem('user', JSON.stringify(user));
    }

    return {
      user,
      requiresOTPSetup: requires_otp_setup,
      requiresOTPVerify: requires_otp_verify,
    };
  },

  /**
   * Verify OTP code for two-factor authentication
   */
  async verifyOTP(code: string): Promise<{ user: User }> {
    const response = await httpClient.post<{ user: User }>(`${API_BASE_URL}/auth/verify-otp/`, {
      otp_token: code,
    });

    sessionUser = response.data.user;
    localStorage.setItem('user', JSON.stringify(response.data.user));

    return response.data;
  },

  /**
   * Setup OTP for user - returns QR code for authenticator app
   */
  async setupOTP(): Promise<{ qr_code: string; secret: string }> {
    const response = await httpClient.post<{ qr_code: string; secret: string }>(
      `${API_BASE_URL}/auth/setup-otp/`
    );
    return response.data;
  },

  /**
   * Confirm OTP setup with verification code
   */
  async confirmOTPSetup(code: string): Promise<{ success: boolean; user: User }> {
    const response = await httpClient.post<{ success: boolean; user: User }>(
      `${API_BASE_URL}/auth/confirm-otp-setup/`,
      { otp_token: code }
    );

    // After confirming OTP setup, user is fully authenticated
    sessionUser = response.data.user;
    localStorage.setItem('user', JSON.stringify(response.data.user));

    return response.data;
  },

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<{ user: User }> {
    const response = await httpClient.post(`${API_BASE_URL}/auth/register/`, data);
    return response.data;
  },

  /**
   * Logout user and clear session
   */
  async logout(): Promise<void> {
    try {
      await httpClient.post(`${API_BASE_URL}/auth/logout/`);
    } catch (error) {
      if (error instanceof Error) {
        console.debug('Server logout failed, proceeding with client-side logout:', error.message);
      }
    }
    sessionUser = null;
    localStorage.removeItem('user');
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await httpClient.get<User>(`${API_BASE_URL}/auth/me/`);
    sessionUser = response.data;
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  },

  /**
   * Update user profile
   */
  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await httpClient.patch<User>(`${API_BASE_URL}/auth/profile/`, data);
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  },

  /**
   * Change password
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await httpClient.post(`${API_BASE_URL}/auth/change-password/`, {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('user');
  },

  /**
   * Get stored user from localStorage
   */
  getStoredUser(): User | null {
    if (sessionUser) return sessionUser;

    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
    return null;
  },

  /**
   * Check if user has specific role
   */
  hasRole(role: UserRole): boolean {
    const user = this.getStoredUser();
    return user?.role === role;
  },

  /**
   * Check if user is doctor or admin
   */
  canAccessDoctorFeatures(): boolean {
    const user = this.getStoredUser();
    return user?.role === 'doctor' || user?.role === 'admin';
  },
};

export default AuthService;
