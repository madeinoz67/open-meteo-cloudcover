# Open-Meteo CloudCover Integration for Home Assistant

A custom Home Assistant integration that provides cloud cover, weather, and soil condition sensors using the Open-Meteo API.

## Features

This integration creates sensors for:

- **Evapotranspiration** - Water evaporation from soil and plants (mm)
- **Soil Temperature (0cm)** - Surface soil temperature (°C)
- **Soil Moisture (0-1cm)** - Surface soil moisture content (m³/m³)
- **FAO Evapotranspiration** - Reference evapotranspiration using FAO method (mm)
- **Cloud Cover** - Total cloud coverage (%)
- **Cloud Cover Low** - Low-altitude cloud coverage (%)
- **Cloud Cover Mid** - Mid-altitude cloud coverage (%)
- **Cloud Cover High** - High-altitude cloud coverage (%)
- **Direct Radiation** - Direct solar radiation (W/m²)

The integration creates sensors for each metric in multiple time formats:
- **This Hour** - Current hour block value (e.g., at 11:30, shows 11:00 forecast)
- **Next Hour** - Next hour block value (e.g., at 11:30, shows 12:00 forecast)
- **Hourly Sensors** - Hours 1-24 from current time (disabled by default)
- **Daily Sensors** - Days 0-7 (Today through Day 7)
  - Days 0-2 (Today, Tomorrow, Day 2) enabled by default
  - Days 3-7 disabled by default

For **day-based** sensors, the reported value depends on the metric type:

- **Cumulative metrics** (`Evapotranspiration`, `FAO Evapotranspiration`) report the **daily total** (mm/day), taken from Open-Meteo's authoritative `daily=` values (falling back to the sum of hourly values). This is the value irrigation controllers such as [HA Smart Irrigation](https://github.com/jeroenterheijdt/hass-smart-irrigation) expect.
- **Instantaneous metrics** (`Cloud Cover`, `Soil Temperature`, `Soil Moisture`, `Direct Radiation`) report the **daily average**.

Each daily sensor also includes:
- Hourly forecast data for the day
- Min / max / average values
- A `total` attribute (cumulative metrics only)
- Location metadata (latitude, longitude, timezone, elevation)

Each hourly sensor includes:
- Specific hour forecast value
- Hour offset from current time
- Location metadata

## Installation

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/madeinoz67/open-meteo-cloudcover`
6. Select category: "Integration"
7. Click "Add"
8. Click "Install" on the Open-Meteo CloudCover card
9. Restart Home Assistant
10. Go to Settings → Devices & Services → Add Integration
11. Search for "Open-Meteo CloudCover"
12. Enter a location name and your coordinates (or use defaults)

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/madeinoz67/open-meteo-cloudcover/releases)
2. Extract the `custom_components/open_meteo_cloudcover` directory to your Home Assistant's `custom_components` directory
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration
5. Search for "Open-Meteo CloudCover"
6. Enter a location name and your coordinates (or use defaults)

## Configuration

The integration uses a config flow for setup:

1. **Name** - A friendly name for this location (used in the device name, e.g. "Home")
2. **Latitude** - Defaults to your Home Assistant instance location
3. **Longitude** - Defaults to your Home Assistant instance location

You can simply click "Submit" without changing anything to use your Home Assistant's configured location.

## Data Updates

The integration fetches data from the Open-Meteo API at hourly boundaries (XX:00:05). This alignment ensures fresh data is available at the start of each hour while respecting the API's free tier. The hourly cadence is fixed and not user-configurable.

## Sensors

All sensors are grouped under a single device called "Open-Meteo CloudCover" for easy organization.

**Total Sensors**: 306 sensors (30 enabled by default)
- This Hour sensors: 9 (6 enabled — Cloud Cover Low/Mid/High disabled)
- Next Hour sensors: 9 (6 enabled)
- Hourly sensors: 216 (24 hours × 9 metrics, all disabled by default)
- Daily sensors (Days 0-2): 27 (18 enabled — Cloud Cover Low/Mid/High disabled)
- Extended daily sensors (Days 3-7): 45 (disabled by default)

**Disabled by Default**:
- Cloud Cover Low, Mid, and High sensors (all time periods)
- All hourly forecast sensors (Hours 1-24)
- Extended daily forecast sensors (Days 3-7)

All disabled sensors can be enabled via the entity registry in Home Assistant.

### Example Daily Sensor Attributes — instantaneous metric (Cloud Cover)

The state is the daily average:

```yaml
state: 45.5            # daily average
date: "2026-07-16"
day_offset: 0
day_name: "Today"
latitude: -33.375
longitude: 115.625
timezone: "Australia/Perth"
elevation: 3.0
forecast_data:
  "2026-07-16T00:00": 42
  "2026-07-16T01:00": 43
  # ... (hourly data for the day)
  "2026-07-16T23:00": 48
