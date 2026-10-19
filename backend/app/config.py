"""
backend/app/config.py
----------------------
Centralised configuration via pydantic-settings.
Reads from .env file (or environment variables).
"""

from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "energypulse"
    db_user: str = "energyuser"
    db_password: str = "energypass123"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "INFO"

    # Frontend
    vite_api_base_url: str = "http://localhost:8000"
    vite_ws_url: str = "ws://localhost:8000/ws/live"

    # Simulator
    sim_default_speed: float = 1.0
    sim_default_start_date: str = "2006-12-16"
    sim_loop: bool = True

    # Tariff
    default_tariff_inr_per_kwh: float = 8.0

    # Anomaly detection
    anomaly_window: int = 60
    anomaly_z_threshold: float = 3.0
    anomaly_iqr_multiplier: float = 1.5
    anomaly_abs_threshold_kw: float = 5.0

    # Classification thresholds
    class_low_threshold: float = 0.33
    class_high_threshold: float = 0.67


@lru_cache()
def get_settings() -> Settings:
    return Settings()
