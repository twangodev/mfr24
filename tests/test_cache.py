from __future__ import annotations

from mfr24.cache import InMemoryTTLCache
from mfr24.models import Flight

_FLIGHT = Flight(
    date="2026-05-20",
    from_iata="CPH",
    to_iata="LHR",
    dep_time="13:00",
    arr_time="15:00",
)


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_set_then_get():
    cache = InMemoryTTLCache(ttl=10, clock=_Clock())
    cache.set("cph", [_FLIGHT])
    assert cache.get("cph") == [_FLIGHT]


def test_missing_key_returns_none():
    assert InMemoryTTLCache(clock=_Clock()).get("nope") is None


def test_entry_expires_after_ttl():
    clock = _Clock()
    cache = InMemoryTTLCache(ttl=10, clock=clock)
    cache.set("cph", [_FLIGHT])
    clock.now = 9.9
    assert cache.get("cph") == [_FLIGHT]
    clock.now = 10.0
    assert cache.get("cph") is None


def test_get_returns_a_defensive_copy():
    cache = InMemoryTTLCache(clock=_Clock())
    cache.set("cph", [_FLIGHT])
    cache.get("cph").append(_FLIGHT)
    assert cache.get("cph") == [_FLIGHT]
