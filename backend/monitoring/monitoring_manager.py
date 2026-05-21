# backend/monitoring/monitoring_manager.py
import asyncio
import logging
from fastapi import WebSocket
from typing import Dict, List

logger = logging.getLogger(__name__)

class MonitoringManager:
    def __init__(self):
        self.is_running = False
        self._task = None
        # app_id -> list of connected websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, app_id: int, websocket: WebSocket):
        await websocket.accept()
        if app_id not in self.active_connections:
            self.active_connections[app_id] = []
        self.active_connections[app_id].append(websocket)
        logger.info(f"WebSocket connected for app_id {app_id}")

    def disconnect(self, app_id: int, websocket: WebSocket):
        if app_id in self.active_connections:
            if websocket in self.active_connections[app_id]:
                self.active_connections[app_id].remove(websocket)
            if not self.active_connections[app_id]:
                del self.active_connections[app_id]
        logger.info(f"WebSocket disconnected for app_id {app_id}")

    async def broadcast_alert(self, app_id: int, alert: dict):
        if app_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[app_id]:
                try:
                    await connection.send_json(alert)
                except Exception as e:
                    logger.error(f"Error sending to websocket: {e}")
                    dead_connections.append(connection)
            for dc in dead_connections:
                self.disconnect(app_id, dc)

    async def start_background_task(self):
        """
        Start the background monitoring task.
        """
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting AlgoShield background monitoring loop...")
        self._task = asyncio.create_task(self._monitoring_loop())

    async def stop_background_task(self):
        """
        Stop the background monitoring task.
        """
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("AlgoShield background monitoring loop stopped.")

    async def _monitoring_loop(self):
        from monitoring.monitor_service import run_monitoring_cycle
        while self.is_running:
            try:
                await run_monitoring_cycle()
            except Exception as e:
                logger.error(f"Error in monitoring loop iteration: {e}")
            await asyncio.sleep(30)  # Wait 30 seconds before next cycle

manager = MonitoringManager()
