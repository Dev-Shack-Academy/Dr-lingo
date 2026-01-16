import ApiClient from '../ApiClient';
import routes from '../routes';
import type {
  ChatRoom,
  ChatMessage,
  CreateChatRoomData,
  SendMessageData,
  PatientContextData,
  SenderType,
  PaginatedResponse,
} from '../../types';

// Re-export types for backward compatibility
export type { ChatRoom, ChatMessage, CreateChatRoomData, SendMessageData, SenderType };

// Legacy interface for backward compatibility
export interface SendMessageRequest {
  sender_type: SenderType;
  text: string;
  image?: string;
  audio?: string; // base64 encoded audio
}

const ChatService = {
  // Get all chat rooms
  getChatRooms: async (): Promise<ChatRoom[]> => {
    const response = await ApiClient.get<PaginatedResponse<ChatRoom> | ChatRoom[]>(
      routes.CHAT_ROOMS
    );
    // Handle paginated response from Django REST Framework
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results;
    }
    // Handle direct array response
    return Array.isArray(response) ? response : [];
  },

  // Get a specific chat room with messages
  getChatRoom: async (id: number): Promise<ChatRoom> =>
    ApiClient.get<ChatRoom>(`${routes.CHAT_ROOMS}${id}/`),

  // Create a new chat room
  createChatRoom: async (data: CreateChatRoomData): Promise<ChatRoom> =>
    ApiClient.post<ChatRoom>(routes.CHAT_ROOMS, data),

  // Send a message in a chat room
  sendMessage: async (roomId: number, data: SendMessageRequest): Promise<ChatMessage> =>
    ApiClient.post<ChatMessage>(`${routes.CHAT_ROOMS}${roomId}/send_message/`, data),

  // Get messages for a room
  getMessages: async (roomId: number): Promise<ChatMessage[]> => {
    const response = await ApiClient.get<PaginatedResponse<ChatMessage> | ChatMessage[]>(
      `${routes.MESSAGES}?room_id=${roomId}`
    );
    // Handle paginated response from Django REST Framework
    if (response && typeof response === 'object' && 'results' in response) {
      return response.results;
    }
    // Handle direct array response
    return Array.isArray(response) ? response : [];
  },

  // Delete a chat room
  deleteChatRoom: async (id: number): Promise<void> =>
    ApiClient.delete<void>(`${routes.CHAT_ROOMS}${id}/`),

  // Convert audio blob to base64
  audioBlobToBase64: async (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        // Remove the data URL prefix (e.g., "data:audio/webm;base64,")
        const base64Data = base64.split(',')[1];
        resolve(base64Data);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  },

  // Add patient context to RAG collection
  addPatientContext: async (
    roomId: number,
    data: PatientContextData
  ): Promise<{ success: boolean; message: string }> =>
    ApiClient.post(`${routes.CHAT_ROOMS}${roomId}/add_patient_context/`, data),

  // Get doctor assistance from RAG
  getDoctorAssistance: async (
    roomId: number
  ): Promise<{
    assistance: string;
    context: string[];
    suggestions: string[];
  }> => ApiClient.get(`${routes.CHAT_ROOMS}${roomId}/get_doctor_assistance/`),
};

export default ChatService;
