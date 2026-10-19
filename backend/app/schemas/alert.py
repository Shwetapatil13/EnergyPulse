"""Pydantic schemas for alerts."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    timestamp: datetime
    alert_type: str
    severity: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    rule_description: Optional[str] = None
    acknowledged: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
