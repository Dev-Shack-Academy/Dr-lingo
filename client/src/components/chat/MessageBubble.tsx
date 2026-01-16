import { useState, useRef } from 'react';
import { VolumeUp, Mic } from '@mui/icons-material';
import type { MessageBubbleProps } from './types';

export function MessageBubble({ message, isMyMessage, getLanguageLabel }: MessageBubbleProps) {
  const [showOriginal, setShowOriginal] = useState(false);
  const [isPlayingTTS, setIsPlayingTTS] = useState(false);
  const ttsAudioRef = useRef<HTMLAudioElement | null>(null);

  const isTranslating =
    message.translated_text === '[Translating...]' ||
    message.translated_text === '[Processing...]' ||
    message.original_text === '[Processing audio...]';

  const displayText = showOriginal ? message.original_text : message.translated_text;
  const displayLang = showOriginal ? message.original_language : message.translated_language;

  const handlePlayTTS = () => {
    if (!message.tts_audio_url) return;

    if (isPlayingTTS && ttsAudioRef.current) {
      ttsAudioRef.current.pause();
      ttsAudioRef.current.currentTime = 0;
      setIsPlayingTTS(false);
    } else {
      if (!ttsAudioRef.current) {
        ttsAudioRef.current = new Audio(message.tts_audio_url);
        ttsAudioRef.current.onended = () => setIsPlayingTTS(false);
        ttsAudioRef.current.onerror = () => setIsPlayingTTS(false);
      }
      ttsAudioRef.current.play();
      setIsPlayingTTS(true);
    }
  };

  return (
    <div className={`flex gap-3 ${isMyMessage ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`flex max-w-[80%] flex-col gap-2 rounded-2xl px-4 py-3 shadow-sm relative group ${
          isMyMessage ? 'bg-black text-white' : 'bg-white border border-gray-200 text-gray-900'
        }`}
      >
        {/* Toggle Button */}
        {message.translated_text && !isTranslating && (
          <button
            onClick={() => setShowOriginal(!showOriginal)}
            className={`absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 rounded text-xs font-medium ${
              isMyMessage
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            {showOriginal ? 'Translation' : 'Original'}
          </button>
        )}

        {/* Header */}
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-semibold uppercase tracking-wide ${
              isMyMessage ? 'text-gray-300' : 'text-gray-500'
            }`}
          >
            {message.sender_type === 'patient' ? 'Patient' : 'Doctor'}
          </span>
          {message.has_audio && <Mic className="w-3 h-3 opacity-60" />}
          {isTranslating && (
            <span
              className={`text-xs flex items-center gap-1 ${isMyMessage ? 'text-blue-300' : 'text-blue-500'}`}
            >
              <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Translating...
            </span>
          )}
        </div>

        {/* Audio playback */}
        {message.has_audio && message.audio_url && (
          <div className={`p-2 rounded-lg ${isMyMessage ? 'bg-gray-800' : 'bg-gray-50'}`}>
            <div className="flex items-center gap-2">
              <VolumeUp className="w-4 h-4 opacity-60" />
              <audio src={message.audio_url} controls className="h-8 flex-1" />
            </div>
          </div>
        )}

        {/* Message text */}
        <p className="text-sm leading-relaxed">
          {isTranslating ? message.original_text : displayText || message.original_text}
        </p>

        {/* Language label */}
        {!isTranslating && (
          <div className="flex items-center justify-between mt-1">
            <span className={`text-xs ${isMyMessage ? 'text-gray-400' : 'text-gray-500'}`}>
              {showOriginal ? 'Original' : 'Translation'}: {getLanguageLabel(displayLang)}
            </span>
          </div>
        )}

        {/* TTS Play Button */}
        {!isTranslating && message.tts_audio_url && (
          <button
            onClick={handlePlayTTS}
            className={`mt-2 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              isMyMessage
                ? isPlayingTTS
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                : isPlayingTTS
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            <VolumeUp className="w-3 h-3" />
            {isPlayingTTS ? 'Stop' : 'Listen'}
          </button>
        )}

        {/* Timestamp */}
        <span className={`text-xs mt-1 ${isMyMessage ? 'text-gray-400' : 'text-gray-400'}`}>
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>

        {/* Image description */}
        {message.image_description && (
          <div
            className={`mt-2 pt-2 border-t ${isMyMessage ? 'border-gray-700' : 'border-gray-200'}`}
          >
            <p className="text-xs font-semibold mb-1">Image Analysis</p>
            <p className="text-xs opacity-80">{message.image_description}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
