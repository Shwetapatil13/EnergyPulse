"""
backend/app/services/ws_manager.py
-----------------------------------
WebSocket connection manager for live data broadcasting.
"""

from __future__ import annotations
import asyncio
import json
import logging
from typing import Set
from fastapi import WebSocket

log = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        log.info("WS client connected. Total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        log.info("WS client disconnected. Total: %d", len(self.active_connections))

    async def broadcast(self, data: dict):
        """Broadcast JSON data to all connected clients."""
        if not self.active_connections:
            return
        message = json.dumps(data, default=str)
        dead = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active_connections.discard(ws)

    async def send_personal(self, websocket: WebSocket, data: dict):
        message = json.dumps(data, default=str)
        await websocket.send_text(message)


# Global singleton
_manager: ConnectionManager = ConnectionManager()


def get_ws_manager() -> ConnectionManager:
    return _manager
