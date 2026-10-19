"""
scripts/run_preprocessing.py
------------------------------
Run the full preprocessing pipeline.
Outputs: data/processed/readings_1min.parquet + hourly/daily aggregates.

Usage:
    python scripts/run_preprocessing.py
"""

import sys
import pathlib
import logging

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


def main():
    from backend.app.preprocessing.cleaner import run_pipeline
    from backend.app.config import get_settings

    settings = get_settings()
    tariff = settings.default_tariff_inr_per_kwh

    print("Running preprocessing pipeline...")
    df_min, df_hr, df_day, stats = run_pipeline(tariff_inr=tariff)

    print(f"\nPreprocessing complete!")
    print(f"  Minute rows: {stats['total_rows']:,}")
    print(f"  Date range: {stats['date_range'][0]} -> {stats['date_range'][1]}")
    print(f"  Hourly rows: {len(df_hr):,}")
    print(f"  Daily rows: {len(df_day):,}")
    print(f"  Gap rows flagged: {stats['missing_value_stats'].get('_flagged_long_gap', 0):,}")

    print("\nOutput files:")
    for k, v in stats["output_paths"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
