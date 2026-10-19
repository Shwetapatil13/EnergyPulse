"""
backend/app/services/ingestion.py
----------------------------------
Ingestion pipeline: validate → calc kWh/cost → anomaly → classify → DB insert → WS broadcast.
This is called by the simulator on every tick.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from backend.app.services.db import get_db, get_setting
from backend.app.services.ws_manager import get_ws_manager
from backend.app.models.database import Reading, Alert
from backend.app.ml.anomaly import RealTimeAnomalyDetector
from backend.app.ml.classifier import PercentileClassifier

log = logging.getLogger(__name__)

# Module-level singletons (loaded once at startup)
_detector: Optional[RealTimeAnomalyDetector] = None
_classifier: Optional[PercentileClassifier] = None


def get_detector() -> RealTimeAnomalyDetector:
    global _detector
    if _detector is None:
        _detector = RealTimeAnomalyDetector(
            window=int(get_setting("anomaly_window_minutes", "60")),
            z_threshold=float(get_setting("anomaly_z_threshold", "3.0")),
            iqr_multiplier=float(get_setting("anomaly_iqr_multiplier", "1.5")),
            abs_threshold_kw=float(get_setting("anomaly_abs_threshold_kw", "5.0")),
            delta_threshold_kw=2.0,
        )
    return _detector


def get_classifier() -> Optional[PercentileClassifier]:
    global _classifier
    if _classifier is None:
        try:
            _classifier = PercentileClassifier.load()
            log.info("Loaded PercentileClassifier from disk.")
        except Exception:
            log.warning("PercentileClassifier not yet trained. Classification disabled.")
    return _classifier


def reset_singletons():
    """Force reload of detector/classifier (e.g. after settings change)."""
    global _detector, _classifier
    _detector = None
    _classifier = None


async def process_reading(raw: dict) -> dict:
    """
    Full ingestion pipeline for one reading dict.

    Steps:
      1. Validate and extract fields
      2. Compute kWh and cost
      3. Check anomalies
      4. Classify consumption
      5. Insert into DB
      6. Broadcast via WebSocket
      7. Return enriched reading dict
    """
    # 1. Extract fields
    ts_str = raw.get("timestamp")
    try:
        ts = datetime.fromisoformat(ts_str) if ts_str else datetime.utcnow()
    except Exception:
        ts = datetime.utcnow()

    active_kw = raw.get("active_power_kw")
    reactive_kw = raw.get("reactive_power_kw")
    voltage = raw.get("voltage_v")
    current = raw.get("current_a")
    sm1 = raw.get("sub_metering_1_wh")
    sm2 = raw.get("sub_metering_2_wh")
    sm3 = raw.get("sub_metering_3_wh")
    is_gap = raw.get("is_gap", False)

    # 2. kWh and cost
    tariff = float(get_setting("tariff_inr_per_kwh", "8.0"))
    energy_kwh = (active_kw / 60.0) if active_kw is not None else None
    cost_inr = (energy_kwh * tariff) if energy_kwh is not None else None

    # 3. Anomaly detection
    is_anomaly = False
    anomaly_results = []
    if active_kw is not None:
        detector = get_detector()
        anomaly_results = detector.check(active_kw)
        is_anomaly = len(anomaly_results) > 0

    # 4. Classification
    class_label = None
    clf = get_classifier()
    if clf and active_kw is not None:
        try:
            class_label = clf.predict_one(active_kw)
        except Exception:
            pass

    # 5. DB insert
    reading_id = None
    try:
        with get_db() as session:
            reading = Reading(
                timestamp=ts,
                active_power_kw=active_kw,
                reactive_power_kw=reactive_kw,
                voltage_v=voltage,
                current_a=current,
                sub_metering_1_wh=sm1,
                sub_metering_2_wh=sm2,
                sub_metering_3_wh=sm3,
                energy_kwh=energy_kwh,
                cost_inr=cost_inr,
                class_label=class_label,
                is_simulated=True,
                is_anomaly=is_anomaly,
                is_gap=is_gap,
            )
            session.add(reading)
            session.flush()
            reading_id = reading.id

            # Insert alerts
            for ar in anomaly_results:
                alert = Alert(
                    timestamp=ts,
                    alert_type=ar.alert_type,
                    severity=ar.severity,
                    value=ar.value,
                    threshold=ar.threshold,
                    rule_description=ar.rule_description,
                )
                session.add(alert)
    except Exception as exc:
        log.error("DB insert failed: %s", exc)

    # 6. Build broadcast payload
    payload = {
        "type": "reading",
        "timestamp": ts.isoformat(),
        "active_power_kw": active_kw,
        "reactive_power_kw": reactive_kw,
        "voltage_v": voltage,
        "current_a": current,
        "sub_metering_1_wh": sm1,
        "sub_metering_2_wh": sm2,
        "sub_metering_3_wh": sm3,
        "energy_kwh": energy_kwh,
        "cost_inr": cost_inr,
        "tariff_inr_per_kwh": tariff,
        "class_label": class_label,
        "is_anomaly": is_anomaly,
        "is_gap": is_gap,
        "is_simulated": True,
        "reading_id": reading_id,
        "data_source": "Dataset-based simulation, not physical sensor measurements",
        "alerts": [
            {
                "type": ar.alert_type,
                "severity": ar.severity,
                "value": ar.value,
                "threshold": ar.threshold,
                "description": ar.rule_description,
            }
            for ar in anomaly_results
        ],
    }

    # 7. Broadcast
    ws_manager = get_ws_manager()
    await ws_manager.broadcast(payload)

    return payload
