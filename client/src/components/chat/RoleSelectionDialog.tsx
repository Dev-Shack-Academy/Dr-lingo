import { Close, Person, LocalHospital } from '@mui/icons-material';
import type { RoleSelectionDialogProps } from './types';

export function RoleSelectionDialog({
  open,
  onClose,
  onSelectRole,
  roomName,
  isAdmin,
}: RoleSelectionDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold">Join Chat Room</h3>
              <p className="text-gray-300 text-sm mt-1">{roomName}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-full transition-colors"
            >
              <Close className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600 text-center mb-6">
            {isAdmin
              ? 'Select a role to join this conversation'
              : 'Confirm your role to join this conversation'}
          </p>

          <div className="grid gap-4">
            {/* Patient Option */}
            <button
              onClick={() => onSelectRole('patient')}
              className="group flex items-center gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-black hover:bg-gray-50 transition-all"
            >
              <div className="w-14 h-14 rounded-full bg-gray-100 group-hover:bg-black group-hover:text-white flex items-center justify-center transition-colors">
                <Person className="w-7 h-7" />
              </div>
              <div className="text-left flex-1">
                <h4 className="font-semibold text-gray-900 text-lg">Patient</h4>
                <p className="text-gray-500 text-sm">Join as the patient in this consultation</p>
              </div>
            </button>

            {/* Doctor Option */}
            <button
              onClick={() => onSelectRole('doctor')}
              className="group flex items-center gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-black hover:bg-gray-50 transition-all"
            >
              <div className="w-14 h-14 rounded-full bg-gray-100 group-hover:bg-black group-hover:text-white flex items-center justify-center transition-colors">
                <LocalHospital className="w-7 h-7" />
              </div>
              <div className="text-left flex-1">
                <h4 className="font-semibold text-gray-900 text-lg">Doctor</h4>
                <p className="text-gray-500 text-sm">Join as the healthcare provider</p>
              </div>
            </button>
          </div>

          {isAdmin && (
            <p className="text-xs text-gray-400 text-center mt-4">
              Admin mode: You can join as either role for testing
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
          <button
            onClick={onClose}
            className="w-full py-2.5 text-gray-600 hover:text-gray-900 font-medium transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default RoleSelectionDialog;
