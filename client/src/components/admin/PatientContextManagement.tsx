import { useState, useEffect } from 'react';
import {
  Add,
  Edit,
  Delete,
  Refresh,
  Person,
  Article,
  Close,
  Chat,
  MedicalServices,
  ExpandMore,
  ExpandLess,
  MenuBook,
} from '@mui/icons-material';
import AdminService from '../../api/services/AdminService';
import type {
  Collection,
  CollectionItem,
  CreateCollectionData,
  CreateCollectionItemData,
} from '../../types/collection';
import type { ChatRoom } from '../../types/chat';
import { useToast } from '../../contexts/ToastContext';
import { useAIConfig } from '../../hooks/useAIConfig';

export default function PatientContextManagement() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<Collection[]>([]);
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null);
  const [expandedCollection, setExpandedCollection] = useState<number | null>(null);
  const { showError, showSuccess } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [collectionsData, roomsData] = await Promise.all([
        AdminService.getCollections(),
        AdminService.getChatRooms(),
      ]);
      const patientContexts = collectionsData.filter(
        (c: Collection) => c.collection_type === 'patient_context'
      );
      const kbs = collectionsData.filter((c: Collection) => c.collection_type === 'knowledge_base');
      setCollections(patientContexts);
      setKnowledgeBases(kbs);
      setChatRooms(roomsData);
    } catch (err) {
      showError(err, 'Failed to load patient contexts');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this patient context?')) return;
    try {
      await AdminService.deleteCollection(id);
      showSuccess('Patient context deleted');
      loadData();
    } catch (err) {
      showError(err, 'Failed to delete');
    }
  };

  const getChatRoomName = (chatRoomId: number | null) => {
    if (!chatRoomId) return 'Not linked';
    const room = chatRooms.find((r) => r.id === chatRoomId);
    return room?.name || 'Unknown';
  };

  const toggleExpand = (id: number) => {
    setExpandedCollection(expandedCollection === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
            <Person className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Patient Context</h2>
            <p className="text-sm text-gray-500">
              Per-patient details for personalized translations
            </p>
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
            Add Patient
          </button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Person className="w-5 h-5 text-green-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-green-900">What is Patient Context?</h3>
            <p className="text-sm text-green-700 mt-1">
              Store individual patient details like medical history, cultural background, and
              communication preferences. Link them to chat rooms for personalized translations.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading patient contexts...</div>
        </div>
      ) : collections.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Person className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Patient Contexts Yet</h3>
          <p className="text-gray-500 mb-4">Create patient contexts to personalize translations</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            <Add className="w-4 h-4" />
            Add Patient
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {collections.map((collection) => {
            const isExpanded = expandedCollection === collection.id;
            return (
              <PatientContextCard
                key={collection.id}
                collection={collection}
                chatRoomName={collection.chat_room_name || getChatRoomName(collection.chat_room)}
                isExpanded={isExpanded}
                onToggleExpand={() => toggleExpand(collection.id)}
                onEdit={() => setEditingCollection(collection)}
                onDelete={() => handleDelete(collection.id)}
                onRefresh={loadData}
              />
            );
          })}
        </div>
      )}

      {showCreateModal && (
        <PatientContextModal
          chatRooms={chatRooms}
          knowledgeBases={knowledgeBases}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadData();
          }}
        />
      )}

      {editingCollection && (
        <PatientContextModal
          collection={editingCollection}
          chatRooms={chatRooms}
          knowledgeBases={knowledgeBases}
          onClose={() => setEditingCollection(null)}
          onSuccess={() => {
            setEditingCollection(null);
            loadData();
          }}
        />
      )}
    </div>
  );
}

