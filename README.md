# EnviroSync
**Student:** Karan Chauhan (400606872)
**Course:** SFWRTECH 4SA3 - Software Architecture

## Project Purpose
EnviroSync is a backend IoT telemetry system that aggregates local sensor data (from M5StickC) and compares it against regional weather data (OpenWeatherMap) to ensure environmental consistency in HIL test labs.

## Architecture & Patterns
1. **Adapter Pattern:** Wraps the OpenWeatherMap API.
2. **Circuit Breaker:** Prevents cascading failures when the external API is down.
3. **Factory Method:** Generates specific Alert objects based on telemetry.