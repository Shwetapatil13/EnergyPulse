"""
scripts/run_ml_training.py
---------------------------
Train all ML models (classifier + forecaster) and save evaluation to docs/.
Produces docs/model_evaluation.md with REAL metrics from the dataset.

Usage:
    python scripts/run_ml_training.py
"""

import sys
import pathlib
import logging
import json
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

DOCS_DIR = pathlib.Path(__file__).parent.parent / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def main():
    import pandas as pd

    PROCESSED_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"

    # Load processed data
    minute_path = PROCESSED_DIR / "readings_1min.parquet"
    hourly_path = PROCESSED_DIR / "hourly_aggregates.parquet"

    if not minute_path.exists():
        log.error("Processed data not found. Run: python scripts/run_preprocessing.py first.")
        sys.exit(1)

    log.info("Loading minute-level data...")
    df_min = pd.read_parquet(minute_path)
    log.info("Loaded %d rows", len(df_min))

    log.info("Loading hourly data...")
    df_hourly = pd.read_parquet(hourly_path)
    log.info("Loaded %d hourly rows", len(df_hourly))

    results = {}

    # 1. Classification
    log.info("\n--- Training Classification Models ---")
    try:
        from backend.app.ml.classifier import train_and_evaluate
        clf_results = train_and_evaluate(df_min)
        results["classification"] = clf_results
        log.info("Classification training complete.")
    except Exception as exc:
        log.error("Classification failed: %s", exc)
        results["classification"] = {"error": str(exc)}

    # 2. Forecasting
    log.info("\n--- Training Forecasting Models ---")
    try:
        from backend.app.ml.forecaster import train_and_evaluate_forecast
        fc_results = train_and_evaluate_forecast(df_hourly)
        results["forecasting"] = fc_results
        log.info("Forecasting training complete.")
    except Exception as exc:
        log.error("Forecasting failed: %s", exc)
        results["forecasting"] = {"error": str(exc)}

    # 3. Save metrics to DB
    try:
        from backend.app.services.db import init_db, get_db
        from backend.app.models.database import ModelRun
        init_db()

        with get_db() as session:
            # Classifier runs
            clf = results.get("classification", {})
            if "ml_classifier" in clf:
                run = ModelRun(
                    model_name="random_forest_classifier",
                    task="classifier",
                    metrics=clf["ml_classifier"],
                    train_rows=clf["ml_classifier"].get("train_rows"),
                    test_rows=clf["ml_classifier"].get("test_rows"),
                    trained_at=datetime.utcnow(),
                    model_path="backend/app/ml/saved_models/random_forest_classifier.joblib",
                )
                session.add(run)

            # Forecaster runs
            fc = results.get("forecasting", {})
            for mname in ["linear_regression", "ridge_regression", "random_forest"]:
                if mname in fc and "model" in fc[mname]:
                    m = fc[mname]
                    run = ModelRun(
                        model_name=mname,
                        task="forecaster",
                        metrics=m,
                        train_rows=m.get("train_rows"),
                        test_rows=m.get("test_rows"),
                        trained_at=datetime.utcnow(),
                        model_path=f"backend/app/ml/saved_models/{mname}_forecaster.joblib",
                    )
                    session.add(run)

        log.info("Metrics saved to DB.")
    except Exception as exc:
        log.warning("Could not save metrics to DB: %s", exc)

    # 4. Write evaluation report
    write_evaluation_report(results)
    log.info("Evaluation report written to docs/model_evaluation.md")


