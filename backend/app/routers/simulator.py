"""
backend/app/routers/simulator.py
---------------------------------
REST endpoints for Virtual IoT Simulator control.
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from backend.app.schemas.simulator import SimControlRequest, SimStatusOut
from backend.app.simulator.engine import get_simulator, SimulatorConfig

router = APIRouter(prefix="/api/simulator", tags=["Simulator"])


@router.get("/status", response_model=SimStatusOut)
async def get_status():
    """Get current simulator status."""
    sim = get_simulator()
    s = sim.get_status()
    progress = (s.current_index / s.total_rows * 100) if s.total_rows > 0 else 0
    return SimStatusOut(
        state=s.state.value,
        current_timestamp=s.current_timestamp,
        current_index=s.current_index,
        total_rows=s.total_rows,
        speed=s.speed,
        loop=s.loop,
        ticks_emitted=s.ticks_emitted,
        start_time=s.start_time,
        progress_pct=round(progress, 2),
    )


@router.post("/control")
async def control(req: SimControlRequest):
    """
    Control the simulator.
    
    Actions:
    - **start**: Start or restart (optionally with start_date, speed, loop)
    - **pause**: Pause at current position
    - **resume**: Resume from paused state
    - **stop**: Stop and reset position
    - **seek**: Seek to a specific date (ISO format)
    - **set_speed**: Change speed multiplier (0.1–3600)
    """
    sim = get_simulator()
    action = req.action.lower()

    if action == "start":
        config = SimulatorConfig(
            start_date=req.start_date,
            speed=req.speed or sim._config.speed,
            loop=req.loop if req.loop is not None else sim._config.loop,
        )
        await sim.start(config)
        return {"status": "started", "speed": config.speed}

    elif action == "pause":
        await sim.pause()
        return {"status": "paused"}

    elif action == "resume":
        await sim.resume()
        return {"status": "resumed"}

    elif action == "stop":
        await sim.stop()
        return {"status": "stopped"}

    elif action == "seek":
        if not req.start_date:
            raise HTTPException(400, "start_date required for seek action")
        await sim.seek(req.start_date)
        return {"status": "seeked", "target": req.start_date}

    elif action == "set_speed":
        if req.speed is None:
            raise HTTPException(400, "speed required for set_speed action")
        sim.set_speed(req.speed)
        return {"status": "speed_changed", "speed": req.speed}

    else:
        raise HTTPException(400, f"Unknown action: {action}. Use start|pause|resume|stop|seek|set_speed")
