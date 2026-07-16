"""Constants for the Open-Meteo CloudCover integration."""

DOMAIN = "open_meteo_cloudcover"

# Configuration
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_FORECAST_DAYS = "forecast_days"
CONF_NAME = "name"

# Defaults
DEFAULT_NAME = "Home"
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds
DEFAULT_FORECAST_DAYS = 7  # Current day + next 6 days
MIN_FORECAST_DAYS = 1
MAX_FORECAST_DAYS = 7

# API
API_URL = "https://api.open-meteo.com/v1/forecast"

# Metrics whose daily value is a cumulative total (mm/day), not an average.
# Day-based sensors for these report the authoritative daily total from the
# Open-Meteo `daily=` API instead of the mean of hourly values (issue #1).
CUMULATIVE_METRICS = frozenset({"evapotranspiration", "et0_fao_evapotranspiration"})


# Day names for forecast sensors
def get_day_name(day_offset: int) -> str:
    """Get friendly name for day offset."""
    if day_offset == 0:
        return "Today"
    elif day_offset == 1:
        return "Tomorrow"
    else:
        return f"Day {day_offset}"


# Sensor types
SENSOR_TYPES = {
    "evapotranspiration": {
        "name": "Evapotranspiration",
        "unit": "mm",
        "icon": "mdi:water-outline",
        "device_class": None,
        "state_class": "measurement",
    },
    "soil_temperature_0cm": {
        "name": "Soil Temperature (0cm)",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    "soil_moisture_0_to_1cm": {
        "name": "Soil Moisture (0-1cm)",
        "unit": "m³/m³",
        "icon": "mdi:water-percent",
        "device_class": None,
        "state_class": "measurement",
    },
    "et0_fao_evapotranspiration": {
        "name": "FAO Evapotranspiration",
        "unit": "mm",
        "icon": "mdi:water-outline",
        "device_class": None,
        "state_class": "measurement",
    },
    "cloud_cover": {
        "name": "Cloud Cover",
        "unit": "%",
        "icon": "mdi:cloud",
        "device_class": None,
        "state_class": "measurement",
    },
    "cloud_cover_low": {
        "name": "Cloud Cover Low",
        "unit": "%",
        "icon": "mdi:cloud",
        "device_class": None,
        "state_class": "measurement",
    },
    "cloud_cover_mid": {
        "name": "Cloud Cover Mid",
        "unit": "%",
        "icon": "mdi:cloud",
        "device_class": None,
        "state_class": "measurement",
    },
    "cloud_cover_high": {
        "name": "Cloud Cover High",
        "unit": "%",
        "icon": "mdi:cloud",
        "device_class": None,
        "state_class": "measurement",
    },
    "direct_radiation": {
        "name": "Direct Radiation",
        "unit": "W/m²",
        "icon": "mdi:sun-wireless",
        "device_class": "irradiance",
        "state_class": "measurement",
    },
}
