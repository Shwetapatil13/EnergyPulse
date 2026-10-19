"""
backend/app/ml/classifier.py
-----------------------------
Consumption Classification: low / moderate / high

Method 1 (Primary, Transparent):
  - Percentile-based thresholds computed from TRAINING data only
  - Tercile boundaries (33rd and 67th percentile of active_power_kw)
  - Simple, interpretable, no leakage risk

Method 2 (Optional, ML):
  - Random Forest classifier on lag + time features
  - Labels derived from percentile method on training set
  - IMPORTANT: The label is derived from Global_active_power values
    from the SAME row; we mitigate leakage by using ONLY lag/time features,
    never current active_power_kw, as a predictor.
  - Evaluated with accuracy, precision, recall, F1, confusion matrix
  - Train/test: chronological split (last 20% as test)

Usage:
    from backend.app.ml.classifier import PercentileClassifier, MLClassifier
"""

from __future__ import annotations

import json
import logging
import pathlib
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix
)
from sklearn.tree import DecisionTreeClassifier

log = logging.getLogger(__name__)

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "backend" / "app" / "ml" / "saved_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CLASSES = ["low", "moderate", "high"]

# Features used for ML classifier (NO current active_power to avoid label leakage)
ML_FEATURES = [
    "hour", "day_of_week", "is_weekend", "month",
    "lag_1h", "lag_24h", "lag_7d",
    "rolling_mean_1h", "rolling_std_1h", "rolling_mean_24h",
]


class PercentileClassifier:
    """
    Transparent percentile-based classifier.

    Assigns class labels based on tercile boundaries computed from training data:
      - low      : value <= p33
      - moderate : p33 < value <= p67
      - high     : value > p67

    These boundaries are computed ONLY from training data to avoid data leakage.
    """

    def __init__(self, low_pct: float = 33.0, high_pct: float = 67.0):
        self.low_pct = low_pct
        self.high_pct = high_pct
        self.low_threshold: Optional[float] = None
        self.high_threshold: Optional[float] = None
        self._fitted = False

    def fit(self, train_values: pd.Series) -> "PercentileClassifier":
        """Compute thresholds from training data only."""
        self.low_threshold = float(np.percentile(train_values.dropna(), self.low_pct))
        self.high_threshold = float(np.percentile(train_values.dropna(), self.high_pct))
        self._fitted = True
        log.info(
            "PercentileClassifier fitted: low≤%.4f kW, high>%.4f kW (p%d/p%d from training)",
            self.low_threshold, self.high_threshold, int(self.low_pct), int(self.high_pct),
        )
        return self

    def predict_one(self, value: float) -> str:
        """Classify a single reading."""
        if not self._fitted:
            raise RuntimeError("Call fit() first.")
        if value <= self.low_threshold:
            return "low"
        elif value <= self.high_threshold:
            return "moderate"
        return "high"

    def predict(self, values: pd.Series) -> pd.Series:
        """Classify a series of readings."""
        return values.apply(self.predict_one)

    def to_dict(self) -> dict:
        return {
            "type": "percentile",
            "low_pct": self.low_pct,
            "high_pct": self.high_pct,
            "low_threshold_kw": self.low_threshold,
            "high_threshold_kw": self.high_threshold,
        }

    def save(self, path: Optional[pathlib.Path] = None) -> pathlib.Path:
        path = path or (MODEL_DIR / "percentile_classifier.joblib")
        joblib.dump(self, path)
        log.info("PercentileClassifier saved → %s", path)
        return path

    @staticmethod
    def load(path: Optional[pathlib.Path] = None) -> "PercentileClassifier":
        path = path or (MODEL_DIR / "percentile_classifier.joblib")
        return joblib.load(path)


