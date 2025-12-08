import apiClient from '../apiClient';

export interface ChatRoom {
  id: number;
  name: string;
  room_type: string;
  patient_language: string;
  doctor_language: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count?: number;
  last_message?: {
    text: string;
    sender: string;
    created_at: string;
  };
}

export interface ChatMessage {
  id: number;
  room: number;
  sender_type: 'patient' | 'doctor';
  original_text: string;
  original_language: string;
  translated_text: string;
  translated_language: string;
  has_image: boolean;
  image_url?: string;
  image_description?: string;
  created_at: string;
}

export interface SendMessageRequest {
  sender_type: 'patient' | 'doctor';
  text: string;
  image?: string;
}

class ChatService {
  // Get all chat rooms
  async getChatRooms(): Promise<ChatRoom[]> {
    const response = await apiClient.get('/chat-rooms/');
    return response.data;
  }

  // Get a specific chat room with messages
  async getChatRoom(id: number): Promise<ChatRoom> {
    const response = await apiClient.get(`/chat-rooms/${id}/`);
    return response.data;
  }

  // Create a new chat room
  async createChatRoom(data: Partial<ChatRoom>): Promise<ChatRoom> {
    const response = await apiClient.post('/chat-rooms/', data);
    return response.data;
  }

  // Send a message in a chat room
  async sendMessage(roomId: number, data: SendMessageRequest): Promise<ChatMessage> {
    const response = await apiClient.post(`/chat-rooms/${roomId}/send_message/`, data);
    return response.data;
  }

  // Get messages for a room
  async getMessages(roomId: number): Promise<ChatMessage[]> {
    const response = await apiClient.get(`/messages/?room_id=${roomId}`);
    return response.data;
  }

  // Delete a chat room
  async deleteChatRoom(id: number): Promise<void> {
    await apiClient.delete(`/chat-rooms/${id}/`);
  }
}

export default new ChatService();
