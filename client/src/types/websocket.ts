/**
 * WebSocket-related type definitions
 */

export type WebSocketStatus =
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'disconnected'
  | 'error';

export interface WebSocketMessage<T = unknown> {
  type: string;
  [key: string]: T | string;
}

// Events received from server
export interface ConnectionEstablishedEvent {
  type: 'connection.established';
  room_id: number;
  user_id: number;
  message: string;
}

export interface MessageNewEvent {
  type: 'message.new';
  message_id: number;
  room_id: number;
  sender_type: 'patient' | 'doctor';
  original_text: string;
  has_audio: boolean;
  timestamp: string;
}

export interface MessageTranslatedEvent {
  type: 'message.translated';
  message_id: number;
  room_id: number;
  translated_text: string;
  target_lang: string;
}

export interface MessageTranscribedEvent {
  type: 'message.transcribed';
  message_id: number;
  room_id: number;
  transcription: string;
  detected_language: string;
}

export interface TTSGeneratedEvent {
  type: 'tts.generated';
  message_id: number;
  room_id: number;
  audio_url: string;
}

export interface UserTypingEvent {
  type: 'user.typing';
  user_id: number;
  sender_type: 'patient' | 'doctor';
}

export interface UserStoppedTypingEvent {
  type: 'user.stopped_typing';
  user_id: number;
}

export interface UserDisconnectedEvent {
  type: 'user.disconnected';
  user_id: number;
}

export interface PongEvent {
  type: 'pong';
  timestamp: number;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
}

// Union type for all server events
export type ServerEvent =
  | ConnectionEstablishedEvent
  | MessageNewEvent
  | MessageTranslatedEvent
  | MessageTranscribedEvent
  | TTSGeneratedEvent
  | UserTypingEvent
  | UserStoppedTypingEvent
  | UserDisconnectedEvent
  | PongEvent
  | ErrorEvent;

// Events sent to server
export interface TypingClientEvent {
  type: 'typing';
}

export interface StopTypingClientEvent {
  type: 'stop_typing';
}

export interface PingClientEvent {
  type: 'ping';
}

export type ClientEvent = TypingClientEvent | StopTypingClientEvent | PingClientEvent;

// WebSocket hook options
export interface UseWebSocketOptions {
  url: string;
  onMessage?: (event: ServerEvent) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

export interface UseWebSocketReturn {
  status: WebSocketStatus;
  send: (message: ClientEvent) => void;
  disconnect: () => void;
  reconnect: () => void;
}
