import { useState } from 'react';
import ItemService from '../api/services/ItemService';

interface CreateItemFormProps {
  onItemCreated: () => void;
}

function CreateItemForm({ onItemCreated }: CreateItemFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !description.trim()) {
      setError('Name and description are required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await ItemService.createItem({ name, description });

      // Reset form
      setName('');
      setDescription('');
      setShowForm(false);

      // Notify parent to refresh list
      onItemCreated();
    } catch (err) {
      setError('Failed to create item. Please try again.');
      console.error('Error creating item:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!showForm) {
    return (
      <div className="mb-8 text-center">
        <button
          onClick={() => setShowForm(true)}
          className="bg-black hover:bg-gray-800 text-white font-semibold px-8 py-4 rounded-lg transition-colors text-lg"
        >
          + Create New Item
        </button>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <div className="bg-gray-50 border-2 border-gray-200 rounded-xl p-8">
        <h3 className="text-2xl font-bold text-black mb-6">Create New Item</h3>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-semibold text-black mb-2">
              Name *
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-black focus:outline-none transition-colors"
              placeholder="Enter item name"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-semibold text-black mb-2">
              Description *
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-black focus:outline-none transition-colors resize-none"
              placeholder="Enter item description"
              disabled={loading}
            />
          </div>

          {error && (
            <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
              <p className="text-red-600 font-medium">{error}</p>
            </div>
          )}

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-black hover:bg-gray-800 text-white font-semibold px-6 py-3 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Item'}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                setName('');
                setDescription('');
                setError(null);
              }}
              disabled={loading}
              className="flex-1 bg-white hover:bg-gray-100 text-black font-semibold px-6 py-3 rounded-lg border-2 border-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CreateItemForm;
