import { useState, useCallback, useRef, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import type {
  WebSocketStatus,
  ServerEvent,
  MessageNewEvent,
  MessageTranslatedEvent,
  MessageTranscribedEvent,
  TTSGeneratedEvent,
  TranslationFailedEvent,
  AudioProcessingFailedEvent,
  UserTypingEvent,
} from '../types/websocket';
import type { ChatMessage } from '../types/chat';

// Typing indicator state
export interface TypingUser {
  userId: number;
  senderType: 'patient' | 'doctor';
  timestamp: number;
}

export interface UseChatWebSocketOptions {
  roomId: number;
  userType?: 'patient' | 'doctor';
  enabled?: boolean;
  onNewMessage?: (event: MessageNewEvent) => void;
  onMessageTranslated?: (event: MessageTranslatedEvent) => void;
  onMessageTranscribed?: (event: MessageTranscribedEvent) => void;
  onTTSGenerated?: (event: TTSGeneratedEvent) => void;
  onTranslationFailed?: (event: TranslationFailedEvent) => void;
  onAudioProcessingFailed?: (event: AudioProcessingFailedEvent) => void;
  onError?: (message: string) => void;
}

export interface UseChatWebSocketReturn {
  status: WebSocketStatus;
  typingUsers: TypingUser[];
  sendTyping: () => void;
  sendStopTyping: () => void;
  reconnect: () => void;
  updateMessageInPlace: (messageId: number, updates: Partial<ChatMessage>) => void;
}

// Debounce typing events (don't send more than once per second)
const TYPING_DEBOUNCE_MS = 1000;
// Clear typing indicator after 3 seconds of no updates
const TYPING_TIMEOUT_MS = 3000;

/**
 * Get WebSocket URL for a chat room.
 * In development, connects directly to Daphne on port 8001.
 * In production, uses the same host as the page.
 */
function getWebSocketUrl(roomId: number): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

  // In development, connect directly to Daphne WebSocket server
  if (import.meta.env.DEV) {
    return `ws://localhost:8001/ws/chat/${roomId}/`;
  }

  // In production, use the same host (assumes reverse proxy handles /ws/)
  const host = window.location.host;
  return `${protocol}//${host}/ws/chat/${roomId}/`;
}

/**
 * Chat-specific WebSocket hook that handles message updates, typing indicators, etc.
 */
export function useChatWebSocket(options: UseChatWebSocketOptions): UseChatWebSocketReturn {
  const {
    roomId,
    userType,
    enabled = true,
    onNewMessage,
    onMessageTranslated,
    onMessageTranscribed,
    onTTSGenerated,
    onTranslationFailed,
    onAudioProcessingFailed,
    onError,
  } = options;

  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);
  const lastTypingSentRef = useRef<number>(0);
  const messageUpdatesRef = useRef<Map<number, Partial<ChatMessage>>>(new Map());

  // Handle incoming WebSocket messages
  const handleMessage = useCallback(
    (event: ServerEvent) => {
      switch (event.type) {
        case 'connection.established':
          console.log('[ChatWS] Connected to room:', event.room_id);
          break;

        case 'message.new':
          console.log('[ChatWS] New message:', event.message_id);
          onNewMessage?.(event as MessageNewEvent);
          break;

        case 'message.translated':
          console.log('[ChatWS] Message translated:', event.message_id);
          onMessageTranslated?.(event as MessageTranslatedEvent);
          break;

        case 'message.transcribed':
          console.log('[ChatWS] Message transcribed:', event.message_id);
          onMessageTranscribed?.(event as MessageTranscribedEvent);
          break;

        case 'tts.generated':
          console.log('[ChatWS] TTS generated:', event.message_id);
          onTTSGenerated?.(event as TTSGeneratedEvent);
          break;

        case 'translation.failed':
          console.log('[ChatWS] Translation failed:', event.message_id);
          onTranslationFailed?.(event as TranslationFailedEvent);
          break;

        case 'audio.processing_failed':
          console.log('[ChatWS] Audio processing failed:', event.message_id);
          onAudioProcessingFailed?.(event as AudioProcessingFailedEvent);
          break;

        case 'user.typing':
          const typingEvent = event as UserTypingEvent;
          setTypingUsers((prev) => {
            // Update or add typing user
            const existing = prev.find((u) => u.userId === typingEvent.user_id);
            if (existing) {
              return prev.map((u) =>
                u.userId === typingEvent.user_id ? { ...u, timestamp: Date.now() } : u
              );
            }
            return [
              ...prev,
              {
                userId: typingEvent.user_id,
                senderType: typingEvent.sender_type,
                timestamp: Date.now(),
              },
            ];
          });
          break;

        case 'user.stopped_typing':
          setTypingUsers((prev) => prev.filter((u) => u.userId !== event.user_id));
          break;

        case 'user.disconnected':
          setTypingUsers((prev) => prev.filter((u) => u.userId !== event.user_id));
          break;

        case 'error':
          console.error('[ChatWS] Error:', event.message);
          onError?.(event.message);
          break;

        case 'pong':
          // Keep-alive response, no action needed
          break;

        default:
          console.log('[ChatWS] Unknown event:', event);
      }
    },
    [
      onNewMessage,
      onMessageTranslated,
      onMessageTranscribed,
      onTTSGenerated,
      onTranslationFailed,
      onAudioProcessingFailed,
      onError,
    ]
  );

  // Clean up stale typing indicators
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setTypingUsers((prev) => prev.filter((u) => now - u.timestamp < TYPING_TIMEOUT_MS));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Create WebSocket URL
  const wsUrl = enabled ? getWebSocketUrl(roomId) : '';

  // Use the generic WebSocket hook
  const { status, send, reconnect } = useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
    onConnect: () => console.log('[ChatWS] WebSocket connected'),
    onDisconnect: () => console.log('[ChatWS] WebSocket disconnected'),
    onError: () => onError?.('WebSocket connection error'),
    reconnect: true,
    reconnectInterval: 1000,
    maxReconnectAttempts: 10,
    pingInterval: 30000,
  });

  // Send typing indicator (debounced)
  const sendTyping = useCallback(() => {
    const now = Date.now();
    if (now - lastTypingSentRef.current >= TYPING_DEBOUNCE_MS) {
      send({ type: 'typing', sender_type: userType });
      lastTypingSentRef.current = now;
    }
  }, [send, userType]);

  // Send stop typing indicator
  const sendStopTyping = useCallback(() => {
    send({ type: 'stop_typing', sender_type: userType });
    lastTypingSentRef.current = 0;
  }, [send, userType]);

  // Helper to update a message in place (for parent component to use)
  const updateMessageInPlace = useCallback((messageId: number, updates: Partial<ChatMessage>) => {
    const existing = messageUpdatesRef.current.get(messageId) || {};
    messageUpdatesRef.current.set(messageId, { ...existing, ...updates });
  }, []);

  return {
    status,
    typingUsers,
    sendTyping,
    sendStopTyping,
    reconnect,
    updateMessageInPlace,
  };
}

export default useChatWebSocket;
