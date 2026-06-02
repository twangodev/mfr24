from __future__ import annotations

from enum import Enum
from http import HTTPStatus
from json import JSONDecodeError

from curl_cffi.requests import Response, Session

from mfr24 import transport
from mfr24.cache import CacheBackend, InMemoryTTLCache
from mfr24.constants import (
    BATCH_SIZE,
    DEFAULT_BASE_URL,
    DEFAULT_HEADERS,
    FLIGHT_LIST_PATH,
    FLIGHT_LIST_TIMEOUT,
    PROFILE_FLIGHTS_PATH,
    PROFILE_TIMEOUT,
)
from mfr24.exceptions import Fr24ParseError, Fr24UnavailableError, Fr24UserNotFoundError
from mfr24.models import Flight
from mfr24.parse import parse_api_row, parse_profile_rows


class _Unset(Enum):
    token = 0


_UNSET = _Unset.token


class MyFlightRadar24Client:
    """Synchronous client for a public MyFlightRadar24 profile.

    Each client gets its own in-memory cache by default; pass ``cache=None`` to
    disable caching or ``cache=`` to share an explicit backend.
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        client: Session | None = None,
        cache: CacheBackend | None | _Unset = _UNSET,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = client if client is not None else transport.build_session()
        self._owns_session = client is None
        self._cache: CacheBackend | None = (
            InMemoryTTLCache() if cache is _UNSET else cache
        )

    def __enter__(self) -> MyFlightRadar24Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def flights(self, username: str, *, page_size: int = BATCH_SIZE) -> list[Flight]:
        """Return every logged flight for ``username``, newest first."""
        username = username.strip()
        if not username:
            msg = "username must not be empty"
            raise ValueError(msg)
        if self._cache is not None:
            cached = self._cache.get(username)
            if cached is not None:
                return cached
        rows = self._collect_rows(username, page_size)
        flights = [rows[number] for number in sorted(rows)]
        if self._cache is not None:
            self._cache.set(username, flights)
        return flights

    def _collect_rows(self, username: str, page_size: int) -> dict[int, Flight]:
        rows = self._seed_rows(username)
        last_row = max(rows) if rows else 0
        while True:
            url = self._base_url + FLIGHT_LIST_PATH.format(
                username=username, start_row=last_row
            )
            response = self._get(url, FLIGHT_LIST_TIMEOUT, username)
            data = self._json(response)
            if not data:
                break
            try:
                keys = [int(key) for key in data]
                for key in data:
                    rows[int(key)] = parse_api_row(data[key])
                max_key = max(keys)
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise Fr24ParseError("unexpected flight-list row shape") from exc
            if len(data) < page_size or max_key <= last_row:
                break
            last_row = max_key
        return rows

    def _seed_rows(self, username: str) -> dict[int, Flight]:
        url = self._base_url + PROFILE_FLIGHTS_PATH.format(username=username)
        response = self._get(url, PROFILE_TIMEOUT, username)
        return parse_profile_rows(response.text)

    def _get(self, url: str, timeout: float, username: str) -> Response:
        headers = {**DEFAULT_HEADERS, "Referer": f"{self._base_url}/{username}"}
        response = transport.fetch(self._session, url, headers=headers, timeout=timeout)
        if response.status_code == HTTPStatus.NOT_FOUND:
            raise Fr24UserNotFoundError(username)
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise Fr24UnavailableError(f"{url} returned {response.status_code}")
        return response

    @staticmethod
    def _json(response: Response) -> dict[str, list]:
        try:
            return response.json()
        except (JSONDecodeError, ValueError) as exc:
            raise Fr24ParseError("flight-list response was not JSON") from exc
