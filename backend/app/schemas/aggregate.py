"""Pydantic schemas for aggregate data."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class HourlyAggOut(BaseModel):
    id: int
    timestamp: datetime
    avg_power_kw: Optional[float] = None
    max_power_kw: Optional[float] = None
    min_power_kw: Optional[float] = None
    total_energy_kwh: Optional[float] = None
    total_cost_inr: Optional[float] = None
    avg_voltage_v: Optional[float] = None
    avg_current_a: Optional[float] = None
    sub_metering_1_total_wh: Optional[float] = None
    sub_metering_2_total_wh: Optional[float] = None
    sub_metering_3_total_wh: Optional[float] = None
    reading_count: Optional[int] = None
    anomaly_count: int = 0

    model_config = {"from_attributes": True}


class DailyAggOut(BaseModel):
    id: int
    date: datetime
    avg_power_kw: Optional[float] = None
    max_power_kw: Optional[float] = None
    min_power_kw: Optional[float] = None
    total_energy_kwh: Optional[float] = None
    total_cost_inr: Optional[float] = None
    sub_metering_1_total_wh: Optional[float] = None
    sub_metering_2_total_wh: Optional[float] = None
    sub_metering_3_total_wh: Optional[float] = None
    peak_hour: Optional[int] = None
    load_factor: Optional[float] = None
    day_of_week: Optional[int] = None
    is_weekend: Optional[bool] = None
    reading_count: Optional[int] = None
    anomaly_count: int = 0

    model_config = {"from_attributes": True}
