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

### Smart Energy Monitoring & Analytics Dashboard

*Real-Time IoT Simulation &bull; Machine Learning Pipeline &bull; Interactive Telemetry*

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev)
[![MySQL](https://img.shields.io/badge/MySQL_8-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

<br/>

> **Academic Simulation Project**  
> Replays 2,075,259 real electricity readings from the UCI Household Power Consumption dataset (France, 2006–2010) through a virtual IoT streaming pipeline.

<br/>

</div>

---

<div align="center">

## Overview

</div>

EnergyPulse streams minute-level electricity readings through a **virtual IoT simulator**, processes them in real-time through an ML pipeline, and visualizes everything in a sleek dark-mode dashboard — live charts, anomaly alerts, forecasts, and sustainability recommendations.

<br/>

<div align="center">

## Dashboard Modules

</div>

<table>
<tr>
<td width="50%">

**Live Monitor**
- Real-time dataset replay at up to 3600x speed
- WebSocket streaming with auto-reconnect
- Animated power gauge and rolling chart
- Playback controls: Start &bull; Pause &bull; Resume &bull; Stop &bull; Seek

</td>
<td width="50%">

**Historical Analysis**
- Full 4-year dataset (2006–2010) exploration
- Hourly &amp; daily power trend charts
- Day-of-week &times; Hour heatmap (7&times;24 grid)
- Date range filter + CSV export

</td>
</tr>
<tr>
<td>

**Load Classification**
- Percentile-based labeling: Low / Moderate / High
- Class distribution &amp; accuracy metrics
- Training data statistics
- Real-time classification per reading

</td>
<td>

**Energy Forecast**
- ML or naive-baseline energy predictions
- Predicted vs actual comparison chart
- MAE, RMSE model metrics
- 24-hour ahead forecast

</td>
</tr>
<tr>
<td>

**Anomaly Alerts**
- Z-score, IQR &amp; absolute threshold detection
- Severity levels: Low / Medium / High / Critical
- Filter, acknowledge &amp; track alert history
- CSV export

</td>
<td>

**Recommendations**
- Data-driven sustainability tips
- Estimated savings in kWh &amp; ₹
- Peak-shift, standby &amp; appliance advice
- Pattern-based insights from 4 years of data

</td>
</tr>
<tr>
<td>

**Reports**
- Full KPI summary cards
- Daily trend bar chart
- Load class &amp; alert breakdown tables
- One-click CSV export for readings &amp; alerts

</td>
<td>

**Settings**
- Configurable electricity tariff (₹/kWh)
- Anomaly detection thresholds
- Simulator speed &amp; loop controls
- Real-time settings applied to pipeline

</td>
</tr>
</table>

---

<div align="center">

## Project Structure

</div>

```
EnergyPulse/
├── backend/                         FastAPI REST + WebSocket backend
│   └── app/
│       ├── main.py                  Entry point, CORS, WebSocket /ws/live
│       ├── config.py                Pydantic settings (reads .env)
│       ├── models/                  SQLAlchemy ORM — readings, alerts, aggregates, predictions
│       ├── routers/                 REST endpoints — readings, aggregates, alerts, ml, sim...
│       ├── schemas/                 Pydantic request/response schemas
│       ├── services/                DB session factory, WebSocket manager, ingestion pipeline
│       ├── simulator/               Async dataset replay engine (asyncio.Task)
│       ├── ml/                      Classifier, forecaster, and anomaly detector
│       └── preprocessing/           UCI dataset cleaning -> Parquet pipeline
├── frontend/                        React 18 + Vite SPA
│   └── src/
│       ├── pages/                   8 pages (Live, Historical, Classification, Forecast...)
│       ├── hooks/useWebSocket.js    Auto-reconnect WebSocket hook
│       └── api.js                   Axios client and blob CSV downloads
├── scripts/                         download_data, init_db, load_historical, run_ml_training
├── docker-compose.yml               MySQL 8 container configuration
├── requirements.txt                 Python dependencies
└── start.ps1                        One-click Windows launcher
```

---

<div align="center">

## Quick Start

</div>

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Backend API &amp; ML Pipeline |
| Node.js | 18+ | Frontend Dashboard |
| MySQL | 8+ **or** Docker | Relational Database |

<br/>

### Step 1 — Clone &amp; Install Dependencies

```bash
git clone https://github.com/Shwetapatil13/EnergyPulse.git
cd EnergyPulse

# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..
```

### Step 2 — Configure Environment

```bash
cp .env.example .env
# Edit .env -> set DB_HOST, DB_USER, DB_PASSWORD
```

### Step 3 — Start MySQL

```bash
docker-compose up -d mysql
```

### Step 4 — Initialize Database &amp; Preprocess Data

```bash
# 1. Create all DB tables
python scripts/init_db.py

# 2. Download UCI dataset (~130 MB ZIP)
python scripts/download_data.py

# 3. Clean & preprocess -> Parquet files (~2M rows)
python -m backend.app.preprocessing.cleaner

# 4. Bulk load into MySQL
#    --with-readings loads full 2M minute readings (~8 min, recommended)
python scripts/load_historical.py --with-readings
```

### Step 5 — Launch Application

**Windows (One-click script):**
```powershell
.\start.ps1
```

**Manual (Two separate terminals):**
```bash
# Terminal 1 — Backend API on :8000
python -m backend.app.main

# Terminal 2 — Frontend Dashboard on :5173
cd frontend && npm run dev
```

> Application Interface: **http://localhost:5173**  
> Interactive API Docs: **http://localhost:8000/docs**

---

<div align="center">

## API Endpoints

</div>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root health check |
| `GET` | `/health` | Health check and simulator status |
| `WS` | `/ws/live` | Live reading stream via WebSocket |
| `POST` | `/api/simulator/control` | Playback control: `start`, `pause`, `resume`, `stop`, `seek`, `set_speed` |
| `GET` | `/api/readings/` | Historical readings (paginated, filterable) |
| `GET` | `/api/readings/latest` | Last N readings for rolling telemetry |
| `GET` | `/api/readings/summary` | Aggregate metrics for specified date range |
| `GET` | `/api/readings/export/csv` | Download readings as CSV |
| `GET` | `/api/aggregates/hourly` | Hourly energy aggregates |
| `GET` | `/api/aggregates/daily` | Daily energy aggregates |
| `GET` | `/api/aggregates/heatmap` | 7&times;24 power heatmap matrix |
| `GET` | `/api/aggregates/comparison` | Period-over-period comparison |
| `GET` | `/api/alerts/` | Anomaly alerts (filterable by severity) |
| `GET` | `/api/alerts/summary` | Alert distribution by severity and type |
| `POST` | `/api/alerts/{id}/acknowledge` | Mark anomaly alert as acknowledged |
| `GET` | `/api/alerts/export/csv` | Download anomaly alerts as CSV |
| `GET` | `/api/ml/classification/summary` | Load class distribution summary |
| `GET` | `/api/ml/forecast` | Energy demand forecast |
| `GET` | `/api/ml/metrics` | Model training and validation metrics |
| `GET` | `/api/recommendations/` | Data-driven sustainability recommendations |
| `GET/PUT` | `/api/settings/` | System configuration and detection thresholds |
| `GET` | `/docs` | Interactive Swagger UI documentation |

---

<div align="center">

## Tech Stack

</div>

<table>
<tr>
<th>Layer</th><th>Technology</th><th>Version</th><th>Purpose</th>
</tr>
<tr><td rowspan="5"><strong>Backend</strong></td><td>FastAPI</td><td>0.115</td><td>REST API + WebSocket</td></tr>
<tr><td>SQLAlchemy</td><td>2.x</td><td>ORM + migrations</td></tr>
<tr><td>Uvicorn</td><td>0.30</td><td>ASGI server</td></tr>
<tr><td>Pandas + NumPy</td><td>2.x</td><td>Data processing</td></tr>
<tr><td>Scikit-learn</td><td>1.x</td><td>ML models</td></tr>
<tr><td rowspan="4"><strong>Frontend</strong></td><td>React</td><td>18</td><td>UI framework</td></tr>
<tr><td>Vite</td><td>5/8</td><td>Build tool (HMR)</td></tr>
<tr><td>Recharts</td><td>2.x</td><td>Data visualization</td></tr>
<tr><td>Axios</td><td>1.x</td><td>HTTP + blob downloads</td></tr>
<tr><td rowspan="2"><strong>Data Storage</strong></td><td>MySQL</td><td>8.0</td><td>Primary database</td></tr>
<tr><td>Apache Parquet</td><td>—</td><td>Preprocessed dataset cache</td></tr>
<tr><td><strong>DevOps</strong></td><td>Docker Compose</td><td>—</td><td>MySQL container</td></tr>
</table>

<br/>

**Dataset:** [UCI Individual Household Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)  
`2,075,259 rows` &bull; `1-minute intervals` &bull; `Dec 2006 – Nov 2010` &bull; French household

---

<div align="center">

## Important Disclaimers

</div>

> - **Simulation Scope:** All data replays the UCI dataset. No physical sensors or live smart meters are involved.  
> - **Tariff Model:** Cost estimates use an assumed flat rate of ₹8/kWh (configurable in Settings).  
> - **ML Classification:** Power demand classification is percentile-based (Low: &le; P33, Moderate: P33–P67, High: &gt; P67).  
> - **Recommendations:** Sustainability tips and projected savings are academic estimates, not financial advice.  
> - **Temporal Scope:** Dataset covers 2006–2010; comparison and aggregate features operate within this historical horizon.

---

<div align="center">

## Author

**Shweta Patil**

[![GitHub](https://img.shields.io/badge/@Shwetapatil13-181717?style=for-the-badge&logo=github)](https://github.com/Shwetapatil13)

<br/>

---

*EnergyPulse &bull; Distributed &amp; Autonomous Sensor Systems Course Project*

<br/>

![stars](https://img.shields.io/badge/dynamic/json?url=https://api.github.com/repos/Shwetapatil13/EnergyPulse&label=GitHub%20Stars&query=stargazers_count&color=3b82f6&style=flat-square&logo=github)
![forks](https://img.shields.io/badge/dynamic/json?url=https://api.github.com/repos/Shwetapatil13/EnergyPulse&label=Forks&query=forks_count&color=10b981&style=flat-square&logo=github)

</div>
