import type { ChatMessage } from '../../api/services/ChatService';

export interface MessageBubbleProps {
  message: ChatMessage;
  isMyMessage: boolean;
  getLanguageLabel: (lang: string) => string;
}

export interface ChatInputProps {
  newMessage: string;
  setNewMessage: (message: string) => void;
  onSendMessage: (e: React.FormEvent) => void;
  onToggleRecording: () => void;
  isRecording: boolean;
  recordingDuration: number;
  audioPreviewURL: string | null;
  onClearAudio: () => void;
  loading: boolean;
  recordedAudio: Blob | null;
  myLanguage: string;
  getLanguageLabel: (lang: string) => string;
  sendTyping: () => void;
  sendStopTyping: () => void;
}

export interface ChatMessagesProps {
  messages: ChatMessage[];
  userType: 'patient' | 'doctor';
  getLanguageLabel: (lang: string) => string;
  typingUsers: Array<{ senderType: string }>;
}

export interface TypingIndicatorProps {
  typingUsers: Array<{ senderType: string }>;
}

export interface RecordingIndicatorProps {
  duration: number;
}

export interface AudioPreviewProps {
  audioURL: string;
  onClear: () => void;
}

export interface RoleSelectionDialogProps {
  open: boolean;
  onClose: () => void;
  onSelectRole: (role: 'patient' | 'doctor') => void;
  roomName: string;
  isAdmin: boolean;
}
