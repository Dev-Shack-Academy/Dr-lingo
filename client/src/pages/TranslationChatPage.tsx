import { useState } from 'react';
import { ArrowBack, Wifi, WifiOff, Person, LocalHospital } from '@mui/icons-material';
import ChatRoomList from '../components/ChatRoomList';
import TranslationChat from '../components/TranslationChat';
import type { ChatRoom } from '../api/services/ChatService';

const LANGUAGES: Record<string, string> = {
  en: 'English',
  es: 'Spanish',
  fr: 'French',
  de: 'German',
  zh: 'Chinese',
  ar: 'Arabic',
  hi: 'Hindi',
  pt: 'Portuguese',
  ru: 'Russian',
  ja: 'Japanese',
  af: 'Afrikaans',
  zu: 'Zulu',
  xh: 'Xhosa',
  st: 'Sesotho',
  tn: 'Setswana',
};

function TranslationChatPage() {
  const [selectedRoom, setSelectedRoom] = useState<{
    roomId: number;
    userType: 'patient' | 'doctor';
  } | null>(null);
  const [room, setRoom] = useState<ChatRoom | null>(null);
  const [wsStatus, setWsStatus] = useState<
    'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting'
  >('connecting');

  const handleSelectRoom = (roomId: number, userType: 'patient' | 'doctor') => {
    setSelectedRoom({ roomId, userType });
  };

  const handleBackToList = () => {
    setSelectedRoom(null);
    setRoom(null);
  };

  const getLanguageLabel = (lang: string) => LANGUAGES[lang] || lang;

  // Full screen chat view
  if (selectedRoom) {
    const myLanguage = room
      ? selectedRoom.userType === 'patient'
        ? room.patient_language
        : room.doctor_language
      : '';
    const otherLanguage = room
      ? selectedRoom.userType === 'patient'
        ? room.doctor_language
        : room.patient_language
      : '';

    return (
      <div className="h-screen flex flex-col bg-gray-50">
        {/* Chat header bar */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={handleBackToList}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium transition-colors"
            >
              <ArrowBack className="w-5 h-5" />
            </button>
            {room && (
              <div className="flex items-center gap-3">
                <h1 className="font-semibold text-gray-900">{room.name}</h1>
                <span className="text-gray-300">|</span>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span className="bg-gray-100 px-2 py-0.5 rounded">
                    {getLanguageLabel(myLanguage)}
                  </span>
                  <span className="text-gray-400">→</span>
                  <span className="bg-gray-100 px-2 py-0.5 rounded">
                    {getLanguageLabel(otherLanguage)}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-4">
            {/* Role badge */}
            <div className="flex items-center gap-1.5 bg-black text-white px-3 py-1.5 rounded-full text-sm font-medium">
              {selectedRoom.userType === 'patient' ? (
                <>
                  <Person className="w-4 h-4" /> Patient
                </>
              ) : (
                <>
                  <LocalHospital className="w-4 h-4" /> Doctor
                </>
              )}
            </div>
          </div>
        </div>

        {/* Full height chat */}
        <div className="flex-1 overflow-hidden">
          <TranslationChat
            roomId={selectedRoom.roomId}
            userType={selectedRoom.userType}
            onRoomLoaded={setRoom}
            onWsStatusChange={setWsStatus}
          />
        </div>
      </div>
    );
  }

  // Room list view
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Patient-Doctor Translation Chat</h1>
          <p className="text-gray-600">Break language barriers in healthcare</p>
        </div>
        <ChatRoomList onSelectRoom={handleSelectRoom} />
      </div>
    </div>
  );
}

export default TranslationChatPage;
