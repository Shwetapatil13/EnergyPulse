"""
backend/app/models/database.py
-------------------------------
SQLAlchemy ORM models for EnergyPulse.

Tables:
  - readings          : per-minute sensor readings (simulated)
  - alerts            : anomaly/threshold alerts
  - hourly_aggregates : pre-computed hourly stats
  - daily_aggregates  : pre-computed daily stats
  - model_runs        : ML model training metadata & metrics
  - predictions       : forecast predictions
  - settings          : user-configurable app settings
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Index, Integer,
    JSON, String, Text, UniqueConstraint, create_engine, text
)
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class Reading(Base):
    """Per-minute power consumption reading (from simulator replay)."""
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Raw sensor columns (units per UCI docs)
    active_power_kw = Column(Float, nullable=True)       # Global_active_power (kW)
    reactive_power_kw = Column(Float, nullable=True)     # Global_reactive_power (kW)
    voltage_v = Column(Float, nullable=True)             # Voltage (V)
    current_a = Column(Float, nullable=True)             # Global_intensity (A)

    # Circuit zone meters (Wh) — NOT individual appliances
    sub_metering_1_wh = Column(Float, nullable=True)     # Zone 1 (Wh)
    sub_metering_2_wh = Column(Float, nullable=True)     # Zone 2 (Wh)
    sub_metering_3_wh = Column(Float, nullable=True)     # Zone 3 (Wh)

    # Derived
    energy_kwh = Column(Float, nullable=True)            # active_power_kw / 60
    cost_inr = Column(Float, nullable=True)              # energy_kwh × tariff
    class_label = Column(String(16), nullable=True)      # low / moderate / high

    # Flags
    is_simulated = Column(Boolean, default=True, nullable=False)
    is_anomaly = Column(Boolean, default=False)
    is_gap = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("timestamp", name="uq_readings_timestamp"),
        {"mysql_charset": "utf8mb4"},
    )


class Alert(Base):
    """Anomaly / threshold alert record."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    alert_type = Column(String(64), nullable=False)    # z_score / iqr / abs_threshold / delta
    severity = Column(String(16), nullable=False)      # low / medium / high / critical
    value = Column(Float, nullable=True)               # The triggering value
    threshold = Column(Float, nullable=True)           # The threshold breached
    rule_description = Column(Text, nullable=True)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class HourlyAggregate(Base):
    """Hourly consumption aggregate."""
    __tablename__ = "hourly_aggregates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, unique=True, index=True)  # Hour start

    avg_power_kw = Column(Float, nullable=True)
    max_power_kw = Column(Float, nullable=True)
    min_power_kw = Column(Float, nullable=True)
    total_energy_kwh = Column(Float, nullable=True)
    total_cost_inr = Column(Float, nullable=True)
    avg_voltage_v = Column(Float, nullable=True)
    avg_current_a = Column(Float, nullable=True)

    sub_metering_1_total_wh = Column(Float, nullable=True)
    sub_metering_2_total_wh = Column(Float, nullable=True)
    sub_metering_3_total_wh = Column(Float, nullable=True)

    reading_count = Column(Integer, nullable=True)
    anomaly_count = Column(Integer, default=0)


class DailyAggregate(Base):
    """Daily consumption aggregate."""
    __tablename__ = "daily_aggregates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)  # Day start

    avg_power_kw = Column(Float, nullable=True)
    max_power_kw = Column(Float, nullable=True)
    min_power_kw = Column(Float, nullable=True)
    total_energy_kwh = Column(Float, nullable=True)
    total_cost_inr = Column(Float, nullable=True)

    sub_metering_1_total_wh = Column(Float, nullable=True)
    sub_metering_2_total_wh = Column(Float, nullable=True)
    sub_metering_3_total_wh = Column(Float, nullable=True)

    peak_hour = Column(Integer, nullable=True)           # 0-23
    load_factor = Column(Float, nullable=True)           # avg/peak
    day_of_week = Column(Integer, nullable=True)         # 0=Mon
    is_weekend = Column(Boolean, nullable=True)
    reading_count = Column(Integer, nullable=True)
    anomaly_count = Column(Integer, default=0)


class ModelRun(Base):
    """ML model training run record."""
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(64), nullable=False)     # e.g. linear_regression
    task = Column(String(32), nullable=False)           # classifier / forecaster / anomaly
    params = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)               # MAE, RMSE, accuracy, etc.
    train_rows = Column(Integer, nullable=True)
    test_rows = Column(Integer, nullable=True)
    trained_at = Column(DateTime, default=datetime.utcnow)
    model_path = Column(String(256), nullable=True)     # path to joblib file


class Prediction(Base):
    """Stored forecast predictions."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_timestamp = Column(DateTime, nullable=False, index=True)
    predicted_kwh = Column(Float, nullable=True)
    actual_kwh = Column(Float, nullable=True)
    model_name = Column(String(64), nullable=True)
    model_run_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AppSettings(Base):
    """User-configurable application settings (key-value store)."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), nullable=False, unique=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Default settings seed data
DEFAULT_SETTINGS = [
    ("tariff_inr_per_kwh", "8.0",
     "Flat electricity tariff in INR per kWh. ASSUMED VALUE — verify against your utility bill."),
    ("anomaly_z_threshold", "3.0",
     "Z-score threshold for rolling mean anomaly detection."),
    ("anomaly_window_minutes", "60",
     "Rolling window size (minutes) for anomaly detection."),
    ("anomaly_abs_threshold_kw", "5.0",
     "Absolute active power threshold (kW) that triggers an alert."),
    ("sim_speed", "1.0",
     "Simulator speed multiplier. 1 = 1 reading/second (1 min data/sec)."),
    ("sim_loop", "true",
     "Whether the simulator loops back to start when data ends."),
    ("class_low_pct", "33.0",
     "Percentile boundary (computed from training data) for 'low' class."),
    ("class_high_pct", "67.0",
     "Percentile boundary (computed from training data) for 'high' class."),
]
