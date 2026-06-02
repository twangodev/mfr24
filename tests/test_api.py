from __future__ import annotations

from fastapi.testclient import TestClient

from mfr24.api.app import create_app
from mfr24.exceptions import Fr24UserNotFoundError
from mfr24.models import Flight

from .fakes import StubClient

_FLIGHTS = [Flight("2026-06-15", "CPH", "LHR", "13:00", "14:00", "SK505")]


def test_healthz():
    client = TestClient(create_app(StubClient()))
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_flight_arcs_payload():
    client = TestClient(create_app(StubClient(_FLIGHTS)))
    response = client.get("/v1/users/someone/flight-arcs")
    assert response.status_code == 200
    body = response.json()
    assert body["arcs"][0]["fromIata"] == "CPH"
    assert body["airports"]
    assert body["meta"]["username"] == "someone"
    assert response.headers["Cache-Control"].startswith("public")
    assert response.headers["ETag"].startswith('W/"')


def test_flight_arcs_user_not_found():
    client = TestClient(create_app(StubClient(error=Fr24UserNotFoundError("nope"))))
    response = client.get("/v1/users/none/flight-arcs")
    assert response.status_code == 404
    assert response.json()["error"] == "user_not_found"


def test_flight_arcs_etag_304():
    client = TestClient(create_app(StubClient(_FLIGHTS)))
    first = client.get("/v1/users/someone/flight-arcs")
    etag = first.headers["ETag"]
    second = client.get(
        "/v1/users/someone/flight-arcs", headers={"If-None-Match": etag}
    )
    assert second.status_code == 304
