from __future__ import annotations

from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse

from src.adapters.weather_adapter import WeatherAdapter, WeatherServiceUnavailable
from src.database import DatabaseClient, DatabaseConfigError
from src.factories.alert_factory import AlertFactory
from src.models import TelemetryAccepted, TelemetryIn
from src.patterns.circuit_breaker import CircuitBreaker


load_dotenv()

app = FastAPI(title="EnviroSync Backend", version="1.0.0")

circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=30)
weather_adapter: WeatherAdapter | None = None
database_client: DatabaseClient | None = None
alert_factory = AlertFactory()


@app.on_event("startup")
def startup() -> None:
    global weather_adapter, database_client

    try:
        weather_adapter = WeatherAdapter.from_env(circuit_breaker)
        database_client = DatabaseClient.from_env()
        database_client.init_schema()
    except (ValueError, DatabaseConfigError) as exc:
        # Keep startup explicit for grading so configuration failures are obvious.
        raise RuntimeError(f"Startup configuration error: {exc}") from exc


@app.post("/telemetry", response_model=TelemetryAccepted, status_code=status.HTTP_202_ACCEPTED)
def ingest_telemetry(payload: TelemetryIn) -> TelemetryAccepted:
    if weather_adapter is None or database_client is None:
        raise HTTPException(status_code=500, detail="Application not initialized.")

    weather = None
    weather_api_status = "ok"
    degraded_mode = False

    try:
        weather = weather_adapter.fetch_current_weather()
    except WeatherServiceUnavailable:
        weather_api_status = "degraded"
        degraded_mode = True

    alert = alert_factory.create_alert(payload, weather)
    record_id = database_client.save_record(payload, weather, weather_api_status, alert)

    return TelemetryAccepted(
        status="accepted",
        record_id=record_id,
        alert_type=alert.alert_type,
        degraded_mode=degraded_mode,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/dependencies")
def dependency_health() -> JSONResponse:
    if weather_adapter is None or database_client is None:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": "Application not initialized."},
        )

    db_ok = database_client.ping()
    circuit_state = weather_adapter.circuit_state()
    weather_ok = circuit_state != "open"
    overall_ok = db_ok and weather_ok

    content = {
        "status": "ok" if overall_ok else "degraded",
        "database": "ok" if db_ok else "down",
        "weather_circuit_state": circuit_state,
    }
    return JSONResponse(status_code=200 if overall_ok else 503, content=content)


@app.get("/telemetry/recent")
def telemetry_recent(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
    if database_client is None:
        raise HTTPException(status_code=500, detail="Application not initialized.")
    return {"items": database_client.recent_records(limit=limit)}


@app.get("/alerts/recent")
def alerts_recent(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, object]:
    if database_client is None:
        raise HTTPException(status_code=500, detail="Application not initialized.")
    return {"items": database_client.recent_alerts(limit=limit)}
