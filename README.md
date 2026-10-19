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

### ⚡ Smart Energy Monitoring & Analytics Dashboard

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev)
[![MySQL](https://img.shields.io/badge/MySQL_8-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

<br/>

> 🔬 **Academic Simulation Project** · Replays 2,075,259 real electricity readings from the  
> UCI Household Power Consumption dataset (France, 2006–2010) through a virtual IoT pipeline.

<br/>

</div>

---

<div align="center">

## 🎯 What Does It Do?

</div>

EnergyPulse streams minute-level electricity readings through a **virtual IoT simulator**, processes them in real-time through an ML pipeline, and visualizes everything in a sleek dark-mode dashboard — live charts, anomaly alerts, forecasts, and sustainability recommendations.

<br/>

<div align="center">

## 📸 Dashboard Pages

</div>

<table>
<tr>
<td width="50%">

**⚡ Live Monitor**
- Real-time dataset replay at up to 3600× speed
- WebSocket streaming with auto-reconnect
- Animated power gauge and rolling chart
- Playback controls: Start · Pause · Resume · Stop · Seek

</td>
<td width="50%">

**📊 Historical Analysis**
- Full 4-year dataset (2006–2010) exploration
- Hourly & daily power trend charts
- Day-of-week × Hour heatmap (7×24 grid)
- Date range filter + CSV export

</td>
</tr>
<tr>
<td>

**🧠 Load Classification**
- Percentile-based labeling: Low / Moderate / High
- Class distribution & accuracy metrics
- Training data statistics
- Real-time classification per reading

</td>
<td>

**📈 Energy Forecast**
- ML or naive-baseline energy predictions
- Predicted vs actual comparison chart
- MAE, RMSE model metrics
- 24-hour ahead forecast

</td>
</tr>
<tr>
<td>

**🔔 Anomaly Alerts**
- Z-score, IQR & absolute threshold detection
- Severity levels: Low / Medium / High / Critical
- Filter, acknowledge & track alert history
- CSV export

</td>
<td>

**💡 Recommendations**
- Data-driven sustainability tips
- Estimated savings in kWh & ₹
- Peak-shift, standby & appliance advice
- Pattern-based insights from 4 years of data

</td>
</tr>
<tr>
<td>

**📄 Reports**
- Full KPI summary cards
- Daily trend bar chart
- Load class & alert breakdown tables
- One-click CSV export for readings & alerts

</td>
<td>

**⚙️ Settings**
- Configurable electricity tariff (₹/kWh)
- Anomaly detection thresholds
- Simulator speed & loop controls
- Real-time settings applied to pipeline

</td>
</tr>
</table>

---

<div align="center">

## 🗂️ Project Structure

</div>

```
EnergyPulse/
│
├── 🐍  backend/                     FastAPI REST + WebSocket backend
│    └── app/
│         ├── main.py                Entry point, CORS, WebSocket /ws/live
│         ├── config.py              Pydantic settings (reads .env)
│         ├── models/                SQLAlchemy ORM — readings, alerts, aggregates, predictions
│         ├── routers/               REST endpoints — readings, aggregates, alerts, ml, sim…
│         ├── schemas/               Pydantic request/response schemas
│         ├── services/              DB session factory, WebSocket manager, ingestion pipeline
│         ├── simulator/             Async dataset replay engine (asyncio.Task)
│         ├── ml/                    Classifier · Forecaster · Anomaly Detector
│         └── preprocessing/        UCI dataset cleaning → Parquet pipeline
│
├── ⚛️   frontend/                    React 18 + Vite SPA
│    └── src/
│         ├── pages/                 8 pages (Live, Historical, Classification, Forecast…)
│         ├── hooks/useWebSocket.js  Auto-reconnect WebSocket hook
│         └── api.js                 Axios client + blob CSV downloads
│
├── 📜  scripts/                     download_data · init_db · load_historical · run_ml_training
├── 🐳  docker-compose.yml           MySQL 8 container
├── 📋  requirements.txt             All Python dependencies
└── 🚀  start.ps1                    One-click Windows launcher
```

---

<div align="center">

## ⚙️ Quick Start

</div>

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Backend |
| Node.js | 18+ | Frontend |
| MySQL | 8+ **or** Docker | Database |

<br/>

### Step 1 — Clone & Install

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
# Edit .env → set DB_HOST, DB_USER, DB_PASSWORD
```

### Step 3 — Start MySQL

```bash
docker-compose up -d mysql
```

### Step 4 — Load the Dataset

```bash
# 1. Create all DB tables
python scripts/init_db.py

# 2. Download UCI dataset (~130 MB ZIP)
python scripts/download_data.py

# 3. Clean & preprocess → Parquet files (~2M rows)
python -m backend.app.preprocessing.cleaner

# 4. Bulk load into MySQL
#    --with-readings loads full 2M minute readings (~8 min, recommended)
python scripts/load_historical.py --with-readings
```

### Step 5 — Launch 🚀

**Windows (one command):**
```powershell
.\start.ps1
```

**Manual (two terminals):**
```bash
# Terminal 1 — Backend API on :8000
python -m backend.app.main

# Terminal 2 — Frontend on :5173
cd frontend && npm run dev
```

> Open **http://localhost:5173** · API docs at **http://localhost:8000/docs**

---

<div align="center">

## 📡 API Endpoints

</div>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root health check |
| `GET` | `/health` | Health + simulator state |
| `WS` | `/ws/live` | 🔴 Live reading stream |
| `POST` | `/api/simulator/control` | `start` · `pause` · `resume` · `stop` · `seek` · `set_speed` |
| `GET` | `/api/readings/` | Historical readings (paginated, filterable) |
| `GET` | `/api/readings/latest` | Last N readings for live chart |
| `GET` | `/api/readings/summary` | Aggregate stats for date range |
| `GET` | `/api/readings/export/csv` | ⬇️ Download readings as CSV |
| `GET` | `/api/aggregates/hourly` | Hourly energy aggregates |
| `GET` | `/api/aggregates/daily` | Daily energy aggregates |
| `GET` | `/api/aggregates/heatmap` | 7×24 power heatmap matrix |
| `GET` | `/api/aggregates/comparison` | Period-over-period comparison |
| `GET` | `/api/alerts/` | Anomaly alerts (severity filter) |
| `GET` | `/api/alerts/summary` | Counts by severity & type |
| `POST` | `/api/alerts/{id}/acknowledge` | Mark alert as read |
| `GET` | `/api/alerts/export/csv` | ⬇️ Download alerts as CSV |
| `GET` | `/api/ml/classification/summary` | Load class distribution |
| `GET` | `/api/ml/forecast` | Energy forecast |
| `GET` | `/api/ml/metrics` | Model training metrics |
| `GET` | `/api/recommendations/` | Sustainability recommendations |
| `GET/PUT` | `/api/settings/` | App configuration |
| `GET` | `/docs` | 📖 Swagger UI |

---

<div align="center">

## 🧰 Tech Stack

</div>

<table>
<tr>
<th>Layer</th><th>Technology</th><th>Version</th><th>Purpose</th>
</tr>
<tr><td rowspan="5">🐍 Backend</td><td>FastAPI</td><td>0.115</td><td>REST API + WebSocket</td></tr>
<tr><td>SQLAlchemy</td><td>2.x</td><td>ORM + migrations</td></tr>
<tr><td>Uvicorn</td><td>0.30</td><td>ASGI server</td></tr>
<tr><td>Pandas + NumPy</td><td>2.x</td><td>Data processing</td></tr>
<tr><td>Scikit-learn</td><td>1.x</td><td>ML models</td></tr>
<tr><td rowspan="4">⚛️ Frontend</td><td>React</td><td>18</td><td>UI framework</td></tr>
<tr><td>Vite</td><td>5/8</td><td>Build tool (HMR)</td></tr>
<tr><td>Recharts</td><td>2.x</td><td>Data visualisation</td></tr>
<tr><td>Axios</td><td>1.x</td><td>HTTP + blob downloads</td></tr>
<tr><td rowspan="2">🗄️ Data</td><td>MySQL</td><td>8.0</td><td>Primary database</td></tr>
<tr><td>Apache Parquet</td><td>—</td><td>Preprocessed dataset cache</td></tr>
<tr><td>📦 DevOps</td><td>Docker Compose</td><td>—</td><td>MySQL container</td></tr>
</table>

<br/>

**Dataset:** [UCI Individual Household Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)  
`2,075,259 rows` · `1-minute intervals` · `Dec 2006 – Nov 2010` · French household

---

<div align="center">

## ⚠️ Important Disclaimers

</div>

> 🔬 **Simulation only** — All data replays the UCI dataset. No physical sensors are involved.  
> 💰 **Assumed tariff** — Cost estimates use ₹8/kWh flat rate (configurable in Settings).  
> 📊 **ML thresholds** — Classification is percentile-based (low ≤ p33 · moderate p33–p67 · high > p67).  
> 💡 **Recommendations** — Rough estimates for academic purposes, not financial advice.  
> 🕐 **Date range** — Dataset covers 2006–2010; comparison features use this historical range.

---

<div align="center">

## 👩‍💻 Author

**Shweta Patil**

[![GitHub](https://img.shields.io/badge/@Shwetapatil13-181717?style=for-the-badge&logo=github)](https://github.com/Shwetapatil13)

<br/>

---

*Made with ❤️ · EnergyPulse · DASS Course Project*

<br/>

![visitors](https://img.shields.io/badge/dynamic/json?url=https://api.github.com/repos/Shwetapatil13/EnergyPulse&label=⭐%20Stars&query=stargazers_count&color=3b82f6&style=flat-square)
![forks](https://img.shields.io/badge/dynamic/json?url=https://api.github.com/repos/Shwetapatil13/EnergyPulse&label=🍴%20Forks&query=forks_count&color=10b981&style=flat-square)

</div>
