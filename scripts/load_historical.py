"""
scripts/load_historical.py
---------------------------
Bulk-load preprocessed historical data into MySQL.
Loads: hourly_aggregates, daily_aggregates (fast, small).
Optionally loads minute-level readings (large: ~2M rows).

Usage:
    python scripts/load_historical.py              # hourly + daily only
    python scripts/load_historical.py --with-readings  # + minute readings (slow)
"""

import sys
import pathlib
import argparse
import logging
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

PROCESSED_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
CHUNK_SIZE = 5000


def safe(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return float(v)


def load_hourly(engine):
    path = PROCESSED_DIR / "hourly_aggregates.parquet"
    if not path.exists():
        log.warning("hourly_aggregates.parquet not found. Run preprocessing first.")
        return 0

    df = pd.read_parquet(path)
    log.info("Loading %d hourly rows (upsert)...", len(df))

    from sqlalchemy import text
    inserted = 0

    with engine.begin() as conn:
        for i in range(0, len(df), CHUNK_SIZE):
            chunk = df.iloc[i:i + CHUNK_SIZE]
            rows = []
            for ts, row in chunk.iterrows():
                rows.append({
                    "timestamp": ts.to_pydatetime(),
                    "avg_power_kw": safe(row.get("active_power_kw")),
                    "total_energy_kwh": safe(row.get("energy_kwh")),
                    "total_cost_inr": safe(row.get("cost_inr")),
                    "avg_voltage_v": safe(row.get("Voltage")),
                    "avg_current_a": safe(row.get("Global_intensity")),
                    "sub_metering_1_total_wh": safe(row.get("Sub_metering_1")),
                    "sub_metering_2_total_wh": safe(row.get("Sub_metering_2")),
                    "sub_metering_3_total_wh": safe(row.get("Sub_metering_3")),
                    "reading_count": None,
                    "anomaly_count": 0,
                    "max_power_kw": None,
                    "min_power_kw": None,
                })

            conn.execute(text("""
                INSERT INTO hourly_aggregates
                    (timestamp, avg_power_kw, max_power_kw, min_power_kw,
                     total_energy_kwh, total_cost_inr, avg_voltage_v, avg_current_a,
                     sub_metering_1_total_wh, sub_metering_2_total_wh, sub_metering_3_total_wh,
                     reading_count, anomaly_count)
                VALUES
                    (:timestamp, :avg_power_kw, :max_power_kw, :min_power_kw,
                     :total_energy_kwh, :total_cost_inr, :avg_voltage_v, :avg_current_a,
                     :sub_metering_1_total_wh, :sub_metering_2_total_wh, :sub_metering_3_total_wh,
                     :reading_count, :anomaly_count)
                ON DUPLICATE KEY UPDATE
                    avg_power_kw         = VALUES(avg_power_kw),
                    total_energy_kwh     = VALUES(total_energy_kwh),
                    total_cost_inr       = VALUES(total_cost_inr),
                    avg_voltage_v        = VALUES(avg_voltage_v),
                    avg_current_a        = VALUES(avg_current_a),
                    sub_metering_1_total_wh = VALUES(sub_metering_1_total_wh),
                    sub_metering_2_total_wh = VALUES(sub_metering_2_total_wh),
                    sub_metering_3_total_wh = VALUES(sub_metering_3_total_wh)
            """), rows)

            inserted += len(rows)
            log.info("  Hourly: %d / %d upserted", min(i + CHUNK_SIZE, len(df)), len(df))

    log.info("Hourly aggregates done: %d rows", inserted)
    return inserted


def load_daily(engine):
    path = PROCESSED_DIR / "daily_aggregates.parquet"
    if not path.exists():
        log.warning("daily_aggregates.parquet not found. Run preprocessing first.")
        return 0

    df = pd.read_parquet(path)
    df.columns = ["_".join(c) if isinstance(c, tuple) else c for c in df.columns]
    log.info("Loading %d daily rows (upsert)...", len(df))

    from sqlalchemy import text
    inserted = 0

    with engine.begin() as conn:
        for i in range(0, len(df), CHUNK_SIZE):
            chunk = df.iloc[i:i + CHUNK_SIZE]
            rows = []
            for ts, row in chunk.iterrows():
                avg_kw = safe(row.get("active_power_kw_mean") or row.get("active_power_kw"))
                max_kw = safe(row.get("active_power_kw_max"))
                lf = (avg_kw / max_kw) if avg_kw and max_kw and max_kw > 0 else None
                dow_raw = row.get("day_of_week", 0)
                dow = int(dow_raw) if dow_raw is not None and not (isinstance(dow_raw, float) and np.isnan(dow_raw)) else None

                rows.append({
                    "date": ts.to_pydatetime(),
                    "avg_power_kw": avg_kw,
                    "max_power_kw": max_kw,
                    "min_power_kw": safe(row.get("active_power_kw_min")),
                    "total_energy_kwh": safe(row.get("energy_kwh")),
                    "total_cost_inr": safe(row.get("cost_inr")),
                    "sub_metering_1_total_wh": safe(row.get("Sub_metering_1")),
                    "sub_metering_2_total_wh": safe(row.get("Sub_metering_2")),
                    "sub_metering_3_total_wh": safe(row.get("Sub_metering_3")),
                    "peak_hour": None,
                    "load_factor": lf,
                    "day_of_week": dow,
                    "is_weekend": bool(row.get("is_weekend", False)),
                    "reading_count": None,
                    "anomaly_count": 0,
                })

            conn.execute(text("""
                INSERT INTO daily_aggregates
                    (date, avg_power_kw, max_power_kw, min_power_kw,
                     total_energy_kwh, total_cost_inr,
                     sub_metering_1_total_wh, sub_metering_2_total_wh, sub_metering_3_total_wh,
                     peak_hour, load_factor, day_of_week, is_weekend,
                     reading_count, anomaly_count)
                VALUES
                    (:date, :avg_power_kw, :max_power_kw, :min_power_kw,
                     :total_energy_kwh, :total_cost_inr,
                     :sub_metering_1_total_wh, :sub_metering_2_total_wh, :sub_metering_3_total_wh,
                     :peak_hour, :load_factor, :day_of_week, :is_weekend,
                     :reading_count, :anomaly_count)
                ON DUPLICATE KEY UPDATE
                    avg_power_kw         = VALUES(avg_power_kw),
                    max_power_kw         = VALUES(max_power_kw),
                    min_power_kw         = VALUES(min_power_kw),
                    total_energy_kwh     = VALUES(total_energy_kwh),
                    total_cost_inr       = VALUES(total_cost_inr),
                    sub_metering_1_total_wh = VALUES(sub_metering_1_total_wh),
                    sub_metering_2_total_wh = VALUES(sub_metering_2_total_wh),
                    sub_metering_3_total_wh = VALUES(sub_metering_3_total_wh),
                    load_factor          = VALUES(load_factor),
                    day_of_week          = VALUES(day_of_week),
                    is_weekend           = VALUES(is_weekend)
            """), rows)

            inserted += len(rows)
            log.info("  Daily: %d / %d upserted", min(i + CHUNK_SIZE, len(df)), len(df))

    log.info("Daily aggregates done: %d rows", inserted)
    return inserted


def load_readings(engine):
    """Bulk-load minute-level readings from parquet into DB. This is ~2M rows — takes time."""
    path = PROCESSED_DIR / "readings_1min.parquet"
    if not path.exists():
        log.warning("readings_1min.parquet not found. Run preprocessing first.")
        return 0

    df = pd.read_parquet(path)
    log.info("Loading %d minute-level readings (upsert, this will take several minutes)...", len(df))

    from sqlalchemy import text

    # Compute class label using percentile thresholds on this data
    p33 = float(df["active_power_kw"].quantile(0.33))
    p67 = float(df["active_power_kw"].quantile(0.67))
    log.info("Class thresholds: low<=%.4f, moderate=%.4f-%.4f, high>%.4f", p33, p33, p67, p67)

    def get_class(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        if v <= p33:
            return "low"
        elif v <= p67:
            return "moderate"
        else:
            return "high"

    inserted = 0
    total = len(df)

    for i in range(0, total, CHUNK_SIZE):
        chunk = df.iloc[i:i + CHUNK_SIZE]
        rows = []
        for ts, row in chunk.iterrows():
            ap = safe(row.get("active_power_kw"))
            rows.append({
                "timestamp": ts.to_pydatetime(),
                "active_power_kw": ap,
                "reactive_power_kw": safe(row.get("Global_reactive_power")),
                "voltage_v": safe(row.get("Voltage")),
                "current_a": safe(row.get("Global_intensity")),
                "sub_metering_1_wh": safe(row.get("Sub_metering_1")),
                "sub_metering_2_wh": safe(row.get("Sub_metering_2")),
                "sub_metering_3_wh": safe(row.get("Sub_metering_3")),
                "energy_kwh": safe(row.get("energy_kwh")),
                "cost_inr": safe(row.get("cost_inr")),
                "class_label": get_class(ap) if ap is not None else None,
                "is_simulated": 1,
                "is_anomaly": 0,
                "is_gap": int(bool(row.get("is_gap", False))),
            })

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO readings
                    (timestamp, active_power_kw, reactive_power_kw, voltage_v, current_a,
                     sub_metering_1_wh, sub_metering_2_wh, sub_metering_3_wh,
                     energy_kwh, cost_inr, class_label, is_simulated, is_anomaly, is_gap)
                VALUES
                    (:timestamp, :active_power_kw, :reactive_power_kw, :voltage_v, :current_a,
                     :sub_metering_1_wh, :sub_metering_2_wh, :sub_metering_3_wh,
                     :energy_kwh, :cost_inr, :class_label, :is_simulated, :is_anomaly, :is_gap)
                ON DUPLICATE KEY UPDATE
                    active_power_kw    = VALUES(active_power_kw),
                    reactive_power_kw  = VALUES(reactive_power_kw),
                    voltage_v          = VALUES(voltage_v),
                    current_a          = VALUES(current_a),
                    energy_kwh         = VALUES(energy_kwh),
                    cost_inr           = VALUES(cost_inr),
                    class_label        = VALUES(class_label),
                    is_gap             = VALUES(is_gap)
            """), rows)

        inserted += len(rows)
        pct = inserted / total * 100
        log.info("  Readings: %d / %d  (%.1f%%)", inserted, total, pct)

    log.info("Minute readings done: %d rows", inserted)
    return inserted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-readings", action="store_true",
                        help="Also bulk-load minute readings (~2M rows, slow but gives full historical data)")
    args = parser.parse_args()

    from backend.app.services.db import get_engine, init_db
    init_db()
    engine = get_engine()

    log.info("=== Loading hourly aggregates ===")
    n_hourly = load_hourly(engine)

    log.info("=== Loading daily aggregates ===")
    n_daily = load_daily(engine)

    if args.with_readings:
        log.info("=== Loading minute-level readings (this is large — ~2M rows) ===")
        n_readings = load_readings(engine)
        log.info("Done. Hourly=%d  Daily=%d  Readings=%d", n_hourly, n_daily, n_readings)
    else:
        log.info("Done. Hourly=%d  Daily=%d  (use --with-readings to bulk-load 2M minute readings)", n_hourly, n_daily)


if __name__ == "__main__":
    main()
