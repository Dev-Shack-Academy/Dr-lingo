import { useState, useEffect, useRef, useCallback } from 'react';
import { Psychology, Info, Refresh } from '@mui/icons-material';
import ChatService, { ChatRoom, ChatMessage } from '../api/services/ChatService';
import PatientContextManager from './PatientContextManager';
import { useToast } from '../contexts/ToastContext';
import { useChatWebSocket } from '../hooks/useChatWebSocket';
import { ChatMessages, ChatInput } from './chat';
import type {
  MessageNewEvent,
  MessageTranslatedEvent,
  MessageTranscribedEvent,
  TTSGeneratedEvent,
  TranslationFailedEvent,
  AudioProcessingFailedEvent,
} from '../types/websocket';

interface TranslationChatProps {
  roomId: number;
  userType: 'patient' | 'doctor';
  onRoomLoaded?: (room: ChatRoom) => void;
  wsStatus?: 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting';
  onWsStatusChange?: (
    status: 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting'
  ) => void;
}

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

function TranslationChat({
  roomId,
  userType,
  onRoomLoaded,
  onWsStatusChange,
}: TranslationChatProps) {
  const [room, setRoom] = useState<ChatRoom | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState<Blob | null>(null);
  const [audioPreviewURL, setAudioPreviewURL] = useState<string | null>(null);
  const [recordingDuration, setRecordingDuration] = useState<number>(0);
  const [doctorAssistance, setDoctorAssistance] = useState<any>(null);
  const [loadingAssistance, setLoadingAssistance] = useState(false);
  const { showError, showWarning } = useToast();

  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingStartTimeRef = useRef<number>(0);
  const loadMessagesRef = useRef<(() => Promise<void>) | null>(null);

  const getLanguageLabel = (lang: string) => LANGUAGES[lang] || lang;

  // Load messages
  const loadMessages = useCallback(async () => {
    try {
      const data = await ChatService.getMessages(roomId);
      setMessages(data);
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  }, [roomId]);

  loadMessagesRef.current = loadMessages;

  // WebSocket handlers
  const handleNewMessage = useCallback((_event: MessageNewEvent) => {
    loadMessagesRef.current?.();
  }, []);

  const handleMessageTranslated = useCallback((event: MessageTranslatedEvent) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === event.message_id
          ? {
              ...msg,
              translated_text: event.translated_text,
              translated_language: event.target_lang,
            }
          : msg
      )
    );
  }, []);

  const handleMessageTranscribed = useCallback((event: MessageTranscribedEvent) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === event.message_id
          ? { ...msg, original_text: event.transcription, audio_transcription: event.transcription }
          : msg
      )
    );
  }, []);

  const handleTTSGenerated = useCallback((event: TTSGeneratedEvent) => {
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === event.message_id ? { ...msg, tts_audio_url: event.audio_url } : msg
      )
    );
  }, []);

  const handleTranslationFailed = useCallback(
    (event: TranslationFailedEvent) => {
      console.error('[ChatWS] Translation failed:', event);
      showError(new Error(event.error), 'Translation Failed');
    },
    [showError]
  );

  const handleAudioProcessingFailed = useCallback(
    (event: AudioProcessingFailedEvent) => {
      console.error('[ChatWS] Audio processing failed:', event);
      showError(new Error(event.error), 'Audio Processing Failed');
    },
    [showError]
  );

  const {
    status: wsStatus,
    typingUsers,
    sendTyping,
    sendStopTyping,
  } = useChatWebSocket({
    roomId,
    userType,
    enabled: !!room,
    onNewMessage: handleNewMessage,
    onMessageTranslated: handleMessageTranslated,
    onMessageTranscribed: handleMessageTranscribed,
    onTTSGenerated: handleTTSGenerated,
    onTranslationFailed: handleTranslationFailed,
    onAudioProcessingFailed: handleAudioProcessingFailed,
    onError: (message) => showError(new Error(message), 'WebSocket Error'),
  });

  // Initial load
  useEffect(() => {
    loadChatRoom();
    loadMessages();
  }, [roomId, loadMessages]);

  // WebSocket disconnect warning
  const wasConnectedRef = useRef(false);
  useEffect(() => {
    if (wsStatus === 'connected') {
      wasConnectedRef.current = true;
    } else if ((wsStatus === 'error' || wsStatus === 'disconnected') && wasConnectedRef.current) {
      showWarning('Real-time connection lost. Please refresh the page.', 'WebSocket Disconnected');
    }
  }, [wsStatus, showWarning]);

  // Cleanup audio URL
  useEffect(() => {
    return () => {
      if (audioPreviewURL) URL.revokeObjectURL(audioPreviewURL);
    };
  }, [audioPreviewURL]);

  const loadChatRoom = async () => {
    try {
      const data = await ChatService.getChatRoom(roomId);
      setRoom(data);
      onRoomLoaded?.(data);
    } catch (err) {
      showError(err, 'Failed to load chat room');
    }
  };

  // Notify parent of ws status changes
  useEffect(() => {
    onWsStatusChange?.(wsStatus);
  }, [wsStatus, onWsStatusChange]);

  const loadDoctorAssistance = async () => {
    if (!room?.rag_collection) return;
    setLoadingAssistance(true);
    try {
      const assistance = await ChatService.getDoctorAssistance(roomId);
      setDoctorAssistance(assistance);
    } catch (err) {
      console.error('Failed to load doctor assistance:', err);
      showError(err, 'Failed to load AI assistance');
      setDoctorAssistance({ status: 'error', message: 'Failed to load AI assistance.' });
    } finally {
      setLoadingAssistance(false);
    }
  };

  // Audio Recording (non-English)
  const startAudioRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunksRef.current = [];
      recordingStartTimeRef.current = Date.now();

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const duration = Date.now() - recordingStartTimeRef.current;
        if (duration < 1000) {
          showWarning(
            'Recording too short. Please speak for at least 1 second.',
            'Recording Error'
          );
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (audioBlob.size < 500) {
          showWarning('No audio detected. Please check your microphone.', 'Recording Error');
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        setRecordedAudio(audioBlob);
        setAudioPreviewURL(URL.createObjectURL(audioBlob));
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);

      const durationInterval = setInterval(() => {
        setRecordingDuration(Date.now() - recordingStartTimeRef.current);
      }, 100);
      (mediaRecorder as any).durationInterval = durationInterval;
    } catch (err) {
      console.error('Failed to start audio recording:', err);
      showError(err, 'Microphone access denied');
    }
  };

  const stopAudioRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      const interval = (mediaRecorderRef.current as any).durationInterval;
      if (interval) clearInterval(interval);
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Speech Recognition (English)
  const startSpeechRecognition = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      showWarning('Speech recognition not supported. Try Chrome or Edge.', 'Not Supported');
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) final += event.results[i][0].transcript + ' ';
      }
      if (final) setNewMessage((prev) => prev + final);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
      showError(new Error(event.error), 'Speech recognition failed');
    };

    recognition.onend = () => setIsRecording(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
  };

  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleToggleRecording = () => {
    if (isRecording) {
      myLanguage === 'en' ? stopSpeechRecognition() : stopAudioRecording();
    } else {
      myLanguage === 'en' ? startSpeechRecognition() : startAudioRecording();
    }
  };

  const handleClearAudio = () => {
    if (audioPreviewURL) URL.revokeObjectURL(audioPreviewURL);
    setRecordedAudio(null);
    setAudioPreviewURL(null);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() && !recordedAudio) return;

    try {
      setLoading(true);
      const messageData: any = { sender_type: userType, text: newMessage || '[Voice Message]' };

      if (recordedAudio) {
        const base64Audio = await ChatService.audioBlobToBase64(recordedAudio);
        messageData.audio = base64Audio;
      }

      await ChatService.sendMessage(roomId, messageData);
      setNewMessage('');
      handleClearAudio();
      await loadMessages();
    } catch (err) {
      showError(err, 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  if (!room) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading chat room...</div>
      </div>
    );
  }

  const myLanguage = userType === 'patient' ? room.patient_language : room.doctor_language;
  // otherLanguage now handled in TranslationChatPage header

  return (
    <div className="flex gap-0 h-full">
      {/* Main Chat */}
      <div className="flex-1 flex flex-col bg-white overflow-hidden">
        <ChatMessages
          messages={messages}
          userType={userType}
          getLanguageLabel={getLanguageLabel}
          typingUsers={typingUsers}
        />

        <ChatInput
          newMessage={newMessage}
          setNewMessage={setNewMessage}
          onSendMessage={handleSendMessage}
          onToggleRecording={handleToggleRecording}
          isRecording={isRecording}
          recordingDuration={recordingDuration}
          audioPreviewURL={audioPreviewURL}
          onClearAudio={handleClearAudio}
          loading={loading}
          recordedAudio={recordedAudio}
          myLanguage={myLanguage}
          getLanguageLabel={getLanguageLabel}
          sendTyping={sendTyping}
          sendStopTyping={sendStopTyping}
        />
      </div>

      {/* RAG Context Panel */}
      {room.rag_collection && userType === 'doctor' && (
        <div className="w-80 bg-white border-l border-gray-200 overflow-hidden flex flex-col">
          <div className="bg-gradient-to-r from-purple-600 to-purple-700 text-white p-4">
            <div className="flex items-center gap-2 mb-1">
              <Psychology className="w-5 h-5" />
              <h3 className="font-bold text-lg">Patient Context</h3>
            </div>
            <p className="text-xs text-purple-100">RAG-Enhanced Information</p>
          </div>

          <div className="flex-1 p-4 space-y-3 overflow-y-auto">
            <PatientContextManager
              roomId={roomId}
              roomName={room.name}
              currentCollection={room.rag_collection}
              onUpdate={loadChatRoom}
            />

            <button
              onClick={loadDoctorAssistance}
              disabled={loadingAssistance}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold px-4 py-3 rounded-lg transition-colors disabled:bg-gray-400 text-sm flex items-center justify-center gap-2"
            >
              {loadingAssistance ? (
                <>
                  <Refresh className="w-4 h-4 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <Psychology className="w-4 h-4" />
                  Get AI Assistance
                </>
              )}
            </button>

            {doctorAssistance?.status === 'success' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 max-h-96 overflow-y-auto">
                <div className="flex items-center gap-2 mb-2">
                  <Psychology className="w-4 h-4 text-blue-600" />
                  <p className="text-xs font-semibold text-blue-900">AI Suggestions</p>
                </div>
                <div className="text-xs text-blue-800 whitespace-pre-wrap leading-relaxed">
                  {doctorAssistance.assistance}
                </div>
                {doctorAssistance.sources?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <p className="text-xs font-semibold text-blue-900 mb-2">Sources</p>
                    <div className="space-y-1">
                      {doctorAssistance.sources.map((source: any, idx: number) => (
                        <div key={idx} className="flex items-start gap-2 text-xs text-blue-700">
                          <span className="text-blue-500">•</span>
                          <span>
                            {source.name} ({(source.similarity * 100).toFixed(0)}% match)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {doctorAssistance?.status === 'error' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-red-600" />
                  <p className="text-xs font-semibold text-red-900">Error</p>
                </div>
                <p className="text-xs text-red-700 mt-1">{doctorAssistance.message}</p>
              </div>
            )}

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-purple-900 mb-1">RAG Active</p>
                  <p className="text-xs text-purple-700 leading-relaxed">
                    Translations are enhanced with patient context for better accuracy.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TranslationChat;
