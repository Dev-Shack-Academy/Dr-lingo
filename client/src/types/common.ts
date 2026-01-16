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
  // International Languages
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'ja', name: 'Japanese' },
  // South African Languages (Official)
  { code: 'zul', name: 'isiZulu' },
  { code: 'xho', name: 'isiXhosa' },
  { code: 'afr', name: 'Afrikaans' },
  { code: 'sot', name: 'Sesotho' },
  { code: 'tsn', name: 'Setswana' },
  { code: 'nso', name: 'Sepedi (Northern Sotho)' },
  { code: 'ssw', name: 'siSwati' },
  { code: 'ven', name: 'Tshivenda' },
  { code: 'tso', name: 'Xitsonga' },
  { code: 'nbl', name: 'isiNdebele' },
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
