# Data provenance, license and time semantics

## Official trip records

Provider: Capital Bikeshare. Landing page: https://capitalbikeshare.com/system-data

Official download index: https://s3.amazonaws.com/capitalbikeshare-data/index.html

License: https://capitalbikeshare.com/data-license-agreement

The project uses the 24 files `YYYYMM-capitalbikeshare-tripdata.zip`, January 2024 through December 2025. Actual file names, sizes, UTC download times, S3 modification dates, SHA-256 hashes and ZIP members are recorded in `data/raw/trip_manifest.json`. Individual download records are retained beside each ZIP. `results/monthly_audit.csv` and `results/data_audit.json` document the actual schema, row accounting, missing fields and time anomalies.

The website describes upstream filtering of staff/test trips and very short trips. This project does not assume that description exactly matches the modern files: it audits the observed durations and does not delete valid departures solely because of an end-time issue or short duration. The target is departures present in the provider's released files, after the documented identity/start-time checks. It cannot measure attempts that failed because no bicycle was available.

Naive timestamps are interpreted as local America/New_York wall times. Because the data contain no per-trip UTC offset, ambiguous fall-back starts are retained in `data/processed/unresolved_dst_counts.csv`; the two corresponding UTC target hours each year are unavailable for modelling. Nonexistent spring-forward starts, if found, are excluded and counted in the audit. No UTC fold is guessed. Ordinary hours are aligned on a unique UTC grid. The 2024 leap day is included.

The project verifies complete monthly archives and that every expected local date has trips before interpreting empty non-ambiguous hourly bins as observed zeros. Missing target bins due to DST stay missing. These checks cannot prove there was no partial provider outage or unknown upstream filtering.

## Weather

Provider and documentation: https://open-meteo.com/en/docs/historical-weather-api

Endpoint: https://archive-api.open-meteo.com/v1/archive

Requested coordinate: latitude 38.9072, longitude -77.0369 (Washington, DC).

Explicit model: `era5` (hourly retrospective reanalysis; atmospheric grid about 0.25 degrees). The actual response coordinate and elevation, units, full request URL and retrieval timestamp are recorded in `weather_era5.json`, its `.download.json`, and `results/data_audit.json`. The response may use an interpolated/selected grid coordinate rather than exactly the requested point. No station-level representativeness is assumed.

Requested UTC dates extend from 2024-01-01 through 2026-01-02 to cover both local study years and the last interval-end rainfall value. Use UTC Unix timestamps and convert calendar features locally. This avoids relying on the API's ISO fixed-offset handling of daylight saving changes.

Variables: temperature at 2 m (C), relative humidity at 2 m (%), precipitation (mm), total cloud cover (%) and wind speed at 10 m (km/h). Temperature/humidity/cloud/wind use the interval-start timestamp. Precipitation at `t+1 hour` is the preceding-hour sum and therefore describes `[t,t+1 hour)`, the same target interval. This alignment uses retrospective information. It supports conditional estimation under known weather, not a test of a true advance weather forecast.

Attribution: Weather data by [Open-Meteo.com](https://open-meteo.com/), ERA5 reanalysis from the Copernicus Climate Change Service. API data are provided under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Modifications: variable selection, interval alignment of precipitation, and joining hourly values to derived departure counts. See https://open-meteo.com/en/licence and https://doi.org/10.24381/cds.adbb2d47 .

## Repository packaging

This is a non-commercial course study. Original monthly ZIPs are retained locally and excluded from Git. The repository includes the small derived hourly modelling table only as source material for the accompanying analysis, together with code and official acquisition instructions. It is not a stand-alone data mirror. Capital Bikeshare does not endorse this study. Third-party data remain subject to their own licenses; a software license must not be applied to those data.

The public license permits lawful analyses and has restrictions on publishing data as a stand-alone dataset. Consult the linked agreement before repackaging for a different purpose. This project avoids extracting private information, identifying riders, bypassing access restrictions, or scraping website content for data.
