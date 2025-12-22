import { useState, useEffect } from 'react';
import { Add, Edit, Delete, Refresh, Chat, Close, Translate } from '@mui/icons-material';
import AdminService, {
  ChatRoom,
  CreateChatRoomData,
  Collection,
} from '../../api/services/AdminService';
import { useToast } from '../../contexts/ToastContext';

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'afr', name: 'Afrikaans' },
  { code: 'ja', name: 'Japanese' },
  { code: 'zulu', name: 'Zulu' },
  { code: 'tsawana', name: 'Tswana' },
  { code: 'xhosa', name: 'Xhosa' },
  { code: 'chichewe', name: 'Chichewe' },
];

export default function ChatRoomManagement() {
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRoom, setEditingRoom] = useState<ChatRoom | null>(null);
  const { showError, showSuccess } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [roomsData, collectionsData] = await Promise.all([
        AdminService.getChatRooms(),
        AdminService.getCollections(),
      ]);
      setRooms(roomsData);
      setCollections(collectionsData);
    } catch (err) {
      showError(err, 'Failed to load chat rooms');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this chat room?')) return;
    try {
      await AdminService.deleteChatRoom(id);
      showSuccess('Chat room deleted');
      loadData();
    } catch (err) {
      showError(err, 'Failed to delete chat room');
    }
  };

  const getLanguageName = (code: string) => {
    return LANGUAGES.find((l) => l.code === code)?.name || code.toUpperCase();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
            <Chat className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Chat Room Management</h2>
            <p className="text-sm text-gray-500">{rooms.length} rooms total</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadData}
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
            Create Room
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading chat rooms...</div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Room
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Languages
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Patient
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Collection
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
              {rooms.map((room) => (
                <tr key={room.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                        <Chat className="w-5 h-5 text-gray-500" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">{room.name}</p>
                        <p className="text-xs text-gray-500">ID: {room.id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium text-gray-700">
                        {getLanguageName(room.patient_language)}
                      </span>
                      <Translate className="w-4 h-4 text-gray-400" />
                      <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium text-gray-700">
                        {getLanguageName(room.doctor_language)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{room.patient_name || '—'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {room.rag_collection
                      ? collections.find((c) => c.id === room.rag_collection)?.name || 'Unknown'
                      : '—'}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-3 py-1 text-xs font-semibold rounded-full ${
                        room.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {room.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => setEditingRoom(room)}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(room.id)}
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
        <ChatRoomModal
          collections={collections}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadData();
          }}
        />
      )}

      {editingRoom && (
        <ChatRoomModal
          room={editingRoom}
          collections={collections}
          onClose={() => setEditingRoom(null)}
          onSuccess={() => {
            setEditingRoom(null);
            loadData();
          }}
        />
      )}
    </div>
  );
}

function ChatRoomModal({
  room,
  collections,
  onClose,
  onSuccess,
}: {
  room?: ChatRoom;
  collections: Collection[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<CreateChatRoomData>({
    name: room?.name || '',
    patient_language: room?.patient_language || 'es',
    doctor_language: room?.doctor_language || 'en',
    patient_name: room?.patient_name || '',
    rag_collection: room?.rag_collection || undefined,
  });
  const [loading, setLoading] = useState(false);
  const { showError, showSuccess } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      if (room) {
        await AdminService.updateChatRoom(room.id, formData);
        showSuccess('Chat room updated');
      } else {
        await AdminService.createChatRoom(formData);
        showSuccess('Chat room created');
      }
      onSuccess();
    } catch (err) {
      showError(err, 'Failed to save chat room');
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
              <Chat className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">
              {room ? 'Edit Chat Room' : 'Create Chat Room'}
            </h3>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Close className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Room Name *</label>
            <input
              type="text"
              placeholder="e.g., Emergency Consultation"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Patient Language
              </label>
              <select
                value={formData.patient_language}
                onChange={(e) => setFormData({ ...formData, patient_language: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Doctor Language
              </label>
              <select
                value={formData.doctor_language}
                onChange={(e) => setFormData({ ...formData, doctor_language: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Patient Name</label>
            <input
              type="text"
              placeholder="Optional"
              value={formData.patient_name}
              onChange={(e) => setFormData({ ...formData, patient_name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              RAG Collection (Optional)
            </label>
            <select
              value={formData.rag_collection || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  rag_collection: e.target.value ? Number(e.target.value) : undefined,
                })
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            >
              <option value="">No Collection</option>
              {collections.map((col) => (
                <option key={col.id} value={col.id}>
                  {col.name}
                </option>
              ))}
            </select>
          </div>

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
              {loading ? 'Saving...' : room ? 'Save Changes' : 'Create Room'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
