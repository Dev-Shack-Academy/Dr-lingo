import React, { useState, useEffect } from 'react';
import { InfoOutlined, CheckCircleOutline, CancelOutlined } from '@mui/icons-material';
import ChatService from '../api/services/ChatService';
import RAGService, { Collection } from '../api/services/RAGService';
import { useToast } from '../contexts/ToastContext';

interface AddPatientContextProps {
  roomId: number;
  roomName: string;
  currentCollection?: number;
  onClose: () => void;
  onSuccess: () => void;
}

const AddPatientContext: React.FC<AddPatientContextProps> = ({
  roomId,
  roomName,
  currentCollection,
  onClose,
  onSuccess,
}) => {
  const { showError, showSuccess } = useToast();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<number | null>(
    currentCollection || null
  );
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'select' | 'form'>(currentCollection ? 'form' : 'select');
  const [creatingCollection, setCreatingCollection] = useState(false);
  const [createNewCollection, setCreateNewCollection] = useState(false);
  const [formData, setFormData] = useState({
    patient_name: '',
    cultural_background: '',
    medical_history: '',
    language_notes: '',
  });
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      const data = await RAGService.getCollections();
      setCollections(data);
    } catch (error) {
      showError(error, 'Failed to load collections');
    }
  };

  const handleCreateCollectionAndProceed = () => {
    setCreateNewCollection(true);
    setStep('form');
  };

  const handleLinkCollectionOnly = async () => {
    if (!selectedCollection) return;

    setLoading(true);
    setStatus(null);

    try {
      // Link collection by adding empty context (which will just link the collection)
      await ChatService.addPatientContext(roomId, {
        collection_id: selectedCollection,
        patient_name: 'Existing Context',
        cultural_background: 'Using existing collection context',
        medical_history: 'See collection documents',
        language_notes: 'See collection documents',
      });

      setStatus({ type: 'success', message: 'Collection linked successfully!' });
      showSuccess('Collection linked successfully!');
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1000);
    } catch (error) {
      console.error('Link collection error:', error);
      showError(error, 'Failed to link collection');
      setStatus({ type: 'error', message: 'Failed to link collection' });
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

      // Create new collection if needed
      if (createNewCollection) {
        setStatus({ type: 'success', message: 'Creating collection...' });
        try {
          const timestamp = new Date().toISOString().slice(0, 19).replace('T', ' ');
          const newCollection = await RAGService.createCollection({
            name: `${roomName} - Patient Context - ${timestamp}`,
            description: `Medical and cultural context for ${roomName}`,
            embedding_provider: 'gemini',
            embedding_model: 'text-embedding-004',
            embedding_dimensions: 768,
            completion_model: 'h-exp',
            chunking_strategy: 'fixed-length',
            chunk_length: 1000,
            chunk_overlap: 200,
          });
          collectionId = newCollection.id;
          setStatus({ type: 'success', message: 'Collection created! Adding patient context...' });
        } catch (collectionError) {
          console.error('Collection creation error:', collectionError);
          showError(collectionError, 'Failed to create collection');
          setStatus({ type: 'error', message: 'Failed to create collection' });
          setLoading(false);
          return;
        }
      }

      if (!collectionId) {
        setStatus({ type: 'error', message: 'Please select a RAG collection first' });
        setLoading(false);
        return;
      }

      // Add patient context to RAG collection
      await ChatService.addPatientContext(roomId, {
        ...formData,
        collection_id: collectionId,
      });

      setStatus({ type: 'success', message: 'Patient context added successfully!' });
      showSuccess('Patient context added successfully!');
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (error) {
      showError(error, 'Failed to add patient context');
      setStatus({ type: 'error', message: 'Failed to add patient context' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-2xl font-bold text-gray-900">Add Patient Context</h3>
              <p className="text-sm text-gray-600 mt-1">Room: {roomName}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
            >
              ×
            </button>
          </div>

          {/* Info Banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex gap-3">
            <InfoOutlined className="text-blue-600 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <p className="font-semibold mb-1">What is Patient Context?</p>
              <p>
                Add cultural background, medical history, and language notes to help the AI provide
                more accurate and culturally-sensitive translations during the conversation.
              </p>
            </div>
          </div>

          {/* Step 1: Select Collection */}
          {step === 'select' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">
                  Select RAG Collection
                </label>
                <select
                  value={selectedCollection || ''}
                  onChange={(e) => setSelectedCollection(Number(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                >
                  <option value="">Choose a collection...</option>
                  {collections.map((collection) => (
                    <option key={collection.id} value={collection.id}>
                      {collection.name} ({collection.items_count} documents)
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Select an existing collection or create a new one below
                </p>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">OR</span>
                </div>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h4 className="font-semibold text-purple-900 mb-2">Create New Collection</h4>
                <p className="text-sm text-purple-700 mb-3">
                  We'll create a new collection specifically for this patient's context
                </p>
                <button
                  type="button"
                  onClick={handleCreateCollectionAndProceed}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
                >
                  Create New Collection & Add Context
                </button>
              </div>

              <div className="space-y-3 pt-4">
                {/* Link existing collection directly */}
                {selectedCollection && (
                  <button
                    type="button"
                    onClick={handleLinkCollectionOnly}
                    disabled={loading}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors disabled:bg-gray-400"
                  >
                    {loading ? 'Linking...' : 'Link This Collection (Use Existing Context)'}
                  </button>
                )}

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-3 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => setStep('form')}
                    disabled={!selectedCollection}
                    className="flex-1 bg-black hover:bg-gray-800 text-white font-semibold px-6 py-3 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    Add New Context
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Add Context Form */}
          {step === 'form' && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">
                  Patient Name
                </label>
                <input
                  type="text"
                  value={formData.patient_name}
                  onChange={(e) => setFormData({ ...formData, patient_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                  placeholder="e.g., John Doe"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">
                  Cultural Background
                </label>
                <textarea
                  value={formData.cultural_background}
                  onChange={(e) =>
                    setFormData({ ...formData, cultural_background: e.target.value })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                  rows={4}
                  placeholder="Cultural beliefs, practices, dietary restrictions, religious considerations, etc."
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Include cultural beliefs, practices, and sensitivities
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">
                  Medical History
                </label>
                <textarea
                  value={formData.medical_history}
                  onChange={(e) => setFormData({ ...formData, medical_history: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                  rows={4}
                  placeholder="Previous conditions, medications, allergies, surgeries, chronic illnesses, etc."
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Previous conditions, medications, allergies, etc.
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">
                  Language & Communication Notes
                </label>
                <textarea
                  value={formData.language_notes}
                  onChange={(e) => setFormData({ ...formData, language_notes: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                  rows={3}
                  placeholder="Preferred terms, idioms, communication style, literacy level, etc."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Preferred terms, idioms, communication preferences
                </p>
              </div>

              {/* Status Message */}
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
                  <span className="text-sm font-medium">{status.message}</span>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setStep('select');
                    setCreateNewCollection(false);
                  }}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-3 rounded-lg transition-colors"
                  disabled={loading}
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-black hover:bg-gray-800 text-white font-semibold px-6 py-3 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {loading
                    ? createNewCollection
                      ? 'Creating Collection & Adding Context...'
                      : 'Adding Context...'
                    : createNewCollection
                      ? 'Create Collection & Add Context'
                      : 'Add Context'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default AddPatientContext;
