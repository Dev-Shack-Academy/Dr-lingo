import { useState, useEffect, useRef } from 'react';
import ChatService, { ChatRoom, ChatMessage } from '../api/services/ChatService';

interface TranslationChatProps {
  roomId: number;
  userType: 'patient' | 'doctor';
}

function TranslationChat({ roomId, userType }: TranslationChatProps) {
  const [room, setRoom] = useState<ChatRoom | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    loadChatRoom();
    loadMessages();
    // Poll for new messages every 3 seconds
    const interval = setInterval(loadMessages, 3000);
    return () => clearInterval(interval);
  }, [roomId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChatRoom = async () => {
    try {
      const data = await ChatService.getChatRoom(roomId);
      setRoom(data);
    } catch (err) {
      setError('Failed to load chat room');
      console.error(err);
    }
  };

  const loadMessages = async () => {
    try {
      const data = await ChatService.getMessages(roomId);
      setMessages(data);
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newMessage.trim()) return;

    try {
      setLoading(true);
      setError(null);

      await ChatService.sendMessage(roomId, {
        sender_type: userType,
        text: newMessage,
      });

      setNewMessage('');
      await loadMessages();
    } catch (err) {
      setError('Failed to send message');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getLanguageLabel = (lang: string) => {
    const languages: Record<string, string> = {
      en: 'English',
      es: 'Spanish',
      fr: 'French',
      de: 'German',
      zh: 'Chinese',
      ar: 'Arabic',
      hi: 'Hindi',
    };
    return languages[lang] || lang;
  };

  if (!room) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading chat room...</div>
      </div>
    );
  }

  const myLanguage = userType === 'patient' ? room.patient_language : room.doctor_language;
  const otherLanguage = userType === 'patient' ? room.doctor_language : room.patient_language;

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-xl shadow-lg border-2 border-gray-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 rounded-t-xl">
        <h2 className="text-xl font-bold">{room.name}</h2>
        <p className="text-sm text-blue-100">
          You speak {getLanguageLabel(myLanguage)} • Other person speaks{' '}
          {getLanguageLabel(otherLanguage)}
        </p>
        <p className="text-xs text-blue-200 mt-1">
          Role: {userType === 'patient' ? '🏥 Patient' : '👨‍⚕️ Doctor'}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 mt-8">
            No messages yet. Start the conversation!
          </div>
        ) : (
          messages.map((message) => {
            const isMyMessage = message.sender_type === userType;

            return (
              <div
                key={message.id}
                className={`flex ${isMyMessage ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] rounded-lg p-3 ${
                    isMyMessage
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border-2 border-gray-200 text-gray-800'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold opacity-75">
                      {message.sender_type === 'patient' ? '🏥 Patient' : '👨‍⚕️ Doctor'}
                    </span>
                  </div>

                  {/* Original text (what they typed) */}
                  <div className="mb-2">
                    <p className="text-sm font-medium">{message.original_text}</p>
                    <p className="text-xs opacity-60 mt-1">
                      Original ({getLanguageLabel(message.original_language)})
                    </p>
                  </div>

                  {/* Translated text */}
                  {message.translated_text && (
                    <div
                      className={`pt-2 border-t ${isMyMessage ? 'border-blue-400' : 'border-gray-200'}`}
                    >
                      <p className="text-sm italic">{message.translated_text}</p>
                      <p className="text-xs opacity-60 mt-1">
                        Translation ({getLanguageLabel(message.translated_language)})
                      </p>
                    </div>
                  )}

                  {/* Image description if available */}
                  {message.image_description && (
                    <div
                      className={`mt-2 pt-2 border-t ${isMyMessage ? 'border-blue-400' : 'border-gray-200'}`}
                    >
                      <p className="text-xs font-semibold mb-1">📷 Image Analysis:</p>
                      <p className="text-xs">{message.image_description}</p>
                    </div>
                  )}

                  <p className="text-xs opacity-50 mt-2">
                    {new Date(message.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSendMessage}
        className="p-4 bg-white border-t-2 border-gray-200 rounded-b-xl"
      >
        {error && <div className="mb-2 text-sm text-red-600 bg-red-50 p-2 rounded">{error}</div>}

        <div className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder={`Type in ${getLanguageLabel(myLanguage)}...`}
            className="flex-1 px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-600 focus:outline-none"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !newMessage.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>

        <p className="text-xs text-gray-500 mt-2">
          💡 Your message will be automatically translated to {getLanguageLabel(otherLanguage)}
        </p>
      </form>
    </div>
  );
}

export default TranslationChat;
