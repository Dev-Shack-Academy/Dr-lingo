import { useState, useEffect } from 'react';
import httpClient from '../api/HttpClient';
import type { EmbeddingProvider, ChunkingStrategy } from '../types/collection';

export interface AIConfig {
  ai_provider: 'ollama' | 'gemini';
  translation_model: string;
  completion_model: string;
  embedding_model: string;
  embedding_provider: EmbeddingProvider;
  embedding_dimensions: number;
  chunking_strategy: ChunkingStrategy;
  chunk_length: number;
  chunk_overlap: number;
  ollama_base_url?: string;
}

const DEFAULT_CONFIG: AIConfig = {
  ai_provider: 'ollama',
  translation_model: 'granite:latest',
  completion_model: 'granite3.3:8b',
  embedding_model: 'nomic-embed-text:v1.5',
  embedding_provider: 'ollama',
  embedding_dimensions: 768,
  chunking_strategy: 'fixed-length',
  chunk_length: 1000,
  chunk_overlap: 200,
};

let cachedConfig: AIConfig | null = null;

export function useAIConfig() {
  const [config, setConfig] = useState<AIConfig>(cachedConfig || DEFAULT_CONFIG);
  const [loading, setLoading] = useState(!cachedConfig);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cachedConfig) {
      setConfig(cachedConfig);
      setLoading(false);
      return;
    }

    const fetchConfig = async () => {
      try {
        console.log('Fetching AI config from /api/config/ai/...');
        const response = await httpClient.get('/api/config/ai/');
        console.log('AI config response:', response.data);
        // Ensure the response matches our types
        const data = response.data;
        const typedConfig: AIConfig = {
          ai_provider: data.ai_provider || 'ollama',
          translation_model: data.translation_model || DEFAULT_CONFIG.translation_model,
          completion_model: data.completion_model || DEFAULT_CONFIG.completion_model,
          embedding_model: data.embedding_model || DEFAULT_CONFIG.embedding_model,
          embedding_provider:
            (data.embedding_provider as EmbeddingProvider) || DEFAULT_CONFIG.embedding_provider,
          embedding_dimensions: data.embedding_dimensions || DEFAULT_CONFIG.embedding_dimensions,
          chunking_strategy:
            (data.chunking_strategy as ChunkingStrategy) || DEFAULT_CONFIG.chunking_strategy,
          chunk_length: data.chunk_length || DEFAULT_CONFIG.chunk_length,
          chunk_overlap: data.chunk_overlap || DEFAULT_CONFIG.chunk_overlap,
          ollama_base_url: data.ollama_base_url,
        };
        console.log('Parsed AI config:', typedConfig);
        cachedConfig = typedConfig;
        setConfig(typedConfig);
      } catch (err) {
        console.warn('Failed to fetch AI config, using defaults:', err);
        setError('Failed to fetch AI config');
        cachedConfig = DEFAULT_CONFIG;
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  return { config, loading, error };
}

// Utility to get config synchronously (returns cached or default)
export function getAIConfigSync(): AIConfig {
  return cachedConfig || DEFAULT_CONFIG;
}
