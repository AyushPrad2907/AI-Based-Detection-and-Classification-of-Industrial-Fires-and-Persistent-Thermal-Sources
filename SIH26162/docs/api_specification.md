# API Specification

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### Health
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/health/` | Service health check | Working |

### Fire Detection
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/fires/` | List fire detections | Placeholder |
| GET | `/fires/{id}` | Get fire detection details | Placeholder |

### Thermal Sources
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/thermal/` | List thermal sources | Placeholder |

### Geospatial
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/geospatial/` | Geospatial queries | Placeholder |

## Interactive Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
