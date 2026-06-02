from __future__ import annotations

from mfr24.models import Flight


class FakeResponse:
    def __init__(
        self, *, status_code: int = 200, text: str = "", json_data: object = None
    ) -> None:
        self.status_code = status_code
        self._text = text
        self._json = json_data

    @property
    def text(self) -> str:
        return self._text

    def json(self) -> object:
        if self._json is None:
            msg = "no json body"
            raise ValueError(msg)
        return self._json


class FakeSession:
    """Routes URLs to canned responses by substring; records every call."""

    def __init__(self, routes: list[tuple[str, FakeResponse]]) -> None:
        self._routes = routes
        self.calls: list[str] = []
        self.closed = False

    def get(
        self, url: str, headers: object = None, timeout: object = None
    ) -> FakeResponse:
        self.calls.append(url)
        for needle, response in self._routes:
            if needle in url:
                return response
        msg = f"unexpected url: {url}"
        raise AssertionError(msg)

    def close(self) -> None:
        self.closed = True


class FlakySession:
    """Raises a given exception for the first N calls, then returns a response."""

    def __init__(
        self, error: Exception, *, fail_times: int, response: FakeResponse | None = None
    ) -> None:
        self._error = error
        self._fail_times = fail_times
        self._response = response or FakeResponse(status_code=200, text="ok")
        self.calls = 0

    def get(
        self, url: str, headers: object = None, timeout: object = None
    ) -> FakeResponse:
        self.calls += 1
        if self.calls <= self._fail_times:
            raise self._error
        return self._response


class StubClient:
    """Stand-in for MyFlightRadar24Client in API and CLI tests."""

    def __init__(
        self, flights: list[Flight] | None = None, *, error: Exception | None = None
    ) -> None:
        self._flights = flights or []
        self._error = error

    def flights(self, username: str, *, page_size: int = 50) -> list[Flight]:
        if self._error is not None:
            raise self._error
        return self._flights

    def __enter__(self) -> StubClient:
        return self

    def __exit__(self, *exc: object) -> None:
        return None
