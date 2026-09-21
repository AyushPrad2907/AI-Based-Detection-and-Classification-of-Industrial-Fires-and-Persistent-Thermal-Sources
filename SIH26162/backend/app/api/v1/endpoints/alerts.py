"""
SIH26162 — Real-Time Alert & Poller Endpoints.

Provides Server-Sent Events (SSE) streaming, recent alert history,
and controls for the background satellite ingestion poller.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.alert_stream import alert_stream_service
from app.services.poller_service import poller_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SimulateAlertRequest(BaseModel):
    zone_name: Optional[str] = Field(None, description="Optional target industrial zone or facility name")
    acute_fire: bool = Field(True, description="True for acute industrial fire, False for persistent flare")


class CustomAlertPayload(BaseModel):
    predicted_class: str = Field("industrial_fire", description="Thermal anomaly class")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    frp_mw: float = Field(..., description="Fire Radiative Power (MW)")
    risk_score: float = Field(90.0, description="Calculated risk score")
    risk_level: str = Field("CRITICAL", description="Risk level (LOW, MODERATE, HIGH, CRITICAL)")
    nearest_facility: Optional[str] = Field(None, description="Nearest industrial facility")
    facility_distance_km: Optional[float] = Field(None, description="Distance to facility in km")
    summary: Optional[str] = Field(None, description="Alert description text")


@router.get("/stream", summary="Live Server-Sent Events (SSE) Thermal Alert Stream")
async def stream_thermal_alerts(request: Request):
    """
    Subscribes to live Server-Sent Events (SSE) stream.
    Pushes high-risk thermal anomalies, acute industrial fire detections,
    and periodic keep-alive heartbeats to connected clients.
    """
    queue = await alert_stream_service.subscribe()

    async def client_event_generator():
        try:
            async for chunk in alert_stream_service.event_generator(queue):
                # Check for client disconnect
                if await request.is_disconnected():
                    break
                yield chunk
        finally:
            await alert_stream_service.unsubscribe(queue)

    return StreamingResponse(
        client_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/recent", summary="Get recent alerts buffer", response_model=List[Dict[str, Any]])
async def get_recent_alerts(limit: int = Query(20, ge=1, le=100)):
    """Retrieve the most recent thermal alerts stored in memory."""
    return await alert_stream_service.get_recent_alerts(limit=limit)


@router.post("/simulate", summary="Trigger instant satellite pass simulation for demo")
async def trigger_instant_simulation(payload: Optional[SimulateAlertRequest] = None):
    """
    Immediately simulates an acute satellite pass over a major industrial zone
    and broadcasts a CRITICAL/HIGH risk alert down the live SSE stream.
    Ideal for evaluators and demonstrations.
    """
    zone = payload.zone_name if payload else None
    acute = payload.acute_fire if payload else True
    alert = await poller_service.trigger_instant_simulation(zone_name=zone, acute_fire=acute)
    return {
        "status": "success",
        "message": "Instant satellite pass triggered and alert broadcasted.",
        "alert": alert,
    }


@router.get("/poller/status", summary="Get background satellite poller status")
async def get_poller_status():
    """Returns whether the background poller is running, interval, and stats."""
    return poller_service.status


@router.post("/poller/start", summary="Start background satellite poller worker")
async def start_poller(interval_seconds: int = Query(20, ge=5, le=3600)):
    """Starts the background satellite ingestion poller loop."""
    poller_service.start(interval_seconds=interval_seconds)
    return {
        "status": "started",
        "message": f"Poller service running with {interval_seconds}s tick interval.",
        "poller": poller_service.status,
    }


@router.post("/poller/stop", summary="Stop background satellite poller worker")
async def stop_poller():
    """Stops the background satellite ingestion poller loop."""
    poller_service.stop()
    return {
        "status": "stopped",
        "message": "Poller service stopped.",
        "poller": poller_service.status,
    }


@router.post("/broadcast", summary="Broadcast manual custom alert")
async def broadcast_manual_alert(alert: CustomAlertPayload):
    """Manually broadcast a customized alert to all active SSE subscribers."""
    import uuid
    from datetime import datetime, timezone

    data = alert.model_dump()
    data["alert_id"] = f"MAN-{uuid.uuid4().hex[:8].upper()}"
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    if not data.get("summary"):
        data["summary"] = f"Manual Alert: {data['predicted_class']} ({data['frp_mw']} MW)"

    await alert_stream_service.broadcast(data)
    return {
        "status": "broadcasted",
        "alert": data,
        "subscribers": alert_stream_service.subscriber_count,
    }
