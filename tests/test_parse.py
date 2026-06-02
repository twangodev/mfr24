from __future__ import annotations

import json
from pathlib import Path

from mfr24.parse import parse_api_row, parse_date, parse_iata, parse_profile_rows

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_iata_variants():
    assert parse_iata('<a class="show-hovercard">LHR</a>') == "LHR"
    assert parse_iata('<span class="tooltip">CPH</span>') == "CPH"
    assert parse_iata("SFO") == "SFO"
    assert parse_iata("") == ""
    assert parse_iata(None) == ""


def test_parse_date():
    assert parse_date('<span class="inner-date">2026-05-20</span>') == "2026-05-20"
    assert parse_date("<span>nope</span>") == ""
    assert parse_date(None) == ""


def test_parse_profile_rows():
    rows = parse_profile_rows((FIXTURES / "profile.html").read_text())
    assert set(rows) == {0, 1}
    assert rows[0].from_iata == "LHR"
    assert rows[0].to_iata == "CPH"
    assert rows[0].date == "2026-05-20"
    assert rows[0].dep_time == "05:40"
    assert rows[0].flight_number == "SK500"
    assert rows[1].from_iata == "CPH"


def test_parse_api_row():
    batch = json.loads((FIXTURES / "flight_list_p1.json").read_text())
    flight = parse_api_row(batch["2"])
    assert flight.from_iata == "DEN"
    assert flight.to_iata == "SFO"
    assert flight.date == "2026-05-08"
    assert flight.dep_time == "15:52"
    assert flight.arr_time == "18:47"
    assert flight.flight_number == "F91093"


def test_parse_api_row_empty_flight_number_is_none():
    batch = json.loads((FIXTURES / "flight_list_p2.json").read_text())
    assert parse_api_row(batch["4"]).flight_number is None


def test_parse_api_row_tolerates_short_rows():
    flight = parse_api_row([])
    assert flight.from_iata == ""
    assert flight.flight_number is None
