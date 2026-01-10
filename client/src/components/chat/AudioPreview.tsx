import { VolumeUp, Close } from '@mui/icons-material';
import type { AudioPreviewProps } from './types';

export function AudioPreview({ audioURL, onClear }: AudioPreviewProps) {
  return (
    <div className="flex items-center gap-3 rounded-2xl bg-gray-50 border border-gray-200 px-4 py-3">
      <VolumeUp className="w-5 h-5 text-gray-600" />
      <audio src={audioURL} controls className="flex-1 h-8" />
      <button
        type="button"
        onClick={onClear}
        className="p-1.5 rounded-full hover:bg-gray-200 text-gray-500 hover:text-red-600 transition-colors"
      >
        <Close className="w-4 h-4" />
      </button>
    </div>
  );
}

export default AudioPreview;
