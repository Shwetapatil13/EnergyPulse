"""
backend/app/routers/recommendations.py
----------------------------------------
Data-derived sustainability recommendations.
Each recommendation states its assumptions explicitly.
Savings estimates include editable assumptions.
"""

from __future__ import annotations
from fastapi import APIRouter
from backend.app.services.db import get_db, get_setting
from backend.app.models.database import Reading, HourlyAggregate, DailyAggregate
from sqlalchemy import func

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


@router.get("/")
def get_recommendations():
    """
    Generate data-derived sustainability recommendations.
    All recommendations state their data source and assumptions.
    Savings estimates use explicit, user-editable tariff assumptions.
    """
    tariff = float(get_setting("tariff_inr_per_kwh", "8.0"))

    recs = []

    with get_db() as session:
        # 1. Peak hour identification
        peak_rows = session.execute(
            func.text("""
                SELECT HOUR(timestamp) as hr, AVG(active_power_kw) as avg_kw
                FROM readings
                WHERE active_power_kw IS NOT NULL
                GROUP BY hr ORDER BY avg_kw DESC LIMIT 3
            """)
        ).fetchall()

        if peak_rows:
            peak_hours = [int(r[0]) for r in peak_rows]
            peak_kw = float(peak_rows[0][1]) if peak_rows[0][1] else 0
            recs.append({
                "id": "peak_hours",
                "title": "Shift Loads from Peak Hours",
                "description": (
                    f"Based on the dataset, your highest average consumption occurs "
                    f"at hours: {peak_hours} (0-23 scale). Average peak power: {peak_kw:.2f} kW."
                ),
                "assumption": (
                    f"Assumes 20% of peak-hour load can be shifted to off-peak hours. "
                    f"Tariff assumed: INR {tariff}/kWh (flat rate)."
                ),
                "estimated_daily_saving_inr": round(peak_kw * 0.20 * 3 * tariff / 60, 2),
                "data_source": "Computed from average hourly active power in readings table.",
                "confidence": "low — estimate only",
            })

        # 2. Base load / night usage
        night_rows = session.execute(
            func.text("""
                SELECT AVG(active_power_kw) as avg_kw
                FROM readings
                WHERE HOUR(timestamp) BETWEEN 0 AND 5
                AND active_power_kw IS NOT NULL
            """)
        ).fetchone()

        if night_rows and night_rows[0]:
            night_kw = float(night_rows[0])
            recs.append({
                "id": "base_load",
                "title": "Reduce Nighttime Base Load",
                "description": (
                    f"Average power consumption between 00:00–05:59 is {night_kw:.3f} kW. "
                    f"This represents standby/base load. Reducing it by switching off idle devices "
                    f"can yield consistent savings."
                ),
                "assumption": (
                    f"Assumes 30% of nighttime base load is reducible standby consumption. "
                    f"Tariff: INR {tariff}/kWh."
                ),
                "estimated_daily_saving_inr": round(night_kw * 0.30 * 6 * tariff / 60, 2),
                "data_source": "Computed from average active power in 00:00–05:59 window.",
                "confidence": "low — estimate only",
            })

        # 3. Weekend vs weekday patterns
        dow_rows = session.execute(
            func.text("""
                SELECT DAYOFWEEK(timestamp) as dow, AVG(active_power_kw) as avg_kw
                FROM readings WHERE active_power_kw IS NOT NULL
                GROUP BY dow ORDER BY dow
            """)
        ).fetchall()

        if dow_rows:
            dow_map = {int(r[0]): float(r[1] or 0) for r in dow_rows}
            weekday_avg = sum(v for k, v in dow_map.items() if k not in [1, 7]) / max(1, len([k for k in dow_map if k not in [1, 7]]))
            weekend_avg = sum(v for k, v in dow_map.items() if k in [1, 7]) / max(1, len([k for k in dow_map if k in [1, 7]]))
            diff = weekend_avg - weekday_avg
            if abs(diff) > 0.05:
                higher = "Weekends" if diff > 0 else "Weekdays"
                recs.append({
                    "id": "weekday_weekend",
                    "title": f"{higher} Have Higher Consumption",
                    "description": (
                        f"Weekday avg: {weekday_avg:.3f} kW. Weekend avg: {weekend_avg:.3f} kW. "
                        f"Difference: {abs(diff):.3f} kW. Consider scheduling high-consumption "
                        f"tasks on lower-consumption days."
                    ),
                    "assumption": "Based on historical patterns in dataset (2006–2010).",
                    "estimated_daily_saving_inr": None,
                    "data_source": "Computed from day-of-week grouping in readings table.",
                    "confidence": "informational",
                })

        # 4. Circuit zone share (sub-metering)
        sm_rows = session.execute(
            func.text("""
                SELECT AVG(sub_metering_1_wh) as sm1, AVG(sub_metering_2_wh) as sm2,
                       AVG(sub_metering_3_wh) as sm3
                FROM readings
                WHERE sub_metering_1_wh IS NOT NULL
            """)
        ).fetchone()

        if sm_rows and any(v for v in sm_rows if v):
            sm1, sm2, sm3 = [float(v or 0) for v in sm_rows]
            total_sm = sm1 + sm2 + sm3
            if total_sm > 0:
                recs.append({
                    "id": "sub_metering",
                    "title": "Circuit Zone Energy Distribution",
                    "description": (
                        f"Average circuit zone usage — "
                        f"Zone 1: {sm1:.2f} Wh ({sm1/total_sm*100:.1f}%), "
                        f"Zone 2: {sm2:.2f} Wh ({sm2/total_sm*100:.1f}%), "
                        f"Zone 3: {sm3:.2f} Wh ({sm3/total_sm*100:.1f}%). "
                        f"Focus reduction efforts on the highest-usage zone."
                    ),
                    "assumption": (
                        "Sub-metering columns are CIRCUIT-LEVEL ZONE meters, "
                        "NOT individual appliance meters. Zone-to-appliance mapping "
                        "is not available in this dataset."
                    ),
                    "estimated_daily_saving_inr": None,
                    "data_source": "Computed from Sub_metering_1/2/3 columns in UCI dataset.",
                    "confidence": "informational",
                })

    return {
        "recommendations": recs,
        "tariff_assumption_inr_per_kwh": tariff,
        "tariff_note": "Tariff is a configurable assumed value. Edit in Settings.",
        "data_label": "Dataset-based simulation, not physical sensor measurements",
        "disclaimer": (
            "All savings estimates are rough approximations based on dataset patterns. "
            "They are NOT financial advice. Verify against your actual utility bills."
        ),
    }
