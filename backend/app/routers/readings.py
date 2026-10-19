"""
backend/app/routers/readings.py
--------------------------------
REST endpoints for sensor readings and live data.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
import csv
import io

from backend.app.services.db import get_db
from backend.app.models.database import Reading
from backend.app.schemas.reading import ReadingOut

router = APIRouter(prefix="/api/readings", tags=["Readings"])


@router.get("/", response_model=List[ReadingOut])
def get_readings(
    start: Optional[str] = Query(None, description="ISO datetime start"),
    end: Optional[str] = Query(None, description="ISO datetime end"),
    limit: int = Query(500, ge=1, le=5000),
    anomaly_only: bool = Query(False),
):
    """Get historical readings with optional date range filter."""
    with get_db() as session:
        q = session.query(Reading)
        if start:
            q = q.filter(Reading.timestamp >= datetime.fromisoformat(start))
        if end:
            q = q.filter(Reading.timestamp <= datetime.fromisoformat(end))
        if anomaly_only:
            q = q.filter(Reading.is_anomaly == True)
        q = q.order_by(Reading.timestamp.desc()).limit(limit)
        rows = q.all()
        return [ReadingOut.model_validate(r) for r in rows]


@router.get("/latest")
def get_latest(n: int = Query(60, ge=1, le=1440)):
    """Get the N most recent readings (for live chart)."""
    with get_db() as session:
        rows = (
            session.query(Reading)
            .order_by(Reading.timestamp.desc())
            .limit(n)
            .all()
        )
        rows = list(reversed(rows))
        return [ReadingOut.model_validate(r) for r in rows]


@router.get("/summary")
def get_summary(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
):
    """Get aggregate statistics for a date range."""
    from sqlalchemy import func
    with get_db() as session:
        q = session.query(
            func.count(Reading.id).label("count"),
            func.sum(Reading.energy_kwh).label("total_energy_kwh"),
            func.sum(Reading.cost_inr).label("total_cost_inr"),
            func.avg(Reading.active_power_kw).label("avg_power_kw"),
            func.max(Reading.active_power_kw).label("peak_power_kw"),
            func.min(Reading.active_power_kw).label("min_power_kw"),
            func.avg(Reading.voltage_v).label("avg_voltage_v"),
            func.avg(Reading.current_a).label("avg_current_a"),
            func.sum(Reading.is_anomaly).label("anomaly_count"),
        )
        if start:
            q = q.filter(Reading.timestamp >= datetime.fromisoformat(start))
        if end:
            q = q.filter(Reading.timestamp <= datetime.fromisoformat(end))
        row = q.one()
        result = {k: (float(v) if v is not None else None) for k, v in row._mapping.items()}
        # Load factor = avg / peak
        if result.get("peak_power_kw") and result.get("avg_power_kw"):
            result["load_factor"] = round(result["avg_power_kw"] / result["peak_power_kw"], 4)
        result["data_source"] = "Dataset-based simulation, not physical sensor measurements"
        return result


@router.get("/export/csv")
def export_csv(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
):
    """Download readings as CSV for the given date range."""
    with get_db() as session:
        q = session.query(Reading)
        if start:
            q = q.filter(Reading.timestamp >= datetime.fromisoformat(start))
        if end:
            q = q.filter(Reading.timestamp <= datetime.fromisoformat(end))
        q = q.order_by(Reading.timestamp).limit(100000)
        rows = q.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp", "active_power_kw", "reactive_power_kw", "voltage_v", "current_a",
        "sub_metering_1_wh", "sub_metering_2_wh", "sub_metering_3_wh",
        "energy_kwh", "cost_inr", "class_label", "is_anomaly", "is_simulated"
    ])
    for r in rows:
        writer.writerow([
            r.timestamp, r.active_power_kw, r.reactive_power_kw, r.voltage_v, r.current_a,
            r.sub_metering_1_wh, r.sub_metering_2_wh, r.sub_metering_3_wh,
            r.energy_kwh, r.cost_inr, r.class_label, r.is_anomaly, r.is_simulated
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=energypulse_readings.csv"},
    )
