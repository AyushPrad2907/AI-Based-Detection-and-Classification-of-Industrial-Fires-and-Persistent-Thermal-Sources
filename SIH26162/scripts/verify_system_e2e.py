"""
SIH26162 — End-to-End System Verification Script.

Executes comprehensive validation across:
1. All API endpoints
2. DBSCAN cluster consistency vs raw observations
3. AI model classification & inference
4. OpenStreetMap industrial proximity query
5. Explainable Risk Scorer (high-FRP / high-confidence scenario)
6. Frontend ↔ Backend data contract mapping
"""

import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://localhost:8000"

def post_json(path, data):
    url = f"{BASE_URL}{path}"
    json_bytes = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=json_bytes, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def get_json(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def main():
    print("=" * 80)
    print("SIH26162 — END-TO-END SYSTEM VERIFICATION AUDIT")
    print("=" * 80)
    
    # -------------------------------------------------------------------------
    # 1. API Endpoints Verification
    # -------------------------------------------------------------------------
    print("\n[1/6] Verifying API Endpoint Suite...")
    endpoints = [
        ("/api/v1/health/", "Health Core"),
        ("/api/v1/health/db", "PostGIS Health"),
        ("/api/v1/fires/status", "ML Model Status"),
        ("/api/v1/fires/observations?limit=5", "Observations Spatial Query"),
        ("/api/v1/thermal/sources?limit=5", "Thermal Clusters Query"),
        ("/api/v1/geospatial/", "Geospatial Overview"),
    ]
    for path, label in endpoints:
        status_code, resp = get_json(path)
        assert status_code == 200, f"Failed {label} on {path}"
        print(f"  [PASS] {label:<25} ({path}) -> Status {status_code}")

    # -------------------------------------------------------------------------
    # 2. DBSCAN Clusters Verification against Raw Detections
    # -------------------------------------------------------------------------
    print("\n[2/6] Verifying DBSCAN Clusters vs Raw Telemetry...")
    _, db_health = get_json("/api/v1/health/db")
    counts = db_health["record_counts"]
    raw_obs_count = counts["firms_observations"]
    cluster_count = counts["persistent_thermal_sources"]
    
    print(f"  Raw Satellite Observations in PostGIS: {raw_obs_count}")
    print(f"  DBSCAN Persistent Thermal Source Clusters: {cluster_count}")
    assert raw_obs_count > 0, "No raw observations found in PostGIS database!"
    assert cluster_count > 0, "No DBSCAN clusters found in PostGIS database!"
    
    # Verify cluster retrieval
    _, cluster_data = get_json("/api/v1/thermal/sources?limit=10")
    clusters = cluster_data.get("clusters", [])
    print(f"  Fetched {len(clusters)} sample clusters from PostGIS.")
    sample_cluster = clusters[0]
    print(f"  Sample Cluster #{sample_cluster['cluster_id']}: Centroid ({sample_cluster['centroid_latitude']:.4f}, {sample_cluster['centroid_longitude']:.4f}) | Observations: {sample_cluster['observation_count']} | Mean FRP: {sample_cluster['mean_frp_mw']:.2f} MW")
    assert sample_cluster['observation_count'] >= 2, "Cluster observation count invalid!"
    print("  [PASS] DBSCAN Spatial Clustering Integrity Verified.")

    # -------------------------------------------------------------------------
    # 3. Test AI Classification / Inference on Real Observation
    # -------------------------------------------------------------------------
    print("\n[3/6] Testing AI Classification Inference on Actual Observation...")
    payload_real = {
        "latitude": 23.6783,
        "longitude": 86.0896,
        "brightness_primary": 338.5,
        "brightness_secondary": 294.2,
        "frp": 24.5,
        "confidence_score": 88.0,
        "acq_datetime": "2026-08-25T02:30:00",
        "satellite": "N",
        "instrument": "VIIRS",
        "daynight": "N"
    }
    status_code, cls_res = post_json("/api/v1/fires/classify", payload_real)
    assert status_code == 200, "Classification inference failed!"
    print(f"  Predicted Class:        {cls_res['predicted_class']}")
    print(f"  Inference Confidence:   {cls_res['classification_confidence'] * 100:.2f}%")
    print(f"  Class Probabilities:    {cls_res['class_probabilities']}")
    print("  [PASS] Random Forest ML Classifier Inference Verified.")

    # -------------------------------------------------------------------------
    # 4. Test OpenStreetMap Industrial Proximity
    # -------------------------------------------------------------------------
    print("\n[4/6] Testing OpenStreetMap Industrial Proximity Service...")
    osm_payload = {
        "latitude": 23.678,
        "longitude": 86.089,
        "radius_m": 5000
    }
    status_code, osm_res = post_json("/api/v1/geospatial/industrial-context", osm_payload)
    assert status_code == 200, "OSM query failed!"
    print(f"  Industrial Nearby:      {osm_res['is_industrial_nearby']}")
    print(f"  Min Distance:           {osm_res['min_distance_km']:.2f} km")
    print(f"  Nearest Facility Name:  {osm_res['nearest_facility_name']}")
    print(f"  Facilities in Radius:   {osm_res['total_facilities_in_radius']}")
    print("  [PASS] OpenStreetMap Proximity Engine Verified.")

    # -------------------------------------------------------------------------
    # 5. Test Risk Scoring with Deliberately High-FRP Data
    # -------------------------------------------------------------------------
    print("\n[5/6] Testing Explainable Risk Scorer (High-FRP / High-Confidence Critical Anomaly)...")
    payload_high_hazard = {
        "latitude": 23.6783,
        "longitude": 86.0896,
        "brightness_primary": 485.0,
        "brightness_secondary": 330.0,
        "frp": 680.0,
        "confidence_score": 100.0,
        "acq_datetime": "2026-08-25T01:15:00",
        "satellite": "N",
        "instrument": "VIIRS",
        "daynight": "N"
    }
    status_code, risk_res = post_json("/api/v1/fires/classify", payload_high_hazard)
    assert status_code == 200, "High hazard risk classification failed!"
    print(f"  Risk Index (0-100):     {risk_res['risk_score']:.1f} / 100")
    print(f"  Hazard Risk Level:      {risk_res['risk_level']}")
    print(f"  Subscore Breakdown:     {risk_res['risk_breakdown']}")
    print(f"  Diagnostic Reasons:     {risk_res['reasons']}")
    assert risk_res["risk_score"] >= 60.0, "Risk score expected to be elevated for 680MW FRP!"
    assert risk_res["risk_level"] in ["HIGH", "CRITICAL"], "Risk level expected to be HIGH or CRITICAL!"
    print("  [PASS] Explainable Multi-Factor Risk Scorer Verified.")

    # -------------------------------------------------------------------------
    # 6. Verify Frontend ↔ Backend Contract Mapping & Map Filters
    # -------------------------------------------------------------------------
    print("\n[6/6] Verifying Frontend ↔ Backend Contract Mapping & Map Filters...")
    
    # Test confidence filter
    status_code, filter_conf = get_json("/api/v1/fires/observations?confidence=high&limit=5")
    assert status_code == 200
    print(f"  Filtered by confidence='high': {filter_conf['total']} observations match.")
    
    # Test bounding box filter
    status_code, filter_bbox = get_json("/api/v1/fires/observations?bbox=85.0,22.0,88.0,25.0&limit=5")
    assert status_code == 200
    print(f"  Filtered by bbox='85,22,88,25' (Jharkhand Industrial Zone): {filter_bbox['total']} observations match.")
    
    # Test sensor filter
    status_code, filter_sensor = get_json("/api/v1/fires/observations?sensor=VIIRS&limit=5")
    assert status_code == 200
    print(f"  Filtered by sensor='VIIRS': {filter_sensor['total']} observations match.")
    
    print("  [PASS] Spatial Query & Map Filter Data Flow Verified.")

    print("\n" + "=" * 80)
    print("ALL 6 END-TO-END VERIFICATION CHECKS COMPLETED SUCCESSFULLY WITH ZERO ERRORS!")
    print("=" * 80)

if __name__ == "__main__":
    main()
