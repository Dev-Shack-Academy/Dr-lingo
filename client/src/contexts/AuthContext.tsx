import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AuthService, { User } from '../api/services/AuthService';

type OTPState = 'none' | 'setup' | 'verify';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  otpState: OTPState;
  login: (username: string, password: string) => Promise<{ otpState: OTPState }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  verifyOTP: (code: string) => Promise<void>;
  setupOTP: () => Promise<{ qr_code: string; secret: string }>;
  confirmOTPSetup: (code: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [otpState, setOtpState] = useState<OTPState>('none');

  useEffect(() => {
    const initAuth = async () => {
      if (AuthService.isAuthenticated()) {
        try {
          const currentUser = await AuthService.getCurrentUser();
          setUser(currentUser);
        } catch {
          await AuthService.logout();
        }
      }
      setIsLoading(false);
    };
    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    const response = await AuthService.login(username, password);

    // Store user temporarily for OTP flow
    setUser(response.user);

    if (response.requiresOTPSetup) {
      setOtpState('setup');
      return { otpState: 'setup' as OTPState };
    }

    if (response.requiresOTPVerify) {
      setOtpState('verify');
      return { otpState: 'verify' as OTPState };
    }

    // No OTP required - fully authenticated
    setOtpState('none');
    return { otpState: 'none' as OTPState };
  };

  const logout = async () => {
    await AuthService.logout();
    setUser(null);
    setOtpState('none');
  };

  const refreshUser = async () => {
    if (AuthService.isAuthenticated()) {
      const currentUser = await AuthService.getCurrentUser();
      setUser(currentUser);
    }
  };

  const verifyOTP = async (code: string) => {
    const response = await AuthService.verifyOTP(code);
    setUser(response.user);
    setOtpState('none');
  };

  const setupOTP = async () => {
    return await AuthService.setupOTP();
  };

  const confirmOTPSetup = async (code: string) => {
    const response = await AuthService.confirmOTPSetup(code);
    setUser(response.user);
    setOtpState('none');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user && otpState === 'none',
        isLoading,
        otpState,
        login,
        logout,
        refreshUser,
        verifyOTP,
        setupOTP,
        confirmOTPSetup,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
