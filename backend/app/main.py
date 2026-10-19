"""
backend/app/main.py
--------------------
EnergyPulse FastAPI Application

Endpoints:
  GET  /                     — health check
  WS   /ws/live              — live reading stream
  REST /api/simulator/*      — simulator control
  REST /api/readings/*       — historical readings
  REST /api/aggregates/*     — hourly/daily aggregates + heatmap
  REST /api/alerts/*         — anomaly alerts
  REST /api/ml/*             — classification, forecast, metrics
  REST /api/recommendations/ — sustainability recommendations
  REST /api/settings/*       — configurable settings
  GET  /docs                 — OpenAPI (auto-generated)

Label: Dataset-based simulation, not physical sensor measurements
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.services.db import init_db
from backend.app.services.ws_manager import get_ws_manager
from backend.app.services.ingestion import process_reading
from backend.app.simulator.engine import get_simulator

# ── Routers ───────────────────────────────────────────────────────────────
from backend.app.routers import (
    simulator as sim_router,
    readings as readings_router,
    aggregates as agg_router,
    alerts as alerts_router,
    ml as ml_router,
    recommendations as rec_router,
    settings as settings_router,
)

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("energypulse")


# ── Lifespan ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown tasks."""
    settings = get_settings()
    log.info("EnergyPulse starting up...")

    # Init DB
    try:
        init_db()
        log.info("Database initialized.")
    except Exception as exc:
        log.error("DB init failed: %s — check MySQL connection.", exc)

    # Load simulator data and register callback
    sim = get_simulator()
    try:
        n = sim.load_data()
        log.info("Simulator loaded %d rows.", n)
    except FileNotFoundError as exc:
        log.warning("Simulator data not found: %s. Run preprocessing first.", exc)
    except Exception as exc:
        log.error("Simulator load error: %s", exc)

    # Register ingestion pipeline as simulator callback
    sim.register_callback(process_reading)
    log.info("Ingestion pipeline registered.")
    log.info("EnergyPulse ready. API docs: http://%s:%d/docs",
             settings.backend_host, settings.backend_port)

    yield

    # Shutdown
    log.info("Shutting down simulator...")
    await sim.stop()
    log.info("EnergyPulse shutdown complete.")


# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="EnergyPulse — Smart Energy Monitoring",
    description=(
        "**Dataset-based simulation, not physical sensor measurements.**\n\n"
        "Smart Energy Monitoring and Analytics Dashboard for DASS course.\n"
        "Replays UCI Household Power Consumption dataset (2006–2010) through "
        "a virtual IoT simulator with real-time analytics, ML classification, "
        "forecasting, anomaly detection, and sustainability recommendations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include routers ───────────────────────────────────────────────────────
app.include_router(sim_router.router)
app.include_router(readings_router.router)
app.include_router(agg_router.router)
app.include_router(alerts_router.router)
app.include_router(ml_router.router)
app.include_router(rec_router.router)
app.include_router(settings_router.router)


# ── Health check ──────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "EnergyPulse",
        "status": "running",
        "data_label": "Dataset-based simulation, not physical sensor measurements",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    sim = get_simulator()
    status = sim.get_status()
    return {
        "status": "healthy",
        "simulator_state": status.state.value,
        "simulator_rows": status.total_rows,
        "data_label": "Dataset-based simulation, not physical sensor measurements",
    }


# ── WebSocket ─────────────────────────────────────────────────────────────
@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """
    Live reading stream WebSocket.
    Connect to receive one JSON message per simulator tick (1/speed seconds).
    Auto-reconnect on disconnect.
    """
    manager = get_ws_manager()
    await manager.connect(websocket)
    try:
        # Send initial status
        sim = get_simulator()
        status = sim.get_status()
        await manager.send_personal(websocket, {
            "type": "connection",
            "simulator_state": status.state.value,
            "data_source": "Dataset-based simulation, not physical sensor measurements",
        })
        # Keep alive — client just listens for broadcasts
        while True:
            await websocket.receive_text()  # Ping/pong or commands
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        log.error("WebSocket error: %s", exc)
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
