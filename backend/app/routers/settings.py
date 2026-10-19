"""
backend/app/routers/settings.py
---------------------------------
REST endpoints for user-configurable settings.
"""

from __future__ import annotations
from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.services.db import get_db, set_setting
from backend.app.models.database import AppSettings
from backend.app.schemas.settings import SettingOut, SettingUpdate
from backend.app.services.ingestion import reset_singletons

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("/", response_model=List[SettingOut])
def list_settings():
    """List all configurable settings."""
    with get_db() as session:
        rows = session.query(AppSettings).order_by(AppSettings.key).all()
        return [SettingOut.model_validate(r) for r in rows]


@router.get("/{key}", response_model=SettingOut)
def get_setting_by_key(key: str):
    """Get a specific setting by key."""
    with get_db() as session:
        row = session.query(AppSettings).filter_by(key=key).first()
        if not row:
            raise HTTPException(404, f"Setting '{key}' not found")
        return SettingOut.model_validate(row)


@router.put("/{key}", response_model=SettingOut)
def update_setting(key: str, update: SettingUpdate):
    """Update a setting value. Triggers anomaly detector reload if threshold changed."""
    with get_db() as session:
        row = session.query(AppSettings).filter_by(key=key).first()
        if not row:
            raise HTTPException(404, f"Setting '{key}' not found")
        row.value = update.value
        session.flush()
        updated = SettingOut.model_validate(row)

    # Reload detector/classifier if threshold settings changed
    if key in ("anomaly_z_threshold", "anomaly_window_minutes", "anomaly_abs_threshold_kw"):
        reset_singletons()

    return updated
