"""Pydantic schemas for sensor readings."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ReadingCreate(BaseModel):
    timestamp: datetime
    active_power_kw: Optional[float] = None
    reactive_power_kw: Optional[float] = None
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    sub_metering_1_wh: Optional[float] = None
    sub_metering_2_wh: Optional[float] = None
    sub_metering_3_wh: Optional[float] = None
    energy_kwh: Optional[float] = None
    cost_inr: Optional[float] = None
    class_label: Optional[str] = None
    is_simulated: bool = True
    is_anomaly: bool = False
    is_gap: bool = False


class ReadingOut(ReadingCreate):
    id: int
    data_source: str = "Dataset-based simulation, not physical sensor measurements"

    model_config = {"from_attributes": True}
