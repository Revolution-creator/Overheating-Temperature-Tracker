"""
Run this ONCE per location, when you first add it, to create its starting
history file. After this, daily_update.py takes over.

Usage:
    python3 seed_location.py heathrow
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

    # We want a record for "yesterday" (the most recent day with fully
    # recorded weather). Its Trm is built from the 7 days BEFORE it
    # (yesterday-1 .. yesterday-7). We also need yesterday's own mean temp
    # for display, so the fetch range covers all 8 of those days.
    record_date = date.today() - timedelta(days=1)
    start = record_date - timedelta(days=7)
    end = record_date

    print(f"Fetching {start} to {end} for {location['name']}...")
    temps_by_date = get_historical_daily_mean_temps(
        location["lat"], location["lon"], TIMEZONE,
        start.isoformat(), end.isoformat()
    )

    record_date_str = record_date.isoformat()
    if record_date_str not in temps_by_date:
        raise SystemExit(f"No data yet for {record_date_str} - try again in a few hours.")

    # The 7 days strictly BEFORE record_date, most-recent-first: [Tod-1 ... Tod-7]
    prior_dates = sorted(
        (d for d in temps_by_date if d != record_date_str),
        reverse=True
    )
    if len(prior_dates) != 7:
        raise SystemExit(f"Expected 7 prior days of data, got {len(prior_dates)}. Try again later.")

    seven_days_temps = [temps_by_date[d] for d in prior_dates]
    trm = seed_running_mean_temp(seven_days_temps, ALPHA)
    tmax = upper_threshold_temp(trm, DELTA_T)

    record = {
        "date": record_date_str,
        "mean_temp_c": round(temps_by_date[record_date_str], 2),
        "trm_c": round(trm, 2),
        "tmax_c": round(tmax, 2),
    }

    with open(file_path, "w") as f:
        json.dump([record], f, indent=2)

    print(f"Seeded {file_path} with starting record: {record}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 seed_location.py <location_key>  e.g. python3 seed_location.py heathrow")
    seed(sys.argv[1])
