"""Pydantic schemas for simulator control."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class SimControlRequest(BaseModel):
    action: str = Field(..., description="start | pause | resume | stop | seek | set_speed")
    start_date: Optional[str] = Field(None, description="ISO date for seek/start (e.g. '2007-01-01')")
    speed: Optional[float] = Field(None, ge=0.1, le=3600, description="Speed multiplier")
    loop: Optional[bool] = None


class SimStatusOut(BaseModel):
    state: str
    current_timestamp: Optional[str] = None
    current_index: int = 0
    total_rows: int = 0
    speed: float = 1.0
    loop: bool = True
    ticks_emitted: int = 0
    start_time: Optional[str] = None
    data_source: str = "Dataset-based simulation, not physical sensor measurements"
    progress_pct: float = 0.0
