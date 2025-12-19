import { useState, useEffect, useRef } from 'react';
import { Mic, Stop, VolumeUp, Psychology, Info, Refresh } from '@mui/icons-material';
import ChatService, { ChatRoom, ChatMessage } from '../api/services/ChatService';
import PatientContextManager from './PatientContextManager';
import { useToast } from '../contexts/ToastContext';

interface MessageBubbleProps {
  message: ChatMessage;
  isMyMessage: boolean;
  getLanguageLabel: (lang: string) => string;
}

function MessageBubble({ message, isMyMessage, getLanguageLabel }: MessageBubbleProps) {
  const [showOriginal, setShowOriginal] = useState(false);

  // Determine what to display
  const displayText = showOriginal ? message.original_text : message.translated_text;
  const displayLang = showOriginal ? message.original_language : message.translated_language;

  return (
    <div className={`flex ${isMyMessage ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] rounded-lg p-4 shadow-sm relative group ${
          isMyMessage ? 'bg-black text-white' : 'bg-white border border-gray-200 text-gray-900'
        }`}
      >
        {/* Toggle Button - Shows on hover */}
        {message.translated_text && (
          <button
            onClick={() => setShowOriginal(!showOriginal)}
            className={`absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 rounded text-xs font-medium ${
              isMyMessage
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            {showOriginal ? 'Show Translation' : 'Show Original'}
          </button>
        )}

        <div className="flex items-center gap-2 mb-3">
          <span
            className={`text-xs font-bold uppercase tracking-wide ${
              isMyMessage ? 'text-gray-300' : 'text-gray-600'
            }`}
          >
            {message.sender_type === 'patient' ? 'Patient' : 'Doctor'}
          </span>
          <span className={`text-xs ${isMyMessage ? 'text-gray-400' : 'text-gray-500'}`}>
            {new Date(message.created_at).toLocaleTimeString()}
          </span>
        </div>

        {/* Audio playback */}
        {message.has_audio && message.audio_url && (
          <div className={`mb-3 p-2 rounded ${isMyMessage ? 'bg-gray-800' : 'bg-gray-50'}`}>
            <div className="flex items-center gap-2">
              <VolumeUp className="w-4 h-4" />
              <audio src={message.audio_url} controls className="h-8 flex-1" />
            </div>
          </div>
        )}

        {/* Message text - Shows translation by default, original on toggle */}
        <div>
          <p className="text-base leading-relaxed">{displayText || message.original_text}</p>
          <p className={`text-xs mt-1 ${isMyMessage ? 'text-gray-400' : 'text-gray-500'}`}>
            {showOriginal ? 'Original' : 'Translation'}: {getLanguageLabel(displayLang)}
          </p>
        </div>

        {/* Image description */}
        {message.image_description && (
          <div
            className={`mt-3 pt-3 border-t ${isMyMessage ? 'border-gray-700' : 'border-gray-200'}`}
          >
            <p className="text-xs font-semibold mb-1">Image Analysis</p>
            <p className="text-xs opacity-80">{message.image_description}</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface TranslationChatProps {
  roomId: number;
  userType: 'patient' | 'doctor';
}

function TranslationChat({ roomId, userType }: TranslationChatProps) {
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

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingStartTimeRef = useRef<number>(0);

  useEffect(() => {
    loadChatRoom();
    loadMessages();
    const interval = setInterval(loadMessages, 3000);
    return () => clearInterval(interval);
  }, [roomId]);

  useEffect(() => {
    // Cleanup audio URL on unmount or when it changes
    return () => {
      if (audioPreviewURL) {
        URL.revokeObjectURL(audioPreviewURL);
      }
    };
  }, [audioPreviewURL]);

  const loadChatRoom = async () => {
    try {
      const data = await ChatService.getChatRoom(roomId);
      setRoom(data);
    } catch (err) {
      showError(err, 'Failed to load chat room');
    }
  };

  const loadDoctorAssistance = async () => {
    if (!room?.rag_collection) return;

    setLoadingAssistance(true);
    try {
      const assistance = await ChatService.getDoctorAssistance(roomId);
      console.log('Doctor assistance loaded:', assistance);
      setDoctorAssistance(assistance);
    } catch (err) {
      console.error('Failed to load doctor assistance:', err);
      showError(err, 'Failed to load AI assistance');
      setDoctorAssistance({
        status: 'error',
        message: 'Failed to load AI assistance. Please try again.',
      });
    } finally {
      setLoadingAssistance(false);
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

  // Audio Recording (for non-English languages)
  const startAudioRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

      audioChunksRef.current = [];
      recordingStartTimeRef.current = Date.now();

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const recordingDuration = Date.now() - recordingStartTimeRef.current;

        // Check minimum recording duration (1 second)
        if (recordingDuration < 1000) {
          showWarning(
            'Recording too short. Please speak for at least 1 second.',
            'Recording Error'
          );
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        console.log('Audio blob size:', audioBlob.size, 'bytes');

        // Check if audio blob is too small (likely empty) - reduced threshold
        if (audioBlob.size < 500) {
          showWarning(
            'No audio detected. Please check your microphone and try again.',
            'Recording Error'
          );
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        setRecordedAudio(audioBlob);
        setAudioPreviewURL(URL.createObjectURL(audioBlob));

        // Stop all tracks to release microphone
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);

      // Update recording duration every 100ms
      const durationInterval = setInterval(() => {
        setRecordingDuration(Date.now() - recordingStartTimeRef.current);
      }, 100);

      // Store interval ID for cleanup
      (mediaRecorder as any).durationInterval = durationInterval;
    } catch (err) {
      console.error('Failed to start audio recording:', err);
      showError(err, 'Microphone access denied or not available');
    }
  };

  const stopAudioRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      // Clear duration interval
      const durationInterval = (mediaRecorderRef.current as any).durationInterval;
      if (durationInterval) {
        clearInterval(durationInterval);
      }

      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Speech-to-Text Recognition (for English only)
  const startSpeechRecognition = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      showWarning(
        'Speech recognition not supported in this browser. Try Chrome or Edge.',
        'Not Supported'
      );
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript + ' ';
        } else {
          interim += transcript;
        }
      }

      if (final) {
        setNewMessage((prev) => prev + final);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
      showError(new Error(event.error), 'Speech recognition failed');
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

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
      // Stop recording based on language
      if (myLanguage === 'en') {
        stopSpeechRecognition();
      } else {
        stopAudioRecording();
      }
    } else {
      // Start recording based on language
      if (myLanguage === 'en') {
        startSpeechRecognition();
      } else {
        startAudioRecording();
      }
    }
  };

  const handleClearAudio = () => {
    if (audioPreviewURL) {
      URL.revokeObjectURL(audioPreviewURL);
    }
    setRecordedAudio(null);
    setAudioPreviewURL(null);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() && !recordedAudio) return;

    try {
      setLoading(true);

      const messageData: any = {
        sender_type: userType,
        text: newMessage || '[Voice Message]',
      };

      // Add audio if recorded (for non-English languages)
      if (recordedAudio) {
        console.log('Converting audio blob to base64, size:', recordedAudio.size);
        const base64Audio = await ChatService.audioBlobToBase64(recordedAudio);
        messageData.audio = base64Audio;
        console.log('Base64 audio length:', base64Audio.length);
      }

      console.log('Sending message with data:', {
        ...messageData,
        audio: messageData.audio ? `[${messageData.audio.length} chars]` : undefined,
      });

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

  const getLanguageLabel = (lang: string) => {
    const languages: Record<string, string> = {
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
    <div className="flex gap-4">
      {/* Main Chat */}
      <div className="flex-1 flex flex-col h-[700px] bg-white rounded-lg shadow-xl border border-gray-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white p-6 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">{room.name}</h2>
              <div className="flex items-center gap-4 text-sm">
                <span className="bg-white/10 px-3 py-1 rounded-full">
                  You: {getLanguageLabel(myLanguage)}
                </span>
                <span className="text-gray-400">→</span>
                <span className="bg-white/10 px-3 py-1 rounded-full">
                  Other: {getLanguageLabel(otherLanguage)}
                </span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-300 mb-1">Your Role</div>
              <div className="bg-white/20 px-4 py-2 rounded-lg font-semibold">
                {userType === 'patient' ? 'Patient' : 'Doctor'}
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-gray-400 text-lg mb-2">No messages yet</div>
              <div className="text-gray-500 text-sm">Start the conversation below</div>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isMyMessage={message.sender_type === userType}
                getLanguageLabel={getLanguageLabel}
              />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form
          onSubmit={handleSendMessage}
          className="p-6 bg-white border-t border-gray-200 rounded-b-lg"
        >
          {/* Recording Indicator */}
          {isRecording && myLanguage !== 'en' && (
            <div className="mb-3 p-3 bg-red-50 rounded-lg border border-red-200 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-red-700">
                  Recording... {(recordingDuration / 1000).toFixed(1)}s
                </span>
                <span className="text-xs text-red-600">(Speak clearly for at least 1 second)</span>
              </div>
            </div>
          )}

          {/* Audio Preview */}
          {audioPreviewURL && (
            <div className="mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center gap-3">
                <VolumeUp className="w-5 h-5 text-purple-600" />
                <audio src={audioPreviewURL} controls className="flex-1 h-8" />
                <button
                  type="button"
                  onClick={handleClearAudio}
                  className="text-red-600 hover:text-red-700 text-sm font-medium"
                >
                  Remove
                </button>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder={`Type your message in ${getLanguageLabel(myLanguage)}...`}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none transition-all text-black placeholder:text-gray-400"
              disabled={loading}
            />

            {/* Speech-to-Text / Audio Recording Button */}
            <button
              type="button"
              onClick={handleToggleRecording}
              className={`p-3 rounded-lg transition-colors ${
                isRecording
                  ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                  : 'bg-purple-600 hover:bg-purple-700 text-white'
              }`}
              title={
                isRecording
                  ? myLanguage === 'en'
                    ? 'Stop speech recognition'
                    : 'Stop audio recording'
                  : myLanguage === 'en'
                    ? 'Start speech-to-text'
                    : 'Record audio for AI transcription'
              }
            >
              {isRecording ? <Stop className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            <button
              type="submit"
              disabled={loading || (!newMessage.trim() && !recordedAudio)}
              className="bg-black hover:bg-gray-800 text-white font-semibold px-8 py-3 rounded-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>

          <div className="flex items-center justify-between mt-3">
            <p className="text-xs text-gray-500">
              Messages are automatically translated to {getLanguageLabel(otherLanguage)}
            </p>
            <p className="text-xs text-gray-500">
              {myLanguage === 'en'
                ? 'Click microphone for speech-to-text'
                : 'Click microphone to record audio'}
            </p>
          </div>
        </form>
      </div>

      {/* RAG Context Panel */}
      {room.rag_collection && userType === 'doctor' && (
        <div className="w-80 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden flex flex-col h-[700px]">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-purple-700 text-white p-4">
            <div className="flex items-center gap-2 mb-1">
              <Psychology className="w-5 h-5" />
              <h3 className="font-bold text-lg">Patient Context</h3>
            </div>
            <p className="text-xs text-purple-100">RAG-Enhanced Information</p>
          </div>

          {/* Content */}
          <div className="flex-1 p-4 space-y-3 overflow-y-auto">
            {/* Patient Context Manager */}
            <PatientContextManager
              roomId={roomId}
              roomName={room.name}
              currentCollection={room.rag_collection}
              onUpdate={loadChatRoom}
            />

            {/* Doctor Assistance Button */}
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

            {/* AI Suggestions or Error */}
            {doctorAssistance && doctorAssistance.status === 'success' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 max-h-96 overflow-y-auto">
                <div className="flex items-center gap-2 mb-2">
                  <Psychology className="w-4 h-4 text-blue-600" />
                  <p className="text-xs font-semibold text-blue-900">AI Suggestions</p>
                </div>
                <div className="text-xs text-blue-800 whitespace-pre-wrap leading-relaxed">
                  {doctorAssistance.assistance}
                </div>
                {doctorAssistance.sources && doctorAssistance.sources.length > 0 && (
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

            {doctorAssistance && doctorAssistance.status === 'error' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-red-600" />
                  <p className="text-xs font-semibold text-red-900">Error</p>
                </div>
                <p className="text-xs text-red-700 mt-1">{doctorAssistance.message}</p>
              </div>
            )}

            {/* Info Banner */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs font-semibold text-purple-900 mb-1">RAG Active</p>
                  <p className="text-xs text-purple-700 leading-relaxed">
                    Translations are enhanced with cultural and medical context from the patient
                    profile.
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
