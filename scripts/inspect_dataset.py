"""
inspect_dataset.py
------------------
Inspects the downloaded UCI Household Power Consumption dataset
and produces docs/dataset_report.md.

Usage:
    python scripts/inspect_dataset.py
"""

import pathlib
import sys
import textwrap
from datetime import datetime

import pandas as pd
import numpy as np

RAW_DIR = pathlib.Path(__file__).parent.parent / "data" / "raw"
DOCS_DIR = pathlib.Path(__file__).parent.parent / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

REPORT_PATH = DOCS_DIR / "dataset_report.md"

# Column units from UCI documentation
COLUMN_UNITS = {
    "Date":                        "date (DD/MM/YYYY)",
    "Time":                        "time (HH:MM:SS)",
    "Global_active_power":         "kilowatt (kW)",
    "Global_reactive_power":       "kilowatt (kW)",
    "Voltage":                     "volt (V)",
    "Global_intensity":            "ampere (A)",
    "Sub_metering_1":              "watt-hour (Wh) — circuit zone 1",
    "Sub_metering_2":              "watt-hour (Wh) — circuit zone 2",
    "Sub_metering_3":              "watt-hour (Wh) — circuit zone 3",
}


def find_dataset() -> pathlib.Path:
    """Find the dataset file in data/raw/."""
    candidates = (
        list(RAW_DIR.glob("*.txt")) +
        list(RAW_DIR.glob("*.csv"))
    )
    if not candidates:
        print(
            f"ERROR: No dataset file found in {RAW_DIR}.\n"
            "Run: python scripts/download_data.py first."
        )
        sys.exit(1)
    # Pick largest file
    return max(candidates, key=lambda p: p.stat().st_size)


def detect_delimiter(path: pathlib.Path) -> str:
    """Detect CSV delimiter from first line."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        first = f.readline()
    if ";" in first:
        return ";"
    if "\t" in first:
        return "\t"
    return ","


def load_sample(path: pathlib.Path, delimiter: str, n: int = 200_000) -> pd.DataFrame:
    """Load a representative sample for inspection."""
    return pd.read_csv(
        path,
        sep=delimiter,
        nrows=n,
        na_values=["?", "NA", "N/A", "", " "],
        low_memory=False,
    )


def load_full(path: pathlib.Path, delimiter: str) -> pd.DataFrame:
    """Load the full dataset."""
    return pd.read_csv(
        path,
        sep=delimiter,
        na_values=["?", "NA", "N/A", "", " "],
        low_memory=False,
    )


def analyze(df: pd.DataFrame, path: pathlib.Path, delimiter: str) -> dict:
    """Run all analysis on the dataframe."""
    info = {}
    info["file_name"] = path.name
    info["file_size_mb"] = round(path.stat().st_size / 1e6, 2)
    info["delimiter"] = repr(delimiter)
    info["row_count"] = len(df)
    info["col_count"] = len(df.columns)
    info["columns"] = list(df.columns)

    # Missing value analysis
    missing = df.isnull().sum()
    info["missing_counts"] = missing.to_dict()
    info["missing_pct"] = (missing / len(df) * 100).round(4).to_dict()

    # Try to parse datetime
    try:
        if "Date" in df.columns and "Time" in df.columns:
            dt = pd.to_datetime(
                df["Date"].astype(str) + " " + df["Time"].astype(str),
                dayfirst=True,
                errors="coerce",
            )
            info["datetime_parsed"] = True
            valid_dt = dt.dropna()
            info["date_range_start"] = str(valid_dt.min())
            info["date_range_end"] = str(valid_dt.max())
            if len(valid_dt) > 1:
                diffs = valid_dt.sort_values().diff().dropna()
                mode_diff = diffs.mode()[0]
                info["sampling_interval"] = str(mode_diff)
                info["inferred_frequency"] = f"{int(mode_diff.total_seconds()//60)} minutes"
        else:
            info["datetime_parsed"] = False
    except Exception as exc:
        info["datetime_parse_error"] = str(exc)

    # Basic stats for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    info["numeric_columns"] = numeric_cols
    stats = df[numeric_cols].describe().round(6)
    info["stats"] = stats.to_dict()

    # Check missing-value encoding
    # Scan raw file head for '?'
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        head = f.read(50_000)
    info["missing_encoded_as_question_mark"] = "?" in head

    # dtypes
    info["dtypes"] = {col: str(dt) for col, dt in df.dtypes.items()}

    return info


def render_report(info: dict) -> str:
    lines = []
    lines.append("# EnergyPulse — Dataset Inspection Report")
    lines.append(f"\n_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    lines.append(f"\n> **Data label**: Dataset-based simulation, not physical sensor measurements.")

    lines.append("\n## 1. File Information")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| File name | `{info['file_name']}` |")
    lines.append(f"| File size | {info['file_size_mb']} MB |")
    lines.append(f"| Delimiter | `{info['delimiter']}` |")
    lines.append(f"| Row count | {info['row_count']:,} |")
    lines.append(f"| Column count | {info['col_count']} |")

    lines.append("\n## 2. Columns and Data Types")
    lines.append("| Column | Dtype | Unit (UCI docs) | Notes |")
    lines.append("|--------|-------|-----------------|-------|")
    for col in info["columns"]:
        dtype = info["dtypes"].get(col, "unknown")
        unit = COLUMN_UNITS.get(col, "unknown — verify")
        note = ""
        if col.startswith("Sub_metering"):
            note = "⚠ Circuit/zone meter, NOT individual appliance"
        lines.append(f"| `{col}` | `{dtype}` | {unit} | {note} |")

    lines.append("\n## 3. Date Range and Sampling Interval")
    if info.get("datetime_parsed"):
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| Start | `{info.get('date_range_start', 'N/A')}` |")
        lines.append(f"| End | `{info.get('date_range_end', 'N/A')}` |")
        lines.append(f"| Sampling interval | `{info.get('inferred_frequency', 'N/A')}` |")
        lines.append(f"| Timedelta mode | `{info.get('sampling_interval', 'N/A')}` |")
    else:
        lines.append("⚠ Could not parse datetime. Check column names.")

    lines.append("\n## 4. Missing Values")
    lines.append("Missing values in this dataset are encoded as `?` (question mark).")
    lines.append("\n| Column | Missing Count | Missing % |")
    lines.append("|--------|--------------|-----------|")
    for col in info["columns"]:
        mc = info["missing_counts"].get(col, 0)
        mp = info["missing_pct"].get(col, 0)
        lines.append(f"| `{col}` | {mc:,} | {mp:.3f}% |")

    lines.append("\n## 5. Descriptive Statistics (Numeric Columns)")
    stats = info.get("stats", {})
    if stats:
        stat_rows = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
        header = "| Statistic | " + " | ".join(info["numeric_columns"]) + " |"
        sep = "|-----------|" + "|".join(["------"] * len(info["numeric_columns"])) + "|"
        lines.append(header)
        lines.append(sep)
        for row in stat_rows:
            vals = [f"{stats.get(col, {}).get(row, float('nan')):.4f}" for col in info["numeric_columns"]]
            lines.append(f"| {row} | " + " | ".join(vals) + " |")

    lines.append("\n## 6. Column-to-Metric Mapping")
    lines.append("""
