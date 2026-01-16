import React, { useState, useEffect } from 'react';
import {
  InfoOutlined,
  CheckCircleOutline,
  CancelOutlined,
  AttachFile,
  Close,
} from '@mui/icons-material';
import ChatService from '../api/services/ChatService';
import RAGService, { Collection } from '../api/services/RAGService';
import { useToast } from '../contexts/ToastContext';
import { useAIConfig } from '../hooks/useAIConfig';

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
  const { config: aiConfig } = useAIConfig();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<number | null>(
    currentCollection || null
  );
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'select' | 'form'>(currentCollection ? 'form' : 'select');
  const [createNewCollection, setCreateNewCollection] = useState(false);
  const [formData, setFormData] = useState({
    patient_name: '',
    cultural_background: '',
    medical_history: '',
    language_notes: '',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
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
            embedding_provider: aiConfig.embedding_provider,
            embedding_model: aiConfig.embedding_model,
            embedding_dimensions: aiConfig.embedding_dimensions,
            completion_model: aiConfig.completion_model,
            collection_type: 'patient_context',
            chat_room: roomId,
            is_global: false,
            chunking_strategy: 'fixed-length',
            chunk_length: aiConfig.chunk_length,
            chunk_overlap: aiConfig.chunk_overlap,
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

      // Use FormData if a file is selected, or if we want to combine text and file
      if (selectedFile) {
        setStatus({ type: 'success', message: 'Uploading PDF document...' });
        const ragFormData = new FormData();
        ragFormData.append('file', selectedFile);
        ragFormData.append('name', formData.patient_name || selectedFile.name);
        ragFormData.append(
          'description',
          `Medical record for ${formData.patient_name || roomName}`
        );

        await RAGService.addDocument(collectionId, ragFormData);
      }

      // Add patient context text fields to RAG collection/link it to the room
      // Even if text fields are empty, we call this to link the collection to the room
      await ChatService.addPatientContext(roomId, {
        ...formData,
        patient_name: formData.patient_name || selectedFile?.name || 'Unknown Patient',
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

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);

    // Auto-fill patient name from filename if not already set
    if (!formData.patient_name) {
      const fileName = file.name.replace(/\.[^/.]+$/, ''); // Remove extension
      setFormData((prev) => ({
        ...prev,
        patient_name: fileName,
      }));
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
              {/* PDF Upload Section */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <label className="block text-sm font-bold mb-3 text-gray-900 flex items-center gap-2">
                  <AttachFile className="w-4 h-4" />
                  Upload Medical Record (PDF)
                </label>
                <div
                  className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                    selectedFile
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-300 bg-white hover:border-gray-400'
                  }`}
                >
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="patient-pdf-upload"
                  />
                  {!selectedFile ? (
                    <label htmlFor="patient-pdf-upload" className="cursor-pointer group block">
                      <AttachFile className="w-8 h-8 text-gray-400 group-hover:text-gray-600 mx-auto mb-2" />
                      <p className="text-sm text-gray-600">
                        <span className="text-blue-600 font-semibold">Click to upload PDF</span> or
                        drag and drop
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        Medical records will be automatically indexed for RAG
                      </p>
                    </label>
                  ) : (
                    <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-green-200">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-green-100 rounded-lg">
                          <AttachFile className="text-green-600" />
                        </div>
                        <div className="text-left">
                          <p className="text-sm font-semibold text-gray-900 truncate max-w-[250px]">
                            {selectedFile.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setSelectedFile(null)}
                        className="p-1 hover:bg-red-50 rounded-full text-red-500 transition-colors"
                      >
                        <Close className="w-5 h-5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">
                  Patient Name *
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
                  rows={3}
                  placeholder="Cultural beliefs, practices, dietary restrictions, religious considerations, etc."
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">
                  Medical History
                </label>
                <textarea
                  value={formData.medical_history}
                  onChange={(e) => setFormData({ ...formData, medical_history: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                  rows={3}
                  placeholder="Previous conditions, medications, allergies, surgeries, chronic illnesses, etc."
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">
                  Language & Communication Notes
                </label>
                <textarea
                  value={formData.language_notes}
                  onChange={(e) => setFormData({ ...formData, language_notes: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none text-black"
                  rows={2}
                  placeholder="Preferred terms, idioms, communication style, literacy level, etc."
                />
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
