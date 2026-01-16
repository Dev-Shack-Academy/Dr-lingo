import type { TypingIndicatorProps } from './types';

export function TypingIndicator({ typingUsers }: TypingIndicatorProps) {
  if (typingUsers.length === 0) return null;

  return (
    <div className="flex justify-start">
      <div className="bg-gray-100 rounded-2xl px-4 py-3 text-sm text-gray-600">
        <span className="inline-flex items-center gap-2">
          <span className="flex gap-1">
            <span
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '0ms' }}
            />
            <span
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '150ms' }}
            />
            <span
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '300ms' }}
            />
          </span>
          <span>{typingUsers[0].senderType === 'patient' ? 'Patient' : 'Doctor'} is typing...</span>
        </span>
      </div>
    </div>
  );
}

export default TypingIndicator;
