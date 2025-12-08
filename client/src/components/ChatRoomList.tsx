import { useState, useEffect } from 'react';
import ChatService, { ChatRoom } from '../api/services/ChatService';

interface ChatRoomListProps {
  onSelectRoom: (roomId: number, userType: 'patient' | 'doctor') => void;
}

function ChatRoomList({ onSelectRoom }: ChatRoomListProps) {
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newRoom, setNewRoom] = useState({
    name: '',
    patient_language: 'en',
    doctor_language: 'es',
  });

  useEffect(() => {
    loadRooms();
  }, []);

  const loadRooms = async () => {
    try {
      setLoading(true);
      const data = await ChatService.getChatRooms();
      setRooms(data);
    } catch (err) {
      console.error('Failed to load rooms:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await ChatService.createChatRoom({
        ...newRoom,
        room_type: 'patient_doctor',
        is_active: true,
      });

      setNewRoom({ name: '', patient_language: 'en', doctor_language: 'es' });
      setShowCreateForm(false);
      await loadRooms();
    } catch (err) {
      console.error('Failed to create room:', err);
    }
  };

  const languages = [
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
  ];

  if (loading) {
    return <div className="text-center py-8">Loading chat rooms...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Translation Chat Rooms</h2>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2 rounded-lg transition-colors"
        >
          {showCreateForm ? 'Cancel' : '+ New Room'}
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
          <h3 className="text-xl font-bold mb-4">Create New Chat Room</h3>
          <form onSubmit={handleCreateRoom} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold mb-2">Room Name</label>
              <input
                type="text"
                value={newRoom.name}
                onChange={(e) => setNewRoom({ ...newRoom, name: e.target.value })}
                className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                placeholder="e.g., Emergency Consultation"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold mb-2">Patient Language</label>
                <select
                  value={newRoom.patient_language}
                  onChange={(e) => setNewRoom({ ...newRoom, patient_language: e.target.value })}
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                >
                  {languages.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Doctor Language</label>
                <select
                  value={newRoom.doctor_language}
                  onChange={(e) => setNewRoom({ ...newRoom, doctor_language: e.target.value })}
                  className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
                >
                  {languages.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
            >
              Create Room
            </button>
          </form>
        </div>
      )}

      <div className="grid gap-4">
        {rooms.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-xl border-2 border-gray-200">
            <p className="text-gray-500">No chat rooms yet. Create one to get started!</p>
          </div>
        ) : (
          rooms.map((room) => (
            <div
              key={room.id}
              className="bg-white border-2 border-gray-200 rounded-xl p-6 hover:border-blue-400 transition-colors"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-800">{room.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    🏥 Patient: {languages.find((l) => l.code === room.patient_language)?.name} • 👨‍⚕️
                    Doctor: {languages.find((l) => l.code === room.doctor_language)?.name}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{room.message_count || 0} messages</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    room.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {room.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              {room.last_message && (
                <div className="bg-gray-50 rounded-lg p-3 mb-4">
                  <p className="text-sm text-gray-700">
                    <span className="font-semibold">{room.last_message.sender}:</span>{' '}
                    {room.last_message.text}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(room.last_message.created_at).toLocaleString()}
                  </p>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => onSelectRoom(room.id, 'patient')}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
                >
                  Join as Patient
                </button>
                <button
                  onClick={() => onSelectRoom(room.id, 'doctor')}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
                >
                  Join as Doctor
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default ChatRoomList;
