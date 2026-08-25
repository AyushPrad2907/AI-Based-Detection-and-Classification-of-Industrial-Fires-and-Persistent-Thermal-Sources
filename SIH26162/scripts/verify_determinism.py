"""
SIH26162 — AI Classifier Determinism Test Script.
"""

import json
import urllib.request
import sys

BASE_URL = "http://localhost:8000"

def main():
    print("=" * 80)
    print("CLASSIFIER & RISK SCORER DETERMINISM AUDIT")
    print("=" * 80)
    
    payload = {
        "latitude": 23.6783,
        "longitude": 86.0896,
        "brightness_primary": 338.5,
        "brightness_secondary": 294.2,
        "frp": 24.5,
        "confidence_score": 88.0,
        "acq_datetime": "2026-08-25T02:30:00",
        "satellite": "VIIRS_SNPP_NRT",
        "instrument": "VIIRS",
        "daynight": "N"
    }
    
    results = []
    for i in range(10):
        req = urllib.request.Request(
            f"{BASE_URL}/api/v1/fires/classify",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results.append(data)
            
    # Check equality across all 10 runs
    first = results[0]
    for idx, r in enumerate(results[1:], start=2):
        assert r["predicted_class"] == first["predicted_class"], f"Mismatch in predicted_class on run {idx}"
        assert r["classification_confidence"] == first["classification_confidence"], f"Mismatch in confidence on run {idx}"
        assert r["class_probabilities"] == first["class_probabilities"], f"Mismatch in probabilities on run {idx}"
        assert r["risk_score"] == first["risk_score"], f"Mismatch in risk_score on run {idx}"
        assert r["risk_level"] == first["risk_level"], f"Mismatch in risk_level on run {idx}"
        
    print(f"[✓] Executed 10 identical requests.")
    print(f"    Predicted Class:          {first['predicted_class']}")
    print(f"    Classification Confidence:{first['classification_confidence']}")
    print(f"    Class Probabilities:      {first['class_probabilities']}")
    print(f"    Risk Score:               {first['risk_score']}")
    print(f"    Risk Level:               {first['risk_level']}")
    print("=" * 80)
    print("CLASSIFIER & RISK ENGINE DETERMINISM 100% VERIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    main()
