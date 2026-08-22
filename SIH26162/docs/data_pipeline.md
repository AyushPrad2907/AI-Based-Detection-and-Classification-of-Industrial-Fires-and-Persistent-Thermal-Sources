# Data Pipeline

## Overview

The data pipeline transforms raw geospatial data into classified fire/thermal detections.

## Pipeline Stages

### Stage 1: Data Ingestion
- **Source**: NASA FIRMS API (VIIRS/MODIS)
- **Format**: CSV with columns: latitude, longitude, brightness, confidence, frp, acq_date
- **Frequency**: Configurable (daily, hourly for NRT data)

### Stage 2: Context Enrichment
- **Source**: OpenStreetMap Overpass API
- **Purpose**: Add land-use context (industrial, residential, forest, agricultural)
- **Radius**: 1km around each thermal detection

### Stage 3: Satellite Data Processing
- **Source**: Sentinel-2 / Landsat-8/9
- **Bands**: SWIR, NIR, Thermal infrared
- **Indices**: NDVI, NBR (for burn severity)

### Stage 4: Feature Engineering
- Combine FIRMS + OSM + satellite features
- Generate temporal features (time patterns)
- Create spatial features (clustering, proximity)

### Stage 5: ML Inference
- Load trained classification model
- Run inference on feature vectors
- Output: class label + confidence score

### Stage 6: Storage & Serving
- Store results in PostGIS database
- Serve via FastAPI REST endpoints
- Push alerts for high-confidence detections
