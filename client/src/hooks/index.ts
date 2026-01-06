/**
 * Custom React hooks
 */

export { useWebSocket } from './useWebSocket';
export { useChatWebSocket } from './useChatWebSocket';
export { useAIConfig } from './useAIConfig';

// Re-export types
export type { UseWebSocketOptions, UseWebSocketReturn } from '../types/websocket';
export type {
  UseChatWebSocketOptions,
  UseChatWebSocketReturn,
  TypingUser,
} from './useChatWebSocket';
