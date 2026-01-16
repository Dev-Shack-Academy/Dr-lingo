import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

interface OTPSetupProps {
  onComplete?: () => void;
  onCancel?: () => void;
}

export default function OTPSetup({ onComplete, onCancel }: OTPSetupProps) {
  const { setupOTP, confirmOTPSetup } = useAuth();
  const { showError, showSuccess } = useToast();
  const [step, setStep] = useState<'intro' | 'qr' | 'verify'>('intro');
  const [qrCode, setQrCode] = useState('');
  const [secret, setSecret] = useState('');
  const [verifyCode, setVerifyCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleStartSetup = async () => {
    setLoading(true);
    try {
      const result = await setupOTP();
      setQrCode(result.qr_code);
      setSecret(result.secret);
      setStep('qr');
    } catch (err) {
      showError(err, 'Failed to start OTP setup');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await confirmOTPSetup(verifyCode);
      showSuccess('Two-factor authentication enabled successfully!');
      onComplete?.();
    } catch (err) {
      showError(err, 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'intro') {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-black rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Set Up Two-Factor Authentication
            </h2>
            <p className="text-gray-600">
              Add an extra layer of security to your account using an authenticator app.
            </p>
          </div>

          <div className="space-y-4 mb-6">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-sm font-medium">1</span>
              </div>
              <p className="text-sm text-gray-600">
                Download an authenticator app like Google Authenticator or Authy
              </p>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-sm font-medium">2</span>
              </div>
              <p className="text-sm text-gray-600">Scan the QR code with your authenticator app</p>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-sm font-medium">3</span>
              </div>
              <p className="text-sm text-gray-600">Enter the 6-digit code to verify setup</p>
            </div>
          </div>

          <button
            onClick={handleStartSetup}
            disabled={loading}
            className="w-full bg-black hover:bg-gray-800 text-white font-semibold py-3 rounded-lg transition-colors disabled:bg-gray-400"
          >
            {loading ? 'Setting up...' : 'Get Started'}
          </button>

          {onCancel && (
            <button
              onClick={onCancel}
              className="mt-3 w-full text-gray-600 hover:text-gray-800 text-sm py-2"
            >
              Skip for now
            </button>
          )}
        </div>
      </div>
    );
  }

  if (step === 'qr') {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">Scan QR Code</h2>
          <p className="text-gray-600 text-center mb-6">
            Open your authenticator app and scan this QR code
          </p>

          {qrCode && (
            <div className="flex justify-center mb-6">
              <img src={qrCode} alt="QR Code for authenticator" className="w-48 h-48" />
            </div>
          )}

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-xs text-gray-500 mb-1">Can't scan? Enter this code manually:</p>
            <code className="text-sm font-mono text-black break-all">{secret}</code>
          </div>

          <button
            onClick={() => setStep('verify')}
            className="w-full bg-black hover:bg-gray-800 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            I've scanned the code
          </button>

          <button
            onClick={() => setStep('intro')}
            className="mt-3 w-full text-gray-600 hover:text-gray-800 text-sm py-2"
          >
            ← Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-xl p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">Verify Setup</h2>
        <p className="text-gray-600 text-center mb-6">
          Enter the 6-digit code from your authenticator app
        </p>

        <form onSubmit={handleVerify} className="space-y-4">
          <div>
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ''))}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-center text-2xl tracking-widest"
              placeholder="000000"
              autoFocus
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || verifyCode.length !== 6}
            className="w-full bg-black hover:bg-gray-800 text-white font-semibold py-3 rounded-lg transition-colors disabled:bg-gray-400"
          >
            {loading ? 'Verifying...' : 'Complete Setup'}
          </button>
        </form>

        <button
          onClick={() => setStep('qr')}
          className="mt-3 w-full text-gray-600 hover:text-gray-800 text-sm py-2"
        >
          ← Back to QR code
        </button>
      </div>
    </div>
  );
}
