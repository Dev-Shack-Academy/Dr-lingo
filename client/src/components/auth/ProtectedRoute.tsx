import { ReactNode } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import LoginForm from './LoginForm';

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
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <LoginForm />
      </div>
    );
  }

  // Check role requirements
  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">
            You don't have permission to access this page. Required role: {requiredRole}
          </p>
        </div>
      </div>
    );
  }

  // Check doctor/admin access
  if (requireDoctorAccess && user?.role === 'patient') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md text-center">
          <h2 className="text-xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">
            This feature is only available to doctors and administrators.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
