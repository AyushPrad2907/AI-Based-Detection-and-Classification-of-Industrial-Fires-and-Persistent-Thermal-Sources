# System Architecture

## Overview

The SIH26162 system follows a modular, layered architecture designed for scalability and maintainability.

## Components

### 1. Data Ingestion Layer
- **NASA FIRMS Client**: Fetches active fire/thermal data via REST API
- **OSM Client**: Queries OpenStreetMap via Overpass API
- **Satellite Downloader**: Retrieves Sentinel-2/Landsat imagery

### 2. Preprocessing Layer
- Data cleaning and validation
- Feature extraction (spatial, temporal, spectral)
- Feature engineering for ML model input

### 3. ML Pipeline
- Model training with PyTorch
- Hyperparameter optimization
- Model evaluation and selection
- Inference engine for real-time predictions

### 4. Backend API (FastAPI)
- RESTful API with versioned endpoints (v1)
- Async database operations with SQLAlchemy
- Service layer pattern for business logic

### 5. Database (PostgreSQL + PostGIS)
- Spatial data storage with PostGIS extension
- Efficient geospatial queries
- Historical data archival

### 6. Frontend (React + Vite)
- Interactive map dashboard
- Real-time fire/thermal source visualization
- Alert management interface

## Data Flow

```
NASA FIRMS API --> Data Ingestion --> Preprocessing --> Feature Engineering
                                                              |
                                                              v
OSM Overpass API --> Data Ingestion --> Context Data --> ML Model Inference
                                                              |
                                                              v
Satellite Imagery --> Preprocessing --> Spectral Data --> Classification Results
                                                              |
                                                              v
                                                     PostgreSQL + PostGIS
                                                              |
                                                              v
                                                     FastAPI REST API
                                                              |
                                                              v
                                                     React Dashboard
```
