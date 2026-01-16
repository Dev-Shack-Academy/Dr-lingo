import { useState, useEffect } from 'react';
import {
  Add,
  Edit,
  Delete,
  Refresh,
  MenuBook,
  Article,
  Close,
  Language,
  LocalHospital,
  Public,
  ExpandMore,
  ExpandLess,
  AttachFile,
} from '@mui/icons-material';
import AdminService from '../../api/services/AdminService';
import type {
  Collection,
  CollectionItem,
  CreateCollectionData,
  CreateCollectionItemData,
} from '../../types/collection';
import { useToast } from '../../contexts/ToastContext';
import { useAIConfig } from '../../hooks/useAIConfig';

export default function KnowledgeBaseManagement() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null);
  const [expandedCollection, setExpandedCollection] = useState<number | null>(null);
  const { showError, showSuccess } = useToast();

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      setLoading(true);
      const data = await AdminService.getCollections();
      const knowledgeBase = data.filter((c: Collection) => c.collection_type === 'knowledge_base');
      setCollections(knowledgeBase);
    } catch (err) {
      showError(err, 'Failed to load knowledge base');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (
      !confirm(
        'Are you sure you want to delete this knowledge base? All documents will be deleted.'
      )
    )
      return;
    try {
      await AdminService.deleteCollection(id);
      showSuccess('Knowledge base deleted');
      loadCollections();
    } catch (err) {
      showError(err, 'Failed to delete');
    }
  };

  const getCategoryIcon = (name: string) => {
    const lower = name.toLowerCase();
    if (lower.includes('language') || lower.includes('translation')) return Language;
    if (lower.includes('medical') || lower.includes('health')) return LocalHospital;
    return Public;
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
            <MenuBook className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Knowledge Base</h2>
            <p className="text-sm text-gray-500">Global reference data for all translations</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadCollections}
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
            Add Knowledge Base
          </button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <MenuBook className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-blue-900">What is Knowledge Base?</h3>
            <p className="text-sm text-blue-700 mt-1">
              Knowledge Base collections contain global reference data that improves ALL
              translations. Add medical terminology, language guides, cultural context, and regional
              information here.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading knowledge base...</div>
        </div>
      ) : collections.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <MenuBook className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Knowledge Base Yet</h3>
          <p className="text-gray-500 mb-4">
            Create your first knowledge base to improve translation quality
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            <Add className="w-4 h-4" />
            Add Knowledge Base
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {collections.map((collection) => {
            const CategoryIcon = getCategoryIcon(collection.name);
            const isExpanded = expandedCollection === collection.id;
            return (
              <KnowledgeBaseCard
                key={collection.id}
                collection={collection}
                CategoryIcon={CategoryIcon}
                isExpanded={isExpanded}
                onToggleExpand={() => toggleExpand(collection.id)}
                onEdit={() => setEditingCollection(collection)}
                onDelete={() => handleDelete(collection.id)}
                onRefresh={loadCollections}
              />
            );
          })}
        </div>
      )}

      {showCreateModal && (
        <KnowledgeBaseModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadCollections();
          }}
        />
      )}

      {editingCollection && (
        <KnowledgeBaseModal
          collection={editingCollection}
          onClose={() => setEditingCollection(null)}
          onSuccess={() => {
            setEditingCollection(null);
            loadCollections();
          }}
        />
      )}
    </div>
  );
}

