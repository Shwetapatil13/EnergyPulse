# EnergyPulse — Dataset Inspection Report

_Generated: 2026-10-19 10:40:52_

> **Data label**: Dataset-based simulation, not physical sensor measurements.

## 1. File Information
| Field | Value |
|-------|-------|
| File name | `household_power_consumption.txt` |
| File size | 132.96 MB |
| Delimiter | `';'` |
| Row count | 2,075,259 |
| Column count | 9 |

## 2. Columns and Data Types
| Column | Dtype | Unit (UCI docs) | Notes |
|--------|-------|-----------------|-------|
| `Date` | `str` | date (DD/MM/YYYY) |  |
| `Time` | `str` | time (HH:MM:SS) |  |
| `Global_active_power` | `float64` | kilowatt (kW) |  |
| `Global_reactive_power` | `float64` | kilowatt (kW) |  |
| `Voltage` | `float64` | volt (V) |  |
| `Global_intensity` | `float64` | ampere (A) |  |
| `Sub_metering_1` | `float64` | watt-hour (Wh) — circuit zone 1 | ⚠ Circuit/zone meter, NOT individual appliance |
| `Sub_metering_2` | `float64` | watt-hour (Wh) — circuit zone 2 | ⚠ Circuit/zone meter, NOT individual appliance |
| `Sub_metering_3` | `float64` | watt-hour (Wh) — circuit zone 3 | ⚠ Circuit/zone meter, NOT individual appliance |

## 3. Date Range and Sampling Interval
| Field | Value |
|-------|-------|
| Start | `2006-12-16 17:24:00` |
| End | `2010-11-26 21:02:00` |
| Sampling interval | `1 minutes` |
| Timedelta mode | `0 days 00:01:00` |

## 4. Missing Values
Missing values in this dataset are encoded as `?` (question mark).

| Column | Missing Count | Missing % |
|--------|--------------|-----------|
| `Date` | 0 | 0.000% |
| `Time` | 0 | 0.000% |
| `Global_active_power` | 25,979 | 1.252% |
| `Global_reactive_power` | 25,979 | 1.252% |
| `Voltage` | 25,979 | 1.252% |
| `Global_intensity` | 25,979 | 1.252% |
| `Sub_metering_1` | 25,979 | 1.252% |
| `Sub_metering_2` | 25,979 | 1.252% |
| `Sub_metering_3` | 25,979 | 1.252% |

## 5. Descriptive Statistics (Numeric Columns)
| Statistic | Global_active_power | Global_reactive_power | Voltage | Global_intensity | Sub_metering_1 | Sub_metering_2 | Sub_metering_3 |
|-----------|------|------|------|------|------|------|------|
| count | 2049280.0000 | 2049280.0000 | 2049280.0000 | 2049280.0000 | 2049280.0000 | 2049280.0000 | 2049280.0000 |
| mean | 1.0916 | 0.1237 | 240.8399 | 4.6278 | 1.1219 | 1.2985 | 6.4584 |
| std | 1.0573 | 0.1127 | 3.2400 | 4.4444 | 6.1530 | 5.8220 | 8.4372 |
| min | 0.0760 | 0.0000 | 223.2000 | 0.2000 | 0.0000 | 0.0000 | 0.0000 |
| 25% | 0.3080 | 0.0480 | 238.9900 | 1.4000 | 0.0000 | 0.0000 | 0.0000 |
| 50% | 0.6020 | 0.1000 | 241.0100 | 2.6000 | 0.0000 | 0.0000 | 1.0000 |
| 75% | 1.5280 | 0.1940 | 242.8900 | 6.4000 | 0.0000 | 1.0000 | 17.0000 |
| max | 11.1220 | 1.3900 | 254.1500 | 48.4000 | 88.0000 | 80.0000 | 31.0000 |

## 6. Column-to-Metric Mapping

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


## 7. Key Findings & Assumptions

- **Missing value encoding**: `?` (question mark) in the raw CSV; parsed as `NaN`.
- **Sub-metering columns**: These are **circuit-level zone meters** (e.g., kitchen circuit, laundry circuit, HVAC circuit), **not individual appliance meters**. They are labeled accordingly throughout the project.
- **Units confirmed**: Active power = kW, Voltage = V, Intensity = A, Sub-metering = Wh. These match UCI documentation.
- **Sampling interval**: 1 minute (verified from timestamp differences).
- **Date format**: DD/MM/YYYY (day-first). `dayfirst=True` is used in parsing.
- **Cost calculation assumption**: Flat tariff of INR 8.00/kWh (default, user-configurable). This is an assumed value modeled on MSEDCL residential tariffs and **must be verified against actual tariff schedules** for real use.
