"""
Runs once a day (via GitHub Actions). For every location in config.py:
  1. reads that location's history file
  2. works out Trm for the next day using ONLY the previous record
     (this is the correct TM52 convention - today's threshold doesn't
     depend on today's own weather, only on prior days)
  3. fetches that new day's actual mean temperature, for display/comparison
  4. appends the new day's record and saves

If a location has no history file yet, it's skipped with a warning -
run seed_location.py for it first.
"""

import json
import os
from datetime import date, timedelta

from config import LOCATIONS, ALPHA, DELTA_T, DATA_DIR, TIMEZONE, HOURLY_PAST_DAYS
from weather import get_recent_daily_mean_temps, get_recent_hourly_temps
from tm52_calc import next_running_mean_temp, upper_threshold_temp


def update_location(location_key: str, location: dict):
    file_path = os.path.join(DATA_DIR, f"{location_key}.json")

    if not os.path.exists(file_path):
        print(f"[skip] {location_key}: no history file yet - run seed_location.py {location_key} first.")
        return

    with open(file_path) as f:
        history = json.load(f)

    last_record = history[-1]
    last_date = date.fromisoformat(last_record["date"])
    new_date = last_date + timedelta(days=1)

    if new_date > date.today():
        print(f"[skip] {location_key}: already up to date (last record {last_date}).")
        return

    new_trm = next_running_mean_temp(last_record["trm_c"], last_record["mean_temp_c"], ALPHA)
    new_tmax = upper_threshold_temp(new_trm, DELTA_T)

    temps_by_date = get_recent_daily_mean_temps(location["lat"], location["lon"], TIMEZONE)
    new_date_str = new_date.isoformat()

    if new_date_str not in temps_by_date:
        print(f"[skip] {location_key}: weather data for {new_date_str} not available yet, try again later.")
        return

    record = {
        "date": new_date_str,
        "mean_temp_c": round(temps_by_date[new_date_str], 2),
        "trm_c": round(new_trm, 2),
        "tmax_c": round(new_tmax, 2),
    }
    history.append(record)

    with open(file_path, "w") as f:
        json.dump(history, f, indent=2)

    print(f"[ok] {location_key}: added {record}")


def update_hourly(location_key: str, location: dict):
    """
    Overwrites the hourly file each run with the latest rolling window -
    this is a display-only dataset, not part of the TM52 calculation,
    so there's no need to keep it forever or append to it.
    """
    file_path = os.path.join(DATA_DIR, f"{location_key}_hourly.json")
    hourly_pairs = get_recent_hourly_temps(location["lat"], location["lon"], TIMEZONE, HOURLY_PAST_DAYS)

    records = [
        {"time": timestamp, "temp_c": round(temp, 2)}
        for timestamp, temp in hourly_pairs
        if temp is not None
    ]

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"[ok] {location_key}: hourly data refreshed ({len(records)} points)")


if __name__ == "__main__":
    for key, loc in LOCATIONS.items():
        update_location(key, loc)
        update_hourly(key, loc)
