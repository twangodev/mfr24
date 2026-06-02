from __future__ import annotations

import json

from typer.testing import CliRunner

from mfr24.cli import app
from mfr24.models import Flight

from .fakes import StubClient

runner = CliRunner()

_FLIGHTS = [
    Flight("2026-06-15", "CPH", "LHR", "13:00", "14:00", "SK505"),
    Flight("2026-06-14", "LHR", "CPH", "09:00", "11:00", None),
]


def _patch_client(monkeypatch):
    monkeypatch.setattr(
        "mfr24.cli.MyFlightRadar24Client", lambda *a, **k: StubClient(_FLIGHTS)
    )


def test_flights_json(monkeypatch):
    _patch_client(monkeypatch)
    result = runner.invoke(app, ["flights", "someuser", "-j"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data[0]["from_iata"] == "CPH"
    assert data[1]["flight_number"] is None


def test_airports_json(monkeypatch):
    _patch_client(monkeypatch)
    result = runner.invoke(app, ["airports", "someuser", "-j"])
    assert result.exit_code == 0, result.output
    iatas = {airport["iata"] for airport in json.loads(result.stdout)}
    assert {"CPH", "LHR"} <= iatas


def test_export_writes_file(monkeypatch, tmp_path):
    _patch_client(monkeypatch)
    out = tmp_path / "globe.json"
    result = runner.invoke(app, ["export", "someuser", "-o", str(out)])
    assert result.exit_code == 0, result.output
    payload = json.loads(out.read_text())
    assert payload["arcs"][0]["fromIata"] == "CPH"
    assert payload["airports"]
