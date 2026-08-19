"""
Runs once a day (via GitHub Actions). For every location in config.py:
  1. reads that location's history file
  2. fetches yesterday's actual mean external air temperature
  3. updates Trm and Tmax using the TM52 formulas
  4. appends the new day's record and saves

If a location has no history file yet, it's skipped with a warning -
run seed_location.py for it first.
"""

import json
import os
from datetime import date, timedelta

from config import LOCATIONS, ALPHA, DELTA_T, DATA_DIR, TIMEZONE
from weather import get_recent_daily_mean_temps
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
    yesterday = date.today() - timedelta(days=1)

    if last_date >= yesterday:
        print(f"[skip] {location_key}: already up to date (last record {last_date}).")
        return

    temps_by_date = get_recent_daily_mean_temps(location["lat"], location["lon"], TIMEZONE)
    yesterday_str = yesterday.isoformat()

    if yesterday_str not in temps_by_date:
        print(f"[skip] {location_key}: weather data for {yesterday_str} not available yet, try again later.")
        return

    yesterday_mean_temp = temps_by_date[yesterday_str]
    new_trm = next_running_mean_temp(last_record["trm_c"], yesterday_mean_temp, ALPHA)
    new_tmax = upper_threshold_temp(new_trm, DELTA_T)

    record = {
        "date": yesterday_str,
        "mean_temp_c": round(yesterday_mean_temp, 2),
        "trm_c": round(new_trm, 2),
        "tmax_c": round(new_tmax, 2),
    }
    history.append(record)

    with open(file_path, "w") as f:
        json.dump(history, f, indent=2)

    print(f"[ok] {location_key}: added {record}")


if __name__ == "__main__":
    for key, loc in LOCATIONS.items():
        update_location(key, loc)
