import { useState, useEffect } from 'react';
import { People, Chat, LocalHospital, Person, TrendingUp, MenuBook } from '@mui/icons-material';
import AdminService from '../../api/services/AdminService';
import type { Collection } from '../../types/collection';
import { useToast } from '../../contexts/ToastContext';

interface Stats {
  users: number;
  doctors: number;
  patients: number;
  chatRooms: number;
  knowledgeBase: number;
  patientContexts: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const { showError } = useToast();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [users, chatRooms, collections] = await Promise.all([
        AdminService.getUsers(),
        AdminService.getChatRooms(),
        AdminService.getCollections(),
      ]);

      const knowledgeBase = collections.filter(
        (c: Collection) => c.collection_type === 'knowledge_base'
      ).length;
      const patientContexts = collections.filter(
        (c: Collection) => c.collection_type === 'patient_context'
      ).length;

      setStats({
        users: users.length,
        doctors: users.filter((u) => u.role === 'doctor').length,
        patients: users.filter((u) => u.role === 'patient').length,
        chatRooms: chatRooms.length,
        knowledgeBase,
        patientContexts,
      });
    } catch (err) {
      showError(err, 'Failed to load dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      label: 'Total Users',
      value: stats?.users || 0,
      icon: People,
      color: 'bg-black',
    },
    {
      label: 'Doctors',
      value: stats?.doctors || 0,
      icon: LocalHospital,
      color: 'bg-gray-800',
    },
    {
      label: 'Patients',
      value: stats?.patients || 0,
      icon: Person,
      color: 'bg-gray-700',
    },
    {
      label: 'Chat Rooms',
      value: stats?.chatRooms || 0,
      icon: Chat,
      color: 'bg-gray-600',
    },
    {
      label: 'Knowledge Base',
      value: stats?.knowledgeBase || 0,
      icon: MenuBook,
      color: 'bg-blue-600',
    },
    {
      label: 'Patient Contexts',
      value: stats?.patientContexts || 0,
      icon: Person,
      color: 'bg-green-600',
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
          <TrendingUp className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-sm text-gray-500">System overview and statistics</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((stat) => (
          <div
            key={stat.label}
            className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow"
          >
            <div
              className={`w-10 h-10 ${stat.color} rounded-lg flex items-center justify-center mb-3`}
            >
              <stat.icon className="w-5 h-5 text-white" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-all text-left">
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <People className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">Add User</p>
              <p className="text-sm text-gray-500">Create a new user account</p>
            </div>
          </button>
          <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-all text-left">
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
              <Chat className="w-5 h-5 text-gray-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">Create Room</p>
              <p className="text-sm text-gray-500">Start a new chat room</p>
            </div>
          </button>
          <button className="flex items-center gap-3 p-4 border border-blue-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-all text-left">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <MenuBook className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">Knowledge Base</p>
              <p className="text-sm text-gray-500">Add global reference data</p>
            </div>
          </button>
          <button className="flex items-center gap-3 p-4 border border-green-200 rounded-lg hover:bg-green-50 hover:border-green-300 transition-all text-left">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Person className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">Patient Context</p>
              <p className="text-sm text-gray-500">Add patient details</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