function PatientContextCard({
  collection,
  chatRoomName,
  isExpanded,
  onToggleExpand,
  onEdit,
  onDelete,
  onRefresh,
}: {
  collection: Collection;
  chatRoomName: string;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onRefresh: () => void;
}) {
  const [items, setItems] = useState<CollectionItem[]>([]);
  const [loadingItems, setLoadingItems] = useState(false);
  const [showAddDetail, setShowAddDetail] = useState(false);
  const { showError, showSuccess } = useToast();

  useEffect(() => {
    if (isExpanded) {
      loadItems();
    }
  }, [isExpanded, collection.id]);

  const loadItems = async () => {
    try {
      setLoadingItems(true);
      const data = await AdminService.getCollectionItems(collection.id);
      setItems(data);
    } catch (err) {
      showError(err, 'Failed to load items');
    } finally {
      setLoadingItems(false);
    }
  };

  const handleDeleteItem = async (id: number) => {
    if (!confirm('Delete this detail?')) return;
    try {
      await AdminService.deleteCollectionItem(id);
      showSuccess('Detail deleted');
      loadItems();
      onRefresh();
    } catch (err) {
      showError(err, 'Failed to delete');
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Card Header */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Person className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">{collection.name}</h3>
              <div className="flex flex-wrap items-center gap-2 mt-1">
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">
                  Patient
                </span>
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Chat className="w-3 h-3" />
                  {chatRoomName}
                </span>
                {collection.knowledge_bases_details &&
                  collection.knowledge_bases_details.length > 0 && (
                    <span className="text-xs text-blue-600 flex items-center gap-1">
                      <MenuBook className="w-3 h-3" />
                      {collection.knowledge_bases_details.length} KB linked
                    </span>
                  )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAddDetail(true)}
              className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition-colors"
            >
              <Add className="w-4 h-4" />
              Add Detail
            </button>
            <button
              onClick={onEdit}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Edit"
            >
              <Edit className="w-4 h-4" />
            </button>
            <button
              onClick={onDelete}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete"
            >
              <Delete className="w-4 h-4" />
            </button>
            <button
              onClick={onToggleExpand}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {isExpanded ? <ExpandLess className="w-5 h-5" /> : <ExpandMore className="w-5 h-5" />}
            </button>
          </div>
        </div>
        {collection.description && (
          <p className="text-sm text-gray-500 mt-3 ml-13">{collection.description}</p>
        )}
      </div>

      {/* Expanded Details Section */}
      {isExpanded && (
        <div className="border-t border-gray-200 bg-gray-50 p-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Patient Details</h4>
          {loadingItems ? (
            <div className="text-center py-4 text-gray-500 text-sm">Loading details...</div>
          ) : items.length === 0 ? (
            <div className="text-center py-6 bg-white rounded-lg border border-dashed border-gray-300">
              <MedicalServices className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500 mb-3">No details yet</p>
              <button
                onClick={() => setShowAddDetail(true)}
                className="text-sm text-green-600 hover:text-green-700 font-medium"
              >
                + Add patient details
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="bg-white rounded-lg border border-gray-200 p-3 hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <div className="w-8 h-8 bg-green-50 rounded flex items-center justify-center flex-shrink-0">
                        <Article className="w-4 h-4 text-green-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">
                            {item.name}
                          </span>
                          {item.description && (
                            <span className="text-xs text-gray-400">{item.description}</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-700 mt-2 bg-gray-50 p-2 rounded">
                          {item.content}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteItem(item.id)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors flex-shrink-0 ml-2"
                    >
                      <Delete className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {showAddDetail && (
        <AddPatientDetailModal
          collectionId={collection.id}
          patientName={collection.name}
          onClose={() => setShowAddDetail(false)}
          onSuccess={() => {
            setShowAddDetail(false);
            loadItems();
            onRefresh();
          }}
        />
      )}
    </div>
  );
}

function PatientContextModal({
  collection,
  chatRooms,
  knowledgeBases,
  onClose,
  onSuccess,
}: {
  collection?: Collection;
  chatRooms: ChatRoom[];
  knowledgeBases: Collection[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const { config: aiConfig } = useAIConfig();
  const [formData, setFormData] = useState<CreateCollectionData>({
    name: collection?.name || '',
    description: collection?.description || '',
    collection_type: 'patient_context',
    is_global: false,
    chat_room: collection?.chat_room || undefined,
    knowledge_bases: collection?.knowledge_bases || [],
    embedding_provider: collection?.embedding_provider || aiConfig.embedding_provider,
    embedding_model: collection?.embedding_model || aiConfig.embedding_model,
    embedding_dimensions: collection?.embedding_dimensions || aiConfig.embedding_dimensions,
    completion_model: collection?.completion_model || aiConfig.completion_model,
    chunking_strategy: collection?.chunking_strategy || 'no-chunking',
    chunk_length: collection?.chunk_length || aiConfig.chunk_length,
    chunk_overlap: collection?.chunk_overlap || aiConfig.chunk_overlap,
  });
  const [loading, setLoading] = useState(false);
  const { showError, showSuccess } = useToast();

  // Update form when AI config loads
  useEffect(() => {
    if (!collection) {
      setFormData((prev) => ({
        ...prev,
        embedding_provider: aiConfig.embedding_provider,
        embedding_model: aiConfig.embedding_model,
        embedding_dimensions: aiConfig.embedding_dimensions,
        completion_model: aiConfig.completion_model,
        chunk_length: aiConfig.chunk_length,
        chunk_overlap: aiConfig.chunk_overlap,
      }));
    }
  }, [aiConfig, collection]);

  const handleKnowledgeBaseToggle = (kbId: number) => {
    const current = formData.knowledge_bases || [];
    if (current.includes(kbId)) {
      setFormData({ ...formData, knowledge_bases: current.filter((id) => id !== kbId) });
    } else {
      setFormData({ ...formData, knowledge_bases: [...current, kbId] });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      if (collection) {
        await AdminService.updateCollection(collection.id, formData);
        showSuccess('Patient updated');
      } else {
        await AdminService.createCollection(formData);
        showSuccess('Patient added');
      }
      onSuccess();
    } catch (err) {
      showError(err, 'Failed to save');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
              <Person className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">
              {collection ? 'Edit Patient' : 'Add Patient'}
            </h3>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Close className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Patient Name / ID *
            </label>
            <input
              type="text"
              placeholder="e.g., John Doe, Patient #12345"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Link to Chat Room
            </label>
            <select
              value={formData.chat_room || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  chat_room: e.target.value ? Number(e.target.value) : undefined,
                })
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            >
              <option value="">Select a chat room (optional)</option>
              {chatRooms.map((room) => (
                <option key={room.id} value={room.id}>
                  {room.name} ({room.patient_language} ↔ {room.doctor_language})
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Link to a chat room for personalized translations in that conversation
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Completion Model</label>
            <input
              type="text"
              placeholder="e.g., granite3.3:8b"
              value={formData.completion_model || 'granite3.3:8b'}
              onChange={(e) => setFormData({ ...formData, completion_model: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            />
            <p className="text-xs text-gray-500 mt-1">
              Model used to generate answers from this context (default: granite3.3:8b)
            </p>
          </div>

          {/* Knowledge Base Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <span className="flex items-center gap-2">
                <MenuBook className="w-4 h-4 text-blue-600" />
                Link Knowledge Bases
              </span>
            </label>
            {knowledgeBases.length === 0 ? (
              <p className="text-sm text-gray-500 bg-gray-50 p-3 rounded-lg">
                No knowledge bases available. Create one first in the Knowledge Base section.
              </p>
            ) : (
              <div className="border border-gray-200 rounded-lg max-h-40 overflow-y-auto">
                {knowledgeBases.map((kb) => (
                  <label
                    key={kb.id}
                    className="flex items-center gap-3 p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                  >
                    <input
                      type="checkbox"
                      checked={(formData.knowledge_bases || []).includes(kb.id)}
                      onChange={() => handleKnowledgeBaseToggle(kb.id)}
                      className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{kb.name}</p>
                      {kb.description && (
                        <p className="text-xs text-gray-500 truncate">{kb.description}</p>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">{kb.items_count || 0} docs</span>
                  </label>
                ))}
              </div>
            )}
            <p className="text-xs text-gray-500 mt-1">
              Selected knowledge bases will be used for this patient's translations
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Notes (optional)</label>
            <textarea
              placeholder="Brief notes about this patient"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              rows={3}
            />
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
              {loading ? 'Saving...' : collection ? 'Save Changes' : 'Add Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AddPatientDetailModal({
  collectionId,
  patientName,
  onClose,
  onSuccess,
}: {
  collectionId: number;
  patientName: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<CreateCollectionItemData>({
    collection: collectionId,
    name: '',
    description: '',
    content: '',
  });
  const [loading, setLoading] = useState(false);
  const { showError, showSuccess } = useToast();

  const detailTypes = [
    {
      value: 'Medical History',
      label: 'Medical History',
      placeholder: 'Previous conditions, surgeries, ongoing treatments...',
    },
    {
      value: 'Cultural Background',
      label: 'Cultural Background',
      placeholder: 'Cultural practices, beliefs, dietary restrictions...',
    },
    {
      value: 'Communication Preferences',
      label: 'Communication Preferences',
      placeholder: 'Preferred communication style, formality level...',
    },
    { value: 'Allergies', label: 'Allergies', placeholder: 'Known allergies and reactions...' },
    {
      value: 'Language Notes',
      label: 'Language Notes',
      placeholder: 'Dialect preferences, terminology to use/avoid...',
    },
    {
      value: 'Family Context',
      label: 'Family Context',
      placeholder: 'Family members involved in care, decision makers...',
    },
    { value: 'Other', label: 'Other', placeholder: 'Any other relevant information...' },
  ];

  const selectedType = detailTypes.find((t) => t.value === formData.name);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await AdminService.createCollectionItem(formData);
      showSuccess('Detail added');
      onSuccess();
    } catch (err) {
      showError(err, 'Failed to add detail');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
              <MedicalServices className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Add Patient Detail</h3>
              <p className="text-xs text-gray-500">for {patientName}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Close className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Detail Type *</label>
            <select
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              required
            >
              <option value="">Select type</option>
              {detailTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Label (optional)</label>
            <input
              type="text"
              placeholder="e.g., Primary condition, Preferred dialect"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Details *</label>
            <textarea
              placeholder={selectedType?.placeholder || 'Enter the patient details here...'}
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              rows={6}
              required
            />
            <p className="text-xs text-gray-400 mt-1">
              This information will be used to personalize translations for this patient
            </p>
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
              disabled={loading || !formData.content.trim() || !formData.name}
              className="flex-1 px-4 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors font-semibold disabled:bg-gray-400"
            >
              {loading ? 'Adding...' : 'Add Detail'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
