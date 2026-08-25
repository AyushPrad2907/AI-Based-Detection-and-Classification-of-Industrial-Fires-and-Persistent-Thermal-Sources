"""
SIH26162 — Direct PostGIS Spatial Database Verification Script.
Queries PostgreSQL/PostGIS database tables directly (without API layer).
"""

import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from sqlalchemy import text
from app.core.database import async_session

async def main():
    print("=" * 80)
    print("DIRECT POSTGRESQL + POSTGIS SPATIAL DATABASE AUDIT")
    print("=" * 80)
    
    async with async_session() as session:
        # 1. Total Counts
        obs_res = await session.execute(text("SELECT count(*) FROM firms_observations;"))
        obs_count = obs_res.scalar()
        
        cluster_res = await session.execute(text("SELECT count(*) FROM persistent_thermal_sources;"))
        cluster_count = cluster_res.scalar()
        
        print(f"Total firms_observations in PostGIS:        {obs_count}")
        print(f"Total persistent_thermal_sources in PostGIS: {cluster_count}")
        
        # 2. Query cluster matching test coordinate (23.6783, 86.0896)
        query = text("""
            SELECT id, cluster_id, centroid_lat, centroid_lon, observation_count,
                   first_seen_utc, last_seen_utc, persistence_duration_days,
                   mean_frp_mw, max_frp_mw, mean_brightness_kelvin, mean_confidence,
                   night_observation_ratio, spatial_radius_meters, is_persistent,
                   ST_AsText(centroid_geom) as geom_wkt
            FROM persistent_thermal_sources
            WHERE ST_DWithin(
                centroid_geom,
                ST_SetSRID(ST_MakePoint(86.0896, 23.6783), 4326),
                0.05
            )
            ORDER BY observation_count DESC
            LIMIT 1;
        """)
        
        res = await session.execute(query)
        row = res.mappings().first()
        
        if row:
            print("\nFound DB Match for Test Coordinates (23.6783, 86.0896):")
            for k, v in row.items():
                print(f"  {k:<28}: {v}")
        else:
            print("\n[!] No spatial cluster found within 0.05deg of (23.6783, 86.0896)")
            
        # 3. Check observations linked to this cluster ID
        if row:
            cid = row["cluster_id"]
            obs_query = text("""
                SELECT count(*), min(frp), max(frp), avg(frp)
                FROM firms_observations
                WHERE cluster_id = :cid;
            """)
            obs_res = await session.execute(obs_query, {"cid": cid})
            obs_row = obs_res.first()
            print(f"\nRaw Observations linked to Cluster #{cid} in PostGIS:")
            print(f"  Count:    {obs_row[0]}")
            print(f"  Min FRP:  {obs_row[1]:.2f} MW")
            print(f"  Max FRP:  {obs_row[2]:.2f} MW")
            print(f"  Mean FRP: {obs_row[3]:.2f} MW")
            assert obs_row[0] == row["observation_count"], "DB Mismatch between cluster count and raw observation count!"
            print("\n[✓] PostGIS DB Cluster-to-Observation Relationship Integrity VERIFIED.")

if __name__ == "__main__":
    asyncio.run(main())
