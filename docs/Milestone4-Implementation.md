![McMaster University](assets/mcmaster-logo.png)

# 

# **SFWRTECH 4SA3: Software Architecture**   **Project Milestone \#4 \- Final Implementation**  **EnviroSync**

# 1. Implementation Summary

For Milestone 4, I implemented the full EnviroSync pipeline. The M5StickC Plus 2 with ENV III sends local telemetry to a Python FastAPI backend. The backend enriches each reading using OpenWeatherMap (McMaster coordinates), generates an alert, and stores a unified record in PostgreSQL.

# 2. Implemented Components

- `src/main.py`: FastAPI app and runtime orchestration.
- `src/patterns/circuit_breaker.py`: Circuit Breaker implementation for weather API reliability.
- `src/adapters/weather_adapter.py`: Adapter that normalizes OpenWeatherMap responses.
- `src/factories/alert_factory.py`: Factory Method implementation for alert object creation.
- `src/database.py`: PostgreSQL schema setup and insert/query operations.
- `src/models.py`: shared request/response models and domain models.
- `edge/m5stickc_envirosync.yaml`: ESPHome configuration for M5StickC Plus 2 + ENV III.

# 3. Runtime Endpoints

- `POST /telemetry`: receives device payload, enriches data, applies alert logic, stores record, returns `202 Accepted`.
- `GET /health`: basic liveness endpoint.
- `GET /health/dependencies`: reports database status and weather circuit breaker state.
- `GET /telemetry/recent`: returns latest stored telemetry records.
- `GET /alerts/recent`: returns latest generated alerts.

# 4. Environment Configuration

I configured the backend with these `.env` values:

```env
DATABASE_URL=postgresql://username:password@host:5432/database_name
OPENWEATHER_API_KEY=your_openweather_api_key
WEATHER_LAT=43.2609
WEATHER_LON=-79.9192
WEATHER_TIMEOUT_SECONDS=10
```

# 5. How To Run

Install dependencies:

```powershell
uv sync
```

Run the FastAPI backend:

```powershell
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

# 6. Edge Device Push Configuration

I added the ESPHome file `edge/m5stickc_envirosync.yaml` for M5StickC Plus 2 + ENV III. The device sends JSON every 60 seconds to:

```text
http://<PYTHON_SERVER_IP>:8000/telemetry
```

Payload format:

```json
{
  "temperature": 24.2,
  "humidity": 45.1,
  "pressure": 1009.6
}
```

# 7. Pattern Usage in Final Code

- **Adapter Pattern:** `WeatherAdapter` converts raw OpenWeatherMap JSON into a simple `WeatherReading`.
- **Circuit Breaker Pattern:** external weather calls are protected to avoid repeated blocking failures.
- **Factory Method Pattern:** `AlertFactory` creates typed alerts such as safe state, high temperature, or pressure-related warnings.
