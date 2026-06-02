from __future__ import annotations

import pytest
from curl_cffi.requests import exceptions as cffi

from mfr24 import transport
from mfr24.exceptions import Fr24TimeoutError, Fr24UnavailableError

from .fakes import FakeResponse, FlakySession


def _noop_sleep(_seconds: float) -> None:
    return None


def test_retries_then_succeeds():
    session = FlakySession(
        cffi.ConnectionError("boom"),
        fail_times=2,
        response=FakeResponse(status_code=200, text="ok"),
    )
    response = transport.fetch(
        session, "https://x/y", headers={}, timeout=1.0, sleep=_noop_sleep
    )
    assert response.status_code == 200
    assert session.calls == 3


def test_timeout_exhausted_raises_timeout_error():
    session = FlakySession(cffi.ConnectTimeout("slow"), fail_times=99)
    with pytest.raises(Fr24TimeoutError):
        transport.fetch(
            session, "https://x/y", headers={}, timeout=1.0, sleep=_noop_sleep
        )
    assert session.calls == transport.MAX_ATTEMPTS


def test_connection_exhausted_raises_unavailable():
    session = FlakySession(cffi.ConnectionError("down"), fail_times=99)
    with pytest.raises(Fr24UnavailableError):
        transport.fetch(
            session, "https://x/y", headers={}, timeout=1.0, sleep=_noop_sleep
        )


def test_retries_5xx_then_returns_last():
    session = FlakySession(
        cffi.ConnectionError("n/a"),
        fail_times=0,
        response=FakeResponse(status_code=503),
    )
    response = transport.fetch(
        session, "https://x/y", headers={}, timeout=1.0, sleep=_noop_sleep
    )
    assert response.status_code == 503
    assert session.calls == transport.MAX_ATTEMPTS
