import { useState } from 'react';
import ChatRoomList from '../components/ChatRoomList';
import TranslationChat from '../components/TranslationChat';

function TranslationChatPage() {
  const [selectedRoom, setSelectedRoom] = useState<{
    roomId: number;
    userType: 'patient' | 'doctor';
  } | null>(null);

  const handleSelectRoom = (roomId: number, userType: 'patient' | 'doctor') => {
    setSelectedRoom({ roomId, userType });
  };

  const handleBackToList = () => {
    setSelectedRoom(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🏥 Patient-Doctor Translation Chat
          </h1>
          <p className="text-gray-600">
            Real-time translation powered by Gemini AI • Break language barriers in healthcare
          </p>
        </div>

        {selectedRoom ? (
          <div>
            <button
              onClick={handleBackToList}
              className="mb-4 text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-2"
            >
              ← Back to Rooms
            </button>
            <TranslationChat roomId={selectedRoom.roomId} userType={selectedRoom.userType} />
          </div>
        ) : (
          <ChatRoomList onSelectRoom={handleSelectRoom} />
        )}

        <div className="mt-8 bg-white rounded-xl p-6 border-2 border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-3">✨ Features</h3>
          <ul className="space-y-2 text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <span>
                <strong>Real-time Translation:</strong> Messages are automatically translated
                between patient and doctor languages
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <span>
                <strong>Context-Aware:</strong> Gemini AI considers conversation history for
                accurate medical terminology
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <span>
                <strong>Multimodal Support:</strong> Send images for AI-powered analysis and
                description
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <span>
                <strong>Multiple Languages:</strong> Support for English, Spanish, French, German,
                Chinese, Arabic, Hindi, and more
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <span>
                <strong>Dual View:</strong> See both original and translated messages for
                transparency
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default TranslationChatPage;
