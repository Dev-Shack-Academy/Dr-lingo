import { useState, useEffect } from 'react';
import ChatService, { ChatRoom } from '../api/services/ChatService';
import AddPatientContext from './AddPatientContext';
import { Description, MenuBook, Person, ExpandMore, ExpandLess } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { SUPPORTED_LANGUAGES } from '../types/common';
import { RoleSelectionDialog } from './chat';

interface ChatRoomListProps {
  onSelectRoom: (roomId: number, userType: 'patient' | 'doctor') => void;
}

function ChatRoomList({ onSelectRoom }: ChatRoomListProps) {
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showContextDialog, setShowContextDialog] = useState<{
    roomId: number;
    roomName: string;
    collection?: number;
  } | null>(null);
  const [roleDialog, setRoleDialog] = useState<{
    roomId: number;
    roomName: string;
  } | null>(null);
  const [newRoom, setNewRoom] = useState({
    name: '',
    patient_language: 'en',
    doctor_language: 'es',
  });
  const [expandedRooms, setExpandedRooms] = useState<Set<number>>(new Set());
  const { user } = useAuth();

  const canViewContext = user?.role === 'doctor' || user?.role === 'admin' || user?.is_superuser;
  const { showError, showSuccess } = useToast();

  const languages = SUPPORTED_LANGUAGES;

  const toggleRoomExpanded = (roomId: number) => {
    setExpandedRooms((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(roomId)) {
        newSet.delete(roomId);
      } else {
        newSet.add(roomId);
      }
      return newSet;
    });
  };

  useEffect(() => {
    loadRooms();
  }, []);

  const loadRooms = async () => {
    try {
      setLoading(true);
      const data = await ChatService.getChatRooms();
      setRooms(data);
    } catch (err) {
      showError(err, 'Failed to load chat rooms');
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
      setShowCreateDialog(false);
      showSuccess('Chat room created successfully');
      await loadRooms();
    } catch (err) {
      showError(err, 'Failed to create chat room');
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading chat rooms...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Translation Chat Rooms</h2>
        <button
          onClick={() => setShowCreateDialog(true)}
          className="bg-black hover:bg-gray-800 text-white font-semibold px-6 py-2 rounded-lg transition-colors"
        >
          New Room
        </button>
      </div>

      {/* Create Room Dialog */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900">Create New Chat Room</h3>
                <button
                  onClick={() => setShowCreateDialog(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              <form onSubmit={handleCreateRoom} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold mb-2 text-gray-700">
                    Room Name
                  </label>
                  <input
                    type="text"
                    value={newRoom.name}
                    onChange={(e) => setNewRoom({ ...newRoom, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black placeholder:text-gray-400"
                    placeholder="e.g., Emergency Consultation"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2 text-gray-700">
                      Patient Language
                    </label>
                    <select
                      value={newRoom.patient_language}
                      onChange={(e) => setNewRoom({ ...newRoom, patient_language: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                    >
                      {languages.map((lang) => (
                        <option key={lang.code} value={lang.code}>
                          {lang.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2 text-gray-700">
                      Doctor Language
                    </label>
                    <select
                      value={newRoom.doctor_language}
                      onChange={(e) => setNewRoom({ ...newRoom, doctor_language: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                    >
                      {languages.map((lang) => (
                        <option key={lang.code} value={lang.code}>
                          {lang.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateDialog(false)}
                    className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-3 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 bg-black hover:bg-gray-800 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
                  >
                    Create Room
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-4">
        {rooms.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-gray-500">No chat rooms yet. Create one to get started.</p>
          </div>
        ) : (
          rooms.map((room) => (
            <div
              key={room.id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-400 transition-colors shadow-sm"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900">{room.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Patient: {languages.find((l) => l.code === room.patient_language)?.name} •
                    Doctor: {languages.find((l) => l.code === room.doctor_language)?.name}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{room.message_count || 0} messages</p>

                  {/* RAG Status */}
                  {room.has_rag ? (
                    <div className="mt-2 flex items-center gap-2 flex-wrap">
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-semibold">
                        <Description className="w-3 h-3" />
                        RAG: {room.rag_collection_name}
                      </span>
                      {room.patient_name && (
                        <span className="text-xs text-gray-600">Patient: {room.patient_name}</span>
                      )}
                      {/* Show expand button for doctors/admins if there's context data */}
                      {canViewContext &&
                        (room.patient_context?.length || room.linked_knowledge_bases?.length) && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleRoomExpanded(room.id);
                            }}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded text-xs font-semibold transition-colors"
                          >
                            {expandedRooms.has(room.id) ? (
                              <>
                                <ExpandLess className="w-3 h-3" />
                                Hide Details
                              </>
                            ) : (
                              <>
                                <ExpandMore className="w-3 h-3" />
                                View Details
                              </>
                            )}
                          </button>
                        )}
                    </div>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowContextDialog({
                          roomId: room.id,
                          roomName: room.name,
                          collection: room.rag_collection ?? undefined,
                        });
                      }}
                      className="mt-2 inline-flex items-center gap-1 px-3 py-1 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded text-xs font-semibold transition-colors"
                    >
                      <Description className="w-3 h-3" />
                      Add Context
                    </button>
                  )}

                  {/* Expanded Patient Context & Knowledge Bases (for doctors/admins) */}
                  {canViewContext && expandedRooms.has(room.id) && (
                    <div className="mt-3 space-y-3">
                      {/* Patient Context Documents */}
                      {room.patient_context && room.patient_context.length > 0 && (
                        <div className="bg-purple-50 rounded-lg p-3">
                          <h4 className="text-sm font-semibold text-purple-800 flex items-center gap-1 mb-2">
                            <Person className="w-4 h-4" />
                            Patient Context
                          </h4>
                          {room.patient_context.map((context) => (
                            <div key={context.id} className="mb-2">
                              <p className="text-xs font-medium text-purple-700">{context.name}</p>
                              {context.description && (
                                <p className="text-xs text-purple-600 mb-1">
                                  {context.description}
                                </p>
                              )}
                              {context.items.length > 0 && (
                                <div className="space-y-1 mt-1">
                                  {context.items.map((item) => (
                                    <div
                                      key={item.id}
                                      className="bg-white rounded p-2 border border-purple-200"
                                    >
                                      <p className="text-xs font-medium text-gray-700">
                                        {item.name}
                                      </p>
                                      <p className="text-xs text-gray-600 mt-1">{item.content}</p>
                                      {item.metadata && (
                                        <p className="text-xs text-gray-400 mt-1">
                                          Type:{' '}
                                          {(item.metadata as { type?: string })?.type || 'N/A'}
                                        </p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Linked Knowledge Bases */}
                      {room.linked_knowledge_bases && room.linked_knowledge_bases.length > 0 && (
                        <div className="bg-blue-50 rounded-lg p-3">
                          <h4 className="text-sm font-semibold text-blue-800 flex items-center gap-1 mb-2">
                            <MenuBook className="w-4 h-4" />
                            Linked Knowledge Bases
                          </h4>
                          <div className="space-y-2">
                            {room.linked_knowledge_bases.map((kb) => (
                              <div
                                key={kb.id}
                                className="bg-white rounded p-2 border border-blue-200"
                              >
                                <p className="text-xs font-medium text-gray-700">{kb.name}</p>
                                {kb.description && (
                                  <p className="text-xs text-gray-600 mt-1">{kb.description}</p>
                                )}
                                <p className="text-xs text-blue-600 mt-1">
                                  {kb.items_count} document{kb.items_count !== 1 ? 's' : ''}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* No context message */}
                      {(!room.patient_context || room.patient_context.length === 0) &&
                        (!room.linked_knowledge_bases ||
                          room.linked_knowledge_bases.length === 0) && (
                          <p className="text-xs text-gray-500 italic">
                            No patient context or knowledge bases linked yet.
                          </p>
                        )}
                    </div>
                  )}
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
                {/* Patients can only join as patient */}
                {user?.role === 'patient' && (
                  <button
                    onClick={() => onSelectRoom(room.id, 'patient')}
                    className="flex-1 bg-gray-900 hover:bg-gray-800 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
                  >
                    Join Chat
                  </button>
                )}

                {/* Doctors can only join as doctor */}
                {user?.role === 'doctor' && (
                  <button
                    onClick={() => onSelectRoom(room.id, 'doctor')}
                    className="flex-1 bg-gray-900 hover:bg-gray-800 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
                  >
                    Join Chat
                  </button>
                )}

                {/* Admins can join as either role (for testing) */}
                {(user?.role === 'admin' || user?.is_superuser) && (
                  <button
                    onClick={() => setRoleDialog({ roomId: room.id, roomName: room.name })}
                    className="flex-1 bg-gray-900 hover:bg-gray-800 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
                  >
                    Join Chat
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add Patient Context Dialog */}
      {showContextDialog && (
        <AddPatientContext
          roomId={showContextDialog.roomId}
          roomName={showContextDialog.roomName}
          currentCollection={showContextDialog.collection}
          onClose={() => setShowContextDialog(null)}
          onSuccess={loadRooms}
        />
      )}

      {/* Role Selection Dialog (for admins) */}
      <RoleSelectionDialog
        open={!!roleDialog}
        onClose={() => setRoleDialog(null)}
        onSelectRole={(role) => {
          if (roleDialog) {
            onSelectRoom(roleDialog.roomId, role);
            setRoleDialog(null);
          }
        }}
        roomName={roleDialog?.roomName || ''}
        isAdmin={true}
      />
    </div>
  );
}

export default ChatRoomList;
