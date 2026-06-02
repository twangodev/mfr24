from __future__ import annotations

import dataclasses

import pytest

from mfr24.models import Flight


def test_flight_is_frozen():
    flight = Flight("2026-05-20", "CPH", "LHR", "13:00", "15:00")
    with pytest.raises(dataclasses.FrozenInstanceError):
        flight.date = "2026-01-01"  # type: ignore[misc]
