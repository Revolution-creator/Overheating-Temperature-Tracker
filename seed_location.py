"""
Run this ONCE per location, when you first add it, to create its starting
history file. After this, daily_update.py takes over.

Usage:
    python seed_location.py heathrow
"""

import json
import os
import sys
from datetime import date, timedelta

from config import LOCATIONS, ALPHA, DELTA_T, DATA_DIR, TIMEZONE
from weather import get_historical_daily_mean_temps
from tm52_calc import seed_running_mean_temp, upper_threshold_temp


def seed(location_key: str):
    if location_key not in LOCATIONS:
        raise SystemExit(f"Unknown location '{location_key}'. Check config.py.")

    location = LOCATIONS[location_key]
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, f"{location_key}.json")

    if os.path.exists(file_path):
        raise SystemExit(f"{file_path} already exists - delete it first if you really want to re-seed.")

    # Pull the 7 days before yesterday, so the first "real" Trm we save is for yesterday.
    yesterday = date.today() - timedelta(days=1)
    start = yesterday - timedelta(days=7)
    end = yesterday - timedelta(days=1)

    print(f"Fetching {start} to {end} for {location['name']}...")
    temps_by_date = get_historical_daily_mean_temps(
        location["lat"], location["lon"], TIMEZONE,
        start.isoformat(), end.isoformat()
    )

    # Order most-recent-first: [Tod-1, Tod-2, ..., Tod-7]
    ordered_dates = sorted(temps_by_date.keys(), reverse=True)
    if len(ordered_dates) != 7:
        raise SystemExit(f"Expected 7 days of data, got {len(ordered_dates)}. Try again later.")

    seven_days_temps = [temps_by_date[d] for d in ordered_dates]
    trm = seed_running_mean_temp(seven_days_temps, ALPHA)
    tmax = upper_threshold_temp(trm, DELTA_T)

    record = {
        "date": yesterday.isoformat(),
        "mean_temp_c": round(temps_by_date[yesterday.isoformat()], 2),
        "trm_c": round(trm, 2),
        "tmax_c": round(tmax, 2),
    }

    with open(file_path, "w") as f:
        json.dump([record], f, indent=2)

    print(f"Seeded {file_path} with starting record: {record}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python seed_location.py <location_key>  e.g. python seed_location.py heathrow")
    seed(sys.argv[1])
