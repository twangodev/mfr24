from __future__ import annotations

import airportsdata

from mfr24 import geo
from mfr24.models import Flight

DB = airportsdata.load("IATA")


def _flight(
    from_iata, to_iata, *, date="2026-06-15", dep="13:00", arr="14:00", number="SK505"
):
    return Flight(
        date=date,
        from_iata=from_iata,
        to_iata=to_iata,
        dep_time=dep,
        arr_time=arr,
        flight_number=number,
    )


def test_arcs_use_airport_coordinates():
    [arc] = geo.arcs([_flight("CPH", "LHR")])
    assert arc.start_lat == DB["CPH"]["lat"]
    assert arc.start_lng == DB["CPH"]["lon"]
    assert arc.end_lat == DB["LHR"]["lat"]
    assert arc.from_iata == "CPH"
    assert arc.to_iata == "LHR"


def test_arcs_compute_utc_with_timezones():
    [arc] = geo.arcs(
        [_flight("CPH", "LHR", date="2026-06-15", dep="13:00", arr="14:00")]
    )
    assert arc.dep_utc == "2026-06-15T11:00:00Z"
    assert arc.arr_utc == "2026-06-15T13:00:00Z"


def test_arcs_skip_unknown_airports():
    assert geo.arcs([_flight("ZZZ", "LHR")]) == []


def test_arcs_without_times_have_no_utc():
    [arc] = geo.arcs([_flight("CPH", "LHR", dep="", arr="", number=None)])
    assert arc.dep_utc is None
    assert arc.arr_utc is None
    assert arc.flight_number is None


def test_airports_count_visits():
    flights = [_flight("CPH", "LHR"), _flight("LHR", "CPH"), _flight("CPH", "JFK")]
    counts = {a.iata: a.count for a in geo.airports(flights)}
    assert counts == {"CPH": 3, "LHR": 2, "JFK": 1}


def test_to_globe_is_camel_case_and_omits_missing():
    payload = geo.to_globe([_flight("CPH", "LHR", dep="", arr="", number=None)])
    arc = payload["arcs"][0]
    assert set(arc) == {
        "startLat",
        "startLng",
        "endLat",
        "endLng",
        "fromIata",
        "toIata",
        "date",
    }
    assert "depUtc" not in arc
    airport = payload["airports"][0]
    assert set(airport) == {
        "lat",
        "lng",
        "iata",
        "icao",
        "city",
        "subd",
        "name",
        "country",
        "count",
    }
