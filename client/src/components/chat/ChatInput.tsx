import { Mic, Stop, Send } from '@mui/icons-material';
import { RecordingIndicator } from './RecordingIndicator';
import { AudioPreview } from './AudioPreview';
import type { ChatInputProps } from './types';

export function ChatInput({
  newMessage,
  setNewMessage,
  onSendMessage,
  onToggleRecording,
  isRecording,
  recordingDuration,
  audioPreviewURL,
  onClearAudio,
  loading,
  recordedAudio,
  myLanguage,
  getLanguageLabel,
  sendTyping,
  sendStopTyping,
}: ChatInputProps) {
  const isEnglish = myLanguage === 'en';

  return (
    <form onSubmit={onSendMessage} className="p-4 bg-white border-t border-gray-200">
      <div className="max-w-3xl mx-auto space-y-3">
        {/* Recording Indicator */}
        {isRecording && !isEnglish && <RecordingIndicator duration={recordingDuration} />}

        {/* Audio Preview */}
        {audioPreviewURL && <AudioPreview audioURL={audioPreviewURL} onClear={onClearAudio} />}

        {/* Input Row */}
        {!isRecording || isEnglish ? (
          <div className="flex items-end gap-2">
            {/* Mic Button */}
            <button
              type="button"
              onClick={onToggleRecording}
              className={`h-12 w-12 shrink-0 rounded-full flex items-center justify-center transition-all ${
                isRecording
                  ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                  : 'bg-gray-100 hover:bg-black hover:text-white text-gray-700 border border-gray-300'
              }`}
              title={
                isRecording
                  ? isEnglish
                    ? 'Stop speech recognition'
                    : 'Stop recording'
                  : isEnglish
                    ? 'Start speech-to-text'
                    : 'Record audio'
              }
            >
              {isRecording ? <Stop className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            {/* Text Input */}
            <div className="relative flex-1">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => {
                  setNewMessage(e.target.value);
                  if (e.target.value) {
                    sendTyping();
                  } else {
                    sendStopTyping();
                  }
                }}
                onBlur={() => sendStopTyping()}
                placeholder={`Type in ${getLanguageLabel(myLanguage)}...`}
                className="w-full h-12 px-4 pr-14 border border-gray-300 rounded-full focus:border-black focus:ring-2 focus:ring-black/10 focus:outline-none transition-all text-black placeholder:text-gray-400"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || (!newMessage.trim() && !recordedAudio)}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 h-9 w-9 rounded-full bg-black text-white hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          /* Recording State for non-English */
          <div className="flex justify-center">
            <button
              type="button"
              onClick={onToggleRecording}
              className="h-14 w-14 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-colors"
            >
              <Stop className="w-6 h-6" />
            </button>
          </div>
        )}

        {/* Helper Text */}
        <div className="flex items-center justify-between text-xs text-gray-500 px-1">
          <span>Auto-translates to {getLanguageLabel(myLanguage === 'en' ? 'other' : 'en')}</span>
          <span>{isEnglish ? 'Mic: speech-to-text' : 'Mic: record for AI transcription'}</span>
        </div>
      </div>
    </form>
  );
}

export default ChatInput;
