import React, { useState, useEffect } from 'react';
import {
  Psychology,
  Person,
  Description,
  LocalHospital,
  Language,
  Add,
  InfoOutlined,
  CheckCircleOutline,
  CancelOutlined,
  Edit,
} from '@mui/icons-material';
import ChatService from '../api/services/ChatService';
import RAGService, { Collection } from '../api/services/RAGService';

interface PatientContextManagerProps {
  roomId: number;
  roomName: string;
  currentCollection?: number;
  onUpdate?: () => void;
}

const PatientContextManager: React.FC<PatientContextManagerProps> = ({
  roomId,
  roomName,
  currentCollection,
  onUpdate,
}) => {
  const [roomData, setRoomData] = useState<any>(null);
  const [collectionData, setCollectionData] = useState<any>(null);
  const [contextItems, setContextItems] = useState<any[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<number | null>(
    currentCollection || null
  );
  const [step, setStep] = useState<'select' | 'form'>(currentCollection ? 'form' : 'select');
  const [createNewCollection, setCreateNewCollection] = useState(false);
  const [formData, setFormData] = useState({
    patient_name: '',
    cultural_background: '',
    medical_history: '',
    language_notes: '',
  });
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    loadRoomData();
    loadCollections();
  }, [roomId]);

  const loadRoomData = async () => {
    setLoading(true);
    try {
      const room = await ChatService.getChatRoom(roomId);
      setRoomData(room);

      if (room.rag_collection) {
        const collection = await RAGService.getCollection(room.rag_collection);
        setCollectionData(collection);

        const items = await RAGService.getCollectionItems(room.rag_collection);
        setContextItems(items);
      }
    } catch (error) {
      console.error('Error loading RAG data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCollections = async () => {
    try {
      const data = await RAGService.getCollections();
      setCollections(data);
    } catch (error) {
      console.error('Error loading collections:', error);
    }
  };

  const handleOpenDialog = () => {
    setShowDialog(true);
    setStep(currentCollection ? 'form' : 'select');
  };

  const handleCloseDialog = () => {
    setShowDialog(false);
    setStatus(null);
    setFormData({
      patient_name: '',
      cultural_background: '',
      medical_history: '',
      language_notes: '',
    });
  };

  const handleLinkCollectionOnly = async () => {
    if (!selectedCollection) return;

    setLoading(true);
    setStatus(null);

    try {
      await ChatService.addPatientContext(roomId, {
        collection_id: selectedCollection,
        patient_name: 'Existing Context',
        cultural_background: 'Using existing collection context',
        medical_history: 'See collection documents',
        language_notes: 'See collection documents',
      } as any);

      setStatus({ type: 'success', message: 'Collection linked successfully!' });
      setTimeout(() => {
        loadRoomData();
        onUpdate?.();
        handleCloseDialog();
      }, 1000);
    } catch (error: any) {
      setStatus({ type: 'error', message: error.message || 'Failed to link collection' });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setLoading(true);
    setStatus(null);

    try {
      let collectionId = selectedCollection;

      if (createNewCollection) {
        setStatus({ type: 'success', message: 'Creating collection...' });
        const timestamp = new Date().toISOString().slice(0, 19).replace('T', ' ');
        const newCollection = await RAGService.createCollection({
          name: `${roomName} - Patient Context - ${timestamp}`,
          description: `Medical and cultural context for ${roomName}`,
          embedding_provider: 'gemini',
          embedding_model: 'text-embedding-004',
          embedding_dimensions: 768,
          completion_model: 'gemini-2.0-flash-exp',
          chunking_strategy: 'fixed-length',
          chunk_length: 1000,
          chunk_overlap: 200,
        });
        collectionId = newCollection.id;
        setStatus({ type: 'success', message: 'Collection created! Adding patient context...' });
      }

      if (!collectionId) {
        setStatus({ type: 'error', message: 'Please select a RAG collection first' });
        setLoading(false);
        return;
      }

      await ChatService.addPatientContext(roomId, {
        ...formData,
        collection_id: collectionId,
      } as any);

      setStatus({ type: 'success', message: 'Patient context added successfully!' });
      setTimeout(() => {
        loadRoomData();
        onUpdate?.();
        handleCloseDialog();
      }, 1500);
    } catch (error: any) {
      setStatus({ type: 'error', message: error.message || 'Failed to add patient context' });
    } finally {
      setLoading(false);
    }
  };

  // Extract patient context details
  const getPatientDetails = () => {
    if (contextItems.length === 0) return null;

    const patientProfile =
      contextItems.find(
        (item) =>
          item.content &&
          !item.content.includes('Using existing collection context') &&
          item.content.includes('PATIENT PROFILE')
      ) || contextItems[0];

    const content = patientProfile.content || '';
    const extractSection = (sectionName: string) => {
      const regex = new RegExp(`${sectionName}:\\s*([\\s\\S]*?)(?=\\n[A-Z\\s&]+:|$)`, 'i');
      const match = content.match(regex);
      return match ? match[1].trim() : '';
    };

    return {
      cultural: extractSection('CULTURAL BACKGROUND'),
      medical: extractSection('MEDICAL HISTORY'),
      language: extractSection('LANGUAGE & COMMUNICATION NOTES'),
    };
  };

  const details = getPatientDetails();

  return (
    <>
      {/* Display Panel */}
      <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Psychology className="w-5 h-5 text-purple-600" />
            <h3 className="text-base font-bold text-purple-900">Patient Context</h3>
          </div>
          <button
            onClick={handleOpenDialog}
            className="text-purple-600 hover:text-purple-700 p-1 rounded hover:bg-purple-200 transition-colors"
            title={roomData?.rag_collection ? 'Edit context' : 'Add context'}
          >
            {roomData?.rag_collection ? <Edit className="w-4 h-4" /> : <Add className="w-4 h-4" />}
          </button>
        </div>

        {loading && !roomData ? (
          <p className="text-purple-700 text-xs">Loading...</p>
        ) : !roomData?.rag_collection ? (
          <div className="space-y-2">
            <p className="text-purple-800 text-xs">
              No RAG context configured. Add patient context for culturally-aware translations.
            </p>
            <button
              onClick={handleOpenDialog}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold px-3 py-2 rounded-lg transition-colors text-xs"
            >
              Add Patient Context
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Patient Name */}
            {roomData.patient_name && (
              <div className="bg-white rounded-lg p-2 border border-purple-200">
                <div className="flex items-center gap-2 mb-1">
                  <Person className="w-3 h-3 text-purple-600" />
                  <span className="text-xs font-semibold text-purple-900">Patient</span>
                </div>
                <p className="text-xs font-medium text-gray-900">{roomData.patient_name}</p>
              </div>
            )}

            {/* Collection */}
            {collectionData && (
              <div className="bg-white rounded-lg p-2 border border-purple-200">
                <div className="flex items-center gap-2 mb-1">
                  <Description className="w-3 h-3 text-purple-600" />
                  <span className="text-xs font-semibold text-purple-900">Collection</span>
                </div>
                <p className="text-xs text-gray-700">{collectionData.name}</p>
              </div>
            )}

            {/* Context Details */}
            {details && (
              <>
                {details.cultural && details.cultural !== 'Using existing collection context' && (
                  <div className="bg-white rounded-lg p-2 border border-purple-200">
                    <div className="flex items-center gap-2 mb-1">
                      <Person className="w-3 h-3 text-purple-600" />
                      <span className="text-xs font-semibold text-purple-900">Cultural</span>
                    </div>
                    <p className="text-xs text-gray-700 leading-relaxed line-clamp-2">
                      {details.cultural}
                    </p>
                  </div>
                )}

                {details.medical && details.medical !== 'See collection documents' && (
                  <div className="bg-white rounded-lg p-2 border border-purple-200">
                    <div className="flex items-center gap-2 mb-1">
                      <LocalHospital className="w-3 h-3 text-purple-600" />
                      <span className="text-xs font-semibold text-purple-900">Medical</span>
                    </div>
                    <p className="text-xs text-gray-700 leading-relaxed line-clamp-2">
                      {details.medical}
                    </p>
                  </div>
                )}

                {details.language && details.language !== 'See collection documents' && (
                  <div className="bg-white rounded-lg p-2 border border-purple-200">
                    <div className="flex items-center gap-2 mb-1">
                      <Language className="w-3 h-3 text-purple-600" />
                      <span className="text-xs font-semibold text-purple-900">Language</span>
                    </div>
                    <p className="text-xs text-gray-700 leading-relaxed line-clamp-2">
                      {details.language}
                    </p>
                  </div>
                )}
              </>
            )}

            {/* Status */}
            <div className="pt-2 border-t border-purple-300">
              <p className="text-xs text-purple-700 flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                RAG Active
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Dialog */}
      {showDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Patient Context</h3>
                  <p className="text-sm text-gray-600">{roomName}</p>
                </div>
                <button
                  onClick={handleCloseDialog}
                  className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              {step === 'select' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2 text-gray-900">
                      Select Collection
                    </label>
                    <select
                      value={selectedCollection || ''}
                      onChange={(e) => setSelectedCollection(Number(e.target.value))}
                      className="w-full px-4 py-2 border rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                    >
                      <option value="">Choose...</option>
                      {collections.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name} ({c.items_count} docs)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-2 bg-white text-gray-500">OR</span>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setCreateNewCollection(true);
                      setStep('form');
                    }}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold px-4 py-2 rounded-lg"
                  >
                    Create New Collection
                  </button>

                  <div className="flex gap-3 pt-4">
                    {selectedCollection && (
                      <button
                        onClick={handleLinkCollectionOnly}
                        disabled={loading}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded-lg disabled:bg-gray-400"
                      >
                        {loading ? 'Linking...' : 'Link Existing'}
                      </button>
                    )}
                    <button
                      onClick={() => setStep('form')}
                      disabled={!selectedCollection}
                      className="flex-1 bg-black hover:bg-gray-800 text-white font-semibold px-4 py-2 rounded-lg disabled:bg-gray-400"
                    >
                      Add New Context
                    </button>
                  </div>
                </div>
              )}

              {step === 'form' && (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2 text-gray-900">
                      Patient Name
                    </label>
                    <input
                      type="text"
                      value={formData.patient_name}
                      onChange={(e) => setFormData({ ...formData, patient_name: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2 text-gray-900">
                      Cultural Background
                    </label>
                    <textarea
                      value={formData.cultural_background}
                      onChange={(e) =>
                        setFormData({ ...formData, cultural_background: e.target.value })
                      }
                      className="w-full px-4 py-2 border rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                      rows={3}
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2 text-gray-900">
                      Medical History
                    </label>
                    <textarea
                      value={formData.medical_history}
                      onChange={(e) =>
                        setFormData({ ...formData, medical_history: e.target.value })
                      }
                      className="w-full px-4 py-2 border rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                      rows={3}
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2 text-gray-900">
                      Language Notes
                    </label>
                    <textarea
                      value={formData.language_notes}
                      onChange={(e) => setFormData({ ...formData, language_notes: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                      rows={2}
                    />
                  </div>

                  {status && (
                    <div
                      className={`flex items-center gap-2 p-3 rounded-lg ${
                        status.type === 'success'
                          ? 'bg-green-50 border border-green-200 text-green-800'
                          : 'bg-red-50 border border-red-200 text-red-800'
                      }`}
                    >
                      {status.type === 'success' ? (
                        <CheckCircleOutline className="text-green-600" />
                      ) : (
                        <CancelOutlined className="text-red-600" />
                      )}
                      <span className="text-sm">{status.message}</span>
                    </div>
                  )}

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setStep('select');
                        setCreateNewCollection(false);
                      }}
                      className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-4 py-2 rounded-lg"
                      disabled={loading}
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 bg-black hover:bg-gray-800 text-white font-semibold px-4 py-2 rounded-lg disabled:bg-gray-400"
                    >
                      {loading ? 'Saving...' : 'Save Context'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default PatientContextManager;
