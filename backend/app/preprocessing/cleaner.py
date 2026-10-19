"""
backend/app/preprocessing/cleaner.py
--------------------------------------
Cleans and preprocesses the raw UCI Household Power Consumption dataset.

Pipeline:
  1. Load raw CSV with correct delimiter & missing-value encoding
  2. Combine Date + Time → single datetime index (dayfirst=True)
  3. Sort chronologically, remove duplicates
  4. Handle missing values:
     - Forward-fill gaps ≤ 30 minutes
     - Flag (and optionally drop) gaps > 30 minutes
  5. Unit conversion: kWh per minute = Global_active_power (kW) × (1/60)
  6. Resample to hourly and daily aggregates
  7. Feature engineering for ML
  8. Save processed outputs to data/processed/

Usage:
    python -m backend.app.preprocessing.cleaner
    # or import and call run_pipeline()
"""

from __future__ import annotations

import logging
import pathlib
from datetime import timedelta
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────
EXPECTED_COLUMNS = [
    "Date", "Time",
    "Global_active_power", "Global_reactive_power",
    "Voltage", "Global_intensity",
    "Sub_metering_1", "Sub_metering_2", "Sub_metering_3",
]

NUMERIC_COLS = [
    "Global_active_power", "Global_reactive_power",
    "Voltage", "Global_intensity",
    "Sub_metering_1", "Sub_metering_2", "Sub_metering_3",
]

MAX_FILL_GAP_MINUTES = 30  # Forward-fill gaps up to this many minutes


def find_raw_file() -> pathlib.Path:
    """Locate the raw dataset file."""
    candidates = sorted(
        list(RAW_DIR.glob("*.txt")) + list(RAW_DIR.glob("*.csv")),
        key=lambda p: p.stat().st_size,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            f"No raw dataset found in {RAW_DIR}. "
            "Run: python scripts/download_data.py"
        )
    return candidates[0]


def detect_delimiter(path: pathlib.Path) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        first = f.readline()
    return ";" if ";" in first else ("\t" if "\t" in first else ",")


def load_raw(path: Optional[pathlib.Path] = None) -> pd.DataFrame:
    """Load raw CSV into DataFrame with NaN-decoded missing values."""
    if path is None:
        path = find_raw_file()
    delimiter = detect_delimiter(path)
    log.info("Loading %s (delimiter=%r)…", path.name, delimiter)
    df = pd.read_csv(
        path,
        sep=delimiter,
        na_values=["?", "NA", "N/A", "", " "],
        low_memory=False,
    )
    log.info("Loaded %d rows × %d columns", len(df), len(df.columns))
    return df


def build_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine 'Date' and 'Time' columns into a single datetime index.
    Date format is DD/MM/YYYY (day-first).
    """
    log.info("Parsing datetime (dayfirst=True)…")
    dt_str = df["Date"].astype(str) + " " + df["Time"].astype(str)
    dt = pd.to_datetime(dt_str, dayfirst=True, errors="coerce")
    n_failed = dt.isna().sum()
    if n_failed > 0:
        log.warning("%d rows with unparseable datetime — dropped", n_failed)
    df = df.copy()
    df["datetime"] = dt
    df = df.dropna(subset=["datetime"]).set_index("datetime").drop(
        columns=["Date", "Time"], errors="ignore"
    )
    return df


def sort_and_dedup(df: pd.DataFrame) -> pd.DataFrame:
    """Sort chronologically and remove duplicate timestamps."""
    df = df.sort_index()
    n_before = len(df)
    df = df[~df.index.duplicated(keep="first")]
    n_dropped = n_before - len(df)
    if n_dropped > 0:
        log.info("Removed %d duplicate timestamps", n_dropped)
    return df


def check_gaps(df: pd.DataFrame) -> dict:
    """Identify gaps larger than the expected 1-minute interval."""
    diffs = df.index.to_series().diff().dropna()
    expected = timedelta(minutes=1)
    gaps = diffs[diffs > expected]
    gap_info = {
        "total_gap_count": len(gaps),
        "max_gap_minutes": float(gaps.max().total_seconds() / 60) if len(gaps) > 0 else 0,
        "long_gaps": gaps[gaps > timedelta(minutes=MAX_FILL_GAP_MINUTES)].dt.total_seconds().div(60).to_dict(),
    }
    log.info(
        "Gaps found: %d gaps; max gap = %.1f min",
        gap_info["total_gap_count"],
        gap_info["max_gap_minutes"],
    )
    return gap_info


def handle_missing_values(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Missing value strategy:
      - Numeric columns with NaN:
          * Forward-fill within gaps ≤ MAX_FILL_GAP_MINUTES minutes
          * Flag rows in longer gaps with is_gap=True
      - Returns (cleaned_df, stats_dict)
    """
    stats = {}
    total_rows = len(df)

    for col in NUMERIC_COLS:
        if col not in df.columns:
            continue
        n_missing = df[col].isna().sum()
        if n_missing == 0:
            continue
        stats[col] = {"missing_before": int(n_missing)}

        # Reindex to full 1-min frequency to expose gaps
        full_idx = pd.date_range(df.index.min(), df.index.max(), freq="1min")
        series = df[col].reindex(full_idx)

        # Forward-fill limit = MAX_FILL_GAP_MINUTES ticks
        filled = series.ffill(limit=MAX_FILL_GAP_MINUTES)
        stats[col]["filled_by_ffill"] = int(filled.isna().sum() < series.isna().sum())

        # Put back (only rows in original index)
        df[col] = filled.reindex(df.index)
        stats[col]["missing_after"] = int(df[col].isna().sum())

    # Add is_gap flag for rows still missing after fill
    any_missing_mask = df[NUMERIC_COLS].isna().any(axis=1)
    df["is_gap"] = any_missing_mask
    n_flagged = int(any_missing_mask.sum())
    if n_flagged > 0:
        log.warning(
            "%d rows flagged as long-gap (still NaN after ffill limit). "
            "These rows are kept but marked is_gap=True.",
            n_flagged,
        )
    stats["_total_rows"] = total_rows
    stats["_flagged_long_gap"] = n_flagged
    log.info("Missing value handling complete: %s", stats)
    return df, stats


