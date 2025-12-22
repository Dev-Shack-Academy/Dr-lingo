import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  Dashboard,
  People,
  Chat,
  Settings,
  ArrowBack,
  AdminPanelSettings,
  MenuBook,
  Person,
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import AdminDashboard from '../components/admin/AdminDashboard';
import UserManagement from '../components/admin/UserManagement';
import ChatRoomManagement from '../components/admin/ChatRoomManagement';
import KnowledgeBaseManagement from '../components/admin/KnowledgeBaseManagement';
import PatientContextManagement from '../components/admin/PatientContextManagement';

type AdminTab =
  | 'dashboard'
  | 'users'
  | 'chatrooms'
  | 'knowledge-base'
  | 'patient-context'
  | 'settings';

export default function AdminPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<AdminTab>('dashboard');

  // Check if user is admin
  if (user?.role !== 'admin' && !user?.is_superuser) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md text-center border border-gray-200">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AdminPanelSettings className="w-8 h-8 text-gray-400" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-6">You don't have permission to access the admin panel.</p>
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

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Dashboard },
    { id: 'users', label: 'Users', icon: People },
    { id: 'chatrooms', label: 'Chat Rooms', icon: Chat },
    { id: 'knowledge-base', label: 'Knowledge Base', icon: MenuBook },
    { id: 'patient-context', label: 'Patient Context', icon: Person },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <AdminDashboard />;
      case 'users':
        return <UserManagement />;
      case 'chatrooms':
        return <ChatRoomManagement />;
      case 'knowledge-base':
        return <KnowledgeBaseManagement />;
      case 'patient-context':
        return <PatientContextManagement />;
      case 'settings':
        return (
          <div className="bg-white rounded-xl border border-gray-200 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                <Settings className="w-5 h-5 text-gray-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
            </div>
            <p className="text-gray-500">System settings coming soon...</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-black text-white px-6 py-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="p-2 rounded-lg hover:bg-white/10 transition-colors">
              <ArrowBack className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                <AdminPanelSettings className="w-5 h-5 text-black" />
              </div>
              <h1 className="text-xl font-bold">Admin Panel</h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-sm">
              <span className="text-gray-400">Logged in as </span>
              <span className="font-semibold">{user?.username}</span>
            </div>
            <span className="px-2 py-1 bg-white/10 rounded text-xs font-medium uppercase">
              {user?.role}
            </span>
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-56 flex-shrink-0 bg-white border-r border-gray-200 p-4">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as AdminTab)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm ${
                  activeTab === tab.id
                    ? 'bg-black text-white shadow-md'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                <span className="font-medium">{tab.label}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6 bg-gray-50 overflow-auto">{renderContent()}</main>
      </div>
    </div>
  );
}
