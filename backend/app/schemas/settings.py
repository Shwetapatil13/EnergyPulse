"""Pydantic schemas for app settings."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SettingOut(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value: str
