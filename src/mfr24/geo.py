from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from functools import cache
from zoneinfo import ZoneInfo

import airportsdata

from mfr24.models import Airport, Arc, Flight

_MAX_FLIGHT_SECONDS = 24 * 3600


@cache
def _db():
    return airportsdata.load("IATA")


def _to_utc_iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_times(
    date: str,
    dep_time: str,
    arr_time: str,
    from_tz: str | None,
    to_tz: str | None,
) -> tuple[str | None, str | None]:
    if not (date and from_tz):
        return None, None

    dep_utc = None
    if dep_time:
        dep_local = datetime.strptime(f"{date} {dep_time}", "%Y-%m-%d %H:%M")
        dep_utc = dep_local.replace(tzinfo=ZoneInfo(from_tz)).astimezone(UTC)

    arr_utc = None
    if arr_time and to_tz and dep_utc is not None:
        base = datetime.strptime(f"{date} {arr_time}", "%Y-%m-%d %H:%M")
        best: tuple[float, datetime] | None = None
        for delta in (-1, 0, 1):
            candidate = (
                (base + timedelta(days=delta))
                .replace(tzinfo=ZoneInfo(to_tz))
                .astimezone(UTC)
            )
            duration = (candidate - dep_utc).total_seconds()
            if 0 < duration <= _MAX_FLIGHT_SECONDS and (
                best is None or duration < best[0]
            ):
                best = (duration, candidate)
        if best is not None:
            arr_utc = best[1]

    return (
        _to_utc_iso(dep_utc) if dep_utc else None,
        _to_utc_iso(arr_utc) if arr_utc else None,
    )


def arcs(flights: Sequence[Flight]) -> list[Arc]:
    """Build great-circle arcs for flights whose endpoints are known airports."""
    db = _db()
    result: list[Arc] = []
    for flight in flights:
        origin = db.get(flight.from_iata)
        destination = db.get(flight.to_iata)
        if not (origin and destination):
            continue
        dep_utc, arr_utc = _utc_times(
            flight.date,
            flight.dep_time,
            flight.arr_time,
            origin.get("tz"),
            destination.get("tz"),
        )
        result.append(
            Arc(
                start_lat=origin["lat"],
                start_lng=origin["lon"],
                end_lat=destination["lat"],
                end_lng=destination["lon"],
                from_iata=flight.from_iata,
                to_iata=flight.to_iata,
                date=flight.date or None,
                flight_number=flight.flight_number,
                dep_utc=dep_utc,
                arr_utc=arr_utc,
            )
        )
    return result


def airports(flights: Sequence[Flight]) -> list[Airport]:
    """Collect unique airports with how many times each was visited."""
    db = _db()
    counts: Counter[str] = Counter()
    for flight in flights:
        counts[flight.from_iata] += 1
        counts[flight.to_iata] += 1
    result: list[Airport] = []
    for iata, count in counts.items():
        airport = db.get(iata)
        if airport is None:
            continue
        result.append(
            Airport(
                iata=iata,
                icao=airport.get("icao", ""),
                lat=airport["lat"],
                lng=airport["lon"],
                city=airport.get("city", ""),
                subd=airport.get("subd", ""),
                name=airport.get("name", ""),
                country=airport.get("country", ""),
                count=count,
            )
        )
    return result


def to_globe(flights: Sequence[Flight]) -> dict[str, list]:
    """Serialize flights into the camelCase ``{arcs, airports}`` globe contract."""
    return {
        "arcs": [_arc_json(arc) for arc in arcs(flights)],
        "airports": [_airport_json(airport) for airport in airports(flights)],
    }


def _arc_json(arc: Arc) -> dict[str, object]:
    data: dict[str, object] = {
        "startLat": arc.start_lat,
        "startLng": arc.start_lng,
        "endLat": arc.end_lat,
        "endLng": arc.end_lng,
        "fromIata": arc.from_iata,
        "toIata": arc.to_iata,
    }
    if arc.date:
        data["date"] = arc.date
    if arc.flight_number:
        data["flightNumber"] = arc.flight_number
    if arc.dep_utc:
        data["depUtc"] = arc.dep_utc
    if arc.arr_utc:
        data["arrUtc"] = arc.arr_utc
    return data


def _airport_json(airport: Airport) -> dict[str, object]:
    return {
        "lat": airport.lat,
        "lng": airport.lng,
        "iata": airport.iata,
        "icao": airport.icao,
        "city": airport.city,
        "subd": airport.subd,
        "name": airport.name,
        "country": airport.country,
        "count": airport.count,
    }
