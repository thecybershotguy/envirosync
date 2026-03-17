from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests

from src.models import WeatherReading
from src.patterns.circuit_breaker import CircuitBreaker, CircuitOpenError


class WeatherServiceError(Exception):
    """Raised when OpenWeatherMap fails or returns invalid data."""


class WeatherServiceUnavailable(Exception):
    """Raised when weather service cannot be used and fallback is required."""


class WeatherAdapter:
    """
    Adapter around OpenWeatherMap:
    - Shields callers from raw API schema
    - Uses CircuitBreaker to protect external calls
    """

    OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(
        self,
        api_key: str,
        circuit_breaker: CircuitBreaker[requests.Response],
        lat: float = 43.2609,
        lon: float = -79.9192,
        timeout_seconds: int = 10,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OPENWEATHER_API_KEY is empty.")

        self.api_key = api_key.strip()
        self.circuit_breaker = circuit_breaker
        self.lat = lat
        self.lon = lon
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls, circuit_breaker: CircuitBreaker[requests.Response]) -> "WeatherAdapter":
        api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
        lat = float(os.getenv("WEATHER_LAT", "43.2609"))
        lon = float(os.getenv("WEATHER_LON", "-79.9192"))
        timeout_seconds = int(os.getenv("WEATHER_TIMEOUT_SECONDS", "10"))
        return cls(
            api_key=api_key,
            circuit_breaker=circuit_breaker,
            lat=lat,
            lon=lon,
            timeout_seconds=timeout_seconds,
        )

    def fetch_current_weather(self) -> WeatherReading:
        try:
            response = self.circuit_breaker.call(self._request_openweather)
        except CircuitOpenError as exc:
            raise WeatherServiceUnavailable(str(exc)) from exc
        except WeatherServiceError as exc:
            raise WeatherServiceUnavailable(str(exc)) from exc

        return self._to_weather_reading(response.json())

    def circuit_state(self) -> str:
        return self.circuit_breaker.stats().state

    def _request_openweather(self) -> requests.Response:
        params = {
            "lat": self.lat,
            "lon": self.lon,
            "appid": self.api_key,
            "units": "metric",
        }

        try:
            response = requests.get(self.OPENWEATHER_URL, params=params, timeout=self.timeout_seconds)
        except requests.RequestException as exc:
            raise WeatherServiceError(f"Network error while calling weather API: {exc}") from exc

        if response.status_code != 200:
            message = self._extract_api_message(response)
            raise WeatherServiceError(f"Weather API returned {response.status_code}: {message}")

        return response

    @staticmethod
    def _extract_api_message(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text.strip() or "No message"
        return str(payload.get("message", "No message")).strip()

    @staticmethod
    def _to_weather_reading(payload: dict[str, Any]) -> WeatherReading:
        try:
            temperature = float(payload["main"]["temp"])
            condition = str(payload["weather"][0]["main"])
            description = str(payload["weather"][0]["description"])
            unix_time = int(payload["dt"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise WeatherServiceError(f"Unexpected weather payload: {exc}") from exc

        observed_at_utc = datetime.fromtimestamp(unix_time, tz=timezone.utc)
        return WeatherReading(
            temperature=temperature,
            condition=condition,
            description=description,
            observed_at_utc=observed_at_utc,
        )
