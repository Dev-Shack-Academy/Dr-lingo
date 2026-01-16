/**
 * Chat-related type definitions
 */

export type RoomType = 'patient_doctor' | 'group' | 'support';
export type SenderType = 'patient' | 'doctor' | 'system';

export interface PatientContextItem {
  id: number;
  name: string;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface PatientContextCollection {
  id: number;
  name: string;
  description: string;
  items: PatientContextItem[];
}

export interface LinkedKnowledgeBase {
  id: number;
  name: string;
  description: string;
  items_count: number;
}

export interface ChatRoom {
  id: number;
  name: string;
  room_type: RoomType;
  patient_language: string;
  doctor_language: string;
  patient_name: string;
  rag_collection: number | null;
  rag_collection_name?: string;
  is_active: boolean;
  has_rag: boolean;
  patient_context?: PatientContextCollection[] | null;
  linked_knowledge_bases?: LinkedKnowledgeBase[] | null;
  message_count?: number;
  last_message?: {
    sender: string;
    text: string;
    created_at: string;
  };
  created_at: string;
  updated_at?: string;
}

export interface ChatMessage {
  id: number;
  room: number;
  sender_type: SenderType;
  original_text: string;
  original_language: string;
  translated_text: string;
  translated_language: string;
  has_image: boolean;
  image_url?: string;
  image_description?: string;
  has_audio: boolean;
  audio_url?: string;
  audio_duration?: number;
  audio_transcription?: string;
  tts_audio_url?: string;
  created_at: string;
}

export interface CreateChatRoomData {
  name: string;
  room_type?: RoomType;
  patient_language: string;
  doctor_language: string;
  patient_name?: string;
  rag_collection?: number;
  is_active?: boolean;
}

export interface UpdateChatRoomData {
  name?: string;
  patient_language?: string;
  doctor_language?: string;
  patient_name?: string;
  rag_collection?: number | null;
  is_active?: boolean;
}

export interface SendMessageData {
  text: string;
  sender_type: SenderType;
  audio_file?: File;
}

export interface TranslationResponse {
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  cultural_notes?: string;
  rag_context?: string;
}

export interface PatientContextData {
  collection_id?: number;
  patient_name: string;
  cultural_background: string;
  medical_history: string;
  language_notes: string;
}
