"""
Minimal in-memory TTL cache.

Streamlit's @st.cache_data(ttl=3600) handled this for free in the dashboard.
Outside Streamlit we need something equivalent so /api/historical and
/api/map-data don't hit Postgres on every request. This is process-local
(fine for a single-instance API); swap for Redis if you scale to multiple workers.
"""

import time
import threading
from typing import Any, Callable, Dict, Tuple


class TTLCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get_or_set(self, key: str, factory: Callable[[], Any]) -> Any:
        now = time.time()
        with self._lock:
            cached = self._store.get(key)
            if cached is not None:
                ts, value = cached
                if now - ts < self.ttl_seconds:
                    return value

        # Compute outside the lock so slow DB calls don't block other keys.
        value = factory()
        with self._lock:
            self._store[key] = (now, value)
        return value

    def invalidate(self, key: str = None):
        with self._lock:
            if key is None:
                self._store.clear()
            else:
                self._store.pop(key, None)
