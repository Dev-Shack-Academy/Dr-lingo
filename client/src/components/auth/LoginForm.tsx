import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

interface LoginFormProps {
  onSuccess?: () => void;
  onRegisterClick?: () => void;
}

export default function LoginForm({ onSuccess, onRegisterClick }: LoginFormProps) {
  const { login } = useAuth();
  const { showError } = useToast();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(username, password);
      onSuccess?.();
    } catch (err) {
      showError(err, 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

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
