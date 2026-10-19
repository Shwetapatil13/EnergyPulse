"""
backend/app/routers/ml.py
--------------------------
REST endpoints for ML models: classification, forecasting, model metrics.
"""

from __future__ import annotations
import json
import pathlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
import numpy as np

from backend.app.services.db import get_db
from backend.app.models.database import ModelRun, Prediction, Reading, HourlyAggregate
from backend.app.schemas.ml import ModelMetricsOut, ForecastResult

router = APIRouter(prefix="/api/ml", tags=["ML"])

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "backend" / "app" / "ml" / "saved_models"


@router.get("/model-runs")
def get_model_runs():
    """List all trained model runs with their metrics."""
    with get_db() as session:
        runs = session.query(ModelRun).order_by(ModelRun.trained_at.desc()).limit(20).all()
        return [
            {
                "id": r.id,
                "model_name": r.model_name,
                "task": r.task,
                "metrics": r.metrics,
                "train_rows": r.train_rows,
                "test_rows": r.test_rows,
                "trained_at": r.trained_at.isoformat() if r.trained_at else None,
            }
            for r in runs
        ]


@router.get("/classification/summary")
def get_classification_summary(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
):
    """Get distribution of classification labels."""
    from sqlalchemy import func
    with get_db() as session:
        q = session.query(
            Reading.class_label,
            func.count(Reading.id).label("count"),
            func.avg(Reading.active_power_kw).label("avg_kw"),
        ).filter(Reading.class_label.isnot(None))
        if start:
            q = q.filter(Reading.timestamp >= datetime.fromisoformat(start))
        if end:
            q = q.filter(Reading.timestamp <= datetime.fromisoformat(end))
        rows = q.group_by(Reading.class_label).all()
    return {
        "distribution": [
            {"label": r.class_label, "count": r.count, "avg_kw": float(r.avg_kw or 0)}
            for r in rows
        ],
        "method": "percentile_thresholds",
        "note": "Labels: low≤p33, moderate=p33-p67, high>p67 (computed from training data only)",
    }


@router.get("/forecast")
def get_forecast(hours_ahead: int = Query(24, ge=1, le=168)):
    """
    Get stored predictions for the next N hours (if model has been trained).
    Falls back to naive baseline if no ML model available.
    """
    with get_db() as session:
        preds = (
            session.query(Prediction)
            .filter(Prediction.target_timestamp >= datetime.utcnow())
            .order_by(Prediction.target_timestamp)
            .limit(hours_ahead)
            .all()
        )
        if preds:
            return {
                "predictions": [
                    {
                        "target_timestamp": p.target_timestamp.isoformat(),
                        "predicted_kwh": p.predicted_kwh,
                        "actual_kwh": p.actual_kwh,
                        "model_name": p.model_name,
                    }
                    for p in preds
                ],
                "source": "ml_model",
            }

        # Fallback: naive baseline from recent hourly data
        recent = (
            session.query(HourlyAggregate)
            .order_by(HourlyAggregate.timestamp.desc())
            .limit(24)
            .all()
        )
        if not recent:
            return {"predictions": [], "source": "no_data"}

        avg_kwh = float(np.mean([r.total_energy_kwh or 0 for r in recent]))
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        forecasts = []
        for i in range(1, hours_ahead + 1):
            forecasts.append({
                "target_timestamp": (now + timedelta(hours=i)).isoformat(),
                "predicted_kwh": round(avg_kwh, 4),
                "model_name": "naive_rolling_mean",
            })
        return {"predictions": forecasts, "source": "naive_baseline"}


@router.get("/forecast/vs-actual")
def get_forecast_vs_actual(limit: int = Query(168, ge=1, le=2000)):
    """Get predictions with actuals for model evaluation chart."""
    with get_db() as session:
        preds = (
            session.query(Prediction)
            .filter(Prediction.actual_kwh.isnot(None))
            .order_by(Prediction.target_timestamp.desc())
            .limit(limit)
            .all()
        )
    return {
        "data": [
            {
                "timestamp": p.target_timestamp.isoformat(),
                "predicted": p.predicted_kwh,
                "actual": p.actual_kwh,
                "model": p.model_name,
            }
            for p in list(reversed(preds))
        ]
    }


@router.get("/metrics")
def get_metrics():
    """Get all stored model evaluation metrics."""
    model_files = list(MODEL_DIR.glob("*.joblib")) if MODEL_DIR.exists() else []
    with get_db() as session:
        runs = session.query(ModelRun).order_by(ModelRun.trained_at.desc()).all()
        metrics_list = [
            {
                "model_name": r.model_name,
                "task": r.task,
                "metrics": r.metrics,
                "trained_at": r.trained_at.isoformat() if r.trained_at else None,
            }
            for r in runs
        ]
    return {
        "model_runs": metrics_list,
        "saved_model_files": [f.name for f in model_files],
        "note": "All metrics computed from real data on chronological test split (last 20%).",
    }
