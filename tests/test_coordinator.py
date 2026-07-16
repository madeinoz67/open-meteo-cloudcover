"""Tests for OpenMeteoDataUpdateCoordinator.

Covers issue #1: day-based evapotranspiration sensors must report the
authoritative daily total from the Open-Meteo `daily=` API, not the mean of
hourly values (which under-reports by ~24x).
"""

from __future__ import annotations

import os
from typing import Any

import pytest
from homeassistant.util import dt as dt_util

from custom_components.open_meteo_cloudcover.coordinator import (
    OpenMeteoDataUpdateCoordinator,
)


def _today_hourly_times(now: Any) -> list[str]:
    """24 naive ISO hour strings for the current local day."""
    return [
        now.replace(hour=h, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")
        for h in range(24)
    ]


def _payload(now: Any, *, et0_hourly: list[float], et0_daily: float):
    """One-day synthetic API payload (today) for ET0 + a non-cumulative metric."""
    times = _today_hourly_times(now)
    hourly: dict[str, Any] = {
        "time": times,
        "et0_fao_evapotranspiration": list(et0_hourly),
        "cloud_cover": [80] * 24,
    }
    daily: dict[str, Any] = {
        "time": [now.date().isoformat()],
        "et0_fao_evapotranspiration": [et0_daily],
    }
    return times, hourly, daily


async def test_cumulative_day_sensor_uses_authoritative_daily_total(hass) -> None:
    """Issue #1: ET0 day sensor reports the daily total, not the hourly avg."""
    now = dt_util.now()
    coord = OpenMeteoDataUpdateCoordinator(hass, latitude=-33.33, longitude=115.63)
    times, hourly, daily = _payload(now, et0_hourly=[0.1] * 24, et0_daily=1.4)

    data = coord._group_by_day(times, hourly, daily)

    today = data["et0_fao_evapotranspiration_0"]
    assert today["total"] == 1.4
    assert today["avg"] == pytest.approx(0.1)
    assert today["total"] != today["avg"]


async def test_non_cumulative_day_sensor_has_no_total(hass) -> None:
    """Cloud cover keeps the daily average and gets no total attribute."""
    now = dt_util.now()
    coord = OpenMeteoDataUpdateCoordinator(hass, latitude=-33.33, longitude=115.63)
    times, hourly, daily = _payload(now, et0_hourly=[0.1] * 24, et0_daily=1.4)

    data = coord._group_by_day(times, hourly, daily)

    today = data["cloud_cover_0"]
    assert "total" not in today
    assert today["avg"] == 80


async def test_cumulative_falls_back_to_sum_when_daily_missing(hass) -> None:
    """If the daily API omits/None's today's total, fall back to sum of hourly."""
    now = dt_util.now()
    coord = OpenMeteoDataUpdateCoordinator(hass, latitude=-33.33, longitude=115.63)
    times, hourly, _ = _payload(now, et0_hourly=[0.1] * 24, et0_daily=1.4)
    daily = {"time": [now.date().isoformat()], "et0_fao_evapotranspiration": [None]}

    data = coord._group_by_day(times, hourly, daily)

    today = data["et0_fao_evapotranspiration_0"]
    assert today["total"] == pytest.approx(2.4)  # 24 * 0.1


async def test_async_update_requests_daily_param_and_maps_total(hass) -> None:
    """End-to-end: request only valid daily vars; total wired through."""
    now = dt_util.now()
    coord = OpenMeteoDataUpdateCoordinator(hass, latitude=-33.33, longitude=115.63)

    payload = {
        "hourly": {
            "time": _today_hourly_times(now),
            "et0_fao_evapotranspiration": [0.1] * 24,
            "evapotranspiration": [0.1] * 24,
            "cloud_cover": [80] * 24,
        },
        "daily": {
            "time": [now.date().isoformat()],
            "et0_fao_evapotranspiration": [5.6],
            # evapotranspiration is hourly-only on Open-Meteo, so the API never
            # returns it here — its daily total falls back to sum-of-hourly.
        },
    }

    captured: dict[str, Any] = {}

    class _Response:
        async def __aenter__(self) -> _Response:
            return self

        async def __aexit__(self, *exc: object) -> bool:
            return False

        def raise_for_status(self) -> None:
            return None

        async def json(self) -> dict[str, Any]:
            return payload

    class _Session:
        async def __aenter__(self) -> _Session:
            return self

        async def __aexit__(self, *exc: object) -> bool:
            return False

        def get(self, url: str, params: dict[str, Any] | None = None) -> _Response:
            captured["url"] = url
            captured["params"] = params
            return _Response()

    from unittest.mock import patch

    with patch(
        "custom_components.open_meteo_cloudcover.coordinator.aiohttp.ClientSession",
        return_value=_Session(),
    ):
        data = await coord._async_update_data()

    # The request must ask ONLY for daily vars that exist on Open-Meteo.
    # daily=evapotranspiration 400s the whole call (it's hourly-only) — see 2026.7.2.
    assert captured["params"]["daily"] == "et0_fao_evapotranspiration"
    # et0 uses the authoritative API total...
    assert data["et0_fao_evapotranspiration_0"]["total"] == 5.6
    # ...while evapotranspiration (hourly-only) falls back to sum of hourly.
    assert data["evapotranspiration_0"]["total"] == pytest.approx(2.4)


@pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_API_TESTS"),
    reason="hits the live Open-Meteo API; set RUN_LIVE_API_TESTS=1 to run",
)
async def test_async_update_against_real_api(hass) -> None:
    """Live smoke test: the real API request must succeed (no invalid params).

    Guards against requesting variables Open-Meteo rejects — e.g. requesting
    daily=evapotranspiration 400s the entire call and breaks the integration
    (the 2026.7.1 regression). Deselected by default; run with
    RUN_LIVE_API_TESTS=1 pytest -k real_api
    """
    coord = OpenMeteoDataUpdateCoordinator(hass, latitude=-33.33, longitude=115.63)
    data = await coord._async_update_data()  # real network call
    assert "et0_fao_evapotranspiration_0" in data
    assert data["et0_fao_evapotranspiration_0"]["total"] is not None
