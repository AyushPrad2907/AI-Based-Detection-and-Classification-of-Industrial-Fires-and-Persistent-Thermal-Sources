"""
SIH26162 — Real-Time Alert Broadcast & Streaming Service.

Provides a Server-Sent Events (SSE) pub/sub broadcast mechanism and in-memory
alert buffer for near real-time distribution of high-risk thermal anomalies.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class AlertStreamService:
    """
    Manages active SSE client queues and in-memory alert ring buffer.
    Thread-safe and asyncio-native.
    """

    def __init__(self, max_history: int = 50):
        self._subscribers: Set[asyncio.Queue] = set()
        self._max_history = max_history
        self._recent_alerts: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    async def subscribe(self) -> asyncio.Queue:
        """Register a new SSE client queue."""
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(q)
        logger.info("SSE Client subscribed. Active listeners: %d", len(self._subscribers))
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        """Remove a disconnected SSE client queue."""
        async with self._lock:
            self._subscribers.discard(q)
        logger.info("SSE Client unsubscribed. Remaining listeners: %d", len(self._subscribers))

    async def broadcast(self, alert_data: Dict[str, Any]) -> None:
        """
        Broadcast an alert payload to all connected SSE clients
        and store it in the recent alerts buffer.
        """
        if "timestamp" not in alert_data:
            alert_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        async with self._lock:
            # Maintain ring buffer
            self._recent_alerts.insert(0, alert_data)
            if len(self._recent_alerts) > self._max_history:
                self._recent_alerts.pop()

            dead_queues = []
            for q in list(self._subscribers):
                try:
                    q.put_nowait(alert_data)
                except asyncio.QueueFull:
                    # Drop slow clients or clean them up
                    dead_queues.append(q)

            for dead_q in dead_queues:
                self._subscribers.discard(dead_q)

        logger.info(
            "Broadcasted alert '%s' [Risk %s] to %d clients",
            alert_data.get("alert_id", "unknown"),
            alert_data.get("risk_level", "UNKNOWN"),
            len(self._subscribers),
        )

    async def get_recent_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent alerts buffer."""
        async with self._lock:
            return list(self._recent_alerts[:limit])

    async def event_generator(self, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
        """
        Yields standard SSE formatted chunks:
        event: <type>
        data: <json>
        """
        # Send initial connected greeting
        init_payload = json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to SIH26162 Real-Time Alert Radar Stream",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        yield f"event: ping\ndata: {init_payload}\n\n"

        try:
            while True:
                try:
                    # Wait for next alert with a 15-second heartbeat ping
                    alert = await asyncio.wait_for(queue.get(), timeout=15.0)
                    payload = json.dumps(alert)
                    yield f"event: thermal_alert\ndata: payload\n\n".replace("payload", payload)
                except asyncio.TimeoutError:
                    # Send keep-alive comment to prevent socket termination
                    heartbeat = json.dumps({
                        "type": "HEARTBEAT",
                        "active_listeners": len(self._subscribers),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    yield f"event: heartbeat\ndata: {heartbeat}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await self.unsubscribe(queue)


# Global singleton instance
alert_stream_service = AlertStreamService()
