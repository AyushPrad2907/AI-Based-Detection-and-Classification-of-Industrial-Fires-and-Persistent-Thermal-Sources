"""
SIH26162 — Phase 5 End-to-End Verification & Validation Suite.

Executes complete workflow simulation:
Telemetry -> PostGIS Lookup -> Cluster Matching -> AI Classification ->
Probabilities -> Industrial Proximity -> Risk Scoring -> Explanations ->
Persistence -> Dashboard Retrieval -> Frontend Accessibility -> Concurrent Load.
"""

import sys
import json
import time
import math
import urllib.request
import urllib.parse
import concurrent.futures
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(1, str(REPO_ROOT / "backend"))

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def print_section(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80, flush=True)

def post_json(url, payload, timeout=15):
    req = urllib.request.Request(url, method="POST", headers={"Content-Type": "application/json"})
    data = json.dumps(payload).encode("utf-8")
    with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def get_json(url, timeout=15):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def get_html(url, timeout=15):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8")

def main():
    print_section("PHASE 5: END-TO-END VALIDATION & VERIFICATION SUITE")
    
    # 1. System Health Probes
    status_health, res_health = get_json(f"{BASE_URL}/api/v1/health")
    assert status_health == 200 and res_health.get("status") == "healthy"
    print("  [✓] Step 1: API Health Probe -> OK")
    
    status_db, res_db = get_json(f"{BASE_URL}/api/v1/health/db")
    assert status_db == 200 and res_db.get("healthy") is True
    print(f"  [✓] Step 2: PostGIS DB Diagnostics -> Connected (Lat: {res_db['latency_ms']} ms)")
    print(f"      - FIRMS Observations: {res_db['record_counts']['firms_observations']}")
    print(f"      - Persistent Clusters: {res_db['record_counts']['persistent_thermal_sources']}")

    # 2. Telemetry & Spatial Lookup Workflow
    bbox_url = f"{BASE_URL}/api/v1/fires/observations?bbox=80.0,20.0,90.0,28.0&limit=5"
    status_obs, res_obs = get_json(bbox_url)
    assert status_obs == 200 and res_obs["total"] > 0
    sample_obs = res_obs["observations"][0]
    print(f"  [✓] Step 3: PostGIS Spatial Observation Query -> Found {res_obs['total']} records")
    print(f"      - Sample Obs #{sample_obs['id']}: ({sample_obs['latitude']:.4f}, {sample_obs['longitude']:.4f}) | FRP: {sample_obs['frp']} MW")

    # 3. Persistent Thermal Cluster Query
    cluster_url = f"{BASE_URL}/api/v1/thermal/sources?limit=5"
    status_cls, res_cls = get_json(cluster_url)
    assert status_cls == 200 and len(res_cls["clusters"]) > 0
    sample_cluster = res_cls["clusters"][0]
    print(f"  [✓] Step 4: Persistent Cluster Lookup -> {res_cls['total_clusters']} clusters in PostGIS")
    print(f"      - Sample Cluster #{sample_cluster['cluster_id']}: Centroid ({sample_cluster['centroid_latitude']:.4f}, {sample_cluster['centroid_longitude']:.4f}) | Passes: {sample_cluster['observation_count']}")

    # 4. Multi-Scenario AI Classification & Risk Scoring Correctness
    print_section("AI CLASSIFICATION & EXPLAINABLE RISK ENGINE VERIFICATION")
    
    # Scenario A: Persistent Industrial
    scen_a_payload = {
        "latitude": 23.6783,
        "longitude": 86.0896,
        "brightness_primary": 338.5,
        "brightness_secondary": 294.2,
        "frp": 24.5,
        "confidence_score": 100,
        "daynight": "N",
        "query_osm": False,
        "persist": True
    }
    st_a, res_a = post_json(f"{BASE_URL}/api/v1/fires/classify", scen_a_payload)
    assert st_a == 200
    assert res_a["predicted_class"] == "persistent_industrial"
    assert math.isclose(sum(res_a["class_probabilities"].values()), 1.0, abs_tol=1e-4)
    assert 0.0 <= res_a["risk_score"] <= 100.0
    print(f"  [✓] Scenario A (Persistent Industrial): Class={res_a['predicted_class']} | Conf={res_a['classification_confidence']} | Risk={res_a['risk_score']} ({res_a['risk_level']})")
    
    # Scenario B: Low Risk Anomaly
    scen_b_payload = {
        "latitude": 20.5, "longitude": 78.5, "frp": 2.0, "confidence_score": 30, "daynight": "D", "query_osm": False, "persist": False
    }
    st_b, res_b = post_json(f"{BASE_URL}/api/v1/fires/classify", scen_b_payload)
    assert st_b == 200
    assert res_b["risk_level"] == "LOW"
    print(f"  [✓] Scenario B (Low Risk Anomaly): Class={res_b['predicted_class']} | Risk={res_b['risk_score']} ({res_b['risk_level']})")
    
    # Scenario C: High/Critical Risk Anomaly
    scen_c_payload = {
        "latitude": 22.1, "longitude": 82.3, "frp": 350.0, "confidence_score": 100, "daynight": "N", "query_osm": False, "persist": False
    }
    st_c, res_c = post_json(f"{BASE_URL}/api/v1/fires/classify", scen_c_payload)
    assert st_c == 200
    assert res_c["risk_level"] in ["HIGH", "CRITICAL"]
    print(f"  [✓] Scenario C (High/Critical Anomaly): Class={res_c['predicted_class']} | Risk={res_c['risk_score']} ({res_c['risk_level']})")

    # Scenario D: Input Validation Errors (HTTP 422)
    invalid_payload = {"latitude": 150.0, "longitude": 80.0, "frp": -10.0}
    try:
        post_json(f"{BASE_URL}/api/v1/fires/classify", invalid_payload)
        print("  [✗] Scenario D: Expected HTTP 422 validation failure!")
        sys.exit(1)
    except urllib.error.HTTPError as err:
        assert err.code == 422
        print("  [✓] Scenario D (Invalid Input Bounds): Returned HTTP 422 Unprocessable Entity as expected")

    # 5. Stored Classifications Dashboard Retrieval
    st_st, res_st = get_json(f"{BASE_URL}/api/v1/fires/classifications?limit=10")
    assert st_st == 200 and len(res_st["classifications"]) > 0
    print(f"  [✓] Step 5: PostGIS Stored Classifications Retrieval -> {res_st['total']} total records")

    # 6. Frontend Accessibility Check
    st_fe, html_fe = get_html(FRONTEND_URL)
    assert st_fe == 200
    print(f"  [✓] Step 6: Live React Dashboard -> Accessible on {FRONTEND_URL} (HTTP 200)")

    # 7. Concurrent Load Test (25 Concurrent Requests)
    print_section("CONCURRENT LOAD STABILITY TEST (25 CONCURRENT REQUESTS)")
    def make_req(idx):
        t0 = time.perf_counter()
        st, res = post_json(f"{BASE_URL}/api/v1/fires/classify", scen_a_payload)
        t1 = time.perf_counter()
        return st == 200, (t1 - t0) * 1000.0

    t_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(make_req, i) for i in range(25)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    t_end = time.perf_counter()
    
    succ = sum(1 for s, _ in results if s)
    lats = sorted([l for _, l in results])
    avg_l = sum(lats) / len(lats)
    p50_l = lats[int(len(lats) * 0.5)]
    p95_l = lats[int(len(lats) * 0.95)]
    throughput = len(results) / (t_end - t_start)
    
    print(f"  [✓] Concurrent Load Results:")
    print(f"      - Requests:   25 total | Successes: {succ} | Failures: {len(results) - succ}")
    print(f"      - Latencies:  Avg: {avg_l:.2f} ms | p50: {p50_l:.2f} ms | p95: {p95_l:.2f} ms")
    print(f"      - Throughput: {throughput:.1f} req/sec under 25-worker load")
    
    assert succ == 25, "Concurrent load test encountered request failures!"
    
    print_section("PHASE 5 END-TO-END VALIDATION COMPLETED WITH 100% SUCCESS!")

if __name__ == "__main__":
    main()
