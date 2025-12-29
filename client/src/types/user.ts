/**
 * User-related type definitions
 */

export type UserRole = 'patient' | 'doctor' | 'admin';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  preferred_language: string;
  is_active: boolean;
  is_superuser: boolean;
  phone_number?: string;
  medical_license?: string;
  patient_id?: string;
  department?: string;
  date_joined?: string;
  last_login?: string;
}

export interface UserProfile {
  id: number;
  user: number;
  cultural_background: string;
  communication_preferences: Record<string, any>;
  medical_conditions: string;
  allergies: string;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  role?: UserRole;
  preferred_language?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  user: User;
  requiresOTPSetup?: boolean;
  requiresOTPVerify?: boolean;
}

export interface CreateUserData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  preferred_language?: string;
}

export interface UpdateUserData {
  first_name?: string;
  last_name?: string;
  email?: string;
  role?: UserRole;
  preferred_language?: string;
  is_active?: boolean;
}
