"""
backend/app/routers/alerts.py
------------------------------
REST endpoints for anomaly alerts.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import csv, io
from backend.app.services.db import get_db
from backend.app.models.database import Alert
from backend.app.schemas.alert import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("/", response_model=List[AlertOut])
def get_alerts(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, description="low|medium|high|critical"),
    limit: int = Query(200, ge=1, le=2000),
):
    """Get recent alerts with optional filters."""
    with get_db() as session:
        q = session.query(Alert)
        if start:
            q = q.filter(Alert.timestamp >= datetime.fromisoformat(start))
        if end:
            q = q.filter(Alert.timestamp <= datetime.fromisoformat(end))
        if severity:
            q = q.filter(Alert.severity == severity)
        rows = q.order_by(Alert.timestamp.desc()).limit(limit).all()
        return [AlertOut.model_validate(r) for r in rows]


@router.get("/summary")
def get_alert_summary():
    """Count alerts by type and severity."""
    from sqlalchemy import func
    with get_db() as session:
        by_severity = session.query(
            Alert.severity, func.count(Alert.id)
        ).group_by(Alert.severity).all()
        by_type = session.query(
            Alert.alert_type, func.count(Alert.id)
        ).group_by(Alert.alert_type).all()
    return {
        "by_severity": {s: c for s, c in by_severity},
        "by_type": {t: c for t, c in by_type},
        "total": sum(c for _, c in by_severity),
    }


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int):
    """Mark an alert as acknowledged."""
    with get_db() as session:
        alert = session.query(Alert).filter_by(id=alert_id).first()
        if not alert:
            from fastapi import HTTPException
            raise HTTPException(404, "Alert not found")
        alert.acknowledged = True
    return {"status": "acknowledged", "alert_id": alert_id}


@router.get("/export/csv")
def export_alerts_csv(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
):
    """Export alerts as CSV."""
    with get_db() as session:
        q = session.query(Alert)
        if start:
            q = q.filter(Alert.timestamp >= datetime.fromisoformat(start))
        if end:
            q = q.filter(Alert.timestamp <= datetime.fromisoformat(end))
        rows = q.order_by(Alert.timestamp).limit(50000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "timestamp", "alert_type", "severity", "value", "threshold", "rule_description", "acknowledged"])
    for r in rows:
        writer.writerow([r.id, r.timestamp, r.alert_type, r.severity, r.value, r.threshold, r.rule_description, r.acknowledged])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=energypulse_alerts.csv"},
    )
