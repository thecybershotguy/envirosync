![McMaster University](docs/assets/mcmaster-logo.png)

# EnviroSync

**Student:** Karan Chauhan (400606872)  
**Course:** SFWRTECH 4SA3 - Software Architecture

## Milestone Documents
- [Milestone 1 - Proposal](docs/Milestone1-Proposal.md)
- [Milestone 2 - Architecture](docs/Milestone2-Architecture.md)
- [Milestone 3 - Architecture Viewpoints (4+1)](docs/Milestone3-Architecture.md)
- [Milestone 4 - Final Implementation](docs/Milestone4-Implementation.md)

## Project Purpose
EnviroSync is a backend IoT telemetry system that receives local readings from M5StickC Plus 2 + ENV III, enriches the readings with OpenWeatherMap data, applies alert rules, and stores unified records in PostgreSQL.

## Design Patterns Implemented
1. **Adapter Pattern** (`src/adapters/weather_adapter.py`): wraps OpenWeatherMap and returns a normalized `WeatherReading`.
2. **Circuit Breaker Pattern** (`src/patterns/circuit_breaker.py`): protects external weather calls with fail-fast behavior during repeated failures.
3. **Factory Method Pattern** (`src/factories/alert_factory.py`): generates alert objects from telemetry and weather context.

## Project Structure
- `src/main.py`: FastAPI application and endpoints.
- `src/database.py`: PostgreSQL schema setup and data persistence.
- `src/models.py`: shared request/response models and alert dataclasses.
- `edge/m5stickc_envirosync.yaml`: ESPHome config for M5StickC Plus 2 + ENV III push.

## Local Setup (Milestone 4 Runtime)

### 1. Install dependencies
```powershell
uv sync
```

### 2. Configure environment variables
Create `.env` in the project root:

```env
DATABASE_URL=postgresql://username:password@host:5432/database_name
OPENWEATHER_API_KEY=your_openweather_api_key
WEATHER_LAT=43.2609
WEATHER_LON=-79.9192
WEATHER_TIMEOUT_SECONDS=10
```

### 3. Run FastAPI server
```powershell
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test endpoints
Swagger UI:
```powershell
start http://127.0.0.1:8000/docs
```

Health:
```powershell
curl http://127.0.0.1:8000/health
```

Ingest telemetry:
```powershell
curl -X POST http://127.0.0.1:8000/telemetry ^
  -H "Content-Type: application/json" ^
  -d "{\"temperature\":24.2,\"humidity\":45.1,\"pressure\":1009.6,\"device_id\":\"m5stickc-plus2\"}"
```

Recent records:
```powershell
curl "http://127.0.0.1:8000/telemetry/recent?limit=10"
```

Recent alerts:
```powershell
curl "http://127.0.0.1:8000/alerts/recent?limit=10"
```

Note: `GET /` is not implemented, so `http://127.0.0.1:8000/` returns `{"detail":"Not Found"}` by design.

## M5StickC Plus 2 (ESPHome)
- Use `edge/m5stickc_envirosync.yaml`.
- Replace Wi-Fi credentials and `http://<PYTHON_SERVER_IP>:8000/telemetry`.
- Flash to M5StickC Plus 2 with ENV III connected via I2C.
- Device posts temperature, humidity, and pressure every 60 seconds.
