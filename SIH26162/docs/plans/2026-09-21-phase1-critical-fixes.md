# Phase I Critical PS Compliance Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve the 0-sample `industrial_fire` training deficit via physics-informed synthetic generation and retrained 5-class model artifacts, and embed live Sentinel-2 cloudless / ESRI optical satellite raster tile layers directly inside Leaflet.

**Architecture:** Refactor `WeakSupervisionLabeler` to prevent night-pass shadowing of acute industrial thermal spikes, engineer a physics-informed `SyntheticFireGenerator` using real Indian industrial facility locations (from `data/industrial_facilities_india.json`), retrain `FireClassifier` to serialize a complete 5-class model artifact, and extend `CommandCenterMap.tsx` with high-resolution Copernicus Sentinel-2 and ESRI Satellite tile layers.

**Tech Stack:** Python 3.10, scikit-learn, pandas, numpy, joblib, React 18, Leaflet, TypeScript, Vite, Tailwind CSS.

---

### Task 1: Refactor WeakSupervisionLabeler Rule Priority

**Files:**
- Modify: `ml/preprocessing/weak_labeler.py:80-110`
- Test: `tests/ml/test_weak_labeler.py`

**Step 1: Write the failing test**
Create a test that asserts an observation within 1km of an industrial site with FRP >= 80 MW at night is classified as `industrial_fire` (currently it is shadowed and misclassified as `persistent_industrial`).

**Step 2: Run test to verify it fails**
Run: `py -m pytest tests/ml/test_weak_labeler.py -k test_acute_industrial_fire_at_night -v`
Expected: FAIL (returns `persistent_industrial` due to night condition in Rule 2)

**Step 3: Write minimal implementation**
Adjust `ml/preprocessing/weak_labeler.py` so Rule 3 (`industrial_fire`: acute thermal spike `frp >= self.acute_fire_frp_threshold_mw` near industrial facility) is evaluated prior to routine `persistent_industrial` classification.

**Step 4: Run test to verify it passes**
Run: `py -m pytest tests/ml/test_weak_labeler.py -v`
Expected: PASS

**Step 5: Commit**
Run: `git commit -m "fix(ml): prioritize acute industrial fire rule over persistent nocturnal flaring"`

---

### Task 2: Implement Physics-Informed Synthetic Industrial Fire Generator

**Files:**
- Create: `ml/preprocessing/synthetic_generator.py`
- Test: `tests/ml/test_synthetic_generator.py`

**Step 1: Write the failing test**
Assert generator produces valid FIRMS-compliant observations co-located with Indian facilities having FRP >= 60 MW, `dist_to_industrial_km` <= 2.0 km, and classified by `WeakSupervisionLabeler` as `industrial_fire`.

**Step 2: Run test to verify it fails**
Run: `py -m pytest tests/ml/test_synthetic_generator.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Implement SyntheticFireGenerator**
Generate ~150 synthetic samples based on satellite combustion physics:
- High FRP (60 to 350 MW, log-normal distribution)
- Primary brightness 345K to 395K
- Bounding locations within 0.1km - 1.5km of real Indian refineries/power/steel complexes
- Export to `data/processed/firms/firms_synthetic_industrial_fire_processed.csv`

**Step 4: Run test to verify it passes**
Run: `py -m pytest tests/ml/test_synthetic_generator.py -v`
Expected: PASS

**Step 5: Commit**
Run: `git commit -m "feat(ml): add physics-informed synthetic industrial fire generator"`

---

### Task 3: Retrain FireClassifier & Update 5-Class Evaluation Artifacts

**Files:**
- Modify: `scripts/train_model.py`
- Artifacts: `ml/saved_models/fire_classifier.joblib`, `ml/saved_models/reports/test_evaluation_report.json`, `ml/saved_models/training_summary.json`
- Test: `tests/ml/test_model_pipeline.py`

**Step 1: Execute Retraining CLI**
Run: `py scripts/train_model.py --model-type random_forest --n-estimators 150`
Expected: Training completes with 5 distinct classes: `agricultural_burn`, `industrial_fire`, `persistent_industrial`, `uncertain_anomaly`, `wildfire`.

**Step 2: Verify Artifact Class Support**
Verify `test_evaluation_report.json` contains `industrial_fire` with support > 0 and F1-score >= 0.90.

**Step 3: Run full backend test suite**
Run: `py -m pytest tests/ -v`
Expected: All 50+ tests PASS.

**Step 4: Commit**
Run: `git commit -m "feat(ml): retrain classifier with 5-class support including industrial_fire"`

---

### Task 4: Embed Sentinel-2 Cloudless & HD Satellite Tile Layers in Leaflet

**Files:**
- Modify: `frontend/src/components/dashboard/CommandCenterMap.tsx`
- Modify: `frontend/src/components/dashboard/DetailPanel.tsx`

**Step 1: Extend Basemap Configs in CommandCenterMap.tsx**
Add:
- `satellite`: Esri World Imagery (high-resolution true-color satellite)
- `sentinel`: EOx Sentinel-2 Cloudless true-color optical layer
- Update layer toggle UI with `Dark | Satellite | Sentinel-2 | Street` pill selector.

**Step 2: Add Visual Direct Link & Inspection in DetailPanel.tsx**
Add a quick-switch button to toggle map directly to Sentinel-2/Satellite view focused on the selected anomaly.

**Step 3: Test Frontend Build**
Run: `npm run build` inside `frontend/`
Expected: Build succeeds with 0 TypeScript/CSS errors.

**Step 4: Commit**
Run: `git commit -m "feat(frontend): embed Sentinel-2 cloudless and Esri satellite tile layers in Leaflet"`

---

### Task 5: End-to-End System & PS Compliance Verification

**Files:**
- Verify: Full backend test suite (`py -m pytest`)
- Verify: ML inference determinism (`py scripts/verify_determinism.py`)
- Verify: Frontend production build (`npm run build`)

**Step 1: Run comprehensive verification**
Run verification commands and check outputs.

**Step 2: Update README with updated class distribution audit**
Document the scientific rationale and 5-class metrics.

**Step 3: Final Commit & Summary**
Run: `git commit -m "docs: update audit matrix and PS compliance report for Phase I"`
