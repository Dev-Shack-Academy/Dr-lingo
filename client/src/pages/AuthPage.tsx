import { useState } from 'react';
import { LoginForm, RegisterForm } from '../components/auth';

interface AuthPageProps {
  onSuccess?: () => void;
}

export default function AuthPage({ onSuccess }: AuthPageProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Medical Translation</h1>
          <p className="text-gray-400">AI-powered medical communication</p>
        </div>

        {/* Auth Form */}
        {mode === 'login' ? (
          <LoginForm onSuccess={onSuccess} onRegisterClick={() => setMode('register')} />
        ) : (
          <RegisterForm onSuccess={() => setMode('login')} onLoginClick={() => setMode('login')} />
        )}
      </div>
    </div>
  );
}
