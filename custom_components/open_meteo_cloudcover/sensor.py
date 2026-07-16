"""Sensor platform for Open-Meteo CloudCover integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, CUMULATIVE_METRICS, DEFAULT_NAME, DOMAIN, SENSOR_TYPES, get_day_name
from .coordinator import OpenMeteoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Open-Meteo CloudCover sensor entities."""
    coordinator: OpenMeteoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get the forecast days from coordinator (fixed at 7)
    forecast_days = coordinator.forecast_days

    # Create sensor entities for each sensor type and each day
    entities = []
    for sensor_type in SENSOR_TYPES:
        # Create "This Hour" and "Next Hour" sensors
        entities.append(
            OpenMeteoSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_type=sensor_type,
                day_offset=None,
                special_type="this_hour",
            )
        )
        entities.append(
            OpenMeteoSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_type=sensor_type,
                day_offset=None,
                special_type="next_hour",
            )
        )

        # Create hourly sensors (hours 1-24, disabled by default)
        for hour_offset in range(1, 25):
            entities.append(
                OpenMeteoSensor(
                    coordinator=coordinator,
                    entry=entry,
                    sensor_type=sensor_type,
                    day_offset=None,
                    special_type="hourly",
                    hour_offset=hour_offset,
                )
            )

        # Create a sensor for each day (0 = today, 1 = tomorrow, etc.)
        for day_offset in range(forecast_days + 1):  # +1 to include today
            entities.append(
                OpenMeteoSensor(
                    coordinator=coordinator,
                    entry=entry,
                    sensor_type=sensor_type,
                    day_offset=day_offset,
                    special_type=None,
                )
            )

    async_add_entities(entities)


class OpenMeteoSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Open-Meteo CloudCover sensor."""

    def __init__(
        self,
        coordinator: OpenMeteoDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
        day_offset: int | None,
        special_type: str | None = None,
        hour_offset: int | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._sensor_type = sensor_type
        self._day_offset = day_offset
        self._special_type = special_type
        self._hour_offset = hour_offset

        # Build sensor key and name based on type
        base_name = SENSOR_TYPES[sensor_type]["name"]

        if special_type == "this_hour":
            self._sensor_key = f"{sensor_type}_this_hour"
            self._attr_name = f"{base_name} This Hour"
            self._attr_unique_id = f"{entry.entry_id}_{sensor_type}_this_hour"
        elif special_type == "next_hour":
            self._sensor_key = f"{sensor_type}_next_hour"
            self._attr_name = f"{base_name} Next Hour"
            self._attr_unique_id = f"{entry.entry_id}_{sensor_type}_next_hour"
        elif special_type == "hourly":
            self._sensor_key = f"{sensor_type}_hour_{hour_offset}"
            self._attr_name = f"{base_name} Hour {hour_offset}"
            self._attr_unique_id = f"{entry.entry_id}_{sensor_type}_hour_{hour_offset}"
        else:
            # Regular day-based sensor
            self._sensor_key = f"{sensor_type}_{day_offset}"
            day_name = get_day_name(day_offset)
            self._attr_name = f"{base_name} {day_name}"
            self._attr_unique_id = f"{entry.entry_id}_{sensor_type}_{day_offset}"

        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]

        # Set device class if available
        if SENSOR_TYPES[sensor_type]["device_class"]:
            self._attr_device_class = SENSOR_TYPES[sensor_type]["device_class"]

        # Set state class
        if SENSOR_TYPES[sensor_type]["state_class"]:
            self._attr_state_class = SENSOR_TYPES[sensor_type]["state_class"]

        # Disable by default for:
        # - cloud_cover_low, cloud_cover_mid, cloud_cover_high
        # - all hourly sensors
        # - extended daily sensors (days 3-7)
        if (
            sensor_type in ("cloud_cover_low", "cloud_cover_mid", "cloud_cover_high")
            or special_type == "hourly"
            or (day_offset is not None and day_offset >= 3)
        ):
            self._attr_entity_registry_enabled_default = False

        # Device info to group all sensors under one device
        location_name = entry.data.get(CONF_NAME, DEFAULT_NAME)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Open-Meteo CloudCover - {location_name}",
            manufacturer="Open-Meteo",
            model="CloudCover Station",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://open-meteo.com",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            sensor_data = self.coordinator.data.get(self._sensor_key)
            if sensor_data:
                # For this_hour, next_hour, and hourly sensors, return the value directly
                if self._special_type in ("this_hour", "next_hour", "hourly"):
                    return sensor_data.get("value")
                # For day-based sensors: cumulative metrics report the
                # authoritative daily total; others report the daily average.
                if self._sensor_type in CUMULATIVE_METRICS:
                    total = sensor_data.get("total")
                    if total is not None:
                        return total
                return sensor_data.get("avg")
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return SENSOR_TYPES[self._sensor_type]["unit"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        sensor_data = self.coordinator.data.get(self._sensor_key, {})
        metadata = self.coordinator.data.get("_metadata", {})

        # For this_hour, next_hour, and hourly sensors, return minimal attributes
        if self._special_type in ("this_hour", "next_hour", "hourly"):
            attributes = {
                "latitude": metadata.get("latitude"),
                "longitude": metadata.get("longitude"),
                "timezone": metadata.get("timezone"),
                "elevation": metadata.get("elevation"),
            }
            # Add hour_offset for hourly sensors
            if self._special_type == "hourly":
                attributes["hour_offset"] = sensor_data.get("hour_offset")
            return attributes

        # For day-based sensors, include full forecast data
        attributes = {
            "date": sensor_data.get("date"),
            "day_offset": sensor_data.get("day_offset"),
            "day_name": get_day_name(self._day_offset),
            "latitude": metadata.get("latitude"),
            "longitude": metadata.get("longitude"),
            "timezone": metadata.get("timezone"),
            "elevation": metadata.get("elevation"),
        }

        # Add hourly forecast data for this day
        hourly_data = sensor_data.get("hourly_data", {})
        if hourly_data:
            attributes["forecast_data"] = hourly_data
            attributes["min"] = sensor_data.get("min")
            attributes["max"] = sensor_data.get("max")
            attributes["avg"] = sensor_data.get("avg")
            # Cumulative metrics also expose the authoritative daily total.
            if self._sensor_type in CUMULATIVE_METRICS:
                total = sensor_data.get("total")
                if total is not None:
                    attributes["total"] = total

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._sensor_key in self.coordinator.data
        )
