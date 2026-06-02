from __future__ import annotations

import time
from collections.abc import Callable, Mapping

from curl_cffi.requests import Response, Session
from curl_cffi.requests import exceptions as cffi

from mfr24.constants import MAX_ATTEMPTS, MAX_BACKOFF_SECONDS
from mfr24.exceptions import Fr24TimeoutError, Fr24UnavailableError

_RETRYABLE_STATUS = frozenset({500, 502, 503, 504})


def build_session() -> Session:
    return Session(impersonate="chrome")


def _backoff_seconds(attempt: int) -> float:
    return min(2.0**attempt, MAX_BACKOFF_SECONDS)


def fetch(
    session: Session,
    url: str,
    *,
    headers: Mapping[str, str],
    timeout: float,
    sleep: Callable[[float], None] = time.sleep,
) -> Response:
    """GET ``url``, retrying transient failures with exponential backoff.

    Connection and timeout failures are raised as :class:`Fr24Error` subclasses
    once attempts are exhausted; 5xx responses are retried then returned for the
    caller to classify.
    """
    for attempt in range(MAX_ATTEMPTS):
        final = attempt + 1 == MAX_ATTEMPTS
        try:
            response = session.get(url, headers=dict(headers), timeout=timeout)
        except cffi.Timeout as exc:
            if final:
                raise Fr24TimeoutError(url) from exc
        except cffi.RequestException as exc:
            if final:
                raise Fr24UnavailableError(url) from exc
        else:
            if final or response.status_code not in _RETRYABLE_STATUS:
                return response
        sleep(_backoff_seconds(attempt))
    raise Fr24UnavailableError(url)
