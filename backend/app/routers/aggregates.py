"""
backend/app/routers/aggregates.py
----------------------------------
REST endpoints for hourly and daily aggregates.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query
from backend.app.services.db import get_db
from backend.app.models.database import HourlyAggregate, DailyAggregate, Reading
from backend.app.schemas.aggregate import HourlyAggOut, DailyAggOut
from sqlalchemy import func

router = APIRouter(prefix="/api/aggregates", tags=["Aggregates"])


@router.get("/hourly", response_model=List[HourlyAggOut])
def get_hourly(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    limit: int = Query(168, ge=1, le=8760),
):
    """Get hourly aggregates (default: last 168 hours = 1 week)."""
    with get_db() as session:
        q = session.query(HourlyAggregate)
        if start:
            q = q.filter(HourlyAggregate.timestamp >= datetime.fromisoformat(start))
        if end:
            q = q.filter(HourlyAggregate.timestamp <= datetime.fromisoformat(end))
        rows = q.order_by(HourlyAggregate.timestamp.desc()).limit(limit).all()
        return [HourlyAggOut.model_validate(r) for r in list(reversed(rows))]


@router.get("/daily", response_model=List[DailyAggOut])
def get_daily(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    limit: int = Query(90, ge=1, le=1500),
):
    """Get daily aggregates (default: last 90 days)."""
    with get_db() as session:
        q = session.query(DailyAggregate)
        if start:
            q = q.filter(DailyAggregate.date >= datetime.fromisoformat(start))
        if end:
            q = q.filter(DailyAggregate.date <= datetime.fromisoformat(end))
        rows = q.order_by(DailyAggregate.date.desc()).limit(limit).all()
        return [DailyAggOut.model_validate(r) for r in list(reversed(rows))]


@router.get("/heatmap")
def get_heatmap():
    """
    Hour-of-day × day-of-week average power heatmap.
    Returns 7×24 matrix from DB readings.
    """
    with get_db() as session:
        rows = session.query(
            func.hour(Reading.timestamp).label("hour"),
            func.dayofweek(Reading.timestamp).label("dow"),
            func.avg(Reading.active_power_kw).label("avg_kw"),
            func.count(Reading.id).label("count"),
        ).group_by("hour", "dow").all()

    data = [
        {"hour": int(r.hour), "dow": int(r.dow), "avg_kw": float(r.avg_kw or 0), "count": int(r.count)}
        for r in rows
    ]
    return {"heatmap": data, "note": "Dataset-based simulation, not physical sensor measurements"}


@router.get("/comparison")
def get_comparison(
    period: str = Query("week", description="week | month"),
    reference_start: Optional[str] = Query(None),
):
    """Compare current vs previous period energy totals."""
    from sqlalchemy import text
    with get_db() as session:
        if period == "week":
            sql = text("""
                SELECT
                  DATE(timestamp) as day,
                  SUM(energy_kwh) as total_kwh,
                  SUM(cost_inr) as total_cost
                FROM readings
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                GROUP BY DATE(timestamp)
                ORDER BY day
            """)
        else:
            sql = text("""
                SELECT
                  DATE_FORMAT(timestamp, '%Y-%m') as month,
                  SUM(energy_kwh) as total_kwh,
                  SUM(cost_inr) as total_cost
                FROM readings
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 2 MONTH)
                GROUP BY month
                ORDER BY month
            """)
        result = session.execute(sql).fetchall()
    return {
        "period": period,
        "data": [dict(r._mapping) for r in result],
        "note": "Dataset-based simulation, not physical sensor measurements"
    }
