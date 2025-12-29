import { useState } from 'react';
import AuthService, { RegisterData } from '../../api/services/AuthService';
import { useToast } from '../../contexts/ToastContext';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LockIcon from '@mui/icons-material/Lock';
import SecurityIcon from '@mui/icons-material/Security';

interface RegisterFormProps {
  onSuccess?: () => void;
  onLoginClick?: () => void;
}

export default function RegisterForm({ onSuccess, onLoginClick }: RegisterFormProps) {
  const { showError, showSuccess, showWarning } = useToast();
  const [formData, setFormData] = useState<RegisterData>({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    role: 'patient',
    preferred_language: 'en',
  });
  const [loading, setLoading] = useState(false);
  const [registrationComplete, setRegistrationComplete] = useState(false);
  const [newUsername, setNewUsername] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.password_confirm) {
      showWarning('Passwords do not match', 'Validation Error');
      return;
    }

    if (formData.password.length < 8) {
      showWarning('Password must be at least 8 characters long', 'Validation Error');
      return;
    }

    setLoading(true);
    try {
      await AuthService.register(formData);
      setNewUsername(formData.username);
      setRegistrationComplete(true);
    } catch (err) {
      showError(err, 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Show success screen with next steps
  if (registrationComplete) {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <div className="text-center mb-6">
            <CheckCircleIcon sx={{ fontSize: 64, color: '#000', marginBottom: 2 }} />
            <h2 className="text-2xl font-bold text-gray-900">Account Created!</h2>
            <p className="text-gray-600 mt-2">Welcome to Dr-Lingo</p>
          </div>

          <div className="bg-gray-50 rounded-lg p-6 mb-6 space-y-4">
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center h-8 w-8 rounded-full bg-black text-white text-sm font-bold">
                  1
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Sign In</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Use your username{' '}
                  <span className="font-mono bg-white px-2 py-1 rounded">{newUsername}</span> to
                  sign in
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center h-8 w-8 rounded-full bg-black text-white text-sm font-bold">
                  2
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <SecurityIcon sx={{ fontSize: 18 }} />
                  Set Up Two-Factor Authentication
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  You'll be prompted to set up 2FA with your authenticator app (Google
                  Authenticator, Authy, etc.)
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="flex items-center justify-center h-8 w-8 rounded-full bg-black text-white text-sm font-bold">
                  3
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Start Using Dr-Lingo</h3>
                <p className="text-sm text-gray-600 mt-1">
                  After 2FA setup, you'll have full access to the platform
                </p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border items-center border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-900 flex items-center gap-2">
              <LockIcon sx={{ fontSize: 18 }} />
              <span>Sign in and secure your account</span>
            </p>
          </div>

          <button
            onClick={() => {
              setRegistrationComplete(false);
              onLoginClick?.();
            }}
            className="w-full bg-black hover:bg-gray-800 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            Sign In Now
          </button>

          <p className="mt-4 text-center text-xs text-gray-500">
            You'll set up two-factor authentication after signing in
          </p>
        </div>
      </div>
    );
  }

  const languages = [
    // International Languages
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ar', name: 'Arabic' },
    { code: 'hi', name: 'Hindi' },
    { code: 'pt', name: 'Portuguese' },
    // South African Languages
    { code: 'zul', name: 'isiZulu' },
    { code: 'xho', name: 'isiXhosa' },
    { code: 'afr', name: 'Afrikaans' },
    { code: 'sot', name: 'Sesotho' },
    { code: 'tsn', name: 'Setswana' },
    { code: 'nso', name: 'Sepedi' },
    { code: 'ssw', name: 'siSwati' },
    { code: 'ven', name: 'Tshivenda' },
    { code: 'tso', name: 'Xitsonga' },
    { code: 'nbl', name: 'isiNdebele' },
  ];

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-xl p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Create Account</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username *</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              >
                <option value="patient">Patient</option>
                <option value="doctor">Doctor</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
              <select
                name="preferred_language"
                value={formData.preferred_language}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confirm Password *
            </label>
            <input
              type="password"
              name="password_confirm"
              value={formData.password_confirm}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black hover:bg-gray-800 text-white font-semibold py-3 rounded-lg transition-colors disabled:bg-gray-400"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        {onLoginClick && (
          <p className="mt-6 text-center text-sm text-gray-600">
            Already have an account?{' '}
            <button onClick={onLoginClick} className="text-black font-semibold hover:underline">
              Sign In
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
