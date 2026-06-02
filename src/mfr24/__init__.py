"""mfr24 — unofficial Python SDK for MyFlightRadar24 flight lists.

Quickstart::

    from mfr24 import MyFlightRadar24Client, arcs, airports

    client = MyFlightRadar24Client()
    flights = client.flights("johndoe")
    routes = arcs(flights)
    visited = airports(flights)
"""

from __future__ import annotations

from mfr24._version import __version__
from mfr24.client import MyFlightRadar24Client
from mfr24.exceptions import (
    Fr24Error,
    Fr24ParseError,
    Fr24TimeoutError,
    Fr24UnavailableError,
    Fr24UserNotFoundError,
)
from mfr24.geo import airports, arcs, to_globe
from mfr24.models import Airport, Arc, Flight

Client = MyFlightRadar24Client


def flights(
    username: str, *, client: MyFlightRadar24Client | None = None
) -> list[Flight]:
    """Fetch a username's flights via ``client`` or a throwaway default client."""
    target = client if client is not None else MyFlightRadar24Client()
    return target.flights(username)


__all__ = [
    "Airport",
    "Arc",
    "Client",
    "Flight",
    "Fr24Error",
    "Fr24ParseError",
    "Fr24TimeoutError",
    "Fr24UnavailableError",
    "Fr24UserNotFoundError",
    "MyFlightRadar24Client",
    "__version__",
    "airports",
    "arcs",
    "flights",
    "to_globe",
]
