from __future__ import annotations

from src.models import (
    Alert,
    HighHumidityAlert,
    HighTemperatureAlert,
    PressureDropAlert,
    SafeStateAlert,
    TelemetryIn,
    TemperatureDeltaAlert,
    WeatherReading,
)


class AlertFactory:
    """
    Factory Method for creating domain alert objects from readings.
    """

    def __init__(
        self,
        high_temp_c: float = 27.0,
        high_humidity_pct: float = 70.0,
        low_pressure_hpa: float = 970.0,
        max_temp_delta_c: float = 10.0,
    ) -> None:
        self.high_temp_c = high_temp_c
        self.high_humidity_pct = high_humidity_pct
        self.low_pressure_hpa = low_pressure_hpa
        self.max_temp_delta_c = max_temp_delta_c

    def create_alert(self, telemetry: TelemetryIn, weather: WeatherReading | None) -> Alert:
        if telemetry.temperature > self.high_temp_c:
            return HighTemperatureAlert(
                alert_type="HighTemperatureAlert",
                severity="high",
                message=f"Local temperature {telemetry.temperature:.2f}C exceeds {self.high_temp_c:.2f}C.",
            )

        if telemetry.humidity > self.high_humidity_pct:
            return HighHumidityAlert(
                alert_type="HighHumidityAlert",
                severity="medium",
                message=f"Humidity {telemetry.humidity:.2f}% exceeds {self.high_humidity_pct:.2f}%.",
            )

        if telemetry.pressure < self.low_pressure_hpa:
            return PressureDropAlert(
                alert_type="PressureDropAlert",
                severity="medium",
                message=f"Pressure {telemetry.pressure:.2f}hPa is below {self.low_pressure_hpa:.2f}hPa.",
            )

        if weather is not None:
            delta = abs(telemetry.temperature - weather.temperature)
            if delta > self.max_temp_delta_c:
                return TemperatureDeltaAlert(
                    alert_type="TemperatureDeltaAlert",
                    severity="low",
                    message=f"Local vs regional temperature delta is {delta:.2f}C.",
                )

        return SafeStateAlert(
            alert_type="SafeStateAlert",
            severity="info",
            message="All values are inside configured thresholds.",
        )
