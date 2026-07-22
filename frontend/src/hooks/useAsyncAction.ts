import { useState, useCallback } from 'react';

interface AsyncActionState {
  isLoading: boolean;
  error: string | null;
  success: boolean;
}

export function useAsyncAction<T, Args extends any[]>(
  actionFn: (...args: Args) => Promise<T>,
  options?: {
    onSuccess?: (data: T) => void;
    onError?: (err: any) => void;
  }
) {
  const [state, setState] = useState<AsyncActionState>({
    isLoading: false,
    error: null,
    success: false,
  });

  const execute = useCallback(async (...args: Args) => {
    setState({ isLoading: true, error: null, success: false });
    try {
      const result = await actionFn(...args);
      setState({ isLoading: false, error: null, success: true });
      if (options?.onSuccess) {
        options.onSuccess(result);
      }
      return result;
    } catch (err: any) {
      const errMsg = err.message || 'An error occurred during execution';
      setState({ isLoading: false, error: errMsg, success: false });
      if (options?.onError) {
        options.onError(err);
      }
      throw err;
    }
  }, [actionFn, options]);

  const reset = useCallback(() => {
    setState({ isLoading: false, error: null, success: false });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}
