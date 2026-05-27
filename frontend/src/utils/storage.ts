/* src/utils/storage.ts */

/**
 * Safe localStorage wrapper.
 * Never use this for sensitive tokens in production – prefer httpOnly cookies.
 * This is kept for session metadata only.
 */
export const storage = {
  get<T>(key: string): T | null {
    try {
      const raw = localStorage.getItem(key);
      if (raw === null) return null;
      return JSON.parse(raw) as T;
    } catch {
      return null;
    }
  },

  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* ignore */
    }
  },

  remove(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  },

  clear(): void {
    try {
      localStorage.clear();
    } catch {
      /* ignore */
    }
  },
};
