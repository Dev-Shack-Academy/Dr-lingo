import ApiClient from '../ApiClient';
import routes from '../routes';
import { Item, ItemCreate } from '../../types/item';

const ItemService = {
  getItems: async (): Promise<Item[]> => {
    const response = await ApiClient.get(routes.ITEMS);
    // Handle paginated response from Django REST Framework
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results as Item[];
    }
    // Handle direct array response
    return Array.isArray(response) ? response : [];
  },

  getItem: async (id: number): Promise<Item> => ApiClient.get(`${routes.ITEMS}${id}/`),

  createItem: async (data: ItemCreate): Promise<Item> => ApiClient.post(routes.ITEMS, data),

  updateItem: async (id: number, data: Partial<ItemCreate>): Promise<Item> =>
    ApiClient.put(`${routes.ITEMS}${id}/`, data),

  deleteItem: async (id: number): Promise<void> => ApiClient.delete(`${routes.ITEMS}${id}/`),

  healthCheck: async (): Promise<{ status: string; message: string }> =>
    ApiClient.get(routes.HEALTH_CHECK),
};

export default ItemService;
