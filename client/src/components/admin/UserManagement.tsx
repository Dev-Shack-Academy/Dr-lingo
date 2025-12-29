import { useState, useEffect } from 'react';
import { Add, Edit, Delete, Refresh, People, Close, PersonAdd } from '@mui/icons-material';
import AdminService, { CreateUserData } from '../../api/services/AdminService';
import { User } from '../../api/services/AuthService';
import { useToast } from '../../contexts/ToastContext';

const LANGUAGES = [
  // International Languages
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'ja', name: 'Japanese' },
  // South African Languages (Official)
  { code: 'zul', name: 'isiZulu' },
  { code: 'xho', name: 'isiXhosa' },
  { code: 'afr', name: 'Afrikaans' },
  { code: 'sot', name: 'Sesotho' },
  { code: 'tsn', name: 'Setswana' },
  { code: 'nso', name: 'Sepedi (Northern Sotho)' },
  { code: 'ssw', name: 'siSwati' },
  { code: 'ven', name: 'Tshivenda' },
  { code: 'tso', name: 'Xitsonga' },
  { code: 'nbl', name: 'isiNdebele' },
];

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const { showError, showSuccess } = useToast();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await AdminService.getUsers();
      setUsers(data);
    } catch (err) {
      showError(err, 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await AdminService.deleteUser(id);
      showSuccess('User deleted');
      loadUsers();
    } catch (err) {
      showError(err, 'Failed to delete user');
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-black text-white';
      case 'doctor':
        return 'bg-gray-700 text-white';
      default:
        return 'bg-gray-200 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
            <People className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
            <p className="text-sm text-gray-500">{users.length} users total</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadUsers}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-gray-700"
          >
            <Refresh className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            <Add className="w-4 h-4" />
            Add User
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading users...</div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Language
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-sm font-semibold text-gray-600">
                          {(user.first_name?.[0] || user.username[0]).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">
                          {user.first_name} {user.last_name || user.username}
                        </p>
                        <p className="text-sm text-gray-500">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-3 py-1 text-xs font-semibold rounded-full ${getRoleBadge(user.role)}`}
                    >
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {LANGUAGES.find((l) => l.code === user.preferred_language)?.name ||
                      user.preferred_language?.toUpperCase() ||
                      'EN'}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-3 py-1 text-xs font-semibold rounded-full ${
                        user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => setEditingUser(user)}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(user.id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Delete className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadUsers();
          }}
        />
      )}

      {editingUser && (
        <EditUserModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSuccess={() => {
            setEditingUser(null);
            loadUsers();
          }}
        />
      )}
    </div>
  );
}

function CreateUserModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [formData, setFormData] = useState<CreateUserData>({
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
  const { showError, showSuccess, showWarning } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.password_confirm) {
      showWarning('Passwords do not match', 'Validation Error');
      return;
    }
    if (formData.password.length < 8) {
      showWarning('Password must be at least 8 characters', 'Validation Error');
      return;
    }
    try {
      setLoading(true);
      await AdminService.createUser(formData);
      showSuccess('User created successfully');
      onSuccess();
    } catch (err) {
      showError(err, 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
              <PersonAdd className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">Create New User</h3>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Close className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="First Name"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            />
            <input
              type="text"
              placeholder="Last Name"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            />
          </div>

          <input
            type="text"
            placeholder="Username *"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            required
          />

          <input
            type="email"
            placeholder="Email *"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <select
              value={formData.role}
              onChange={(e) =>
                setFormData({ ...formData, role: e.target.value as 'patient' | 'doctor' | 'admin' })
              }
              className="px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            >
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
              <option value="admin">Admin</option>
            </select>
            <select
              value={formData.preferred_language}
              onChange={(e) => setFormData({ ...formData, preferred_language: e.target.value })}
              className="px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          <input
            type="password"
            placeholder="Password *"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            required
          />

          <input
            type="password"
            placeholder="Confirm Password *"
            value={formData.password_confirm}
            onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            required
          />

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-semibold text-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors font-semibold disabled:bg-gray-400"
            >
              {loading ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditUserModal({
  user,
  onClose,
  onSuccess,
}: {
  user: User;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    email: user.email,
    role: user.role,
    preferred_language: user.preferred_language || 'en',
    is_active: user.is_active,
  });
  const [loading, setLoading] = useState(false);
  const { showError, showSuccess } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await AdminService.updateUser(user.id, formData);
      showSuccess('User updated successfully');
      onSuccess();
    } catch (err) {
      showError(err, 'Failed to update user');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
              <span className="text-sm font-semibold text-gray-600">
                {(user.first_name?.[0] || user.username[0]).toUpperCase()}
              </span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Edit User</h3>
              <p className="text-sm text-gray-500">{user.username}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Close className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="First Name"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            />
            <input
              type="text"
              placeholder="Last Name"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            />
          </div>

          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
          />

          <div className="grid grid-cols-2 gap-4">
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as any })}
              className="px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            >
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
              <option value="admin">Admin</option>
            </select>
            <select
              value={formData.preferred_language}
              onChange={(e) => setFormData({ ...formData, preferred_language: e.target.value })}
              className="px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-5 h-5 rounded border-gray-300 text-black focus:ring-black"
            />
            <span className="text-gray-900 font-medium">Active Account</span>
          </label>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-semibold text-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors font-semibold disabled:bg-gray-400"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
