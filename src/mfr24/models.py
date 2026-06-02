from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Flight:
    """A single logged flight as scraped from a profile, newest first."""

    date: str
    from_iata: str
    to_iata: str
    dep_time: str
    arr_time: str
    flight_number: str | None = None


@dataclass(frozen=True, slots=True)
class Arc:
    """A great-circle route between two airports, ready for a globe."""

    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    from_iata: str
    to_iata: str
    date: str | None = None
    flight_number: str | None = None
    dep_utc: str | None = None
    arr_utc: str | None = None


@dataclass(frozen=True, slots=True)
class Airport:
    """A unique airport with the number of times it was visited."""

    iata: str
    icao: str
    lat: float
    lng: float
    city: str
    subd: str
    name: str
    country: str
    count: int
