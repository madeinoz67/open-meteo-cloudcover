# Changelog

All notable changes to the **Open-Meteo CloudCover** Home Assistant integration
are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (`YYYY.MM.PATCH`).

## [2026.7.2] - 2026-07-16

### Fixed
- **Fixed a 2026.7.1 regression that broke the integration.** 2026.7.1 requested `daily=evapotranspiration`, which is not a valid Open-Meteo daily variable (it is hourly-only), so every API call returned HTTP 400 and the integration failed setup ("Error communicating with Open-Meteo API: 400"). The daily request now asks only for `et0_fao_evapotranspiration` — the one cumulative metric with a daily API form — while `evapotranspiration`'s daily total uses the sum-of-hourly fallback.

### Added
- Unit test pinning the daily request params, plus a (default-skipped, `RUN_LIVE_API_TESTS=1`) live-API smoke test to guard against invalid request params in future.

## [2026.7.1] - 2026-07-16

### Fixed
- **Daily evapotranspiration sensors now report the daily total.** Day-based
  Evapotranspiration and FAO ET0 sensors previously returned the *average* of
  the hourly values (≈ daily total ÷ 24), under-reporting by ~24×. They now use
  the authoritative `daily=` totals from the Open-Meteo API, with the sum of
  hourly values as a fallback. ([#1](https://github.com/madeinoz67/open-meteo-cloudcover/issues/1))
- **Brand icon now displays in Home Assistant.** The icon had been moved out of
  the integration directory — where HA 2026.3+ looks for brand images — so it was
  not shown. Restored under `custom_components/open_meteo_cloudcover/brand/`.

### Added
- pytest test harness (7 tests) covering the daily-total fix end-to-end.
- GitHub Actions CI: runs ruff lint + format checks and the test suite
  (`Tests`), and HA/HACS validation (`Validate` — hassfest + hacs) on every
  push and pull request.

### Changed
- Codebase cleaned up to pass ruff lint and formatting (removed unused imports,
  combined nested context managers, added exception chaining).

## [2025.10.4] - 2025-10-31

### Fixed
- Redact location data in diagnostics.

## [2025.10.3] - 2025-10-31

### Added
- Direct radiation sensor.

## [2025.10.2] - 2025-10-31

### Changed
- Removed the `forecast_days` config option; the forecast window is fixed at 7 days.

## [2025.10.1] - 2025-10-31

### Added
- Major sensor expansion and migration to Calendar Versioning (1.x / 2.x → `YYYY.MM.PATCH`).

---

> Changes prior to `2025.10.1` (the 1.x / 2.x line) are available via
> [`git tag`](https://github.com/madeinoz67/open-meteo-cloudcover/tags).
