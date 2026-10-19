"""
backend/app/ml/forecaster.py
-----------------------------
Energy Consumption Forecasting: predict next-hour kWh.

Models:
  1. Naive baseline: last observed value (lag_1h)
  2. Same-time-yesterday baseline: lag_24h value
  3. Linear Regression on lag + time features
  4. Ridge Regression (regularized variant)
  5. Random Forest Regressor (optional, higher complexity)

Split: CHRONOLOGICAL (last 20% as test). NO random shuffle.
Metric: MAE, RMSE (and MAPE, R² where valid). Compare all models to baselines.

Note: If linear regression underperforms the naive baseline, this is stated
      explicitly in the evaluation report (not hidden or inflated).

Usage:
    from backend.app.ml.forecaster import Forecaster, train_and_evaluate_forecast
"""

from __future__ import annotations

import logging
import pathlib
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

log = logging.getLogger(__name__)

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "backend" / "app" / "ml" / "saved_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Features for hourly forecasting (predicting NEXT hour's kWh sum)
FORECAST_FEATURES = [
    "hour", "day_of_week", "is_weekend", "month",
    "lag_1h",      # Previous hour kWh
    "lag_24h",     # Same hour yesterday
    "lag_7d",      # Same hour last week (if available; 168 hourly lags)
    "rolling_mean_1h",  # Recent mean
    "rolling_mean_24h", # Day-long mean (if available)
]


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, name: str) -> dict:
    """Compute regression metrics. MAPE only if no zeros in y_true."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    metrics = {"model": name, "MAE": round(mae, 6), "RMSE": round(rmse, 6), "R2": round(r2, 6)}
    # MAPE: only if no zeros
    nonzero = y_true != 0
    if nonzero.all():
        mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
        metrics["MAPE_%"] = round(mape, 4)
    return metrics


def prepare_hourly_features(df_hourly: pd.DataFrame) -> pd.DataFrame:
    """
    Build feature matrix for hourly forecasting.
    Target: next-hour energy (energy_kwh shifted -1).
    Uses hourly-resampled data from preprocessing.
    """
    df = df_hourly.copy()

    # Time features
    df["hour"] = df.index.hour
    df["day_of_week"] = df.index.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["month"] = df.index.month

    col = "energy_kwh" if "energy_kwh" in df.columns else "active_power_kw"

    # Lag features (in hourly units)
    df["lag_1h"] = df[col].shift(1)
    df["lag_24h"] = df[col].shift(24)
    df["lag_7d"] = df[col].shift(168)  # 168 hours = 7 days
    df["rolling_mean_1h"] = df[col].rolling(4, min_periods=1).mean()
    df["rolling_mean_24h"] = df[col].rolling(24, min_periods=1).mean()

    # Target: NEXT hour's energy
    df["target"] = df[col].shift(-1)

    return df


class Forecaster:
    """
    Wrapper around a scikit-learn regressor for hourly energy forecasting.
    Includes scaler for feature normalization.
    """

    def __init__(self, model_name: str, model):
        self.model_name = model_name
        self.model = model
        self.scaler = StandardScaler()
        self.features: list[str] = []
        self.metrics: dict = {}
        self._fitted = False

    def fit(
        self,
        df: pd.DataFrame,
        test_frac: float = 0.2,
    ) -> dict:
        """Train on chronological split, return metrics vs baselines."""
        available_features = [f for f in FORECAST_FEATURES if f in df.columns]
        self.features = available_features

        # Drop NaN rows (from lags)
        data = df[available_features + ["target", "lag_1h", "lag_24h"]].dropna()

        n = len(data)
        split = int(n * (1 - test_frac))
        train = data.iloc[:split]
        test = data.iloc[split:]

        X_train = train[available_features]
        y_train = train["target"].values
        X_test = test[available_features]
        y_test = test["target"].values

        # Scale
        X_train_s = self.scaler.fit_transform(X_train)
        X_test_s = self.scaler.transform(X_test)

        log.info(
            "Training %s forecaster: %d train / %d test (chronological)",
            self.model_name, len(X_train), len(X_test),
        )
        self.model.fit(X_train_s, y_train)
        y_pred = self.model.predict(X_test_s)
        # Clip negative predictions to 0
        y_pred = np.clip(y_pred, 0, None)

        # Compute metrics
        model_metrics = compute_metrics(y_test, y_pred, self.model_name)

        # Baseline 1: naive (lag_1h = previous hour)
        naive_pred = test["lag_1h"].values
        naive_metrics = compute_metrics(y_test, naive_pred, "naive_last_hour")

        # Baseline 2: same-time-yesterday
        same_day_pred = test["lag_24h"].values
        same_day_metrics = compute_metrics(y_test, same_day_pred, "naive_same_hour_yesterday")

        self.metrics = {
            "model": model_metrics,
            "baseline_naive_last_hour": naive_metrics,
            "baseline_same_hour_yesterday": same_day_metrics,
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "features_used": available_features,
            "note": (
                "If model MAE > baseline MAE, the baseline performs better. "
                "This is reported honestly below."
            ),
        }

        # Flag if model underperforms baseline
        if model_metrics["MAE"] > naive_metrics["MAE"]:
            self.metrics["warning"] = (
                f"{self.model_name} MAE ({model_metrics['MAE']:.4f}) > "
                f"naive baseline MAE ({naive_metrics['MAE']:.4f}). "
                "The naive baseline outperforms this model on the test set."
            )
            log.warning(self.metrics["warning"])

        self._fitted = True
        log.info(
            "%s — MAE: %.4f, RMSE: %.4f, R²: %.4f | Naive MAE: %.4f",
            self.model_name,
            model_metrics["MAE"], model_metrics["RMSE"], model_metrics["R2"],
            naive_metrics["MAE"],
        )
        return self.metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict on new data. Returns array of predictions."""
        if not self._fitted:
            raise RuntimeError("Call fit() first.")
        available = [f for f in self.features if f in X.columns]
        X_s = self.scaler.transform(X[available])
        preds = self.model.predict(X_s)
        return np.clip(preds, 0, None)

    def predict_next(self, current_features: dict) -> float:
        """Predict next-hour kWh from current feature dict."""
        row = pd.DataFrame([current_features])
        return float(self.predict(row)[0])

    def save(self, path: Optional[pathlib.Path] = None) -> pathlib.Path:
        path = path or (MODEL_DIR / f"{self.model_name}_forecaster.joblib")
        joblib.dump(self, path)
        log.info("Forecaster '%s' saved → %s", self.model_name, path)
        return path

    @staticmethod
    def load(path: pathlib.Path) -> "Forecaster":
        return joblib.load(path)


def train_and_evaluate_forecast(df_hourly: pd.DataFrame) -> dict:
    """
    Full forecast training pipeline.
    Trains Linear Regression, Ridge, and Random Forest.
    Returns all metrics for comparison.
    """
    df_feat = prepare_hourly_features(df_hourly)

    results = {}

    for name, model in [
        ("linear_regression", LinearRegression()),
        ("ridge_regression", Ridge(alpha=1.0)),
        ("random_forest", RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)),
    ]:
        try:
            forecaster = Forecaster(model_name=name, model=model)
            metrics = forecaster.fit(df_feat)
            forecaster.save()
            results[name] = metrics
        except Exception as exc:
            log.error("Failed to train %s: %s", name, exc)
            results[name] = {"error": str(exc)}

    # Determine best model
    valid = {k: v for k, v in results.items() if "error" not in v and "model" in v}
    if valid:
        best = min(valid.keys(), key=lambda k: valid[k]["model"].get("MAE", 1e9))
        results["best_model"] = best
        log.info("Best forecasting model: %s (lowest MAE)", best)

    return results