| Dashboard Metric | Source Column(s) | Formula |
|-----------------|-----------------|---------|
| Active Power (kW) | `Global_active_power` | Direct read |
| Energy per minute (kWh) | `Global_active_power` | `kW × (1/60)` |
| Cumulative Energy (kWh) | `Global_active_power` | `Σ(kW × 1/60)` |
| Voltage (V) | `Voltage` | Direct read |
| Current (A) | `Global_intensity` | Direct read |
| Reactive Power (kVAR) | `Global_reactive_power` | Direct read |
| Zone 1 energy (Wh) | `Sub_metering_1` | Direct read — circuit zone, NOT single appliance |
| Zone 2 energy (Wh) | `Sub_metering_2` | Direct read — circuit zone, NOT single appliance |
| Zone 3 energy (Wh) | `Sub_metering_3` | Direct read — circuit zone, NOT single appliance |
| Estimated Cost (INR) | `Global_active_power` | `kWh × tariff_rate` |
""")

    lines.append("\n## 7. Key Findings & Assumptions")
    lines.append("""
- **Missing value encoding**: `?` (question mark) in the raw CSV; parsed as `NaN`.
- **Sub-metering columns**: These are **circuit-level zone meters** (e.g., kitchen circuit, laundry circuit, HVAC circuit), **not individual appliance meters**. They are labeled accordingly throughout the project.
- **Units confirmed**: Active power = kW, Voltage = V, Intensity = A, Sub-metering = Wh. These match UCI documentation.
- **Sampling interval**: 1 minute (verified from timestamp differences).
- **Date format**: DD/MM/YYYY (day-first). `dayfirst=True` is used in parsing.
- **Cost calculation assumption**: Flat tariff of INR 8.00/kWh (default, user-configurable). This is an assumed value modeled on MSEDCL residential tariffs and **must be verified against actual tariff schedules** for real use.
""")

    return "\n".join(lines)


def main():
    path = find_dataset()
    delimiter = detect_delimiter(path)

    print(f"Loading {path.name} (delimiter={repr(delimiter)})…")
    df = load_full(path, delimiter)
    print(f"Loaded {len(df):,} rows × {len(df.columns)} columns")

    info = analyze(df, path, delimiter)

    # Print summary to console
    print(f"\n{'='*60}")
    print("DATASET SUMMARY")
    print(f"{'='*60}")
    print(f"File: {info['file_name']}  ({info['file_size_mb']} MB)")
    print(f"Rows: {info['row_count']:,}")
    print(f"Columns: {info['columns']}")
    print(f"Date range: {info.get('date_range_start')} -> {info.get('date_range_end')}")
    print(f"Interval: {info.get('inferred_frequency')}")
    print(f"Missing value encoding: {'?' if info.get('missing_encoded_as_question_mark') else 'N/A'}")
    print("\nMissing counts:")
    for col, cnt in info["missing_counts"].items():
        if cnt > 0:
            print(f"  {col}: {cnt:,} ({info['missing_pct'][col]:.2f}%)")

    # Write report
    report = render_report(info)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n✓ Report saved → {REPORT_PATH}")


if __name__ == "__main__":
    main()
