import httpClient from '../HttpClient';
import { API_BASE_URL } from '../routes';
import type { User, CreateUserData, UpdateUserData } from '../../types/user';
import type {
  Collection,
  CreateCollectionData,
  UpdateCollectionData,
  CollectionItem,
  CreateCollectionItemData,
} from '../../types/collection';
import type { ChatRoom, CreateChatRoomData, UpdateChatRoomData } from '../../types/chat';

// Re-export types for backward compatibility
export type {
  User,
  CreateUserData,
  UpdateUserData,
  Collection,
  CreateCollectionData,
  UpdateCollectionData,
  CollectionItem,
  CreateCollectionItemData,
  ChatRoom,
  CreateChatRoomData,
  UpdateChatRoomData,
};

const AdminService = {
  // ==================== USERS ====================
  async getUsers(): Promise<User[]> {
    const response = await httpClient.get(`${API_BASE_URL}/users/`);
    return response.data.results || response.data;
  },

  async getUser(id: number): Promise<User> {
    const response = await httpClient.get(`${API_BASE_URL}/users/${id}/`);
    return response.data;
  },

  async createUser(data: CreateUserData): Promise<User> {
    const response = await httpClient.post(`${API_BASE_URL}/users/`, data);
    return response.data;
  },

  async updateUser(id: number, data: UpdateUserData): Promise<User> {
    const response = await httpClient.patch(`${API_BASE_URL}/users/${id}/`, data);
    return response.data;
  },

  async deleteUser(id: number): Promise<void> {
    await httpClient.delete(`${API_BASE_URL}/users/${id}/`);
  },

  async getDoctors(): Promise<User[]> {
    const response = await httpClient.get(`${API_BASE_URL}/users/doctors/`);
    return response.data;
  },

  async getPatients(): Promise<User[]> {
    const response = await httpClient.get(`${API_BASE_URL}/users/patients/`);
    return response.data;
  },

  // ==================== COLLECTIONS ====================
  async getCollections(): Promise<Collection[]> {
    const response = await httpClient.get(`${API_BASE_URL}/collections/`);
    return response.data.results || response.data;
  },

  async getCollection(id: number): Promise<Collection> {
    const response = await httpClient.get(`${API_BASE_URL}/collections/${id}/`);
    return response.data;
  },

  async createCollection(data: CreateCollectionData): Promise<Collection> {
    const response = await httpClient.post(`${API_BASE_URL}/collections/`, data);
    return response.data;
  },

  async updateCollection(id: number, data: UpdateCollectionData): Promise<Collection> {
    const response = await httpClient.patch(`${API_BASE_URL}/collections/${id}/`, data);
    return response.data;
  },

  async deleteCollection(id: number): Promise<void> {
    await httpClient.delete(`${API_BASE_URL}/collections/${id}/`);
  },

  // ==================== COLLECTION ITEMS ====================
  async getCollectionItems(collectionId?: number): Promise<CollectionItem[]> {
    const url = collectionId
      ? `${API_BASE_URL}/collection-items/?collection=${collectionId}`
      : `${API_BASE_URL}/collection-items/`;
    const response = await httpClient.get(url);
    return response.data.results || response.data;
  },

  async createCollectionItem(data: CreateCollectionItemData): Promise<CollectionItem> {
    const response = await httpClient.post(`${API_BASE_URL}/collection-items/`, data);
    return response.data;
  },

  async deleteCollectionItem(id: number): Promise<void> {
    await httpClient.delete(`${API_BASE_URL}/collection-items/${id}/`);
  },

  // ==================== CHAT ROOMS ====================
  async getChatRooms(): Promise<ChatRoom[]> {
    const response = await httpClient.get(`${API_BASE_URL}/chat-rooms/`);
    return response.data.results || response.data;
  },

  async getChatRoom(id: number): Promise<ChatRoom> {
    const response = await httpClient.get(`${API_BASE_URL}/chat-rooms/${id}/`);
    return response.data;
  },

  async createChatRoom(data: CreateChatRoomData): Promise<ChatRoom> {
    const response = await httpClient.post(`${API_BASE_URL}/chat-rooms/`, data);
    return response.data;
  },

  async updateChatRoom(id: number, data: UpdateChatRoomData): Promise<ChatRoom> {
    const response = await httpClient.patch(`${API_BASE_URL}/chat-rooms/${id}/`, data);
    return response.data;
  },

  async deleteChatRoom(id: number): Promise<void> {
    await httpClient.delete(`${API_BASE_URL}/chat-rooms/${id}/`);
  },

  // ==================== STATS ====================
  async getStats(): Promise<{
    users: number;
    doctors: number;
    patients: number;
    chatRooms: number;
    collections: number;
  }> {
    const [users, chatRooms, collections] = await Promise.all([
      this.getUsers(),
      this.getChatRooms(),
      this.getCollections(),
    ]);

    return {
      users: users.length,
      doctors: users.filter((u) => u.role === 'doctor').length,
      patients: users.filter((u) => u.role === 'patient').length,
      chatRooms: chatRooms.length,
      collections: collections.length,
    };
  },
};

export default AdminService;