def write_evaluation_report(results: dict):
    """Write real model metrics to docs/model_evaluation.md."""
    lines = []
    lines.append("# EnergyPulse — Model Evaluation Report")
    lines.append(f"\n_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    lines.append("\n> **All metrics are computed from real UCI dataset on a chronological 80/20 train/test split. No random shuffling.**")
    lines.append("\n> **Data label: Dataset-based simulation, not physical sensor measurements.**")

    # Classification
    lines.append("\n## 1. Consumption Classification")
    clf = results.get("classification", {})
    if "error" in clf:
        lines.append(f"\n⚠ Error: {clf['error']}")
    else:
        pct = clf.get("percentile_classifier", {})
        lines.append("\n### 1a. Percentile Classifier (Primary Method)")
        lines.append(f"- Method: Tercile thresholds computed from training data")
        lines.append(f"- Low threshold: ≤ **{pct.get('low_threshold_kw', 'N/A'):.4f} kW**")
        lines.append(f"- High threshold: > **{pct.get('high_threshold_kw', 'N/A'):.4f} kW**")
        lines.append(f"- Percentiles used: p{int(pct.get('low_pct', 33))} / p{int(pct.get('high_pct', 67))}")
        lines.append(f"- No leakage: thresholds computed from training data only.")

        ml = clf.get("ml_classifier", {})
        if ml and "accuracy" in ml:
            lines.append("\n### 1b. Random Forest Classifier (Optional ML)")
            lines.append(f"\n| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Accuracy | **{ml['accuracy']:.4f}** |")
            lines.append(f"| Train rows | {ml.get('train_rows', 'N/A'):,} |")
            lines.append(f"| Test rows | {ml.get('test_rows', 'N/A'):,} |")

            cr = ml.get("classification_report", {})
            lines.append("\n**Per-class metrics (test set):**")
            lines.append("| Class | Precision | Recall | F1-Score | Support |")
            lines.append("|-------|-----------|--------|----------|---------|")
            for cls in ["low", "moderate", "high"]:
                if cls in cr:
                    m = cr[cls]
                    lines.append(f"| {cls} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1-score']:.4f} | {int(m['support'])} |")

            cm = ml.get("confusion_matrix")
            if cm:
                lines.append(f"\n**Confusion Matrix** (rows=actual, cols=predicted):")
                lines.append(f"\n| | low | moderate | high |")
                lines.append(f"|---|---|---|---|")
                for i, row in enumerate(cm):
                    lbl = ["low", "moderate", "high"][i]
                    lines.append(f"| **{lbl}** | {row[0]} | {row[1]} | {row[2] if len(row)>2 else '-'} |")

            lines.append(f"\n> **Leakage note**: {ml.get('leakage_note', '')}")

    # Forecasting
    lines.append("\n## 2. Energy Consumption Forecasting")
    fc = results.get("forecasting", {})
    if "error" in fc:
        lines.append(f"\n⚠ Error: {fc['error']}")
    else:
        lines.append("\n### Comparison: All Models vs Baselines")
        lines.append("\n| Model | MAE (kWh) | RMSE (kWh) | R² |")
        lines.append("|-------|-----------|-----------|-----|")

        for mname in ["linear_regression", "ridge_regression", "random_forest"]:
            if mname in fc and "model" in fc[mname]:
                m = fc[mname]["model"]
                b1 = fc[mname].get("baseline_naive_last_hour", {})
                b2 = fc[mname].get("baseline_same_hour_yesterday", {})
                lines.append(f"| **{mname}** | {m['MAE']:.6f} | {m['RMSE']:.6f} | {m['R2']:.4f} |")
                if b1:
                    lines.append(f"| Baseline: naive last hour | {b1['MAE']:.6f} | {b1['RMSE']:.6f} | {b1.get('R2', 'N/A')} |")
                if b2:
                    lines.append(f"| Baseline: same-hour yesterday | {b2['MAE']:.6f} | {b2['RMSE']:.6f} | {b2.get('R2', 'N/A')} |")
                lines.append("|---|---|---|---|")

                if fc[mname].get("warning"):
                    lines.append(f"\n> ⚠ **{fc[mname]['warning']}**")

        best = fc.get("best_model")
        if best:
            lines.append(f"\n**Best model by MAE: `{best}`**")

    lines.append("\n## 3. Notes")
    lines.append("""
- All splits are **chronological** — no data from the future leaks into training.
- MAE/RMSE are in **kWh per hour** (hourly forecast target).
- Anomaly detection uses rule-based methods (z-score, IQR, absolute threshold) — no separate ML evaluation needed.
- Classification labels are derived from active_power_kw percentiles on training data; ML classifier uses only lag/time features.
""")

    report_path = DOCS_DIR / "model_evaluation.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    main()
