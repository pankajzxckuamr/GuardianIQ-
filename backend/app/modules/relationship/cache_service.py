from datetime import datetime, timedelta, timezone
import threading

class MemoryCacheService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(MemoryCacheService, cls).__new__(cls)
                cls._instance.cache = {}
                cls._instance.lock = threading.Lock()
            return cls._instance

    def get(self, key: str):
        with self.lock:
            item = self.cache.get(key)
            if not item:
                return None
            
            val, expires_at = item
            if datetime.now(timezone.utc) > expires_at:
                del self.cache[key]
                return None
            return val

    def set(self, key: str, value: any, ttl_seconds: int = 300):
        with self.lock:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            self.cache[key] = (value, expires_at)

    def invalidate_tenant(self, tenant_id: str):
        with self.lock:
            keys_to_del = [k for k in self.cache.keys() if str(tenant_id) in k]
            for k in keys_to_del:
                del self.cache[k]

    def clear(self):
        with self.lock:
            self.cache.clear()
