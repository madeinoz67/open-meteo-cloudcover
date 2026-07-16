"""Config flow for Open-Meteo CloudCover integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    API_URL,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_coordinates(
    hass: HomeAssistant, latitude: float, longitude: float
) -> dict[str, Any]:
    """Validate the coordinates by making a test API call."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "cloud_cover",
    }

    try:
        async with (
            async_timeout.timeout(10),
            aiohttp.ClientSession() as session,
            session.get(API_URL, params=params) as response,
        ):
            response.raise_for_status()
            data = await response.json()

            if "hourly" not in data:
                raise ValueError("Invalid response from API")

            return True

    except aiohttp.ClientError as err:
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected exception: %s", err)
        raise UnknownError from err


class OpenMeteoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Open-Meteo CloudCover."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OpenMeteoOptionsFlowHandler:
        """Get the options flow for this handler."""
        return OpenMeteoOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_coordinates(
                    self.hass,
                    user_input[CONF_LATITUDE],
                    user_input[CONF_LONGITUDE],
                )

                # Check if already configured
                await self.async_set_unique_id(
                    f"{user_input[CONF_LATITUDE]}_{user_input[CONF_LONGITUDE]}"
                )
                self._abort_if_unique_id_configured()

                # Use location name for the title
                location_name = user_input.get(CONF_NAME, DEFAULT_NAME)

                return self.async_create_entry(title=location_name, data=user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_coords"
            except UnknownError:
                errors["base"] = "unknown"

        # Show form with defaults from Home Assistant configuration
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NAME,
                    default=DEFAULT_NAME,
                ): str,
                vol.Required(
                    CONF_LATITUDE,
                    default=self.hass.config.latitude,
                ): vol.Coerce(float),
                vol.Required(
                    CONF_LONGITUDE,
                    default=self.hass.config.longitude,
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


class OpenMeteoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Open-Meteo CloudCover."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate coordinates if they changed
                new_lat = user_input[CONF_LATITUDE]
                new_lon = user_input[CONF_LONGITUDE]
                old_lat = self.config_entry.data[CONF_LATITUDE]
                old_lon = self.config_entry.data[CONF_LONGITUDE]

                if new_lat != old_lat or new_lon != old_lon:
                    await validate_coordinates(self.hass, new_lat, new_lon)

                # Update the config entry with new data and title if name changed
                location_name = user_input.get(CONF_NAME, DEFAULT_NAME)

                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=location_name,
                    data={
                        CONF_NAME: location_name,
                        CONF_LATITUDE: new_lat,
                        CONF_LONGITUDE: new_lon,
                    },
                )

                # Trigger a coordinator refresh
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                return self.async_create_entry(title="", data={})

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_coords"
            except UnknownError:
                errors["base"] = "unknown"

        # Show form with current values
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NAME,
                    default=self.config_entry.data.get(CONF_NAME, DEFAULT_NAME),
                ): str,
                vol.Required(
                    CONF_LATITUDE,
                    default=self.config_entry.data.get(CONF_LATITUDE),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_LONGITUDE,
                    default=self.config_entry.data.get(CONF_LONGITUDE),
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class UnknownError(Exception):
    """Error to indicate an unknown error occurred."""
