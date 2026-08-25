"""
SIH26162 — Risk Engine Multi-Scenario Verification Matrix.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(1, str(REPO_ROOT / "backend"))

from ml.inference.risk_scorer import RiskScorer

def main():
    print("=" * 80)
    print("RISK SCORER MULTI-SCENARIO VERIFICATION MATRIX")
    print("=" * 80)
    
    scorer = RiskScorer()
    
    scenarios = [
        ("1. Low Risk (Transient/Daytime)", {
            "frp": 2.0, "confidence_score": 30.0, "daynight": "D",
            "persistence_count": 1, "persistence_days": 0.0,
            "dist_to_industrial_km": 10.0, "predicted_class": "uncertain_anomaly"
        }),
        ("2. Moderate Risk (Agricultural Burn)", {
            "frp": 15.0, "confidence_score": 70.0, "daynight": "D",
            "persistence_count": 2, "persistence_days": 0.5,
            "dist_to_industrial_km": 8.0, "predicted_class": "agricultural_burn"
        }),
        ("3. High Risk (Persistent Industrial Anomaly)", {
            "frp": 45.0, "confidence_score": 90.0, "daynight": "N",
            "persistence_count": 30, "persistence_days": 3.7,
            "dist_to_industrial_km": 0.5, "predicted_class": "persistent_industrial"
        }),
        ("4. Critical Risk (Catastrophic Flare / Explosion)", {
            "frp": 680.0, "confidence_score": 100.0, "daynight": "N",
            "persistence_count": 45, "persistence_days": 5.0,
            "dist_to_industrial_km": 0.1, "predicted_class": "persistent_industrial"
        }),
    ]
    
    for name, rec in scenarios:
        res = scorer.calculate_risk(
            frp=rec["frp"],
            confidence=rec["confidence_score"],
            dist_to_industrial_m=rec["dist_to_industrial_km"] * 1000.0,
            persistence_count=rec["persistence_count"],
            persistence_days=rec["persistence_days"],
            is_night=(rec["daynight"] == "N")
        )
        score = res["risk_score"]
        level = res["risk_level"]
        breakdown = res["breakdown"]
        reasons = res["reasons"]
        
        print(f"\nScenario: {name}")
        print(f"  Risk Index:  {score:.1f} / 100")
        print(f"  Risk Level:  {level}")
        print(f"  Subscores:   FRP={breakdown['frp_subscore']:.2f}, Prox={breakdown['industrial_proximity_subscore']:.2f}, Persist={breakdown['persistence_subscore']:.2f}, Conf={breakdown['confidence_subscore']:.2f}, Night={breakdown['nocturnal_subscore']:.2f}")
        print(f"  Reasons:     {reasons[:2]}")
        
        # Invariants assertion
        assert 0.0 <= score <= 100.0, "Risk score out of bounds!"
        assert level in ["LOW", "MODERATE", "HIGH", "CRITICAL"], "Invalid risk level!"
        for sub in breakdown.values():
            assert 0.0 <= sub <= 1.0, f"Subscore {sub} out of bounds 0-1!"
            
    print("\n[✓] All 4 Risk Scorer Scenarios VERIFIED successfully!")

if __name__ == "__main__":
    main()