min: 35
max: 58
avg: 45.5
```

### Example Daily Sensor Attributes — cumulative metric (FAO Evapotranspiration)

The state is the daily total:

```yaml
state: 5.6             # authoritative daily total (mm/day)
total: 5.6
avg: 0.23              # mean of hourly values (informational)
min: 0.0
max: 0.6
# date / metadata / forecast_data as above
```

### Example This Hour / Next Hour Sensor Attributes

```yaml
state: 45
latitude: -33.375
longitude: 115.625
timezone: "Australia/Perth"
elevation: 3.0
```

### Example Hourly Sensor Attributes

```yaml
state: 47
hour_offset: 5
latitude: -33.375
longitude: 115.625
timezone: "Australia/Perth"
elevation: 3.0
```

## API Information

This integration uses the free Open-Meteo API:
- **API Endpoint**: https://api.open-meteo.com/v1/forecast
- **Rate Limits**: The free tier should be sufficient for typical home use
- **Documentation**: https://open-meteo.com/en/docs

No API key is required.

## Use Cases

This integration is perfect for:

- **Garden Automation** - Use soil moisture and temperature to trigger irrigation
- **Cloud Coverage Monitoring** - Track cloud cover for solar panel optimization
- **Evapotranspiration Tracking** - Calculate crop water needs from daily ET totals (pairs well with irrigation controllers like HA Smart Irrigation)
- **Weather Monitoring** - Keep tabs on detailed weather conditions

### Example Automation

```yaml
automation:
  - alias: "Water Garden Based on Soil Moisture"
    trigger:
      - platform: numeric_state
        entity_id: sensor.soil_moisture_0_1cm_this_hour
        below: 0.15
    condition:
      - condition: numeric_state
        entity_id: sensor.evapotranspiration_this_hour
        above: 0.5
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.garden_irrigation
```

Entity IDs follow `sensor.<metric>_<period>` — e.g. `sensor.evapotranspiration_this_hour`, `sensor.fao_evapotranspiration_today`, `sensor.cloud_cover_hour_5`. Confirm the exact IDs under Settings → Devices & Services → Open-Meteo CloudCover.

## Troubleshooting

### No Data Received

If sensors show as unavailable:
1. Check your internet connection
2. Verify the Open-Meteo API is accessible: https://api.open-meteo.com
3. Check Home Assistant logs for error messages

### Invalid Coordinates

Ensure your coordinates are valid:
- Latitude: -90 to 90
- Longitude: -180 to 180

### API Errors

If you see API errors in the logs:
1. Check if the Open-Meteo service is operational
2. Verify network connectivity

## Development

This integration follows Home Assistant's best practices:

- Uses `DataUpdateCoordinator` for efficient API polling
- Implements proper error handling and retry logic
- Provides comprehensive device and sensor information
- Uses async/await patterns throughout
- Includes proper typing hints
- Test suite (`tests/`) plus ruff lint/format checks run via GitHub Actions (`.github/workflows/`)

## Credits

- Weather data provided by [Open-Meteo](https://open-meteo.com)
- Integration developed using Home Assistant's integration guidelines

## License

This project is licensed under the [MIT License](LICENSE).

## Support

For issues or feature requests, please open an issue on the [GitHub repository](https://github.com/madeinoz67/open-meteo-cloudcover/issues).
