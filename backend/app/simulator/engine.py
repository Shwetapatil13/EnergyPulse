"""
backend/app/simulator/engine.py
--------------------------------
Virtual IoT Simulator: Replay engine for the UCI household power dataset.

Reads processed 1-minute readings in timestamp order and emits one reading
per tick at a configurable interval. Each emitted reading goes through the
ingestion pipeline: validate → calc kWh/cost → anomaly check → classify →
DB insert → WebSocket broadcast.

Label: "Dataset-based simulation, not physical sensor measurements"

Configuration:
  - start_date : First timestamp to replay (default: dataset start)
  - speed      : Multiplier (1 = 1 reading/sec, 60 = 60 readings/sec)
  - loop       : Whether to loop back to start when data ends
  - interval   : Tick interval in seconds (= 1/speed)
"""

from __future__ import annotations

import asyncio
import logging
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional

import pandas as pd

log = logging.getLogger(__name__)

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class SimulatorState(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class SimulatorConfig:
    start_date: Optional[str] = None        # ISO date string; None = dataset start
    speed: float = 1.0                       # Readings per second
    loop: bool = True                        # Loop back to start when finished
    interval_seconds: float = 1.0           # Overrides 1/speed if set explicitly


@dataclass
class SimulatorStatus:
    state: SimulatorState = SimulatorState.STOPPED
    current_timestamp: Optional[str] = None
    current_index: int = 0
    total_rows: int = 0
    speed: float = 1.0
    loop: bool = True
    ticks_emitted: int = 0
    start_time: Optional[str] = None
    data_source: str = "Dataset-based simulation, not physical sensor measurements"


class SimulatorEngine:
    """
    Replay engine that reads processed parquet data and emits timed readings.

    The engine runs as an asyncio task. Each tick:
      1. Reads next row from the DataFrame
      2. Passes to registered on_reading callback (the ingestion pipeline)
      3. Sleeps for (1.0 / speed) seconds
    """

    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._config = SimulatorConfig()
        self._state = SimulatorState.STOPPED
        self._current_index: int = 0
        self._ticks_emitted: int = 0
        self._task: Optional[asyncio.Task] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially
        self._on_reading: Optional[Callable] = None  # async callback
        self._start_wall_time: Optional[datetime] = None

    # ── Data loading ──────────────────────────────────────────────────────

    def load_data(self, path: Optional[pathlib.Path] = None) -> int:
        """Load processed parquet into memory. Returns row count."""
        if path is None:
            path = PROCESSED_DIR / "readings_1min.parquet"
        if not path.exists():
            raise FileNotFoundError(
                f"Processed data not found: {path}. "
                "Run preprocessing first: python -m backend.app.preprocessing.cleaner"
            )
        log.info("Loading simulator data from %s …", path)
        self._df = pd.read_parquet(path, engine="pyarrow")
        # Ensure sorted by timestamp
        if not self._df.index.is_monotonic_increasing:
            self._df = self._df.sort_index()
        log.info("Simulator data loaded: %d rows (%s → %s)",
                 len(self._df),
                 self._df.index.min(),
                 self._df.index.max())
        return len(self._df)

    # ── Callback registration ─────────────────────────────────────────────

    def register_callback(self, callback: Callable):
        """Register async callback that receives each emitted reading dict."""
        self._on_reading = callback

    # ── Control API ───────────────────────────────────────────────────────

    async def start(self, config: Optional[SimulatorConfig] = None):
        """Start or restart the simulator."""
        if self._df is None:
            self.load_data()

        if config:
            self._config = config

        # Seek to start_date if specified
        if self._config.start_date:
            self._seek_to_date(self._config.start_date)
        else:
            self._current_index = 0

        # Cancel existing task
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._state = SimulatorState.RUNNING
        self._ticks_emitted = 0
        self._start_wall_time = datetime.utcnow()
        self._pause_event.set()

        self._task = asyncio.create_task(self._run_loop())
        log.info(
            "Simulator STARTED: speed=%.1fx, start_index=%d, loop=%s",
            self._config.speed, self._current_index, self._config.loop,
        )

    async def pause(self):
        """Pause the simulator (keeps position)."""
        if self._state == SimulatorState.RUNNING:
            self._state = SimulatorState.PAUSED
            self._pause_event.clear()
            log.info("Simulator PAUSED at index %d", self._current_index)

    async def resume(self):
        """Resume from paused state."""
        if self._state == SimulatorState.PAUSED:
            self._state = SimulatorState.RUNNING
            self._pause_event.set()
            log.info("Simulator RESUMED from index %d", self._current_index)

    async def stop(self):
        """Stop the simulator."""
        self._state = SimulatorState.STOPPED
        self._pause_event.set()  # Unblock if paused
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._current_index = 0
        self._ticks_emitted = 0
        log.info("Simulator STOPPED")

    async def seek(self, target_date: str):
        """Seek to a specific date in the data."""
        was_running = self._state == SimulatorState.RUNNING
        await self.pause()
        self._seek_to_date(target_date)
        if was_running:
            await self.resume()
        log.info("Simulator SEEKED to %s (index=%d)", target_date, self._current_index)

    def set_speed(self, speed: float):
        """Change playback speed (takes effect on next tick)."""
        self._config.speed = max(0.1, min(speed, 3600.0))  # Clamp to reasonable range
        log.info("Simulator speed changed to %.1fx", self._config.speed)

    # ── Internal ──────────────────────────────────────────────────────────

    def _seek_to_date(self, date_str: str):
        """Find the index closest to the given date string."""
        if self._df is None:
            return
        try:
            target = pd.Timestamp(date_str)
            # Find closest index
            idx = self._df.index.searchsorted(target)
            self._current_index = int(min(idx, len(self._df) - 1))
        except Exception as exc:
            log.warning("Failed to seek to %s: %s — staying at current position", date_str, exc)

    async def _run_loop(self):
        """Main simulator loop."""
        if self._df is None:
            log.error("No data loaded.")
            return

        n = len(self._df)
        log.info("Simulator loop starting at index %d of %d", self._current_index, n)

        try:
            while True:
                # Wait if paused
                await self._pause_event.wait()

                if self._state == SimulatorState.STOPPED:
                    break

                if self._current_index >= n:
                    if self._config.loop:
                        log.info("Simulator looping back to start.")
                        self._current_index = 0
                    else:
                        log.info("Simulator reached end of data. Stopping.")
                        self._state = SimulatorState.STOPPED
                        break

                # Get current row
                row = self._df.iloc[self._current_index]
                ts = self._df.index[self._current_index]
                reading = self._row_to_dict(row, ts)

                # Emit via callback
                if self._on_reading:
                    try:
                        await self._on_reading(reading)
                    except Exception as exc:
                        log.error("Error in reading callback: %s", exc)

                self._current_index += 1
                self._ticks_emitted += 1

                # Sleep based on speed
                sleep_sec = 1.0 / max(self._config.speed, 0.01)
                await asyncio.sleep(sleep_sec)

        except asyncio.CancelledError:
            log.info("Simulator loop cancelled.")
            raise

    def _row_to_dict(self, row: pd.Series, ts: pd.Timestamp) -> dict:
        """Convert a DataFrame row to a reading dict for the ingestion pipeline."""
        def safe(val):
            if pd.isna(val):
                return None
            return float(val)

        return {
            "timestamp": ts.isoformat(),
            "active_power_kw": safe(row.get("active_power_kw") or row.get("Global_active_power")),
            "reactive_power_kw": safe(row.get("Global_reactive_power")),
            "voltage_v": safe(row.get("Voltage")),
            "current_a": safe(row.get("Global_intensity")),
            "sub_metering_1_wh": safe(row.get("Sub_metering_1")),
            "sub_metering_2_wh": safe(row.get("Sub_metering_2")),
            "sub_metering_3_wh": safe(row.get("Sub_metering_3")),
            "energy_kwh": safe(row.get("energy_kwh")),
            "is_simulated": True,
            "is_gap": bool(row.get("is_gap", False)),
            "data_source": "Dataset-based simulation, not physical sensor measurements",
        }

    # ── Status ────────────────────────────────────────────────────────────

    def get_status(self) -> SimulatorStatus:
        n = len(self._df) if self._df is not None else 0
        current_ts = None
        if self._df is not None and 0 <= self._current_index < n:
            current_ts = self._df.index[self._current_index].isoformat()
        return SimulatorStatus(
            state=self._state,
            current_timestamp=current_ts,
            current_index=self._current_index,
            total_rows=n,
            speed=self._config.speed,
            loop=self._config.loop,
            ticks_emitted=self._ticks_emitted,
            start_time=self._start_wall_time.isoformat() if self._start_wall_time else None,
        )


# Global singleton
_engine: Optional[SimulatorEngine] = None


def get_simulator() -> SimulatorEngine:
    global _engine
    if _engine is None:
        _engine = SimulatorEngine()
    return _engine
