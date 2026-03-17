from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
from psycopg2 import Error
from psycopg2.extras import Json, RealDictCursor

from src.models import Alert, TelemetryIn, WeatherReading, utc_now


class DatabaseConfigError(Exception):
    pass


class DatabaseClient:
    def __init__(self, database_url: str) -> None:
        if not database_url.strip():
            raise DatabaseConfigError("DATABASE_URL is empty.")
        self.database_url = database_url.strip()

    @classmethod
    def from_env(cls) -> "DatabaseClient":
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            raise DatabaseConfigError("DATABASE_URL is not set in .env.")
        return cls(database_url=database_url)

    @contextmanager
    def _connect(self) -> Iterator[psycopg2.extensions.connection]:
        connection = psycopg2.connect(self.database_url)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_records (
                    id BIGSERIAL PRIMARY KEY,
                    received_at_utc TIMESTAMPTZ NOT NULL,
                    edge_timestamp_utc TIMESTAMPTZ NULL,
                    device_id TEXT NULL,
                    local_temperature NUMERIC(6, 2) NOT NULL,
                    local_humidity NUMERIC(6, 2) NOT NULL,
                    local_pressure NUMERIC(7, 2) NOT NULL,
                    weather_temperature NUMERIC(6, 2) NULL,
                    weather_condition TEXT NULL,
                    weather_description TEXT NULL,
                    weather_observed_at_utc TIMESTAMPTZ NULL,
                    weather_api_status TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    alert_severity TEXT NOT NULL,
                    alert_message TEXT NOT NULL,
                    raw_payload JSONB NOT NULL
                )
                """
            )

    def save_record(
        self,
        telemetry: TelemetryIn,
        weather: WeatherReading | None,
        weather_api_status: str,
        alert: Alert,
    ) -> int:
        edge_timestamp = telemetry.timestamp
        received_at = utc_now()
        raw_payload: dict[str, Any] = telemetry.model_dump()

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO telemetry_records (
                    received_at_utc,
                    edge_timestamp_utc,
                    device_id,
                    local_temperature,
                    local_humidity,
                    local_pressure,
                    weather_temperature,
                    weather_condition,
                    weather_description,
                    weather_observed_at_utc,
                    weather_api_status,
                    alert_type,
                    alert_severity,
                    alert_message,
                    raw_payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    received_at,
                    edge_timestamp,
                    telemetry.device_id,
                    telemetry.temperature,
                    telemetry.humidity,
                    telemetry.pressure,
                    weather.temperature if weather else None,
                    weather.condition if weather else None,
                    weather.description if weather else None,
                    weather.observed_at_utc if weather else None,
                    weather_api_status,
                    alert.alert_type,
                    alert.severity,
                    alert.message,
                    Json(raw_payload),
                ),
            )
            inserted_id = cursor.fetchone()[0]

        return int(inserted_id)

    def ping(self) -> bool:
        try:
            with self._connect() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone()[0] == 1
        except Error:
            return False

    def recent_records(self, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    received_at_utc,
                    device_id,
                    local_temperature,
                    local_humidity,
                    local_pressure,
                    weather_temperature,
                    weather_condition,
                    weather_api_status,
                    alert_type,
                    alert_severity
                FROM telemetry_records
                ORDER BY id DESC
                LIMIT %s
                """,
                (safe_limit,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def recent_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    received_at_utc,
                    alert_type,
                    alert_severity,
                    alert_message
                FROM telemetry_records
                ORDER BY id DESC
                LIMIT %s
                """,
                (safe_limit,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]
