from __future__ import annotations


class Fr24Error(Exception):
    """Base class for every mfr24 failure."""


class Fr24UserNotFoundError(Fr24Error):
    """The FlightRadar24 profile does not exist or exposes no public flights."""


class Fr24UnavailableError(Fr24Error):
    """FlightRadar24 returned a server error or could not be reached."""


class Fr24TimeoutError(Fr24Error):
    """A request to FlightRadar24 timed out."""


class Fr24ParseError(Fr24Error):
    """A FlightRadar24 response could not be parsed, likely a layout change."""
