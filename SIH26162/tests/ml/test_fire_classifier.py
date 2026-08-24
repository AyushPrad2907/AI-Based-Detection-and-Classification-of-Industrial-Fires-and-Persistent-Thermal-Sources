"""
SIH26162 — Unit Tests for Fire Classifier Model.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from ml.models.fire_classifier import FireClassifier


@pytest.fixture
def dummy_train_val_data():
    np.random.seed(42)
    classes = ["persistent_industrial", "industrial_fire", "wildfire", "agricultural_burn", "uncertain_anomaly"]
    rows = []
    for i in range(100):
        cls = classes[i % len(classes)]
        rows.append({
            "latitude": 20.0 + np.random.randn() * 2,
            "longitude": 78.0 + np.random.randn() * 2,
            "brightness_primary": 310.0 + np.random.rand() * 50,
            "brightness_secondary": 290.0 + np.random.rand() * 20,
            "frp": np.random.rand() * 60,
            "confidence_score": 40.0 + np.random.rand() * 60,
            "acq_datetime": "2026-08-24 12:00:00",
            "daynight": "D" if np.random.rand() > 0.5 else "N",
            "weak_label": cls,
        })
    df = pd.DataFrame(rows)
    return df.iloc[:80], df.iloc[80:]


def test_fire_classifier_train_and_predict(dummy_train_val_data, tmp_path):
    train_df, test_df = dummy_train_val_data

    clf = FireClassifier(model_type="random_forest", n_estimators=30, random_state=42)
    metrics = clf.train(train_data=train_df, val_data=test_df)

    assert clf.is_fitted is True
    assert "train_accuracy" in metrics
    assert "val_accuracy" in metrics

    # Test batch predictions
    preds = clf.predict(test_df)
    assert len(preds) == len(test_df)
    assert all(isinstance(p, str) for p in preds)

    # Test probability matrix
    probs = clf.predict_proba(test_df)
    assert probs.shape[0] == len(test_df)
    assert np.allclose(probs.sum(axis=1), 1.0)

    # Test single observation prediction
    single_res = clf.predict_single(test_df.iloc[0].to_dict())
    assert "predicted_class" in single_res
    assert "confidence" in single_res
    assert "class_probabilities" in single_res

    # Test feature importances
    imp = clf.get_feature_importances()
    assert isinstance(imp, dict)
    assert len(imp) > 0

    # Test serialization roundtrip
    model_file = tmp_path / "test_model.joblib"
    clf.save(model_file)
    assert model_file.exists()

    clf_loaded = FireClassifier()
    clf_loaded.load(model_file)
    assert clf_loaded.is_fitted is True

    loaded_preds = clf_loaded.predict(test_df)
    assert np.array_equal(preds, loaded_preds)
