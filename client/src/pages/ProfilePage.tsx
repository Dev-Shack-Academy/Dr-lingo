import { useAuth } from '../contexts/AuthContext';

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <div className="p-8 text-white">
      <h1 className="text-3xl font-bold mb-4">User Profile</h1>
      <div className="bg-gray-900 p-6 rounded-lg border border-gray-800">
        <p>
          <strong>Username:</strong> {user?.username}
        </p>
        <p>
          <strong>Email:</strong> {user?.email}
        </p>
        <p>
          <strong>Role:</strong> {user?.role}
        </p>
        <p className="mt-4 text-gray-500">Profile editing functionality coming soon...</p>
      </div>
    </div>
  );
}
