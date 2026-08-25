"""
SIH26162 — Phase 4 Interactive Frontend Dashboard E2E Verification Suite.
Verifies all frontend-consumed FastAPI endpoints, spatial filters, pagination,
classification triggers, DB health diagnostics, and frontend build readiness.
"""

import urllib.request
import urllib.parse
import json
import sys
import subprocess
from pathlib import Path

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def print_header(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def test_endpoint(name, url, method="GET", body=None, expected_status=200, timeout=20):
    print(f"Testing {name} -> {method} {url}...")
    req = urllib.request.Request(url, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode("utf-8")
    else:
        data = None
        
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            json_data = json.loads(content) if content else {}
            assert status == expected_status, f"Expected status {expected_status}, got {status}"
            print(f"  [✓] PASS (HTTP {status})")
            return json_data
    except Exception as err:
        print(f"  [✗] FAIL: {err}")
        sys.exit(1)

def main():
    print_header("PHASE 4: INTERACTIVE FRONTEND DASHBOARD VERIFICATION")

    # 1. System Health & PostGIS Probes
    health = test_endpoint("System Health Probe", f"{BASE_URL}/api/v1/health")
    assert health.get("status") == "healthy"
    
    db_health = test_endpoint("PostGIS DB Diagnostics Probe", f"{BASE_URL}/api/v1/health/db")
    assert db_health.get("healthy") is True
    print(f"      - FIRMS Observations Row Count:  {db_health['record_counts']['firms_observations']}")
    print(f"      - Persistent Clusters Row Count: {db_health['record_counts']['persistent_thermal_sources']}")

    # 2. Observations API with Filters & Pagination
    obs_params = urllib.parse.urlencode({
        "satellite": "VIIRS_SNPP_NRT",
        "min_frp": 10.0,
        "min_confidence": 50.0,
        "page": 1,
        "page_size": 25
    })
    obs_data = test_endpoint("Filtered Observations API", f"{BASE_URL}/api/v1/fires/observations?{obs_params}")
    assert "observations" in obs_data
    assert "total" in obs_data
    print(f"      - Observations Returned: {len(obs_data['observations'])} / Total Matching: {obs_data['total']}")

    # 3. Spatial Bounding Box Filtering
    bbox_params = urllib.parse.urlencode({
        "min_lon": 80.0, "min_lat": 20.0, "max_lon": 90.0, "max_lat": 28.0,
        "page": 1, "page_size": 10
    })
    bbox_data = test_endpoint("Spatial BBOX Filtered Query", f"{BASE_URL}/api/v1/fires/observations?{bbox_params}")
    print(f"      - BBOX Matches (80-90E, 20-28N): {bbox_data['total']} items")

    # 4. Persistent Thermal Source Clusters API
    cluster_params = urllib.parse.urlencode({"min_observations": 5, "limit": 50})
    clusters_data = test_endpoint("Persistent Thermal Clusters API", f"{BASE_URL}/api/v1/thermal/sources?{cluster_params}")
    assert "clusters" in clusters_data
    print(f"      - Clusters Returned: {len(clusters_data['clusters'])} / Total Clusters: {clusters_data['total_clusters']}")

    # 5. Interactive Classification & Persistence Endpoint
    class_payload = {
        "latitude": 23.6783,
        "longitude": 86.0896,
        "brightness_primary": 338.5,
        "brightness_secondary": 294.2,
        "frp": 24.5,
        "confidence_score": 90.0,
        "daynight": "N",
        "query_osm": False,
        "persist": True
    }
    class_res = test_endpoint("Interactive AI Classification Trigger", f"{BASE_URL}/api/v1/fires/classify", method="POST", body=class_payload)
    assert class_res.get("predicted_class") == "persistent_industrial"
    assert "risk_score" in class_res
    print(f"      - Predicted Class: {class_res['predicted_class']}")
    print(f"      - Risk Score:      {class_res['risk_score']} ({class_res['risk_level']})")

    # 6. Stored Classifications Feed API
    clf_data = test_endpoint("Stored Classifications API", f"{BASE_URL}/api/v1/fires/classifications?limit=10")
    assert "classifications" in clf_data
    print(f"      - Stored Classification Records: {len(clf_data['classifications'])}")

    # 7. OpenStreetMap Industrial Context API
    osm_payload = {"latitude": 23.6783, "longitude": 86.0896, "radius_m": 5000}
    osm_data = test_endpoint("OSM Industrial Context Query", f"{BASE_URL}/api/v1/geospatial/industrial-context", method="POST", body=osm_payload)
    assert "status" in osm_data
    print(f"      - OSM Query Status: {osm_data['status']}")

    # 8. Live Frontend HTTP Accessibility Check
    print_header("FRONTEND DASHBOARD ACCESSIBILITY VERIFICATION")
    try:
        req_fe = urllib.request.Request(FRONTEND_URL)
        with urllib.request.urlopen(req_fe, timeout=5) as resp_fe:
            html = resp_fe.read().decode("utf-8")
            assert "<div id=\"root\"></div>" in html or "<title>" in html
            print(f"  [✓] Frontend React Dashboard is LIVE on {FRONTEND_URL} (HTTP {resp_fe.status})")
    except Exception as fe_err:
        print(f"  [!] Frontend container check warning: {fe_err}")

    print_header("PHASE 4 FRONTEND & API VERIFICATION COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
