/**
 * RAG Collection type definitions
 */

export type EmbeddingProvider = 'openai' | 'gemini' | 'ollama';
export type ChunkingStrategy = 'fixed-length' | 'window' | 'no-chunking';
export type CollectionType = 'knowledge_base' | 'patient_context';

export interface KnowledgeBaseRef {
  id: number;
  name: string;
}

export interface Collection {
  id: number;
  name: string;
  description: string;
  collection_type: CollectionType;
  is_global: boolean;
  chat_room: number | null;
  chat_room_name?: string;
  knowledge_bases?: number[];
  knowledge_bases_details?: KnowledgeBaseRef[];
  embedding_provider: EmbeddingProvider;
  embedding_model: string;
  embedding_dimensions: number;
  completion_model: string;
  chunking_strategy: ChunkingStrategy;
  chunk_length: number | null;
  chunk_overlap: number | null;
  items_count?: number;
  created_at: string;
  updated_at: string;
}

export interface CollectionItem {
  id: number;
  collection: number;
  name: string;
  description: string;
  content: string;
  metadata: Record<string, any>;
  embedding?: number[];
  created_at: string;
  updated_at: string;
}

export interface CreateCollectionData {
  name: string;
  description?: string;
  collection_type?: CollectionType;
  is_global?: boolean;
  chat_room?: number;
  knowledge_bases?: number[];
  embedding_provider?: EmbeddingProvider;
  embedding_model?: string;
  embedding_dimensions?: number;
  completion_model?: string;
  chunking_strategy?: ChunkingStrategy;
  chunk_length?: number;
  chunk_overlap?: number;
}

export interface UpdateCollectionData {
  name?: string;
  description?: string;
  collection_type?: CollectionType;
  is_global?: boolean;
  chat_room?: number | null;
  knowledge_bases?: number[];
  embedding_provider?: EmbeddingProvider;
  embedding_model?: string;
  embedding_dimensions?: number;
  chunking_strategy?: ChunkingStrategy;
  chunk_length?: number;
  chunk_overlap?: number;
}

export interface CreateCollectionItemData {
  collection: number;
  name: string;
  description?: string;
  content: string;
  metadata?: Record<string, any>;
}

export interface RAGQueryRequest {
  query: string;
  top_k?: number;
  threshold?: number;
}

export interface RAGQueryResult {
  content: string;
  score: number;
  metadata: Record<string, any>;
  item_name: string;
}

export interface RAGQueryResponse {
  query: string;
  results: RAGQueryResult[];
  generated_response?: string;
}
