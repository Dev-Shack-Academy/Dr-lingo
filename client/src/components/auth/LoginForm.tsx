import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import OTPSetup from './OTPSetup';
import LockIcon from '@mui/icons-material/Lock';

interface LoginFormProps {
  onSuccess?: () => void;
  onRegisterClick?: () => void;
}

export default function LoginForm({ onSuccess, onRegisterClick }: LoginFormProps) {
  const { login, verifyOTP, otpState } = useAuth();
  const { showError, showSuccess } = useToast();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await login(username, password);
      if (result.otpState === 'none') {
        onSuccess?.();
      }
      // If otpState is 'setup' or 'verify', the UI will update automatically
    } catch (err) {
      showError(err, 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleOTPVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await verifyOTP(otpCode);
      showSuccess('Verification successful!');
      onSuccess?.();
    } catch (err) {
      showError(err, 'Invalid verification code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Show OTP Setup flow
  if (otpState === 'setup') {
    return (
      <OTPSetup
        onComplete={() => {
          showSuccess('Two-factor authentication enabled!');
          onSuccess?.();
        }}
      />
    );
  }

  // Show OTP Verification form
  if (otpState === 'verify') {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">
            Two-Factor Authentication
          </h2>
          <p className="text-gray-600 text-center mb-6">
            Enter the verification code from your authenticator app
          </p>

          <form onSubmit={handleOTPVerify} className="space-y-4">
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-1">
                Verification Code
              </label>
              <input
                id="otp"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-center text-2xl tracking-widest"
                placeholder="000000"
                autoFocus
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading || otpCode.length !== 6}
              className="w-full bg-black hover:bg-gray-800 text-white font-semibold py-3 rounded-lg transition-colors disabled:bg-gray-400"
            >
              {loading ? 'Verifying...' : 'Verify'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Show Login form
  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-xl p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Sign In</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black hover:bg-gray-800 text-white font-semibold py-3 rounded-lg transition-colors disabled:bg-gray-400"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-gray-500">
          <LockIcon /> Secure session with two-factor authentication
        </p>

        {onRegisterClick && (
          <p className="mt-6 text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <button onClick={onRegisterClick} className="text-black font-semibold hover:underline">
              Register
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
