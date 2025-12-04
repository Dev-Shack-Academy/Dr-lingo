import { useState, useEffect } from 'react';
import ItemService from '../api/services/ItemService';
import { Item } from '../types/item';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import DataArrayOutlinedIcon from '@mui/icons-material/DataArrayOutlined';
import EmojiObjectsIcon from '@mui/icons-material/EmojiObjects';

function ItemList() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await ItemService.getItems();
        setItems(data);
      } catch (err) {
        setError('Failed to load items. Please try again later.');
        console.error('Error fetching items:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchItems();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center py-12 px-4">
        <div className="bg-white rounded-2xl shadow-2xl p-16 text-center max-w-md w-full border border-gray-200">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-gray-200 border-t-black mb-6"></div>
          <p className="text-black text-xl font-semibold">Loading items...</p>
          <p className="text-gray-500 text-sm mt-2">Please wait</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center py-12 px-4">
        <div className="bg-white rounded-2xl shadow-2xl p-12 text-center max-w-md w-full border border-gray-200">
          <ErrorOutlineIcon
            className="text-red"
            style={{ fontSize: 120, marginBottom: '1.5rem' }}
          />
          <p className="text-black text-xl font-semibold mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-black hover:bg-gray-800 text-white font-semibold px-8 py-3 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center py-12 px-4">
        <div className="bg-white rounded-2xl shadow-2xl p-16 text-center max-w-lg w-full border border-gray-200">
          <DataArrayOutlinedIcon
            className="text-black"
            style={{ fontSize: 120, marginBottom: '1.5rem' }}
          />
          <p className="text-black text-2xl font-bold mb-4">No items found</p>
          <p className="text-gray-500 text-lg">Items you create will appear here</p>
          <p className="text-black text-sm mt-2">
            <EmojiObjectsIcon className="text-yellow-500 mb-2 mt-1" /> hint go run poetry run
            manage.py seed_data
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Central Card Container */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-12 border border-gray-200">
          <h2 className="text-4xl font-bold text-black mb-8 text-center">Items</h2>
          <div className="h-1 w-24 bg-black mx-auto mb-12"></div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {items.map((item) => (
              <div
                key={item.id}
                className="border border-gray-200 rounded-lg hover:border-black transition-colors p-6 bg-white"
              >
                <h3 className="text-xl font-bold text-black mb-3">{item.name}</h3>
                <p className="text-gray-600 mb-4 min-h-[3rem]">{item.description}</p>
                <p className="text-xs text-gray-400 pt-4 border-t border-gray-200">
                  {new Date(item.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ItemList;