function KnowledgeBaseCard({
  collection,
  CategoryIcon,
  isExpanded,
  onToggleExpand,
  onEdit,
  onDelete,
  onRefresh,
}: {
  collection: Collection;
  CategoryIcon: typeof Language;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onRefresh: () => void;
}) {
  const [items, setItems] = useState<CollectionItem[]>([]);
  const [loadingItems, setLoadingItems] = useState(false);
  const [showAddDocument, setShowAddDocument] = useState(false);
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
    if (!confirm('Delete this document?')) return;
    try {
      await AdminService.deleteCollectionItem(id);
      showSuccess('Document deleted');
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
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <CategoryIcon className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">{collection.name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                  Global
                </span>
                <span className="text-xs text-gray-500">
                  {collection.items_count || 0} documents
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAddDocument(true)}
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
            >
              <Add className="w-4 h-4" />
              Add Document
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

      {/* Expanded Documents Section */}
      {isExpanded && (
        <div className="border-t border-gray-200 bg-gray-50 p-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Documents</h4>
          {loadingItems ? (
            <div className="text-center py-4 text-gray-500 text-sm">Loading documents...</div>
          ) : items.length === 0 ? (
            <div className="text-center py-6 bg-white rounded-lg border border-dashed border-gray-300">
              <Article className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500 mb-3">No documents yet</p>
              <button
                onClick={() => setShowAddDocument(true)}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                + Add your first document
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
                      <div className="w-8 h-8 bg-blue-50 rounded flex items-center justify-center flex-shrink-0">
                        <Article className="w-4 h-4 text-blue-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{item.name}</p>
                        {item.description && (
                          <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                        )}
                        <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                          {item.content.substring(0, 150)}...
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

      {showAddDocument && (
        <AddDocumentModal
          collectionId={collection.id}
          collectionName={collection.name}
          onClose={() => setShowAddDocument(false)}
          onSuccess={() => {
            setShowAddDocument(false);
            loadItems();
            onRefresh();
          }}
        />
      )}
    </div>
  );
}

function KnowledgeBaseModal({
  collection,
  onClose,
  onSuccess,
}: {
  collection?: Collection;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const { config: aiConfig } = useAIConfig();
  const [formData, setFormData] = useState<CreateCollectionData>({
    name: collection?.name || '',
    description: collection?.description || '',
    collection_type: 'knowledge_base',
    is_global: true,
    embedding_provider: collection?.embedding_provider || aiConfig.embedding_provider,
    embedding_model: collection?.embedding_model || aiConfig.embedding_model,
    completion_model: collection?.completion_model || aiConfig.completion_model,
    embedding_dimensions: collection?.embedding_dimensions || aiConfig.embedding_dimensions,
    chunking_strategy: collection?.chunking_strategy || aiConfig.chunking_strategy,
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
        completion_model: aiConfig.completion_model,
        embedding_dimensions: aiConfig.embedding_dimensions,
        chunking_strategy: aiConfig.chunking_strategy,
        chunk_length: aiConfig.chunk_length,
        chunk_overlap: aiConfig.chunk_overlap,
      }));
    }
  }, [aiConfig, collection]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      if (collection) {
        await AdminService.updateCollection(collection.id, formData);
        showSuccess('Knowledge base updated');
      } else {
        await AdminService.createCollection(formData);
        showSuccess('Knowledge base created');
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
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <MenuBook className="w-5 h-5 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">
              {collection ? 'Edit Knowledge Base' : 'Create Knowledge Base'}
            </h3>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Close className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Name *</label>
            <input
              type="text"
              placeholder="e.g., Medical Terminology, Zulu Language Guide"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea
              placeholder="Describe what this knowledge base contains"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              rows={3}
            />
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Advanced Settings</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Embedding Provider
                </label>
                <select
                  value={formData.embedding_provider}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      embedding_provider: e.target.value as any,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white text-sm"
                >
                  <option value="gemini">Gemini</option>
                  <option value="ollama">Ollama</option>
                  <option value="openai">OpenAI</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Completion Model
                </label>
                <input
                  type="text"
                  value={formData.completion_model}
                  onChange={(e) => setFormData({ ...formData, completion_model: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Chunking Strategy
                </label>
                <select
                  value={formData.chunking_strategy}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      chunking_strategy: e.target.value as any,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white text-sm"
                >
                  <option value="fixed-length">Fixed Length</option>
                  <option value="window">Window</option>
                  <option value="no-chunking">No Chunking</option>
                </select>
              </div>
            </div>
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
              {loading ? 'Saving...' : collection ? 'Save Changes' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AddDocumentModal({
  collectionId,
  collectionName,
  onClose,
  onSuccess,
}: {
  collectionId: number;
  collectionName: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<CreateCollectionItemData>({
    collection: collectionId,
    name: '',
    description: '',
    content: '',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const { showError, showSuccess } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);

      if (selectedFile && selectedFile.name.toLowerCase().endsWith('.pdf')) {
        const formDataPayload = new FormData();
        formDataPayload.append('file', selectedFile);
        formDataPayload.append('name', formData.name || selectedFile.name);
        formDataPayload.append('description', formData.description || '');
        await AdminService.addDocument(collectionId, formDataPayload);
      } else {
        await AdminService.createCollectionItem(formData);
      }

      showSuccess('Document added');
      onSuccess();
    } catch (err) {
      showError(err, 'Failed to add document');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.name.toLowerCase().endsWith('.pdf')) {
      setSelectedFile(file);
      setFormData((prev) => ({
        ...prev,
        name: prev.name || file.name.replace(/\.[^/.]+$/, ''),
        content: '[PDF Content - automatically extracted by server]',
      }));
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setFormData((prev) => ({
        ...prev,
        name: prev.name || file.name.replace(/\.[^/.]+$/, ''),
        content: content,
      }));
      setSelectedFile(null);
    };
    reader.readAsText(file);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Article className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Add Document</h3>
              <p className="text-xs text-gray-500">to {collectionName}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Close className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Document Name *</label>
            <input
              type="text"
              placeholder="e.g., Zulu Medical Terms, Regional Dialects"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (optional)
            </label>
            <input
              type="text"
              placeholder="Brief description of the content"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 bg-white focus:border-black focus:ring-1 focus:ring-black outline-none"
            />
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload File (optional)
            </label>
            <div
              className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
                selectedFile
                  ? 'border-green-300 bg-green-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="file"
                accept=".txt,.md,.csv,.json,.pdf"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              {!selectedFile ? (
                <label htmlFor="file-upload" className="cursor-pointer group block">
                  <div className="flex flex-col items-center">
                    <AttachFile className="w-8 h-8 text-gray-400 group-hover:text-gray-600 mb-2" />
                    <p className="text-sm text-gray-600">
                      <span className="text-blue-600 font-semibold">Click to upload</span> or drag
                      and drop
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      TXT, MD, CSV, JSON, PDF files supported
                    </p>
                  </div>
                </label>
              ) : (
                <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-green-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <AttachFile className="text-green-600" />
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-semibold text-gray-900 truncate max-w-[200px]">
                        {selectedFile.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFile(null);
                      if (
                        formData.content === '[PDF Content - automatically extracted by server]'
                      ) {
                        setFormData((prev) => ({ ...prev, content: '' }));
                      }
                    }}
                    className="p-1 hover:bg-red-50 rounded-full text-red-500 transition-colors"
                  >
                    <Close className="w-5 h-5" />
                  </button>
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {selectedFile ? 'Extracted Content (Read-only)' : 'Content *'}
            </label>
            <textarea
              placeholder={
                selectedFile
                  ? 'PDF content will be processed...'
                  : 'Paste or type your content here...'
              }
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              className={`w-full px-4 py-3 border border-gray-300 rounded-lg text-gray-900 focus:border-black focus:ring-1 focus:ring-black outline-none font-mono text-sm ${selectedFile ? 'bg-gray-50' : 'bg-white'}`}
              rows={selectedFile ? 3 : 10}
              required
              readOnly={!!selectedFile}
            />
            <p className="text-xs text-gray-400 mt-1">
              {selectedFile
                ? 'Submit the form to process this PDF'
                : `${formData.content.length} characters`}
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
              disabled={loading || !formData.content.trim()}
              className="flex-1 px-4 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors font-semibold disabled:bg-gray-400"
            >
              {loading ? 'Adding...' : 'Add Document'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
