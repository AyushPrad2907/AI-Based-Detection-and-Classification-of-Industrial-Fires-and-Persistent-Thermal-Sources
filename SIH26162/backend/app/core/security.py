"""
SIH26162 — Security Utilities.

Contains authentication, authorization, and API key validation logic.
"""
import time
from typing import Dict, Tuple

from fastapi import HTTPException, Security, status, Request
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    if settings.api_key == "":
        return None
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate API key"
        )
    return api_key

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, Tuple[int, float]] = {}

    def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        # Cleanup old entries
        for ip in list(self.requests.keys()):
            if now - self.requests[ip][1] > 60:
                del self.requests[ip]
                
        count, start_time = self.requests.get(client_ip, (0, now))
        if now - start_time > 60:
            count = 0
            start_time = now
            
        if count >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Too many requests")
            
        self.requests[client_ip] = (count + 1, start_time)
        return True

rate_limit = RateLimiter(60)
