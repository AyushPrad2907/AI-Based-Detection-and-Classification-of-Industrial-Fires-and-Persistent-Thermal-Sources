"""
SIH26162 — Phase 5 Baseline Performance & Latency Benchmark.

Measures request counts, success/fail counts, avg, median, p50, p95, p99, min, max latencies,
and throughput (req/sec) across all FastAPI endpoints.
"""

import time
import json
import statistics
import urllib.request
import urllib.parse
from typing import Any, Dict, List

BASE_URL = "http://localhost:8000"

def run_endpoint_benchmark(
    name: str,
    url: str,
    method: str = "GET",
    body: Dict[str, Any] = None,
    iterations: int = 50,
) -> Dict[str, Any]:
    print(f"Benchmarking {name} ({iterations} iterations)...", flush=True)
    latencies: List[float] = []
    successes = 0
    failures = 0
    
    encoded_body = json.dumps(body).encode("utf-8") if body else None
    
    start_total = time.perf_counter()
    for _ in range(iterations):
        req = urllib.request.Request(url, method=method)
        if encoded_body:
            req.add_header("Content-Type", "application/json")
            
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, data=encoded_body, timeout=10) as resp:
                _ = resp.read()
                if resp.status == 200:
                    successes += 1
                else:
                    failures += 1
        except Exception as err:
            failures += 1
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0) # in ms
        
    total_elapsed = time.perf_counter() - start_total
    
    if latencies:
        latencies.sort()
        avg_lat = statistics.mean(latencies)
        median_lat = statistics.median(latencies)
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95) - 1]
        p99 = latencies[int(len(latencies) * 0.99) - 1]
        min_lat = min(latencies)
        max_lat = max(latencies)
    else:
        avg_lat = median_lat = p50 = p95 = p99 = min_lat = max_lat = 0.0
        
    throughput = iterations / total_elapsed if total_elapsed > 0 else 0.0
    
    res = {
        "endpoint": name,
        "method": method,
        "url": url,
        "iterations": iterations,
        "successes": successes,
        "failures": failures,
        "total_time_sec": round(total_elapsed, 3),
        "avg_ms": round(avg_lat, 2),
        "median_ms": round(median_lat, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "min_ms": round(min_lat, 2),
        "max_ms": round(max_lat, 2),
        "throughput_rps": round(throughput, 1),
    }
    
    print(f"  [✓] Avg: {res['avg_ms']} ms | p50: {res['p50_ms']} ms | p95: {res['p95_ms']} ms | p99: {res['p99_ms']} ms | {res['throughput_rps']} req/s")
    return res

def main():
    print("=" * 80)
    print(" SIH26162 — PHASE 5 END-TO-END LATENCY BENCHMARK ENGINE")
    print("=" * 80)
    
    endpoints = [
        ("System Health Probe", f"{BASE_URL}/api/v1/health", "GET", None, 100),
        ("PostGIS DB Diagnostics Probe", f"{BASE_URL}/api/v1/health/db", "GET", None, 50),
        ("Paginated Observations API", f"{BASE_URL}/api/v1/fires/observations?page=1&limit=50", "GET", None, 50),
        ("BBOX Filtered Observations", f"{BASE_URL}/api/v1/fires/observations?bbox=80.0,20.0,90.0,28.0&limit=50", "GET", None, 50),
        ("Persistent Thermal Clusters API", f"{BASE_URL}/api/v1/thermal/sources?limit=50", "GET", None, 50),
        ("Stored Classifications Feed", f"{BASE_URL}/api/v1/fires/classifications?limit=25", "GET", None, 50),
        ("AI Classification Engine (Pure)", f"{BASE_URL}/api/v1/fires/classify", "POST", {
            "latitude": 23.6783,
            "longitude": 86.0896,
            "brightness_primary": 338.5,
            "brightness_secondary": 294.2,
            "frp": 24.5,
            "confidence_score": 90.0,
            "daynight": "N",
            "query_osm": False,
            "persist": False
        }, 50),
        ("AI Classification + PostGIS Persist", f"{BASE_URL}/api/v1/fires/classify", "POST", {
            "latitude": 23.6783,
            "longitude": 86.0896,
            "brightness_primary": 338.5,
            "brightness_secondary": 294.2,
            "frp": 24.5,
            "confidence_score": 90.0,
            "daynight": "N",
            "query_osm": False,
            "persist": True
        }, 50),
        ("OSM Industrial Context Query", f"{BASE_URL}/api/v1/geospatial/industrial-context", "POST", {
            "latitude": 23.6783,
            "longitude": 86.0896,
            "radius_m": 5000
        }, 3),
    ]
    
    results = []
    for name, url, method, body, iters in endpoints:
        r = run_endpoint_benchmark(name, url, method, body, iters)
        results.append(r)
        
    print("\n" + "=" * 80)
    print(" BENCHMARK SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Endpoint':<35} | {'Avg (ms)':<8} | {'p50':<7} | {'p95':<7} | {'p99':<7} | {'Req/s':<6}")
    print("-" * 80)
    for r in results:
        print(f"{r['endpoint']:<35} | {r['avg_ms']:<8} | {r['p50_ms']:<7} | {r['p95_ms']:<7} | {r['p99_ms']:<7} | {r['throughput_rps']:<6}")
    print("=" * 80)

if __name__ == "__main__":
    main()
