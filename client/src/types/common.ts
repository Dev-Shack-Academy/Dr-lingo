/**
 * Common/shared type definitions
 */

// API Response types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}

// Language definitions
export interface Language {
  code: string;
  name: string;
}

export const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'afr', name: 'Afrikaans' },
  { code: 'ja', name: 'Japanese' },
  { code: 'zulu', name: 'Zulu' },
  { code: 'tsawana', name: 'Tswana' },
  { code: 'xhosa', name: 'Xhosa' },
  { code: 'chichewe', name: 'Chichewe' },
];

// Utility types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

// Form status
export interface FormStatus {
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
}
