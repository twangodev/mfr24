from __future__ import annotations

DEFAULT_BASE_URL = "https://my.flightradar24.com"
PROFILE_FLIGHTS_PATH = "/{username}/flights"
FLIGHT_LIST_PATH = "/public-scripts/flight-list/{username}/{start_row}//"
BATCH_SIZE = 50

PROFILE_TIMEOUT = 15.0
FLIGHT_LIST_TIMEOUT = 10.0

MAX_ATTEMPTS = 3
MAX_BACKOFF_SECONDS = 8.0

DEFAULT_CACHE_TTL_SECONDS = 6 * 60 * 60

DEFAULT_HEADERS = {
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
}
