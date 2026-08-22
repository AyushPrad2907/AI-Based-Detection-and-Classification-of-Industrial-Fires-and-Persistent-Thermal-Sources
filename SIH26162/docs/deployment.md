# Deployment Guide

## Development Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Docker Deployment

```bash
cp .env.example .env
# Edit .env with production values
docker-compose up --build -d
```

## Production Considerations (Future)
- Use HTTPS with proper SSL certificates
- Restrict CORS origins to frontend domain
- Use environment-specific .env files
- Set up database backups
- Configure monitoring and logging
- Use a reverse proxy (Nginx) in front of services
