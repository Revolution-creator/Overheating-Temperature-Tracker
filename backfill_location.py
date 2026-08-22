"""
Backfills a location's history from a chosen start date up to yesterday,
replacing whatever's currently in its data file. Run this ONCE whenever
you want to (re)build a longer history - e.g. from the start of 2026.

Usage:
    python3 backfill_location.py heathrow 2026-01-01
"""

import json
import os
import sys
from datetime import date, timedelta

from config import LOCATIONS, ALPHA, DELTA_T, DATA_DIR, TIMEZONE
from weather import get_historical_daily_mean_temps
from tm52_calc import seed_running_mean_temp, next_running_mean_temp, upper_threshold_temp


def backfill(location_key: str, start_date_str: str):
    if location_key not in LOCATIONS:
        raise SystemExit(f"Unknown location '{location_key}'. Check config.py.")

    location = LOCATIONS[location_key]
    start_date = date.fromisoformat(start_date_str)
    end_date = date.today() - timedelta(days=1)   # yesterday - last fully recorded day

    if start_date >= end_date:
        raise SystemExit("start_date must be before yesterday.")

    # Fetch everything needed in one go: 7 days before start_date (to seed Trm)
    # through end_date (so every day, including the last, has its own actual temp).
    fetch_start = start_date - timedelta(days=8)
    fetch_end = end_date

    print(f"Fetching {fetch_start} to {fetch_end} for {location['name']}... (this covers {(fetch_end - fetch_start).days + 1} days, may take a moment)")
    temps_by_date = get_historical_daily_mean_temps(
        location["lat"], location["lon"], TIMEZONE,
        fetch_start.isoformat(), fetch_end.isoformat()
    )

    # Seed Trm using the 7 days immediately before start_date.
    seed_dates = sorted(
        (d for d in temps_by_date if date.fromisoformat(d) < start_date),
        reverse=True
    )[:7]
    if len(seed_dates) != 7:
        raise SystemExit(f"Couldn't get 7 seed days before {start_date} - try an earlier start date.")

    seven_days_temps = [temps_by_date[d] for d in seed_dates]
    trm = seed_running_mean_temp(seven_days_temps, ALPHA)

    # Walk forward day by day from start_date to end_date, building the full history.
    records = []
    current = start_date
    previous_day_temp = temps_by_date[(start_date - timedelta(days=1)).isoformat()]

    while current <= end_date:
        current_str = current.isoformat()
        if current_str not in temps_by_date:
            print(f"[warning] missing data for {current_str}, stopping backfill there.")
            break

        trm = next_running_mean_temp(trm, previous_day_temp, ALPHA)
        tmax = upper_threshold_temp(trm, DELTA_T)

        records.append({
            "date": current_str,
            "mean_temp_c": round(temps_by_date[current_str], 2),
            "trm_c": round(trm, 2),
            "tmax_c": round(tmax, 2),
        })

        previous_day_temp = temps_by_date[current_str]
        current += timedelta(days=1)

    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, f"{location_key}.json")
    with open(file_path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Wrote {len(records)} days of history to {file_path} ({records[0]['date']} to {records[-1]['date']})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 backfill_location.py <location_key> <start_date YYYY-MM-DD>\n"
                          "e.g. python3 backfill_location.py heathrow 2026-01-01")
    backfill(sys.argv[1], sys.argv[2])
