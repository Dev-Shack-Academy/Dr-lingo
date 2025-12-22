import httpClient from '../HttpClient';
import { API_BASE_URL } from '../routes';
import type {
  Collection,
  CollectionItem,
  CreateCollectionData,
  CreateCollectionItemData,
  RAGQueryRequest,
  RAGQueryResponse,
} from '../../types';

// Re-export types for backward compatibility
export type { Collection, CollectionItem, CreateCollectionData, CreateCollectionItemData };

// Legacy interfaces for backward compatibility
export interface QueryResult {
  query: string;
  results: Array<{
    name: string;
    content: string;
    similarity: number;
    metadata: Record<string, any>;
  }>;
}

export interface RAGAnswer {
  status: string;
  answer: string;
  sources: Array<{
    name: string;
    similarity: number;
    content: string;
  }>;
}

const RAGService = {
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

  async updateCollection(id: number, data: Partial<CreateCollectionData>): Promise<Collection> {
    const response = await httpClient.patch(`${API_BASE_URL}/collections/${id}/`, data);
    return response.data;
  },

  async deleteCollection(id: number): Promise<void> {
    await httpClient.delete(`${API_BASE_URL}/collections/${id}/`);
  },

  async addDocument(
    collectionId: number,
    data: { name: string; content: string; description?: string; metadata?: Record<string, any> }
  ): Promise<CollectionItem> {
    const response = await httpClient.post(
      `${API_BASE_URL}/collections/${collectionId}/add_document/`,
      data
    );
    return response.data;
  },

  async queryCollection(
    collectionId: number,
    query: string,
    topK: number = 5
  ): Promise<QueryResult> {
    const response = await httpClient.post(`${API_BASE_URL}/collections/${collectionId}/query/`, {
      query,
      top_k: topK,
    });
    return response.data;
  },

  async queryAndAnswer(collectionId: number, query: string, topK: number = 5): Promise<RAGAnswer> {
    const response = await httpClient.post(
      `${API_BASE_URL}/collections/${collectionId}/query_and_answer/`,
      {
        query,
        top_k: topK,
      }
    );
    return response.data;
  },

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
};

export default RAGService;