def add_energy_and_cost(df: pd.DataFrame, tariff_inr: float = 8.0) -> pd.DataFrame:
    """
    Unit conversion and derived columns:
      - active_power_kw  = Global_active_power  (already in kW)
      - energy_kwh       = active_power_kw × (1/60)   [1-minute intervals]
        Formula: kWh = kW × hours = kW × (1 min / 60 min per hour)
      - cost_inr         = energy_kwh × tariff_inr
    """
    df = df.copy()
    df["active_power_kw"] = df["Global_active_power"]
    df["energy_kwh"] = df["active_power_kw"] / 60.0  # kWh per 1-minute reading
    df["cost_inr"] = df["energy_kwh"] * tariff_inr
    log.info(
        "Energy conversion: kWh = kW × (1/60). Tariff = INR %.2f/kWh (assumed flat rate).",
        tariff_inr,
    )
    return df


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Time-based and lag features for ML:

    Time features:
      - hour          : 0-23
      - day_of_week   : 0=Monday, 6=Sunday
      - is_weekend    : 1 if Saturday/Sunday
      - month         : 1-12
      - day_of_year   : 1-366
      - week_of_year  : 1-53

    Lag features (using active_power_kw, 1-minute resolution):
      - lag_1h        : value 60 rows ago (previous hour)
      - lag_24h       : value 1440 rows ago (same hour previous day)
      - lag_7d        : value 10080 rows ago (same time previous week)

    Rolling statistics:
      - rolling_mean_1h  : 60-period rolling mean
      - rolling_std_1h   : 60-period rolling std
      - rolling_mean_24h : 1440-period rolling mean
    """
    df = df.copy()

    # Time features
    df["hour"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek  # 0=Mon
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["month"] = df.index.month
    df["day_of_year"] = df.index.dayofyear
    df["week_of_year"] = df.index.isocalendar().week.astype(int)

    # Lag features
    power = df["active_power_kw"]
    df["lag_1h"] = power.shift(60)       # 60 minutes = 1 hour
    df["lag_24h"] = power.shift(1440)    # 1440 minutes = 1 day
    df["lag_7d"] = power.shift(10080)    # 10080 minutes = 7 days

    # Rolling statistics
    df["rolling_mean_1h"] = power.rolling(60, min_periods=1).mean()
    df["rolling_std_1h"] = power.rolling(60, min_periods=1).std().fillna(0)
    df["rolling_mean_24h"] = power.rolling(1440, min_periods=1).mean()

    log.info("Feature engineering complete: added %d new columns", 13)
    return df


def resample_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to hourly resolution."""
    agg = {
        "active_power_kw": "mean",
        "Global_reactive_power": "mean",
        "Voltage": "mean",
        "Global_intensity": "mean",
        "energy_kwh": "sum",
        "cost_inr": "sum",
    }
    # Sub-metering if present
    for sm in ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]:
        if sm in df.columns:
            agg[sm] = "sum"

    available = {k: v for k, v in agg.items() if k in df.columns}
    hourly = df.resample("h").agg(available)
    # Add time features
    hourly["hour"] = hourly.index.hour
    hourly["day_of_week"] = hourly.index.dayofweek
    hourly["is_weekend"] = (hourly["day_of_week"] >= 5).astype(int)
    hourly["month"] = hourly.index.month
    log.info("Hourly aggregate: %d rows", len(hourly))
    return hourly


