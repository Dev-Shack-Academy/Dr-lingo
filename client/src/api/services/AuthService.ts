import httpClient, { TokenManager } from '../HttpClient';
import { API_BASE_URL } from '../routes';
import type { User, UserRole, RegisterData, LoginResponse } from '../../types';

// Re-export types for backward compatibility
export type { User, UserRole, RegisterData, LoginResponse };

const AuthService = {
  /**
   * Login user and store tokens
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await httpClient.post<{
      access: string;
      refresh: string;
      user: User;
    }>(`${API_BASE_URL}/auth/login/`, { username, password });

    const { access, refresh, user } = response.data;
    TokenManager.setTokens(access, refresh);

    // Store user info
    localStorage.setItem('user', JSON.stringify(user));

    return {
      user,
      tokens: { access, refresh },
    };
  },

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<{ user: User }> {
    const response = await httpClient.post(`${API_BASE_URL}/auth/register/`, data);
    return response.data;
  },

  /**
   * Logout user and clear tokens
   */
  logout(): void {
    TokenManager.clearTokens();
    localStorage.removeItem('user');
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await httpClient.get<User>(`${API_BASE_URL}/auth/me/`);
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
    return TokenManager.isAuthenticated();
  },

  /**
   * Get stored user from localStorage
   */
  getStoredUser(): User | null {
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
