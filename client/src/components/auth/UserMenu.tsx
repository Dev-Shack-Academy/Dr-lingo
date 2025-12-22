import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Person, Logout, Settings } from '@mui/icons-material';

export default function UserMenu() {
  const { user, logout, isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  if (!isAuthenticated || !user) {
    return null;
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'doctor':
        return 'bg-blue-100 text-blue-800';
      case 'admin':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
          <Person className="w-5 h-5 text-gray-600" />
        </div>
        <div className="text-left hidden sm:block">
          <p className="text-sm font-medium text-gray-900">{user.first_name || user.username}</p>
          <span className={`text-xs px-2 py-0.5 rounded-full ${getRoleBadgeColor(user.role)}`}>
            {user.role}
          </span>
        </div>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
            <div className="p-4 border-b border-gray-100">
              <p className="font-medium text-gray-900">
                {user.first_name} {user.last_name}
              </p>
              <p className="text-sm text-gray-500">{user.email}</p>
            </div>

            <div className="p-2">
              <button
                onClick={() => {
                  setIsOpen(false);
                  // Navigate to settings
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                <Settings className="w-4 h-4" />
                Settings
              </button>

              <button
                onClick={() => {
                  logout();
                  setIsOpen(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
              >
                <Logout className="w-4 h-4" />
                Sign Out
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
