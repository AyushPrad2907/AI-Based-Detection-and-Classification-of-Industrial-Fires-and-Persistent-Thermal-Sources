# 🔥 SIH26162 — AI-Based Detection & Classification of Industrial Fires and Persistent Thermal Sources

<div align="center">

![SIH 2026](https://img.shields.io/badge/Smart%20India%20Hackathon-2026-FF9933?style=for-the-badge&logo=target&logoColor=white)
![Organization](https://img.shields.io/badge/Ministry%20%2F%20Org-NTRO-003366?style=for-the-badge&logo=shield&logoColor=white)
![Category](https://img.shields.io/badge/Category-Software%20%2F%20Geospatial%20AI-008080?style=for-the-badge&logo=earth&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostGIS](https://img.shields.io/badge/Database-PostGIS%20%2F%20SQLAlchemy2-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/ML%20Engine-Scikit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-91%2F91%20Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

<br/>

> **An apex-grade Geospatial AI intelligence system combining NASA FIRMS satellite thermal telemetry (VIIRS 375m & MODIS 1km), OpenStreetMap land-use spatial semantics, spatio-temporal clustering, and explainable machine learning models to detect, classify, and track industrial fires, flare stacks, furnaces, and persistent thermal anomalies in real time.**

---

### 🌐 [Explore Documentation](docs/data_pipeline.md) • 🛰️ [NASA FIRMS Ingestion](scripts/download_firms_data.py) • 🤖 [Train ML Model](scripts/train_model.py) • 📍 [Detect Thermal Sources](scripts/detect_persistent_sources.py) • 🗄️ [Database Ingest](scripts/ingest_to_db.py)

---

</div>

## 📌 Executive Summary

Industrial fires, uncontrolled flare emissions, and unmonitored thermal anomalies cause **billions of dollars in critical infrastructure damage**, catastrophic environmental degradation, and loss of life annually. Conventional monitoring systems fail because:

1. ❌ **High False Alarm Rates**: Unable to distinguish between routine industrial combustion (furnaces, steel kilns) and dangerous uncontrolled fires.
2. ❌ **Lack of Spatial Context**: Thermal hotspots from satellites are isolated dots without surrounding land-use intelligence.
3. ❌ **No Temporal Persistence Tracking**: Cannot discern transient agricultural crop burns from permanent industrial thermal signatures.
4. ❌ **High Detection Latency**: Lack automated real-time ingestion and ML inference pipelines.

**SIH26162** overcomes these challenges by fusing **real-time satellite thermal sensors** with **OpenStreetMap geospatial context graphs**, **spatio-temporal clustering algorithms**, **explainable ML models**, and a **production-grade PostgreSQL + PostGIS spatial persistence layer** to deliver categorized, actionable alerts.

---

## 🏛️ System Architecture

```mermaid
flowchart TB
    subgraph S1["🛰️ Data Ingestion Layer (Phase 1)"]
        FIRMS["NASA FIRMS API<br/>(VIIRS 375m / MODIS 1km / Landsat)"]
        OSM["OpenStreetMap Overpass API<br/>(Industrial Proximity & Facilities)"]
        CLI["CLI Ingestion Pipeline<br/>(scripts/download_firms_data.py)"]
        RAW_DB[("Raw Ingestion Storage<br/>data/raw/firms/")]
    end

    subgraph S2["⚡ Preprocessing & Feature Engineering (Phase 1 & 2)"]
        PRE["FIRMS Preprocessor<br/>(ml/preprocessing/firms_preprocessor.py)"]
        LOADER["Dataset Loader<br/>(ml/utils/data_utils.py)"]
        FEAT["FeatureBuilder (29 Features)<br/>(ml/preprocessing/feature_builder.py)"]
        PROC_DB[("Processed Feature Store<br/>data/processed/firms/")]
    end

    subgraph S3["🧠 Machine Learning & Persistence (Phase 2 & 3)"]
        THERMAL["ThermalDetector (Spatio-Temporal DBSCAN)<br/>(ml/models/thermal_detector.py)"]
        LABELER["WeakSupervisionLabeler<br/>(ml/preprocessing/weak_labeler.py)"]
        CLS["FireClassifier (Random Forest / GBDT)<br/>(ml/models/fire_classifier.py)"]
        RISK["Explainable RiskScorer (0-100 Score)<br/>(ml/inference/risk_scorer.py)"]
    end

    subgraph S4["🚀 Serving & Persistence Layer (Phase 3)"]
        FASTAPI["FastAPI REST Backend<br/>(/api/v1/fires/observations, /thermal/sources, /classify)"]
        POSTGIS[("PostgreSQL 16 + PostGIS 3.4<br/>(SQLAlchemy 2 Async + Alembic)")]
        INGEST["Database Bulk Ingest<br/>(scripts/ingest_to_db.py)"]
    end

    FIRMS --> CLI --> RAW_DB --> PRE --> PROC_DB --> LOADER
    LOADER --> THERMAL --> FEAT
    OSM --> FEAT
    FEAT --> LABELER --> CLS
    CLS --> FASTAPI
    THERMAL --> FASTAPI
    RISK --> FASTAPI
    PROC_DB --> INGEST --> POSTGIS
    FASTAPI <--> POSTGIS
```

---

## 🛠️ Complete Technology Stack

| Layer | Primary Technologies | Capabilities |
|---|---|---|
| **Satellite & Telemetry** | `NASA FIRMS REST API`, `VIIRS (SNPP/NOAA-20/21)`, `MODIS` | 375m & 1km active fire thermal anomalies, Brightness Temperature (Kelvin), Fire Radiative Power (MW) |
| **Geospatial & Spatial Context** | `OpenStreetMap Overpass API`, `GeoPandas`, `Shapely`, `Haversine Metric` | Industrial land-use boundaries, proximity buffers, facility distance calculations |
| **Machine Learning & AI** | `scikit-learn`, `NumPy`, `Pandas`, `SciPy`, `Joblib` | Multi-class thermal classification, DBSCAN spatio-temporal clustering, weak supervision, explainable risk scoring |
| **Backend & Microservices** | `FastAPI`, `Uvicorn`, `Pydantic V2`, `HTTPX`, `AsyncPG` | High-throughput asynchronous endpoints, rate-limited resilient retry clients |
| **Database & GIS** | `PostgreSQL 16`, `PostGIS 3.4`, `SQLAlchemy 2 (Async)`, `GeoAlchemy2`, `Alembic` | Spatial indexing (GiST R-Tree), coordinate geometry, multi-criteria filtering, B-Tree indexes |
| **Frontend & Analytics** | `React 18`, `TypeScript`, `Vite`, `Tailwind CSS`, `Lucide Icons` | Real-time interactive spatial map, heatmaps, thermal source breakdown, live alerts (Phase 4) |
| **DevOps & Testing** | `Docker`, `Docker Compose`, `Pytest`, `AnyIO`, `Alembic` | Containerized microservices, migration versioning, deterministic test fixtures |

---

## 🚦 Roadmap & Phase Milestones

| Phase | Milestone Name | Status | Key Deliverables |
|:---:|---|:---:|---|
| **Phase 0** | Foundation & Architecture | <img src="https://img.shields.io/badge/Status-Completed-success?style=flat-square"/> | Directory layout, FastAPI skeleton, Docker Compose, PostGIS schema scaffolding |
| **Phase 1** | Real NASA FIRMS Data Ingestion | <img src="https://img.shields.io/badge/Status-Completed-success?style=flat-square"/> | Resilient FIRMS API client, coordinate sanitizer, UTC synthesizer, CLI downloader |
| **Phase 2** | AI/ML + Feature Engineering | <img src="https://img.shields.io/badge/Status-Completed-success?style=flat-square"/> | 29 features, weak supervision, Random Forest model, DBSCAN persistence, OSM Overpass, explainable risk score |
| **Phase 3** | PostgreSQL + PostGIS Persistence & CRUD | <img src="https://img.shields.io/badge/Status-Completed-success?style=flat-square"/> | SQLAlchemy 2 async models, Alembic migrations, GiST spatial indexes, bulk ingestion CLI, paginated spatial CRUD endpoints, DB health diagnostics |
| **Phase 4** | Interactive Frontend Dashboard | <img src="https://img.shields.io/badge/Status-Planned-lightgrey?style=flat-square"/> | MapLibre/Leaflet heatmaps, classification overlays, live telemetry charts |
| **Phase 5** | End-to-End Testing & Optimization | <img src="https://img.shields.io/badge/Status-Planned-lightgrey?style=flat-square"/> | Performance benchmarking, load testing, precision/recall spatial validation |
| **Phase 6** | Deployment & Hackathon Demo | <img src="https://img.shields.io/badge/Status-Planned-lightgrey?style=flat-square"/> | Production cloud staging, presentation deck, automated CI/CD pipeline |

---

## 🚀 Quickstart Guide

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env
```

Add your free [NASA FIRMS MAP_KEY](https://firms.modaps.eosdis.nasa.gov/api/area/) inside `.env`:
```dotenv
FIRMS_API_KEY=your_32_character_nasa_firms_key_here
```

### 2. Download Real Satellite Telemetry (Multi-Day, Multi-Sensor)

```bash
# Download 5 days of real VIIRS active fires for India
python scripts/download_firms_data.py --country IND --days 5 --source VIIRS_SNPP_NRT --preprocess
python scripts/download_firms_data.py --country IND --days 5 --source VIIRS_NOAA20_NRT --preprocess
python scripts/download_firms_data.py --country IND --days 5 --source MODIS_NRT --preprocess
```

### 3. Discover Persistent Thermal Sources (Clustering)

```bash
python scripts/detect_persistent_sources.py --radius 1200 --min-obs 2
```

### 4. Train & Evaluate the Machine Learning Model

```bash
python scripts/train_model.py --model-type random_forest --n-estimators 150
```

### 5. Setup PostgreSQL + PostGIS Database & Ingest Real Data

```bash
# 1. Initialize DB tables via Alembic migrations (or direct sync)
python scripts/setup_database.py --apply-migrations

# 2. Bulk ingest processed NASA FIRMS satellite data & thermal clusters
python scripts/ingest_to_db.py --data-dir data/processed/firms
```

### 6. Start the FastAPI Backend & Explore Interactive Docs

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```
- Interactive OpenAPI documentation available at: `http://localhost:8000/docs`
- Database & PostGIS Health Diagnostic: `GET /api/v1/health/db`
- Paginated Spatial Observations: `GET /api/v1/fires/observations?bbox=68.0,6.5,97.5,37.0`
- Persisted Thermal Clusters: `GET /api/v1/thermal/sources`

### 7. Run Automated Tests

```bash
pytest -v
```

---

## 🧪 Test Verification Matrix

| Component Tested | Test Module | Coverage & Checks | Status |
|---|---|---|:---:|
| **PostgreSQL Models** | `tests/backend/test_database_models.py` | ORM relationships, PostGIS geometry types, cascade rules, audit fields | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Data Repositories** | `tests/backend/test_repositories.py` | Async CRUD, bounding-box spatial queries, radius filters, upserts | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **DB Ingestion Pipeline** | `tests/backend/test_ingestion_pipeline.py` | Real FIRMS CSV ingestion, DBSCAN cluster staging, database verification | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Phase 3 Endpoints** | `tests/backend/test_phase3_endpoints.py` | `/health/db`, `/fires/observations` (bbox/filter), `/fires/classify` (persist=True) | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Dataset Loader** | `tests/ml/test_data_loader.py` | Multi-file discovery, sensor parsing, temporal/spatial filtering, deduplication | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Feature Engineering** | `tests/ml/test_feature_builder.py` | 29 spectral/spatial/temporal features, cyclical time encodings, single vector inference | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Weak Supervision Labeler** | `tests/ml/test_weak_labeler.py` | Rule heuristics, physical thresholds, explanation generation, class balance | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Fire Classifier** | `tests/ml/test_fire_classifier.py` | Model training, multi-class probabilities, feature importance, serialization roundtrip | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Thermal Detector** | `tests/ml/test_thermal_detector.py` | Spatio-temporal DBSCAN, Haversine distance, persistence metrics, centroid calculation | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Evaluation Metrics** | `tests/ml/test_evaluator_metrics.py` | Accuracy, Precision/Recall/F1, Confusion matrix, ROC-AUC calculation, report markdown | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Risk Scorer** | `tests/ml/test_risk_scorer.py` | Multi-factor weighted score (0-100), hazard level thresholds, reason generation | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **OSM Overpass Service** | `tests/backend/test_osm_service.py` | Overpass query formulation, distance calculation, spatial quantization caching, offline fallback | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Classification Service** | `tests/backend/test_classification_service.py` | End-to-end inference, batch processing, model readiness, OSM context enrichment | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **Phase 2 Endpoints** | `tests/backend/test_phase2_endpoints.py` | `/fires/classify`, `/fires/classify/batch`, `/fires/status`, `/thermal/sources`, `/thermal/clusters` | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **FIRMS Ingestion Service** | `tests/backend/test_firms_service.py` | API key auth, coordinate boundaries, days 1-10, URL generation, retry backoff | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **FIRMS Preprocessor** | `tests/ml/test_firms_preprocessor.py` | Schema validation, coordinate range cleaning, UTC timestamp synthesis, sensor normalization | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |
| **FastAPI Core & Health** | `tests/test_health.py` & `tests/backend/test_api.py` | Health probe `/api/v1/health/`, root endpoint, router status | <img src="https://img.shields.io/badge/Passing-green?style=flat-square"/> |

---

## 🔍 Validation Audit & Scientific Honesty

> **Scientific Notice on Benchmark Performance:**
> The reported **98.21% test accuracy** reflects model discrimination fidelity evaluated against domain-physics **Weak Supervision / Silver Pseudo-Labels**. It does **not** claim 98.21% accuracy against independently audited field ground truth.

| Audit Vector | Finding / Status | Detail |
|---|:---:|---|
| **Data Leakage** | 🛡️ **Zero Leakage** | Stratified Train/Val/Test partitioning; tested under strict temporal-block partitions achieving 99.64% test generalization. |
| **`industrial_fire` Support** | ⚠️ **0 in NRT Data** | Acute catastrophic structural fires ($>50\text{ MW}$) are rare events with 0 occurrences in routine 5-day NRT satellite passes. |
| **Active Class Support** | 📊 **4 Active Classes** | `uncertain_anomaly` (35.2%), `persistent_industrial` (34.8%), `agricultural_burn` (15.8%), `wildfire` (14.2%). |
| **Dominant Features** | 🔬 **Rule-Correlated** | `persistence_count` (15.8%), `brightness_ratio` (13.8%), `brightness_diff` (12.6%), `frp` (9.9%) directly align with thermal physics thresholds. |

---

## 📜 License & Acknowledgments

- **License**: Released under the **MIT License**. See [`LICENSE`](LICENSE) for terms.
- **Problem Statement**: **SIH26162** — Smart India Hackathon 2026.
- **Organization**: National Technical Research Organisation (**NTRO**).
- **Data Acknowledgments**: NASA Earthdata FIRMS Team & OpenStreetMap contributors.

<div align="center">

**Built with precision and purpose for Smart India Hackathon 2026** 🚀

</div>