def resample_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to daily resolution."""
    agg = {
        "active_power_kw": ["mean", "max", "min"],
        "energy_kwh": "sum",
        "cost_inr": "sum",
        "Voltage": "mean",
        "Global_intensity": "mean",
    }
    for sm in ["Sub_metering_1", "Sub_metering_2", "Sub_metering_3"]:
        if sm in df.columns:
            agg[sm] = "sum"

    available = {k: v for k, v in agg.items() if k in df.columns}
    daily = df.resample("D").agg(available)
    # Flatten multi-level columns
    daily.columns = ["_".join(c).strip("_") if isinstance(c, tuple) else c for c in daily.columns]
    daily["day_of_week"] = daily.index.dayofweek
    daily["is_weekend"] = (daily["day_of_week"] >= 5).astype(int)
    daily["month"] = daily.index.month
    log.info("Daily aggregate: %d rows", len(daily))
    return daily


def save_outputs(
    df_minute: pd.DataFrame,
    df_hourly: pd.DataFrame,
    df_daily: pd.DataFrame,
) -> dict[str, pathlib.Path]:
    """Save processed data to data/processed/."""
    paths = {}

    # Minute-level parquet (primary)
    p = PROCESSED_DIR / "readings_1min.parquet"
    df_minute.to_parquet(p, engine="pyarrow")
    paths["minute_parquet"] = p
    log.info("Saved minute-level: %s (%.1f MB)", p.name, p.stat().st_size / 1e6)

    # Hourly
    p = PROCESSED_DIR / "hourly_aggregates.parquet"
    df_hourly.to_parquet(p, engine="pyarrow")
    paths["hourly_parquet"] = p

    p = PROCESSED_DIR / "hourly_aggregates.csv"
    df_hourly.to_csv(p)
    paths["hourly_csv"] = p

    # Daily
    p = PROCESSED_DIR / "daily_aggregates.parquet"
    df_daily.to_parquet(p, engine="pyarrow")
    paths["daily_parquet"] = p

    p = PROCESSED_DIR / "daily_aggregates.csv"
    df_daily.to_csv(p)
    paths["daily_csv"] = p

    log.info("All processed files saved to %s", PROCESSED_DIR)
    return paths


def run_pipeline(
    raw_path: Optional[pathlib.Path] = None,
    tariff_inr: float = 8.0,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """
    Full preprocessing pipeline.

    Returns:
        (df_minute, df_hourly, df_daily, pipeline_stats)
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # 1. Load
    df = load_raw(raw_path)

    # 2. DateTime index
    df = build_datetime_index(df)

    # 3. Sort + dedup
    df = sort_and_dedup(df)

    # 4. Gap analysis
    gap_info = check_gaps(df)

    # 5. Missing values
    df, mv_stats = handle_missing_values(df)

    # 6. Energy + cost
    df = add_energy_and_cost(df, tariff_inr)

    # 7. Feature engineering
    df = feature_engineering(df)

    # 8. Aggregates
    df_hourly = resample_hourly(df)
    df_daily = resample_daily(df)

    # 9. Save
    paths = save_outputs(df, df_hourly, df_daily)

    stats = {
        "total_rows": len(df),
        "date_range": (str(df.index.min()), str(df.index.max())),
        "gap_info": gap_info,
        "missing_value_stats": mv_stats,
        "output_paths": {k: str(v) for k, v in paths.items()},
    }

    log.info("Pipeline complete. %d minute-level rows.", len(df))
    return df, df_hourly, df_daily, stats


if __name__ == "__main__":
    df_min, df_hr, df_day, stats = run_pipeline()
    print(f"\nPipeline complete!")
    print(f"  Minute rows: {stats['total_rows']:,}")
    print(f"  Date range: {stats['date_range'][0]} → {stats['date_range'][1]}")
    print(f"  Outputs: {list(stats['output_paths'].keys())}")
