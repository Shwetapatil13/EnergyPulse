"""
backend/app/ml/anomaly.py
--------------------------
Anomaly detection for EnergyPulse.

Methods:
  1. Rolling z-score: (value - rolling_mean) / rolling_std > threshold
  2. IQR rule: value < Q1 - k*IQR or value > Q3 + k*IQR
  3. Absolute threshold: value > abs_threshold_kw
  4. Delta rule: |current - previous| > delta_threshold
  5. (Optional) IsolationForest for unsupervised detection

All thresholds are configurable. Results are labeled with type + severity.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    is_anomaly: bool
    alert_type: str
    severity: str         # low / medium / high / critical
    value: float
    threshold: float
    rule_description: str


def compute_zscore_anomaly(
    value: float,
    rolling_mean: float,
    rolling_std: float,
    threshold: float = 3.0,
) -> Optional[AnomalyResult]:
    """
    Rolling Z-score anomaly detection.
    Flags if |z| > threshold.
    severity: |z|>3=medium, |z|>4=high, |z|>5=critical
    """
    if rolling_std < 1e-6:
        return None
    z = (value - rolling_mean) / rolling_std
    if abs(z) > threshold:
        if abs(z) > 5:
            severity = "critical"
        elif abs(z) > 4:
            severity = "high"
        else:
            severity = "medium"
        return AnomalyResult(
            is_anomaly=True,
            alert_type="z_score",
            severity=severity,
            value=value,
            threshold=threshold,
            rule_description=(
                f"Z-score {z:.2f} exceeds threshold ±{threshold:.1f} "
                f"(rolling mean={rolling_mean:.3f} kW, std={rolling_std:.3f} kW)"
            ),
        )
    return None


def compute_iqr_anomaly(
    value: float,
    q1: float,
    q3: float,
    multiplier: float = 1.5,
) -> Optional[AnomalyResult]:
    """
    IQR-based outlier detection.
    Flags if value < Q1 - k*IQR or value > Q3 + k*IQR.
    """
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    if value > upper or value < lower:
        severity = "high" if multiplier >= 3 or value > upper * 1.5 else "medium"
        return AnomalyResult(
            is_anomaly=True,
            alert_type="iqr",
            severity=severity,
            value=value,
            threshold=upper,
            rule_description=(
                f"Value {value:.3f} kW outside IQR bounds [{lower:.3f}, {upper:.3f}] "
                f"(Q1={q1:.3f}, Q3={q3:.3f}, IQR={iqr:.3f}, k={multiplier})"
            ),
        )
    return None


def compute_abs_threshold_anomaly(
    value: float,
    abs_threshold_kw: float = 5.0,
) -> Optional[AnomalyResult]:
    """Absolute threshold: flag if value > abs_threshold_kw."""
    if value > abs_threshold_kw:
        severity = "critical" if value > abs_threshold_kw * 1.5 else "high"
        return AnomalyResult(
            is_anomaly=True,
            alert_type="abs_threshold",
            severity=severity,
            value=value,
            threshold=abs_threshold_kw,
            rule_description=(
                f"Active power {value:.3f} kW exceeds absolute threshold "
                f"{abs_threshold_kw:.1f} kW"
            ),
        )
    return None


def compute_delta_anomaly(
    current: float,
    previous: float,
    delta_threshold_kw: float = 2.0,
) -> Optional[AnomalyResult]:
    """Sudden jump detection: large delta between consecutive readings."""
    delta = abs(current - previous)
    if delta > delta_threshold_kw:
        severity = "high" if delta > delta_threshold_kw * 2 else "medium"
        return AnomalyResult(
            is_anomaly=True,
            alert_type="delta",
            severity=severity,
            value=delta,
            threshold=delta_threshold_kw,
            rule_description=(
                f"Sudden jump of {delta:.3f} kW (prev={previous:.3f}, "
                f"current={current:.3f}) exceeds delta threshold {delta_threshold_kw:.1f} kW"
            ),
        )
    return None


class RealTimeAnomalyDetector:
    """
    Stateful rolling anomaly detector for the streaming pipeline.
    Maintains a circular buffer of recent readings.
    """

    def __init__(
        self,
        window: int = 60,
        z_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        abs_threshold_kw: float = 5.0,
        delta_threshold_kw: float = 2.0,
    ):
        self.window = window
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
        self.abs_threshold_kw = abs_threshold_kw
        self.delta_threshold_kw = delta_threshold_kw
        self._buffer: list[float] = []
        self._prev_value: Optional[float] = None

    def update_thresholds(
        self,
        z_threshold: float = None,
        iqr_multiplier: float = None,
        abs_threshold_kw: float = None,
        delta_threshold_kw: float = None,
    ):
        if z_threshold is not None:
            self.z_threshold = z_threshold
        if iqr_multiplier is not None:
            self.iqr_multiplier = iqr_multiplier
        if abs_threshold_kw is not None:
            self.abs_threshold_kw = abs_threshold_kw
        if delta_threshold_kw is not None:
            self.delta_threshold_kw = delta_threshold_kw

    def check(self, value: float) -> list[AnomalyResult]:
        """
        Check a new value for anomalies.
        Returns list of triggered AnomalyResult (may be empty).
        """
        results = []

        # Update buffer
        self._buffer.append(value)
        if len(self._buffer) > self.window:
            self._buffer.pop(0)

        arr = np.array(self._buffer)

        # Z-score check (need enough data)
        if len(arr) >= 10:
            mean = float(np.mean(arr))
            std = float(np.std(arr))
            r = compute_zscore_anomaly(value, mean, std, self.z_threshold)
            if r:
                results.append(r)

        # IQR check
        if len(arr) >= 20:
            q1, q3 = float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
            r = compute_iqr_anomaly(value, q1, q3, self.iqr_multiplier)
            if r:
                results.append(r)

        # Absolute threshold
        r = compute_abs_threshold_anomaly(value, self.abs_threshold_kw)
        if r:
            results.append(r)

        # Delta (sudden jump)
        if self._prev_value is not None:
            r = compute_delta_anomaly(value, self._prev_value, self.delta_threshold_kw)
            if r:
                results.append(r)

        self._prev_value = value
        return results


class BatchAnomalyDetector:
    """
    Applies anomaly detection to a historical DataFrame.
    Used for pre-loading historical alerts.
    """

    def __init__(
        self,
        window: int = 60,
        z_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        abs_threshold_kw: float = 5.0,
    ):
        self.window = window
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
        self.abs_threshold_kw = abs_threshold_kw

    def detect(self, df: pd.DataFrame, col: str = "active_power_kw") -> pd.DataFrame:
        """
        Run all anomaly rules on a DataFrame column.
        Adds columns: is_anomaly, anomaly_type, anomaly_severity.
        """
        df = df.copy()
        series = df[col].fillna(0)

        # Rolling stats
        roll_mean = series.rolling(self.window, min_periods=10).mean()
        roll_std = series.rolling(self.window, min_periods=10).std()
        z_score = (series - roll_mean) / (roll_std + 1e-8)

        # IQR on rolling window
        q1 = series.rolling(self.window, min_periods=20).quantile(0.25)
        q3 = series.rolling(self.window, min_periods=20).quantile(0.75)
        iqr = q3 - q1
        iqr_upper = q3 + self.iqr_multiplier * iqr

        # Delta
        delta = series.diff().abs()

        # Compute flags
        z_flag = z_score.abs() > self.z_threshold
        iqr_flag = series > iqr_upper
        abs_flag = series > self.abs_threshold_kw

        df["is_anomaly"] = z_flag | iqr_flag | abs_flag
        df["z_score"] = z_score.round(4)
        df["rolling_mean"] = roll_mean.round(4)
        df["rolling_std"] = roll_std.round(4)

        log.info(
            "Batch anomaly detection: %d anomalies in %d rows (%.2f%%)",
            df["is_anomaly"].sum(),
            len(df),
            df["is_anomaly"].mean() * 100,
        )
        return df
