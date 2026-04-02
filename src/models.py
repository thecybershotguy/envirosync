from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class TelemetryIn(BaseModel):
    temperature: float = Field(..., description="Local sensor temperature in C")
    humidity: float = Field(..., description="Local sensor humidity percent")
    pressure: float = Field(..., description="Local sensor pressure hPa")
    device_id: Optional[str] = Field(default=None, description="Optional edge device id")
    timestamp: Optional[datetime] = Field(default=None, description="Optional edge timestamp")


@dataclass(slots=True)
class WeatherReading:
    temperature: float
    condition: str
    description: str
    observed_at_utc: datetime


@dataclass(slots=True)
class Alert:
    alert_type: str
    severity: str
    message: str


@dataclass(slots=True)
class HighTemperatureAlert(Alert):
    pass


@dataclass(slots=True)
class HighHumidityAlert(Alert):
    pass


@dataclass(slots=True)
class PressureDropAlert(Alert):
    pass


@dataclass(slots=True)
class TemperatureDeltaAlert(Alert):
    pass


@dataclass(slots=True)
class SafeStateAlert(Alert):
    pass


class TelemetryAccepted(BaseModel):
    status: str
    record_id: int
    alert_type: str
    degraded_mode: bool


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
