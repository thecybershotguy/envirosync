![McMaster University](assets/mcmaster-logo.png)
# 

# **SFWRTECH 4SA3: Software Architecture**   **Project Milestone \#1 \- Proposal**  **EnviroSync**


- Karan Chauhan (400606872)

## **Proposed Software Name : EnviroSync**

## **Purpose & Target Audience**

EnviroSync is a backend IoT telemetry system designed to aggregate, normalize, and analyze localized environmental data. It bridges the gap between hyper-local sensor readings (from embedded devices like the M5StickC) and regional meteorological data. The system targets Hardware-in-the-Loop (HIL) test engineers (like myself) and server administrators who require automated verification that local environments (labs or server racks) maintain specific parameters relative to external weather conditions.

## **Functionalities**

* **Administrative Interface:** The application will primarily function as a headless backend service. Users will interact with the system via a Command-Line Interface (CLI) to view real-time logs, configure location settings, and check system status.  
* **Telemetry Ingestion:** The system will expose an HTTP endpoint to receive real-time JSON data packets (Temperature, Humidity, Air Pressure) "pushed" from a local IoT device (M5StickC Plus 2).  
* **Location Configuration:** Since the hardware is stationary, the system will allow the user to configure fixed coordinates (Latitude/Longitude) or a City Name in the application settings.  
* Regional Data Synchronization: Upon receiving valid local data, the application will query a third-party weather API to fetch the current regional conditions for the same timestamp.  
* **Data Normalization & Storage:** It will standardize the disparate data sources (local sensor vs. external API) into a unified structure and persist them into a cloud-based database for historical tracking.  
* **Threshold Analysis & Alerting:** The system will analyze incoming data against user-defined safety thresholds (e.g., "Alert if Lab Temp \> 25°C") and flag anomalies in the system logs.

## **Design Patterns**

### **1\. Adapter Pattern (Structural) :**

 Usage: The external weather service returns data in a complex, nested JSON schema that differs significantly from my local sensor's simple flat format. I will use the Adapter pattern to wrap the third-party API interface, translating its data into a common `WeatherReading` domain object. This allows the rest of the system to treat local and remote weather data interchangeably.

### **2\. Circuit Breaker Pattern (Behavioral/Stability)**

**Usage:** Since the application relies on an external third-party service (OpenWeatherMap) for data enrichment, network failures or API rate limits are inevitable. I will implement the Circuit Breaker pattern to wrap these network calls. If the external API fails repeatedly (e.g., timeout or 500 errors), the "Circuit" will open, and the system will immediately fallback to a "Degraded Mode" (logging only local data) without attempting the network call, preventing system-wide lag or crashes.

**Source:** [Martin Fowler \- CircuitBreaker](https://martinfowler.com/bliki/CircuitBreaker.html)

### **3\. Factory Method (Creational)**

**Usage:** To instantiate different types of internal alert events (e.g., `CriticalTemperatureAlert`, `PressureDropAlert`) based on the analysis of the incoming telemetry.

## **Proposed Technologies**

### **Programming Language: Python 3.10+**

* **Role:** Python will be used for the backend logic. It was chosen for its strong support for HTTP requests (`requests` or `https`), robust JSON handling, and structural pattern matching features introduced in version 3.10, which are beneficial for processing telemetry states.

### **Hardware Interface: ESPHome (running on M5StickC Plus 2\)**

* **Role:** The M5StickC Plus 2 (equipped with an ENV III Unit) will run ESPHome firmware. It will handle the hardware interfacing and utilize standard HTTP/REST protocols to push sensor readings to the Python backend.

### **Cloud Database: PostgreSQL**

* **Role:** A hosted PostgreSQL database (via Supabase or Neon) will be used to store the time-series log of environmental readings. It provides the persistence layer required for historical analysis.

### **Third-Party Web Service: OpenWeatherMap API**

* **Role:** This RESTful API will provide the "reference" data. The application will query this API using user-defined coordinates (stored in a configuration file) to retrieve the correct regional weather for comparison.


