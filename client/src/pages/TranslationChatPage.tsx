import { useState } from 'react';
import ChatRoomList from '../components/ChatRoomList';
import TranslationChat from '../components/TranslationChat';
import { useAuth } from '../contexts/AuthContext';

function TranslationChatPage() {
  const { user } = useAuth();
  const [selectedRoom, setSelectedRoom] = useState<{
    roomId: number;
    userType: 'patient' | 'doctor';
  } | null>(null);

  // Determine user type from auth context, default to patient
  const getUserType = (): 'patient' | 'doctor' => {
    if (user?.role === 'doctor' || user?.role === 'admin') {
      return 'doctor';
    }
    return 'patient';
  };

  const handleSelectRoom = (roomId: number, userType: 'patient' | 'doctor') => {
    // Use the authenticated user's role if available
    const actualUserType = user ? getUserType() : userType;
    setSelectedRoom({ roomId, userType: actualUserType });
  };

  const handleBackToList = () => {
    setSelectedRoom(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Patient-Doctor Translation Chat</h1>
          <p className="text-gray-600">Break language barriers in healthcare</p>
        </div>

        {selectedRoom ? (
          <div>
            <button
              onClick={handleBackToList}
              className="mb-4 text-gray-900 hover:text-gray-700 font-semibold flex items-center gap-2"
            >
              ← Back to Rooms
            </button>
            <TranslationChat roomId={selectedRoom.roomId} userType={selectedRoom.userType} />
          </div>
        ) : (
          <ChatRoomList onSelectRoom={handleSelectRoom} />
        )}

        <div
          className={`mt-8 grid grid-cols-1 ${!selectedRoom || selectedRoom.userType === 'doctor' ? 'lg:grid-cols-2' : ''} gap-6`}
        >
          {/* Features Block */}
          <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
            <h3 className="text-lg font-bold text-gray-900 mb-3">Features</h3>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start gap-2">
                <span className="text-black font-bold">•</span>
                <span>
                  <strong>Real-time Translation:</strong> Messages are automatically translated
                  between patient and doctor languages
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-black font-bold">•</span>
                <span>
                  <strong>Context-Aware:</strong> AI considers conversation history for accurate
                  medical terminology
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-black font-bold">•</span>
                <span>
                  <strong>Multimodal Support:</strong> Send images for AI-powered analysis and
                  description
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-black font-bold">•</span>
                <span>
                  <strong>Multiple Languages:</strong> Support for English, Spanish, French, German,
                  Chinese, Arabic, Hindi, and more
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-black font-bold">•</span>
                <span>
                  <strong>Speech-to-Text:</strong> Click the microphone to speak your message
                  instead of typing
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TranslationChatPage;
