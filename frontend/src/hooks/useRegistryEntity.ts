/* src/hooks/useRegistryEntity.ts */

import { useState, useEffect, useCallback } from "react";
import type { ApiResponse } from "../services/registry/registryTypes";

export function useRegistryEntity<T>(
  fetchFn: () => Promise<ApiResponse<T>>,
  deps: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetchFn();
      setData(response.data);
    } catch (err: any) {
      setError(err.message || "Failed to retrieve registry entity");
    } finally {
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    refetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refetch]);

  return {
    data,
    isLoading,
    error,
    refetch
  };
}
