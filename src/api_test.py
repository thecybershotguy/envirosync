from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
import requests


OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
MCMASTER_LAT = 43.2609
MCMASTER_LON = -79.9192
REQUEST_TIMEOUT_SECONDS = 10


def get_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY is not set. Add it to your .env file.")
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY is empty after trimming whitespace.")
    return api_key


def main() -> int:
    try:
        api_key = get_api_key()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    params = {
        "lat": MCMASTER_LAT,
        "lon": MCMASTER_LON,
        "appid": api_key,
        "units": "metric",
    }

    try:
        response = requests.get(
            OPENWEATHER_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.Timeout:
        print("Request timed out while calling OpenWeatherMap.", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"Network error while calling OpenWeatherMap: {exc}", file=sys.stderr)
        return 1

    if response.status_code != 200:
        api_message = ""
        try:
            error_payload = response.json()
            api_message = str(error_payload.get("message", "")).strip()
        except ValueError:
            api_message = response.text.strip()

        if response.status_code == 401:
            print(
                f"OpenWeatherMap returned 401 Unauthorized. API message: {api_message or 'N/A'}",
                file=sys.stderr,
            )
        else:
            print(
                f"OpenWeatherMap returned status {response.status_code}. API message: {api_message or 'N/A'}",
                file=sys.stderr,
            )
        return 1

    try:
        payload = response.json()
        temperature = payload["main"]["temp"]
        condition = payload["weather"][0]["main"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        print(f"Failed to parse weather response: {exc}", file=sys.stderr)
        return 1

    print(
        f"OpenWeatherMap connection successful for McMaster University ({MCMASTER_LAT}, {MCMASTER_LON})"
    )
    print(f"Current temperature: {temperature} C")
    print(f"Current condition: {condition}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
