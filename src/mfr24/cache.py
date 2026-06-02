from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from mfr24.constants import DEFAULT_CACHE_TTL_SECONDS
from mfr24.models import Flight


@runtime_checkable
class CacheBackend(Protocol):
    """Storage for a username's parsed flights."""

    def get(self, key: str) -> list[Flight] | None: ...

    def set(self, key: str, value: list[Flight]) -> None: ...


class InMemoryTTLCache:
    """Process-local cache that expires entries after a fixed duration."""

    def __init__(
        self,
        ttl: float = DEFAULT_CACHE_TTL_SECONDS,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl
        self._clock = clock
        self._store: dict[str, tuple[float, list[Flight]]] = {}

    def get(self, key: str) -> list[Flight] | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if self._clock() >= expires_at:
            del self._store[key]
            return None
        return list(value)

    def set(self, key: str, value: list[Flight]) -> None:
        self._store[key] = (self._clock() + self._ttl, list(value))
