/* src/utils/storage.ts */

/**
 * Safe sessionStorage wrapper.
 * Never use this for sensitive tokens in production – prefer httpOnly cookies.
 * This is kept for session metadata only.
 */
export const storage = {
  get<T>(key: string): T | null {
    try {
      const raw = sessionStorage.getItem(key);
      if (raw === null) return null;
      return JSON.parse(raw) as T;
    } catch {
      return null;
    }
  },

  set<T>(key: string, value: T): void {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* ignore */
    }
  },

  remove(key: string): void {
    try {
      sessionStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  },

  clear(): void {
    try {
      sessionStorage.clear();
    } catch {
      /* ignore */
    }
  },
};

