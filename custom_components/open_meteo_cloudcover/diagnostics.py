"""Diagnostics support for Open-Meteo CloudCover integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import OpenMeteoDataUpdateCoordinator

TO_REDACT = {
    "latitude",
    "longitude",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: OpenMeteoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get coordinator data
    coordinator_data = coordinator.data if coordinator.data else {}

    # Build diagnostics data with redacted location info
    diagnostics_data = {
        "entry": {
            "title": entry.title,
            "data": {
                "latitude": entry.data.get("latitude"),
                "longitude": entry.data.get("longitude"),
                "name": entry.data.get("name"),
            },
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_update_time": coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time
            else None,
            "update_interval": coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None,
            "forecast_days": coordinator.forecast_days,
        },
        "data_summary": {
            "sensor_count": len([k for k in coordinator_data if k != "_metadata"]),
            "metadata": {
                "latitude": coordinator_data.get("_metadata", {}).get("latitude"),
                "longitude": coordinator_data.get("_metadata", {}).get("longitude"),
                "timezone": coordinator_data.get("_metadata", {}).get("timezone"),
                "elevation": coordinator_data.get("_metadata", {}).get("elevation"),
            },
        },
        "sensors": {},
    }

    # Add sample data from each sensor (sanitized)
    for key, value in coordinator_data.items():
        if key == "_metadata":
            continue

        if isinstance(value, dict):
            # Sanitize sensor data - include structure but limit array sizes
            sensor_info = {
                "date": value.get("date"),
                "day_offset": value.get("day_offset"),
                "current": value.get("current"),
                "min": value.get("min"),
                "max": value.get("max"),
                "avg": value.get("avg"),
            }

            # Include hourly data structure but limit to first few entries
            hourly_data = value.get("hourly_data", {})
            if hourly_data:
                # Get first 3 and last 3 entries from the dict
                items = list(hourly_data.items())
                sensor_info["hourly_data_sample"] = {
                    "count": len(items),
                    "first_3": dict(items[:3]) if items else {},
                    "last_3": dict(items[-3:]) if items else {},
                }

            diagnostics_data["sensors"][key] = sensor_info

    # Redact sensitive location data
    return async_redact_data(diagnostics_data, TO_REDACT)
