from __future__ import annotations

import json
from pathlib import Path

import pytest

from mfr24.cache import InMemoryTTLCache
from mfr24.client import MyFlightRadar24Client
from mfr24.exceptions import Fr24ParseError, Fr24UnavailableError, Fr24UserNotFoundError

from .fakes import FakeResponse, FakeSession

FIXTURES = Path(__file__).parent / "fixtures"


def _full_routes() -> list[tuple[str, FakeResponse]]:
    profile = FakeResponse(
        status_code=200, text=(FIXTURES / "profile.html").read_text()
    )
    batch1 = FakeResponse(
        status_code=200,
        json_data=json.loads((FIXTURES / "flight_list_p1.json").read_text()),
    )
    batch2 = FakeResponse(
        status_code=200,
        json_data=json.loads((FIXTURES / "flight_list_p2.json").read_text()),
    )
    return [
        ("/someuser/flights", profile),
        ("flight-list/someuser/1//", batch1),
        ("flight-list/someuser/3//", batch2),
    ]


def test_flights_paginate_and_order():
    session = FakeSession(_full_routes())
    client = MyFlightRadar24Client(client=session, cache=None)
    flights = client.flights("someuser", page_size=2)
    assert [f.from_iata for f in flights] == ["LHR", "CPH", "DEN", "SFO", "LHR"]
    assert [f.to_iata for f in flights] == ["CPH", "LHR", "SFO", "DEN", "JFK"]
    assert len(session.calls) == 3


def test_flights_served_from_cache():
    session = FakeSession(_full_routes())
    client = MyFlightRadar24Client(client=session, cache=InMemoryTTLCache())
    first = client.flights("someuser", page_size=2)
    calls = len(session.calls)
    second = client.flights("someuser", page_size=2)
    assert second == first
    assert len(session.calls) == calls


def test_user_not_found():
    session = FakeSession([("/someuser/flights", FakeResponse(status_code=404))])
    client = MyFlightRadar24Client(client=session, cache=None)
    with pytest.raises(Fr24UserNotFoundError):
        client.flights("someuser")


def test_upstream_error():
    session = FakeSession([("/someuser/flights", FakeResponse(status_code=503))])
    client = MyFlightRadar24Client(client=session, cache=None)
    with pytest.raises(Fr24UnavailableError):
        client.flights("someuser")


def test_non_json_flight_list_raises_parse_error():
    routes = [
        (
            "/someuser/flights",
            FakeResponse(status_code=200, text=(FIXTURES / "profile.html").read_text()),
        ),
        ("flight-list/someuser/1//", FakeResponse(status_code=200, json_data=None)),
    ]
    client = MyFlightRadar24Client(client=FakeSession(routes), cache=None)
    with pytest.raises(Fr24ParseError):
        client.flights("someuser")


def test_blank_username_rejected():
    client = MyFlightRadar24Client(client=FakeSession([]), cache=None)
    with pytest.raises(ValueError, match="username"):
        client.flights("   ")


def test_username_stripped_for_both_key_and_fetch():
    session = FakeSession(_full_routes())
    client = MyFlightRadar24Client(client=session, cache=InMemoryTTLCache())
    first = client.flights("  someuser  ", page_size=2)
    calls = len(session.calls)
    second = client.flights("someuser", page_size=2)
    assert second == first
    assert len(session.calls) == calls


def test_default_cache_not_shared_between_clients():
    first_session = FakeSession(_full_routes())
    second_session = FakeSession(_full_routes())
    MyFlightRadar24Client(client=first_session).flights("someuser", page_size=2)
    MyFlightRadar24Client(client=second_session).flights("someuser", page_size=2)
    assert second_session.calls


def test_returned_flights_isolated_from_cache():
    session = FakeSession(_full_routes())
    client = MyFlightRadar24Client(client=session, cache=InMemoryTTLCache())
    first = client.flights("someuser", page_size=2)
    first.append(first[0])
    second = client.flights("someuser", page_size=2)
    assert len(second) == len(first) - 1
