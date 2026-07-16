"""Sanity tests for constants."""

from custom_components.open_meteo_cloudcover.const import (
    CUMULATIVE_METRICS,
    DOMAIN,
    SENSOR_TYPES,
)


def test_domain() -> None:
    """Domain matches the integration directory."""
    assert DOMAIN == "open_meteo_cloudcover"


def test_cumulative_metrics_are_known_sensor_types() -> None:
    """CUMULATIVE_METRICS must reference real sensor types."""
    assert frozenset({"evapotranspiration", "et0_fao_evapotranspiration"}) == CUMULATIVE_METRICS
    assert CUMULATIVE_METRICS.issubset(SENSOR_TYPES.keys())


def test_cumulative_metrics_are_millimetres() -> None:
    """Cumulative (daily-total) metrics are the mm/day evapotranspiration ones."""
    for metric in CUMULATIVE_METRICS:
        assert SENSOR_TYPES[metric]["unit"] == "mm"
