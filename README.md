<div align="center">

<br/>

```
███████╗███╗   ██╗███████╗██████╗  ██████╗██╗   ██╗██████╗ ██╗   ██╗██╗     ███████╗███████╗
██╔════╝████╗  ██║██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
█████╗  ██╔██╗ ██║█████╗  ██████╔╝██║  ███╗╚████╔╝ ██████╔╝██║   ██║██║     ███████╗█████╗  
██╔══╝  ██║╚██╗██║██╔══╝  ██╔══██╗██║   ██║ ╚██╔╝  ██╔═══╝ ██║   ██║██║     ╚════██║██╔══╝  
███████╗██║ ╚████║███████╗██║  ██║╚██████╔╝  ██║   ██║     ╚██████╔╝███████╗███████║███████╗
╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚═╝      ╚═════╝ ╚══════╝╚══════╝╚══════╝
```

## Smart Energy Monitoring & Analytics Dashboard

**Industrial-Grade IoT Simulation &bull; Real-Time Telemetry &bull; Machine Learning Pipeline**

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev)
[![MySQL](https://img.shields.io/badge/MySQL_8-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

<br/>

> **Academic Simulation Project**  
> Replays 2,075,259 real-world electricity readings from the UCI Household Power Consumption dataset (France, 2006–2010) through a high-frequency virtual IoT telemetry engine with real-time ML anomaly detection and energy forecasting.

<br/>

</div>

---

## Executive Overview

EnergyPulse is a full-stack, real-time energy telemetry and predictive intelligence platform designed to bridge the gap between smart electrical infrastructure and actionable analytics. Built on high-resolution smart meter readings recorded every minute over 4 years, EnergyPulse transforms massive time-series datasets into real-time operational intelligence.

The platform continuously replays historical consumption through an asynchronous streaming engine, processes incoming telemetry through an online machine learning pipeline, flags anomalies across multiple statistical vectors, and serves live analytical visualizations over low-latency WebSockets.

```
+---------------------------------------------------------------------------------+
|                           UCI DATASET (2,075,259 READINGS)                      |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                       Vectorized Data Cleaning & Parquet Cache                  |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                   Asynchronous Simulation Engine (1x - 3600x Replay)            |
+---------------------------------------------------------------------------------+
                         |                                       |
                         v (WebSocket Stream)                    v (Ingestion Pipeline)
+-----------------------------------------------+   +-----------------------------+
|           FastAPI Telemetry Hub               |   |     Online ML & Analytics   |
|         (/ws/live Broadcast Server)           |   | - Rolling Z-Score / IQR     |
+-----------------------------------------------+   | - Tercile Load Classifier   |
                         |                          | - Rolling Window Aggregates |
                         v                          +-----------------------------+
+-----------------------------------------------+                    |
|             React 18 Dashboard                |                    v
|  - Real-Time Power Gauges & Telemetry Charts  |   +-----------------------------+
|  - 7x24 Consumption Heatmaps & Predictions    |   |       MySQL 8 Database      |
|  - Multi-Zone Sub-Meter Energy Breakdown      |   |   (Aggregates, Alerts, ML)  |
+-----------------------------------------------+   +-----------------------------+
```

---

## System Capabilities & Core Features

### 1. Real-Time Telemetry & Virtual IoT Simulator
- **Accelerated Dataset Replay**: Stream 2M+ records at selectable multipliers from 1x up to 3600x real-time speed.
- **Bi-Directional Simulation Controls**: Full interactive transport controls including Start, Pause, Resume, Stop, and Time-Seek across the 4-year timeline.
- **Persistent WebSocket Feed**: Resilient WebSocket streaming (`/ws/live`) with automatic client-side reconnection, packet buffering, and sub-second UI updates.
- **Dynamic Telemetry Gauges**: Live active power gauge displaying instantaneous load, coupled with rolling 60-point real-time trend charts.

### 2. Multi-Vector Anomaly Detection Engine
- **Rolling Z-Score Detection**: Computes moving standard scores against dynamic temporal windows, grading severity into Low, Medium, High, and Critical alerts.
- **Interquartile Range (IQR) Fencing**: Identifies sudden non-Gaussian distribution spikes, isolating unusual energy spikes without false-alarm escalation.
- **Absolute Power Safeguards**: Monitors instantaneous load against customizable kW safety thresholds to detect breaker overload risks.
- **Delta-Rate Spike Analysis**: Evaluates rate-of-change between consecutive readings to catch rapid surges and equipment faults.
- **Alert Triage & Incident Audit**: Filter active alerts by severity or detection rule, acknowledge notifications, and export incident logs to CSV.

### 3. Machine Learning Demand Classification
- **Tercile Percentile Partitioning**: Statistically sound classification into Low, Moderate, and High consumption tiers based strictly on training distributions.
- **Leakage-Free Predictive Modeling**: Chronological 80/20 train-test splits ensuring zero future data contamination during model evaluation.
- **Random Forest & Decision Tree Benchmarks**: Supervised classification models trained purely on lag and temporal indicators (hour, weekday, weekend flag, season).
- **Comprehensive Validation Metrics**: Real-time access to model accuracy, precision, recall, F1-scores, and full confusion matrix outputs directly in the UI.

### 4. Next-Hour Energy Demand Forecasting
- **Multi-Model Regression Suite**: Next-hour kWh consumption prediction powered by Ridge Regression, Linear Regression, and Random Forest regressors.
- **Dual Baseline Comparisons**: Transparent benchmarking against Last-Observed (Lag 1h) and Same-Time-Yesterday (Lag 24h) baseline estimators.
- **Continuous Performance Auditing**: Real-time tracking of Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and R-squared performance metrics.
- **24-Hour Predictive Horizon**: Forward-looking demand trajectory curves plotted directly against actual historical load curves.

### 5. Multi-Zone Sub-Metering Analytics
- **Kitchen Appliance Zone (Sub-Meter 1)**: Granular tracking of microwave, dishwasher, and food preparation energy draws.
- **Laundry & Utility Zone (Sub-Meter 2)**: Dedicated telemetry for washing machines, tumble dryers, and refrigeration units.
- **Climate Control Zone (Sub-Meter 3)**: High-draw thermal monitoring for electric water heating, space heating, and air conditioning.
- **Unmetered Residual Calculation**: Mathematical isolation of ambient household base load and lighting loads by subtracting sub-meter totals from active power.

### 6. Historical Analytics & 7x24 Matrix Heatmaps
- **4-Year High-Resolution Archive**: Query and explore every minute between December 2006 and November 2010.
- **7x24 Day-Hour Matrix**: Interactive 168-cell heatmap mapping load intensity across all 7 days of the week against 24 hourly bins.
- **Temporal Rollup Aggregations**: Pre-indexed hourly and daily rollups enabling instantaneous trend rendering without heavy table scans.
- **Period Comparison Engine**: Side-by-side comparative analytics evaluating week-over-week and month-over-month consumption shifts.

### 7. Tariff-Aware Sustainability & Financial Recommendations
- **Configurable Tariff Engine**: Real-time electricity cost modeling with user-adjustable pricing (default ₹8.00/kWh).
- **Automated Peak Shaving Advice**: Identifies top three diurnal consumption peaks and quantifies the financial savings achievable via load shifting.
- **Vampire Load & Standby Audits**: Identifies continuous overnight baseload draws and computes potential annual savings from smart plug shutdowns.
- **Quantified ROI Projections**: Generates specific, data-backed kWh reduction targets paired with monetary savings estimates.

### 8. Executive Reports & Data Export
- **Comprehensive KPI Telemetry**: Instant summary cards for total consumption, peak active power, aggregate cost, and anomaly frequency.
- **Load Distribution Breakdowns**: Categorized tables showing percentages of time spent in Low, Moderate, and High consumption bands.
- **One-Click CSV Export**: Direct asynchronous downloads for raw time-series readings, aggregate summaries, and anomaly incident logs.

---

## Technical Stack Architecture

| Layer | Component | Version | Role in Architecture |
|-------|-----------|---------|----------------------|
| **Backend API** | FastAPI | 0.115 | High-throughput asynchronous REST endpoints and WebSocket stream management |
| **ASGI Server** | Uvicorn | 0.30 | Lightning-fast asynchronous server gateway interface |
| **ORM & Database Engine** | SQLAlchemy | 2.x | Database connection pooling, session lifecycle, and optimized SQL queries |
| **Data Processing** | Pandas &amp; NumPy | 2.x | High-speed vectorized data preprocessing, rollups, and rolling-window math |
| **Machine Learning** | Scikit-Learn | 1.x | Regression forecasting models, classification trees, and validation metrics |
| **Serialization** | PyArrow / Parquet | Latest | Fast columnar storage for the 2.07M raw reading cache |
| **Frontend Framework** | React | 18 | Declarative single-page application with functional component architecture |
| **Build & Tooling** | Vite | 5/8 | Fast Hot-Module-Replacement (HMR) development and optimized production bundling |
| **Data Visualization** | Recharts | 2.x | Responsive SVG telemetry curves, bar charts, gauges, and heatmap grids |
| **HTTP Client** | Axios | 1.x | REST API integration with custom interceptors and blob-based CSV download support |
| **Database** | MySQL | 8.0 | Primary relational storage with composite indexing on temporal columns |
| **DevOps & Containers** | Docker Compose | Latest | Reproducible, isolated multi-service orchestration |

---

## Dataset Specifications

EnergyPulse uses the canonical **Individual Household Electric Power Consumption** benchmark from the UC Irvine Machine Learning Repository.

```
Total Records      : 2,075,259 measurements
Sampling Frequency : 1-minute intervals
Timeline           : December 16, 2006 (17:24) to November 26, 2010 (21:02)
Geographic Scope   : Sceaux (suburb of Paris), France
Input Dimensions   : 9 variables
```

### Measured Variables

| Attribute | Unit | Description |
|-----------|------|-------------|
| `timestamp` | Datetime | Exact measurement timestamp formatted `YYYY-MM-DD HH:MM:SS` |
| `active_power_kw` | Kilowatts (kW) | Total active power consumed by the household |
| `reactive_power_kvar` | Kilovolt-Amperes Reactive | Total reactive power consumed |
| `voltage` | Volts (V) | Minute-averaged line voltage |
| `intensity_amp` | Amperes (A) | Minute-averaged household electrical current intensity |
| `sub_metering_1` | Watt-hours (Wh) | Kitchen electrical circuits (dishwasher, microwave, oven) |
| `sub_metering_2` | Watt-hours (Wh) | Laundry &amp; cooling (washing machine, dryer, refrigerator) |
| `sub_metering_3` | Watt-hours (Wh) | Climate control (electric water heater, air conditioning) |

---

## Project Directory Layout

```
EnergyPulse/
├── backend/                         FastAPI backend and machine learning pipelines
│   └── app/
│       ├── main.py                  FastAPI server entrypoint, middleware, and WebSocket router
│       ├── config.py                Pydantic settings loaded from environment variables
│       ├── models/                  SQLAlchemy ORM models (Readings, Alerts, Aggregates)
│       ├── routers/                 REST API routers (Readings, Alerts, ML, Simulator, Settings)
│       ├── schemas/                 Pydantic validation schemas for requests and responses
│       ├── services/                Database connection pooling, WebSocket manager, and ingestion
│       ├── simulator/               Asynchronous dataset replay engine (asyncio background task)
│       ├── ml/                      Classifier, regressor forecaster, and anomaly detector
│       └── preprocessing/           UCI dataset extraction, validation, and Parquet caching
├── frontend/                        React 18 single-page dashboard built with Vite
│   └── src/
│       ├── pages/                   Dashboard pages (Live, Historical, Forecast, Alerts, Reports...)
│       ├── hooks/useWebSocket.js    Custom auto-reconnecting WebSocket hook
│       └── api.js                   Axios client with base configuration and blob downloads
├── scripts/                         Operational scripts for setup, data extraction, and seeding
│   ├── init_db.py                   Database table creation and index initialization
│   ├── download_data.py             Automated UCI dataset download from official repository
│   ├── load_historical.py           Bulk dataset ingestion pipeline for MySQL
│   └── run_ml_training.py           Offline model training and evaluation script
├── docker-compose.yml               Docker container definition for MySQL 8
├── requirements.txt                 Pinned Python production dependencies
└── start.ps1                        One-click automated launch script for Windows
```

---

## Quick Start Guide

### System Prerequisites

| Requirement | Supported Version | Notes |
|-------------|-------------------|-------|
| Python | 3.10 or higher | Required for async backend runtime and ML libraries |
| Node.js | 18 or higher | Required for frontend build system |
| MySQL | 8.0 or Docker | Relational database storage |

<br/>

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Shwetapatil13/EnergyPulse.git
cd EnergyPulse
```

### Step 2 — Install Dependencies

```bash
# Install Python backend dependencies
pip install -r requirements.txt

# Install frontend Node dependencies
cd frontend && npm install && cd ..
```

### Step 3 — Environment Configuration

Create your `.env` configuration file from the template:

```bash
cp .env.example .env
```

Ensure your `.env` contains valid credentials:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=energy_user
DB_PASSWORD=energy_pass
DB_NAME=energypulse
```

### Step 4 — Launch MySQL Database

If using Docker Compose:
```bash
docker-compose up -d mysql
```

Or connect directly to your locally installed MySQL 8 server.

### Step 5 — Initialize Schema & Preprocess Data

```bash
# 1. Create tables and indexes
python scripts/init_db.py

# 2. Download UCI dataset (~130 MB ZIP)
python scripts/download_data.py

# 3. Clean and compile dataset into Parquet format
python -m backend.app.preprocessing.cleaner

# 4. Ingest historical readings into MySQL (recommended for full analytical capabilities)
python scripts/load_historical.py --with-readings
```

### Step 6 — Run the Application

#### Option A: One-Click Startup (Windows)
```powershell
.\start.ps1
```

#### Option B: Manual Multi-Terminal Startup

```bash
# Terminal 1 — Start FastAPI Server (Port 8000)
python -m backend.app.main

# Terminal 2 — Start Vite Development Server (Port 5173)
cd frontend && npm run dev
```

Navigate to:
- **Interactive Web Dashboard**: `http://localhost:5173`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`

---

## API Specification Reference

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | System root and service status verification |
| `GET` | `/health` | Health probe reporting database connectivity and simulator state |
| `WS` | `/ws/live` | Low-latency bi-directional WebSocket telemetry stream |
| `POST` | `/api/simulator/control` | Playback dispatcher: `start`, `pause`, `resume`, `stop`, `seek`, `set_speed` |
| `GET` | `/api/readings/` | Paginated historical time-series readings with date-range filters |
| `GET` | `/api/readings/latest` | Most recent telemetry window for real-time charting |
| `GET` | `/api/readings/summary` | Aggregate statistical summary (min, max, mean, sum) over range |
| `GET` | `/api/readings/export/csv` | Stream filtered historical readings as downloadable CSV file |
| `GET` | `/api/aggregates/hourly` | Rollup energy consumption grouped by hour |
| `GET` | `/api/aggregates/daily` | Rollup energy consumption grouped by calendar day |
| `GET` | `/api/aggregates/heatmap` | 7&times;24 day-of-week by hour load intensity matrix |
| `GET` | `/api/aggregates/comparison` | Period-over-period consumption variance and difference calculations |
| `GET` | `/api/alerts/` | Filterable anomaly incident log by severity and alert category |
| `GET` | `/api/alerts/summary` | Aggregate breakdown of alert counts grouped by severity |
| `POST` | `/api/alerts/{id}/acknowledge` | Update state flag of anomaly alert to acknowledged |
| `GET` | `/api/alerts/export/csv` | Download complete anomaly alert history as CSV file |
| `GET` | `/api/ml/classification/summary` | Load category distribution percentages (Low / Moderate / High) |
| `GET` | `/api/ml/forecast` | Next-hour demand forecast with actual vs. predicted curves |
| `GET` | `/api/ml/metrics` | Model evaluation scorecards (MAE, RMSE, R-squared) |
| `GET` | `/api/recommendations/` | Data-backed sustainability and peak-shaving recommendations |
| `GET` | `/api/settings/` | Fetch active tariff, detection thresholds, and simulator speed |
| `PUT` | `/api/settings/` | Update runtime settings and persist to configuration store |
| `GET` | `/docs` | Interactive Swagger UI API documentation and testing workbench |

---

## System Notes & Methodology

- **Academic Simulation Scope**: All telemetry and live readings are synthesized by replaying the UCI benchmark dataset. No physical hardware sensors or smart meters are connected.
- **Cost Estimation Model**: Monetary calculations apply an assumed flat rate of ₹8.00 per kilowatt-hour, fully configurable via the Settings module.
- **Classification Terciles**: Demand classification is bounded by the 33rd percentile (Low load) and 67th percentile (High load) derived strictly from training data.
- **Recommendation Caveat**: Projected kWh savings and financial estimates are derived from analytical heuristics and do not constitute professional energy auditing advice.
- **Historical Scope**: Comparative historical features operate within the December 2006 through November 2010 temporal horizon.

---

<div align="center">

## Author & Maintainer

**Shweta Patil**

[![GitHub Profile](https://img.shields.io/badge/@Shwetapatil13-181717?style=for-the-badge&logo=github)](https://github.com/Shwetapatil13)

<br/>

*EnergyPulse &bull; Distributed &amp; Autonomous Sensor Systems Course Project*

<br/>

[![GitHub Stars](https://img.shields.io/badge/dynamic/json?url=https://api.github.com/repos/Shwetapatil13/EnergyPulse&label=GitHub%20Stars&query=stargazers_count&color=3b82f6&style=flat-square&logo=github)](https://github.com/Shwetapatil13/EnergyPulse)
[![GitHub Forks](https://img.shields.io/badge/dynamic/json?url=https://api.github.com/repos/Shwetapatil13/EnergyPulse&label=Forks&query=forks_count&color=10b981&style=flat-square&logo=github)](https://github.com/Shwetapatil13/EnergyPulse)

</div>
