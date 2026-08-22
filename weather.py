"""
Fetches external air temperature from Open-Meteo (free, no API key needed).

Two endpoints are used:
- The FORECAST API (api.open-meteo.com) also returns the last few days of
  ACTUAL recorded data via the 'past_days' parameter - this is what the
  daily update script uses to get "yesterday's" mean temperature, and what
  the hourly chart uses too.
- The ARCHIVE API (archive-api.open-meteo.com) is used only for backfilling
  a longer run of past days when a location is first set up.
"""

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def get_recent_daily_mean_temps(lat: float, lon: float, timezone: str, past_days: int = 5) -> dict:
    """
    Returns {date_string: mean_temp_celsius} for the last `past_days` days
    (not including today, which isn't finished yet).
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_mean",
        "past_days": past_days,
        "forecast_days": 1,
        "timezone": timezone,
    }
    response = requests.get(FORECAST_URL, params=params, timeout=30)
    response.raise_for_status()
    daily = response.json()["daily"]
    return dict(zip(daily["time"], daily["temperature_2m_mean"]))


def get_recent_hourly_temps(lat: float, lon: float, timezone: str, past_days: int = 7) -> list:
    """
    Returns a list of [timestamp_string, temp_celsius] pairs, hour by hour,
    for the last `past_days` days. Used for the merged chart - NOT used in
    the TM52 calculation itself, which only needs daily means.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "past_days": past_days,
        "forecast_days": 0,
        "timezone": timezone,
    }
    response = requests.get(FORECAST_URL, params=params, timeout=30)
    response.raise_for_status()
    hourly = response.json()["hourly"]
    return list(zip(hourly["time"], hourly["temperature_2m"]))


def get_historical_daily_mean_temps(lat: float, lon: float, timezone: str,
                                     start_date: str, end_date: str) -> dict:
    """
    Returns {date_string: mean_temp_celsius} for a specific date range.
    Used for seeding/backfilling a location with a longer run of history.
    Dates are 'YYYY-MM-DD' strings.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_mean",
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone,
    }
    response = requests.get(ARCHIVE_URL, params=params, timeout=30)
    response.raise_for_status()
    daily = response.json()["daily"]
    return dict(zip(daily["time"], daily["temperature_2m_mean"]))
