import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
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
  Terminal,
} from '@mui/icons-material';
import AdminDashboard from '../components/admin/AdminDashboard';
import UserManagement from '../components/admin/UserManagement';
import ChatRoomManagement from '../components/admin/ChatRoomManagement';
import KnowledgeBaseManagement from '../components/admin/KnowledgeBaseManagement';
import PatientContextManagement from '../components/admin/PatientContextManagement';
import TaskMonitor from '../components/admin/TaskMonitor';

type AdminTab =
  | 'dashboard'
  | 'users'
  | 'chatrooms'
  | 'knowledge-base'
  | 'patient-context'
  | 'task-monitor'
  | 'settings';

export default function AdminPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<AdminTab>('dashboard');

  useEffect(() => {
    const tabParam = searchParams.get('tab') as AdminTab;
    if (tabParam && tabs.some((t) => t.id === tabParam)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  const handleTabChange = (tabId: AdminTab) => {
    setActiveTab(tabId);
    setSearchParams({ tab: tabId });
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Dashboard },
    { id: 'users', label: 'Users', icon: People },
    { id: 'chatrooms', label: 'Chat Rooms', icon: Chat },
    { id: 'knowledge-base', label: 'Knowledge Base', icon: MenuBook },
    { id: 'patient-context', label: 'Patient Context', icon: Person },
    { id: 'task-monitor', label: 'Task Monitor', icon: Terminal },
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
      case 'task-monitor':
        return <TaskMonitor />;
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
                onClick={() => handleTabChange(tab.id as AdminTab)}
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
