"""In-memory cache for export output with time-based expiry."""

import time
from collections.abc import Callable

from attrs import define, field


@define(eq=False)
class ExportCache:
    """Caches export output in memory, expiring each entry `ttl` seconds after it is set.

    Entries are stamped with `clock()` when stored and evicted lazily: an expired entry
    is removed the next time it is read. `clock` defaults to `time.monotonic`, which is
    unaffected by changes to the system clock; tests pass a fake clock to control time.
    """

    ttl: float = 3600.0
    clock: Callable[[], float] = time.monotonic
    _entries: dict[str, tuple[float, str]] = field(factory=dict, init=False, repr=False)

    def get(self, key: str) -> str | None:
        """Return the cached export for `key`, or None if it is missing or expired."""
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, data = entry
        if self.clock() - stored_at >= self.ttl:
            del self._entries[key]
            return None
        return data

    def set(self, key: str, data: str) -> None:
        """Cache `data` under `key`, replacing any existing entry and restarting its TTL."""
        self._entries[key] = (self.clock(), data)
