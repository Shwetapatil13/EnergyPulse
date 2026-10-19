"""Pydantic schemas for ML outputs."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ClassificationResult(BaseModel):
    timestamp: datetime
    active_power_kw: float
    class_label: str
    method: str = "percentile"
    low_threshold_kw: Optional[float] = None
    high_threshold_kw: Optional[float] = None


class ForecastResult(BaseModel):
    target_timestamp: datetime
    predicted_kwh: float
    model_name: str
    actual_kwh: Optional[float] = None


class ModelMetricsOut(BaseModel):
    model_name: str
    task: str
    metrics: dict[str, Any]
    trained_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
