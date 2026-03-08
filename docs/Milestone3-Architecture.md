![McMaster University](assets/mcmaster-logo.png)

# 

# **SFWRTECH 4SA3: Software Architecture**   **Project Milestone \#3 \- Architecture**  **EnviroSync**

# 5. Development Viewpoint

According to the course lectures, the Development Viewpoint focuses on the software module organization (packages and components).

This diagram shows how I organized the Python modules into clear packages. I split the code this way so each package has one clear responsibility. This makes the project easier to maintain now and easier to extend later when I add more sensors, adapters, or processing rules.

```mermaid
flowchart TB
    Controller["Controller<br/>Main orchestration logic"]
    Adapters["Adapters<br/>Weather API wrapper"]
    Patterns["Patterns<br/>Circuit Breaker"]
    Factories["Factories<br/>Alert creation rules"]
    Domain["Domain<br/>Telemetry / Weather / Alert models"]
    Storage["Storage<br/>Persistence layer"]

    Controller --> Adapters
    Controller --> Patterns
    Controller --> Factories
    Controller --> Domain
    Controller --> Storage
    Adapters --> Domain
    Factories --> Domain
```

# 6. Logical Viewpoint

According to the course lectures, the Logical Viewpoint focuses on the functionality for the user and support for functional requirements.

This activity flow shows the main functional pipeline of EnviroSync. The backend receives telemetry, validates it, then checks weather API availability before fetching regional weather. After that, it compares values to thresholds and saves the result. If the weather API is down, the system continues in degraded mode and still stores local telemetry.

```mermaid
flowchart TD
    A([Receive Telemetry]) --> B[Validate Data]
    B --> C{Valid payload?}
    C -- No --> Z[Reject and log validation error]
    C -- Yes --> D{Is weather API up?}
    D -- No --> E[Use degraded mode<br/>local telemetry only]
    D -- Yes --> F[Fetch Regional Weather]
    F --> G{Weather fetch success?}
    G -- No --> E
    G -- Yes --> H[Check Alert Thresholds]
    E --> H
    H --> I[Save to Database]
    I --> J([Done])
```

# 7. Process Viewpoint

According to the course lectures, the Process Viewpoint focuses on runtime behavior and communication between processes during execution.

This sequence diagram shows runtime communication for one telemetry reading. The M5StickC device sends data to the Python backend over HTTP. The backend then calls OpenWeatherMap over HTTPS and writes the combined record to PostgreSQL over TCP. To handle runtime stability, the backend uses request timeout values and can process many readings concurrently with independent request cycles.

```mermaid
sequenceDiagram
    participant Device as M5StickC Device
    participant Backend as Python Backend
    participant OWM as OpenWeatherMap API
    participant DB as PostgreSQL Database

    Device->>Backend: HTTP POST /telemetry (JSON temp/humidity/pressure)
    Backend->>Backend: Validate payload and timestamp
    Backend->>OWM: HTTPS GET /data/2.5/weather?lat=43.2609&lon=-79.9192&appid=API_KEY&units=metric
    alt Weather API responds in time
        OWM-->>Backend: HTTP 200 JSON weather payload
    else Timeout or error
        OWM--xBackend: Timeout / 5xx / network error
        Backend->>Backend: Circuit breaker fallback (degraded mode)
    end
    Backend->>DB: TCP SQL INSERT telemetry + weather/fallback status
    DB-->>Backend: INSERT OK
    Backend-->>Device: HTTP 202 Accepted
```
