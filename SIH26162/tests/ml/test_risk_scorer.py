"""
SIH26162 — Unit Tests for Explainable Risk Scorer.
"""

import pytest
from ml.inference.risk_scorer import RiskScorer


def test_risk_scorer_critical_industrial_fire():
    scorer = RiskScorer()
    res = scorer.calculate_risk(
        frp=120.0,
        confidence=95.0,
        dist_to_industrial_m=150.0,
        facility_name="Petroleum Refinery",
        facility_type="petroleum_refinery",
        persistence_count=3,
        persistence_days=1.5,
        is_night=True,
    )

    assert res["risk_score"] >= 75.0
    assert res["risk_level"] == "CRITICAL"
    assert "breakdown" in res
    assert "reasons" in res
    assert len(res["reasons"]) >= 3
    # Check that refinery is mentioned in reasons
    assert any("Refinery" in r for r in res["reasons"])


def test_risk_scorer_low_risk_transient():
    scorer = RiskScorer()
    res = scorer.calculate_risk(
        frp=1.5,
        confidence=40.0,
        dist_to_industrial_m=8000.0,
        persistence_count=1,
        persistence_days=0.0,
        is_night=False,
    )

    assert res["risk_score"] < 35.0
    assert res["risk_level"] == "LOW"
    assert "breakdown" in res
    assert "weights" in res


def test_risk_scorer_subscores():
    scorer = RiskScorer()
    s_frp, _ = scorer.compute_frp_subscore(0.0)
    assert s_frp == 0.0

    s_prox, _ = scorer.compute_proximity_subscore(50.0, "Power Station", "power")
    assert s_prox == 1.0

    s_persist, _ = scorer.compute_persistence_subscore(5, 3.0)
    assert s_persist == 0.95
