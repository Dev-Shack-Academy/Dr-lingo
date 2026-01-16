import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Snackbar, Alert, AlertColor, AlertTitle } from '@mui/material';

interface ToastMessage {
  id: string;
  title?: string;
  message: string;
  severity: AlertColor;
  details?: string[];
}

interface ToastContextType {
  showToast: (message: string, severity?: AlertColor, title?: string, details?: string[]) => void;
  showError: (error: unknown, fallbackMessage?: string) => void;
  showSuccess: (message: string, title?: string) => void;
  showWarning: (message: string, title?: string) => void;
  showInfo: (message: string, title?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

/**
 * Parse API error response into user-friendly messages
 */
function parseApiError(error: unknown): { message: string; details: string[] } {
  const details: string[] = [];
  let message = 'Something went wrong. Please try again.';

  // Handle ApiError from HttpClient (has data property with response)
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const apiError = error as { data?: unknown; status?: number; message?: string };
    if (apiError.data) {
      return parseErrorObject(apiError.data);
    }
  }

  if (error instanceof Error) {
    const errorText = error.message;

    // Try to parse as JSON (Django REST Framework error format)
    try {
      // Handle "[object Object]" case - the error was stringified incorrectly
      if (errorText === '[object Object]' || errorText === 'API request failed') {
        return { message, details };
      }

      // Try to extract JSON from the error message
      const jsonMatch = errorText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return parseErrorObject(parsed);
      }

      // If it's a plain string error
      if (errorText && errorText !== '[object Object]' && errorText !== 'API request failed') {
        message = errorText;
      }
    } catch {
      // Not JSON, use as-is if it's meaningful
      if (errorText && errorText !== '[object Object]' && errorText !== 'API request failed') {
        message = errorText;
      }
    }
  }

  // Handle axios error response directly
  if (typeof error === 'object' && error !== null) {
    const axiosError = error as { response?: { data?: unknown; status?: number } };
    if (axiosError.response?.data) {
      return parseErrorObject(axiosError.response.data);
    }
  }

  return { message, details };
}

/**
 * Parse error object from API response
 */
function parseErrorObject(data: unknown): { message: string; details: string[] } {
  const details: string[] = [];
  let message = 'Something went wrong. Please try again.';

  if (typeof data === 'string') {
    message = data;
    return { message, details };
  }

  if (typeof data !== 'object' || data === null) {
    return { message, details };
  }

  const errorObj = data as Record<string, unknown>;

  // Handle common Django REST Framework error formats

  // Format: { "detail": "Error message" }
  if (typeof errorObj.detail === 'string') {
    message = errorObj.detail;
    return { message, details };
  }

  // Format: { "error": "Error message" }
  if (typeof errorObj.error === 'string') {
    message = errorObj.error;
    return { message, details };
  }

  // Format: { "message": "Error message" }
  if (typeof errorObj.message === 'string') {
    message = errorObj.message;
    return { message, details };
  }

  // Format: { "non_field_errors": ["Error 1", "Error 2"] }
  if (Array.isArray(errorObj.non_field_errors)) {
    message = 'Validation failed';
    details.push(...errorObj.non_field_errors.map(String));
  }

  // Format: { "field_name": ["Error 1", "Error 2"], ... }
  // Common for form validation errors
  const fieldErrors: string[] = [];
  for (const [key, value] of Object.entries(errorObj)) {
    if (key === 'non_field_errors' || key === 'detail' || key === 'error' || key === 'message') {
      continue;
    }

    const fieldName = formatFieldName(key);

    if (Array.isArray(value)) {
      value.forEach((err) => {
        if (typeof err === 'string') {
          fieldErrors.push(`${fieldName}: ${err}`);
        }
      });
    } else if (typeof value === 'string') {
      fieldErrors.push(`${fieldName}: ${value}`);
    } else if (typeof value === 'object' && value !== null) {
      // Nested errors
      const nested = parseErrorObject(value);
      if (nested.details.length > 0) {
        fieldErrors.push(...nested.details.map((d) => `${fieldName} - ${d}`));
      } else if (nested.message !== 'Something went wrong. Please try again.') {
        fieldErrors.push(`${fieldName}: ${nested.message}`);
      }
    }
  }

  if (fieldErrors.length > 0) {
    message = 'Please fix the following issues:';
    details.push(...fieldErrors);
  }

  return { message, details };
}

/**
 * Format field name for display (snake_case to Title Case)
 */
function formatFieldName(field: string): string {
  return field.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, severity: AlertColor = 'info', title?: string, details?: string[]) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
      setToasts((prev) => [...prev, { id, message, severity, title, details }]);
    },
    []
  );

  const showError = useCallback(
    (error: unknown, fallbackMessage?: string) => {
      console.error('Toast Error:', error);
      const { message, details } = parseApiError(error);
      const finalMessage =
        message === 'Something went wrong. Please try again.' && fallbackMessage
          ? fallbackMessage
          : message;
      showToast(finalMessage, 'error', 'Error', details.length > 0 ? details : undefined);
    },
    [showToast]
  );

  const showSuccess = useCallback(
    (message: string, title?: string) => {
      showToast(message, 'success', title);
    },
    [showToast]
  );

  const showWarning = useCallback(
    (message: string, title?: string) => {
      showToast(message, 'warning', title);
    },
    [showToast]
  );

  const showInfo = useCallback(
    (message: string, title?: string) => {
      showToast(message, 'info', title);
    },
    [showToast]
  );

  return (
    <ToastContext.Provider value={{ showToast, showError, showSuccess, showWarning, showInfo }}>
      {children}
      {toasts.map((toast, index) => (
        <Snackbar
          key={toast.id}
          open={true}
          autoHideDuration={toast.severity === 'error' ? 8000 : 5000}
          onClose={() => removeToast(toast.id)}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ mt: index * 10 }}
        >
          <Alert
            onClose={() => removeToast(toast.id)}
            severity={toast.severity}
            variant="filled"
            sx={{ width: '100%', maxWidth: 400 }}
          >
            {toast.title && <AlertTitle>{toast.title}</AlertTitle>}
            {toast.message}
            {toast.details && toast.details.length > 0 && (
              <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', fontSize: '0.875rem' }}>
                {toast.details.map((detail, i) => (
                  <li key={i}>{detail}</li>
                ))}
              </ul>
            )}
          </Alert>
        </Snackbar>
      ))}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