class MLClassifier:
    """
    ML-based classifier (Random Forest / Decision Tree) trained on lag + time features.

    ⚠ Label leakage note:
      Labels (low/moderate/high) are derived from active_power_kw values.
      To avoid using the current value as a feature predicting its own label,
      we use ONLY lagged and time-based features. The model predicts what
      class the CURRENT reading will be based on PAST readings and time context.
    """

    def __init__(self, model_type: str = "random_forest", **kwargs):
        self.model_type = model_type
        if model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=kwargs.get("n_estimators", 100),
                max_depth=kwargs.get("max_depth", 10),
                random_state=42,
                n_jobs=-1,
            )
        elif model_type == "decision_tree":
            self.model = DecisionTreeClassifier(
                max_depth=kwargs.get("max_depth", 10),
                random_state=42,
            )
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        self.features = ML_FEATURES
        self.label_encoder = {"low": 0, "moderate": 1, "high": 2}
        self.label_decoder = {0: "low", 1: "moderate", 2: "high"}
        self.metrics: dict = {}

    def prepare_data(
        self,
        df: pd.DataFrame,
        label_col: str = "class_label",
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Extract feature matrix and label vector, dropping NaN rows."""
        available_features = [f for f in self.features if f in df.columns]
        if len(available_features) < len(self.features):
            missing = set(self.features) - set(available_features)
            log.warning("Missing ML features: %s — these will be excluded", missing)
        X = df[available_features].copy()
        y = df[label_col].map(self.label_encoder)
        mask = X.notna().all(axis=1) & y.notna()
        return X[mask], y[mask]

    def fit(
        self,
        df: pd.DataFrame,
        label_col: str = "class_label",
        test_frac: float = 0.2,
    ) -> dict:
        """
        Train on chronological split. Returns evaluation metrics.
        """
        n = len(df)
        split = int(n * (1 - test_frac))
        train_df = df.iloc[:split]
        test_df = df.iloc[split:]

        X_train, y_train = self.prepare_data(train_df, label_col)
        X_test, y_test = self.prepare_data(test_df, label_col)

        log.info(
            "Training %s classifier: %d train / %d test rows",
            self.model_type, len(X_train), len(X_test),
        )
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)

        self.metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "classification_report": classification_report(
                y_test, y_pred,
                target_names=CLASSES,
                output_dict=True,
            ),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "train_rows": len(X_train),
            "test_rows": len(X_test),
            "features_used": [f for f in self.features if f in df.columns],
            "leakage_note": (
                "Label (low/moderate/high) derives from active_power_kw. "
                "To prevent leakage, only lag and time features are used — "
                "NOT the current active_power_kw value."
            ),
        }
        log.info(
            "ML Classifier accuracy: %.4f (test set, chronological split)",
            self.metrics["accuracy"],
        )
        return self.metrics

    def predict_one(self, features: dict) -> str:
        row = pd.DataFrame([features])
        available = [f for f in self.features if f in row.columns]
        pred = self.model.predict(row[available])[0]
        return self.label_decoder[int(pred)]

    def save(self, path: Optional[pathlib.Path] = None) -> pathlib.Path:
        path = path or (MODEL_DIR / f"{self.model_type}_classifier.joblib")
        joblib.dump(self, path)
        log.info("MLClassifier saved → %s", path)
        return path

    @staticmethod
    def load(path: pathlib.Path) -> "MLClassifier":
        return joblib.load(path)


def train_and_evaluate(
    df: pd.DataFrame,
    tariff_inr: float = 8.0,
) -> dict:
    """
    Full classification training pipeline.
    1. Fit PercentileClassifier on training data → generate labels
    2. Train MLClassifier on lag/time features
    3. Save both models
    4. Return all metrics
    """
    n = len(df)
    split = int(n * 0.8)
    train_df = df.iloc[:split].copy()

    # Step 1: Fit percentile classifier on training data only
    pct_clf = PercentileClassifier(low_pct=33.0, high_pct=67.0)
    pct_clf.fit(train_df["active_power_kw"].dropna())
    pct_clf.save()

    # Step 2: Generate labels for full dataset
    df = df.copy()
    df["class_label"] = pct_clf.predict(df["active_power_kw"].fillna(0))

    # Step 3: Train ML classifier
    ml_clf = MLClassifier(model_type="random_forest")
    metrics = ml_clf.fit(df, label_col="class_label")
    ml_clf.save()

    results = {
        "percentile_classifier": pct_clf.to_dict(),
        "ml_classifier": metrics,
    }
    log.info("Classification training complete.")
    return results
