import type { RecordingIndicatorProps } from './types';

export function RecordingIndicator({ duration }: RecordingIndicatorProps) {
  return (
    <div className="flex items-center gap-4 rounded-2xl bg-red-50 border border-red-200 px-6 py-4 animate-pulse">
      <div className="flex items-center gap-3 flex-1">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500">
          <div className="w-3 h-3 bg-white rounded-full animate-pulse" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-red-700">Recording...</p>
          <p className="text-xs text-red-600">
            {(duration / 1000).toFixed(1)}s • Speak clearly for at least 1 second
          </p>
        </div>
      </div>
    </div>
  );
}

export default RecordingIndicator;
