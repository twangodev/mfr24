from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from mfr24 import console, geo
from mfr24.client import MyFlightRadar24Client
from mfr24.exceptions import Fr24Error

app = typer.Typer(
    name="mfr24",
    help="Unofficial MyFlightRadar24 SDK — turn a profile's flights into globe arcs.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_show_locals=False,
)

_DISCLAIMER = "unofficial — not affiliated with Flightradar24"

UsernameArg = Annotated[str, typer.Argument(help="FlightRadar24 username")]
JsonOpt = Annotated[bool, typer.Option("--json", "-j", help="emit JSON on stdout")]


def _load_flights(username: str):
    if console.stderr.is_terminal:
        console.stderr.print(f"[dim]{_DISCLAIMER}[/]")
    try:
        with MyFlightRadar24Client() as client:
            return client.flights(username)
    except Fr24Error as err:
        raise console.fail(str(err) or type(err).__name__) from err


@app.command()
def flights(username: UsernameArg, as_json: JsonOpt = False) -> None:
    """List a profile's logged flights."""
    records = _load_flights(username)
    if as_json:
        print(json.dumps([asdict(flight) for flight in records], indent=2))
        return
    table = Table("date", "from", "to", "dep", "arr", "flight")
    for flight in records:
        table.add_row(
            flight.date,
            flight.from_iata,
            flight.to_iata,
            flight.dep_time,
            flight.arr_time,
            flight.flight_number or "",
        )
    console.stderr.print(table)


@app.command()
def airports(username: UsernameArg, as_json: JsonOpt = False) -> None:
    """List the unique airports a profile has visited."""
    records = geo.airports(_load_flights(username))
    if as_json:
        print(json.dumps([asdict(airport) for airport in records], indent=2))
        return
    table = Table("iata", "name", "city", "country", "count")
    for airport in records:
        table.add_row(
            airport.iata,
            airport.name,
            airport.city,
            airport.country,
            str(airport.count),
        )
    console.stderr.print(table)


@app.command()
def export(
    username: UsernameArg,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="write JSON here instead of stdout"),
    ] = None,
) -> None:
    """Export the camelCase globe payload (drop-in for arc-gen)."""
    payload = geo.to_globe(_load_flights(username))
    text = json.dumps(payload, indent=2)
    if output is None:
        print(text)
        return
    output.write_text(text, encoding="utf-8")
    console.stderr.print(
        f"[green]wrote[/] {len(payload['arcs'])} arcs, {len(payload['airports'])} airports → {output}"
    )


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="bind host")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="bind port")] = 8000,
    no_cache: Annotated[
        bool, typer.Option("--no-cache", help="disable the in-memory cache")
    ] = False,
) -> None:
    """Run the HTTP API (requires the 'api' extra)."""
    try:
        import uvicorn

        from mfr24.api.app import build_app
    except ModuleNotFoundError as err:
        raise console.fail(
            "the API needs the 'api' extra: pip install 'mfr24[api]'"
        ) from err
    client = MyFlightRadar24Client(cache=None) if no_cache else MyFlightRadar24Client()
    uvicorn.run(build_app(client), host=host, port=port)
