import { useState, useEffect, useCallback, useRef } from "react";

interface UseAsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

interface UseAsyncOptions {
  onError?: (error: Error) => void;
}

export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  immediate = true,
  options?: UseAsyncOptions,
): UseAsyncState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<UseAsyncState<T>>({
    data: null,
    loading: immediate,
    error: null,
  });

  // Use refs to avoid infinite loops - update refs but don't trigger re-renders
  const functionRef = useRef(asyncFunction);
  const optionsRef = useRef(options);

  // Update refs without changing identity or triggering effects
  functionRef.current = asyncFunction;
  optionsRef.current = options;

  const execute = useCallback(async () => {
    setState({ data: null, loading: true, error: null });
    try {
      // Use current values from refs, not closure values
      const response = await functionRef.current();
      setState({ data: response, loading: false, error: null });
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      setState({ data: null, loading: false, error: err });
      optionsRef.current?.onError?.(err);
    }
  }, []); // Empty dependencies - function doesn't change

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return { ...state, refetch: execute };
}
