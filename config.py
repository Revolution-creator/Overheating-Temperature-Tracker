"""
Configuration for the TM52 overheating threshold tracker.

To add a new location later: add one line to LOCATIONS below.
Nothing else in the project needs to change.
"""

# TM52 / EN16798 adaptive comfort constants
ALPHA = 0.8      # smoothing constant for the running mean temperature
DELTA_T = 3.0    # acceptable range above comfort temp: Cat I=2, Cat II=3 (default), Cat III=4

# Locations to track.
# key: short code used for filenames (no spaces)
# name: human-readable label shown on the site
# lat/lon: coordinates for the Open-Meteo API
LOCATIONS = {
    "heathrow": {
        "name": "London Heathrow",
        "lat": 51.4700,
        "lon": -0.4543,
    },
    "birmingham": {
        "name": "Birmingham",
        "lat": 52.4862,
        "lon": -1.8904,
    },
    "nottingham": {
        "name": "Nottingham",
        "lat": 52.9548,
        "lon": -1.1581,
    },
    "newcastle": {
        "name": "Newcastle",
        "lat": 54.9783,
        "lon": -1.6178,
    },
}

DATA_DIR = "data"
TIMEZONE = "Europe/London"
HOURLY_PAST_DAYS = 30   # how many days of hourly data to keep on the merged chart
