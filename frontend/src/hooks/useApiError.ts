import { useCallback } from 'react';
import { useToast } from '@/components/feedback/Toast';
import { isApiError } from '@/utils/errors';
import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export function useApiError() {
  const { showToast } = useToast();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleError = useCallback((e: unknown) => {
    if (isApiError(e)) {
      if (e.status === 401) {
        logout().then(() => {
          navigate('/login?reason=session_expired');
        });
        showToast('Your session has expired. Please log in again.', 'warning');
      } else {
        showToast(e.message || 'An API error occurred', 'error');
      }
    } else if (e instanceof Error) {
      showToast(e.message, 'error');
    } else {
      showToast('An unexpected error occurred', 'error');
    }
  }, [showToast, logout, navigate]);

  return { handleError };
}
