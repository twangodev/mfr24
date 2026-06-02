from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from http import HTTPStatus

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mfr24 import geo
from mfr24._version import __version__
from mfr24.client import MyFlightRadar24Client
from mfr24.exceptions import (
    Fr24TimeoutError,
    Fr24UnavailableError,
    Fr24UserNotFoundError,
)

_CACHE_CONTROL = "public, max-age=300, stale-while-revalidate=3600"


def _etag(arcs: list, airports: list) -> str:
    digest = hashlib.sha256(
        json.dumps({"arcs": arcs, "airports": airports}, sort_keys=True).encode()
    ).hexdigest()
    return f'W/"{digest[:16]}"'


def create_app(client: MyFlightRadar24Client) -> FastAPI:
    app = FastAPI(title="mfr24", version=__version__)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"]
    )

    @app.get("/healthz")
    def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @app.get(
        "/v1/users/{username}/flight-arcs",
        operation_id="get_user_flight_arcs",
        tags=["flight-arcs"],
    )
    def get_user_flight_arcs(username: str, request: Request) -> Response:
        try:
            flights = client.flights(username)
        except Fr24UserNotFoundError:
            return JSONResponse(
                {"error": "user_not_found", "username": username},
                status_code=HTTPStatus.NOT_FOUND,
            )
        except Fr24TimeoutError:
            return JSONResponse(
                {"error": "upstream_timeout"}, status_code=HTTPStatus.GATEWAY_TIMEOUT
            )
        except Fr24UnavailableError:
            return JSONResponse(
                {"error": "upstream_unavailable"}, status_code=HTTPStatus.BAD_GATEWAY
            )

        payload = geo.to_globe(flights)
        etag = _etag(payload["arcs"], payload["airports"])
        headers = {"Cache-Control": _CACHE_CONTROL, "ETag": etag}
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=HTTPStatus.NOT_MODIFIED, headers=headers)

        meta = {
            "username": username,
            "fetchedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stale": False,
        }
        return JSONResponse({**payload, "meta": meta}, headers=headers)

    return app


def build_app(client: MyFlightRadar24Client | None = None) -> FastAPI:
    return create_app(client if client is not None else MyFlightRadar24Client())
