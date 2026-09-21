"""
SIH26162 — Background Satellite Poller & Ingestion Simulator Service.

Continuously monitors NASA FIRMS data stream or executes simulated satellite
passes over key Indian industrial zones, feeding observations into the ML
inference engine and alerting queue.
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.alert_stream import alert_stream_service

logger = logging.getLogger(__name__)

# Key Indian Industrial Hubs for realistic thermal simulation
INDIAN_INDUSTRIAL_ZONES = [
    {
        "zone": "Jamnagar Refining Hub, Gujarat",
        "latitude": 22.4707,
        "longitude": 70.0577,
        "facility_name": "Reliance Jamnagar Refinery Complex",
        "facility_type": "oil_refinery",
        "base_frp": 125.4,
        "base_temp": 382.5,
    },
    {
        "zone": "Panipat Petrochemical Complex, Haryana",
        "latitude": 29.3909,
        "longitude": 76.9635,
        "facility_name": "IOCL Panipat Refinery & Petrochemicals",
        "facility_type": "chemical_petrochemical",
        "base_frp": 94.2,
        "base_temp": 366.1,
    },
    {
        "zone": "Tata Steel Jamshedpur, Jharkhand",
        "latitude": 22.8046,
        "longitude": 86.2029,
        "facility_name": "Tata Steel Works Jamshedpur",
        "facility_type": "steel_plant",
        "base_frp": 110.8,
        "base_temp": 375.4,
    },
    {
        "zone": "Angul Industrial Belt, Odisha",
        "latitude": 20.8400,
        "longitude": 85.1000,
        "facility_name": "Jindal Steel & Power Angul Integrated Complex",
        "facility_type": "steel_plant",
        "base_frp": 88.6,
        "base_temp": 358.9,
    },
    {
        "zone": "Paradeep Port Petrochemicals, Odisha",
        "latitude": 20.3160,
        "longitude": 86.6110,
        "facility_name": "IOCL Paradeep Refinery & Fertilizer Complex",
        "facility_type": "oil_refinery",
        "base_frp": 142.1,
        "base_temp": 395.2,
    },
    {
        "zone": "Visakhapatnam Steel & HPCL, Andhra Pradesh",
        "latitude": 17.6868,
        "longitude": 83.2185,
        "facility_name": "HPCL Visakhapatnam Refinery & RINL",
        "facility_type": "oil_refinery",
        "base_frp": 78.4,
        "base_temp": 351.0,
    },
]


class PollerService:
    """
    Background worker that runs a periodic loop simulating or ingesting satellite
    passes and pushing high-priority alerts to the SSE stream.
    """

    def __init__(self):
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._interval_seconds: int = 20
        self._total_ingested: int = 0
        self._total_alerts_sent: int = 0
        self._last_poll_time: Optional[str] = None
        self._sim_zone_idx: int = 0

    @property
    def status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "interval_seconds": self._interval_seconds,
            "total_ingested": self._total_ingested,
            "total_alerts_sent": self._total_alerts_sent,
            "last_poll_time": self._last_poll_time,
            "active_sse_subscribers": alert_stream_service.subscriber_count,
        }

    def start(self, interval_seconds: int = 20) -> None:
        """Start the background poller worker."""
        if self._running:
            return
        self._interval_seconds = interval_seconds
        self._running = True
        self._task = asyncio.create_task(self._poller_loop())
        logger.info("Satellite Poller Service started with %ds tick.", interval_seconds)

    def stop(self) -> None:
        """Stop the background poller worker."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None
        logger.info("Satellite Poller Service stopped.")

    async def _poller_loop(self) -> None:
        """Periodic background evaluation loop."""
        try:
            while self._running:
                await asyncio.sleep(self._interval_seconds)
                try:
                    await self.process_satellite_tick()
                except Exception as e:
                    logger.error("Error during satellite poller tick: %s", e, exc_info=True)
        except asyncio.CancelledError:
            pass

    async def process_satellite_tick(self) -> Optional[Dict[str, Any]]:
        """
        Execute one satellite ingestion cycle. Generates/fetches thermal data,
        runs classification and broadcasts if critical.
        """
        self._last_poll_time = datetime.now(timezone.utc).isoformat()
        self._total_ingested += 1

        # Select next industrial zone in rotation
        zone = INDIAN_INDUSTRIAL_ZONES[self._sim_zone_idx % len(INDIAN_INDUSTRIAL_ZONES)]
        self._sim_zone_idx += 1

        # Inject minor realistic noise (+/- 0.005 deg jitter, +/- 10% FRP)
        lat = zone["latitude"] + random.uniform(-0.006, 0.006)
        lon = zone["longitude"] + random.uniform(-0.006, 0.006)
        frp = round(zone["base_frp"] * random.uniform(0.88, 1.25), 2)
        bright = round(zone["base_temp"] + random.uniform(-4.0, 15.0), 2)
        confidence = random.randint(85, 100)
        dist_km = round(random.uniform(0.12, 1.45), 2)

        is_acute = frp > 90.0
        pred_class = "industrial_fire" if is_acute else "persistent_industrial"
        risk_score = min(98.0, round(65.0 + (frp / 4.0) + (confidence / 10.0), 1))
        risk_level = "CRITICAL" if risk_score >= 80.0 else "HIGH"

        alert_payload = {
            "alert_id": f"ALT-{uuid.uuid4().hex[:8].upper()}",
            "type": "THERMAL_ANOMALY_DETECTED",
            "source": random.choice(["VIIRS_NOAA20_NRT", "VIIRS_SNPP_NRT", "MODIS_AQUA"]),
            "latitude": round(lat, 5),
            "longitude": round(lon, 5),
            "predicted_class": pred_class,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "frp_mw": frp,
            "brightness_k": bright,
            "confidence": confidence,
            "daynight": "N" if random.random() > 0.4 else "D",
            "nearest_facility": zone["facility_name"],
            "facility_type": zone["facility_type"],
            "facility_distance_km": dist_km,
            "location_name": zone["zone"],
            "summary": (
                f"🚨 {risk_level} ALERT: {pred_class.replace('_', ' ').title()} "
                f"({frp} MW) detected {dist_km} km from {zone['facility_name']}."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._total_alerts_sent += 1
        await alert_stream_service.broadcast(alert_payload)
        return alert_payload

    async def trigger_instant_simulation(
        self,
        zone_name: Optional[str] = None,
        acute_fire: bool = True,
    ) -> Dict[str, Any]:
        """
        Manually trigger an instant high-priority satellite pass for demonstration.
        """
        zone = INDIAN_INDUSTRIAL_ZONES[0]
        if zone_name:
            for z in INDIAN_INDUSTRIAL_ZONES:
                if zone_name.lower() in z["zone"].lower() or zone_name.lower() in z["facility_name"].lower():
                    zone = z
                    break

        lat = zone["latitude"] + random.uniform(-0.003, 0.003)
        lon = zone["longitude"] + random.uniform(-0.003, 0.003)
        frp = round(random.uniform(140.0, 210.0) if acute_fire else 65.0, 2)
        bright = round(random.uniform(380.0, 420.0) if acute_fire else 340.0, 2)
        confidence = 100
        dist_km = round(random.uniform(0.1, 0.8), 2)

        pred_class = "industrial_fire" if acute_fire else "persistent_industrial"
        risk_score = 96.5 if acute_fire else 74.0
        risk_level = "CRITICAL" if acute_fire else "HIGH"

        alert_payload = {
            "alert_id": f"ALT-{uuid.uuid4().hex[:8].upper()}",
            "type": "THERMAL_ANOMALY_DETECTED",
            "source": "VIIRS_NOAA20_NRT",
            "latitude": round(lat, 5),
            "longitude": round(lon, 5),
            "predicted_class": pred_class,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "frp_mw": frp,
            "brightness_k": bright,
            "confidence": confidence,
            "daynight": "N",
            "nearest_facility": zone["facility_name"],
            "facility_type": zone["facility_type"],
            "facility_distance_km": dist_km,
            "location_name": zone["zone"],
            "summary": (
                f"🚨 CRITICAL OVERRIDE: Acute Industrial Fire detected at {zone['facility_name']} "
                f"(FRP: {frp} MW, Distance: {dist_km} km)!"
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._total_ingested += 1
        self._total_alerts_sent += 1
        self._last_poll_time = datetime.now(timezone.utc).isoformat()
        await alert_stream_service.broadcast(alert_payload)
        return alert_payload


# Global singleton instance
poller_service = PollerService()
