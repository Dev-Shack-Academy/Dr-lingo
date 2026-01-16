import { ReactNode } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { AdminPanelSettings, ArrowBack } from '@mui/icons-material';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: 'patient' | 'doctor' | 'admin';
  requireDoctorAccess?: boolean;
}

export default function ProtectedRoute({
  children,
  requiredRole,
  requireDoctorAccess,
}: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check role requirements (superusers always have admin access)
  if (requiredRole) {
    const hasAccess =
      user?.role === requiredRole || (requiredRole === 'admin' && user?.is_superuser);

    if (!hasAccess) {
      return (
        <div className="min-h-screen bg-black flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md text-center border border-gray-200">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <AdminPanelSettings className="w-8 h-8 text-gray-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600 mb-6">You don't have permission to access this page.</p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 bg-black text-white px-6 py-3 rounded-lg hover:bg-gray-800 transition-colors font-semibold"
            >
              <ArrowBack className="w-4 h-4" />
              Go Home
            </Link>
          </div>
        </div>
      );
    }
  }

  // Check doctor/admin access
  if (requireDoctorAccess && user?.role === 'patient') {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md text-center border border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-6">
            This feature is only available to doctors and administrators.
          </p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 bg-black text-white px-6 py-3 rounded-lg hover:bg-gray-800 transition-colors font-semibold"
          >
            <ArrowBack className="w-4 h-4" />
            Go Home
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
