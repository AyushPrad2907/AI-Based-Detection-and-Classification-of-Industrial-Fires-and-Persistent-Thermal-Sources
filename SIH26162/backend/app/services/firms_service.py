"""
SIH26162 — NASA FIRMS Data Service.

Production-grade client for ingesting active fire & thermal anomaly data from
the official NASA FIRMS (Fire Information for Resource Management System) API.

Data sources:
    - VIIRS (Suomi NPP, NOAA-20, NOAA-21 - 375m)
    - MODIS (Terra & Aqua - 1km)
    - LANDSAT (Landsat 8/9 - 30m)

API Documentation: https://firms.modaps.eosdis.nasa.gov/api/area/
"""

import asyncio
import csv
import io
import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Supported NASA FIRMS Satellite Sources
VALID_SOURCES: Tuple[str, ...] = (
    "VIIRS_SNPP_NRT",
    "VIIRS_SNPP_SP",
    "VIIRS_NOAA20_NRT",
    "VIIRS_NOAA20_SP",
    "VIIRS_NOAA21_NRT",
    "MODIS_NRT",
    "MODIS_SP",
    "LANDSAT_NRT",
)


# =============================================================================
# Custom Exception Hierarchy
# =============================================================================

class FIRMSException(Exception):
    """Base exception for NASA FIRMS client operations."""
    pass


class FIRMSValidationError(FIRMSException):
    """Raised when client-side query parameters fail validation."""
    pass


class FIRMSAPIError(FIRMSException):
    """Raised when the NASA FIRMS API returns an error response."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class FIRMSAuthenticationError(FIRMSAPIError):
    """Raised when MAP_KEY is invalid, missing, or unauthorized."""
    pass


class FIRMSQuotaExceededError(FIRMSAPIError):
    """Raised when API transaction or rate limit is exceeded."""
    pass


class FIRMSNetworkError(FIRMSException):
    """Raised when network connectivity or socket errors occur."""
    pass


class FIRMSTimeoutError(FIRMSNetworkError):
    """Raised when request times out."""
    pass


# =============================================================================
# FIRMS Service
# =============================================================================

class FIRMSService:
    """
    Production-quality NASA FIRMS API ingestion service.

    Features:
    - Area (bounding box) and Country query support
    - Satellite source validation (VIIRS, MODIS, LANDSAT)
    - Retry logic with exponential backoff for transient errors
    - Rate limit (429) & quota detection
    - Sensitive key masking in logs
    - Async and sync ingestion interfaces
    - CSV response parsing into structured records
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_backoff: Optional[float] = None,
    ):
        self.api_key = (api_key or settings.firms_api_key or "").strip()
        self.base_url = (base_url or settings.firms_base_url or "https://firms.modaps.eosdis.nasa.gov").rstrip("/")
        self.timeout = float(timeout if timeout is not None else settings.firms_timeout_seconds)
        self.max_retries = int(max_retries if max_retries is not None else settings.firms_max_retries)
        self.retry_backoff = float(retry_backoff if retry_backoff is not None else settings.firms_retry_backoff_factor)

    def _mask_key(self, key: Optional[str] = None) -> str:
        """Mask API key for safe logging."""
        k = key if key is not None else self.api_key
        if not k:
            return "<EMPTY>"
        if len(k) <= 8:
            return "***"
        return f"{k[:4]}...{k[-4:]}"

    def validate_api_key(self) -> None:
        """Verify that an API key is configured."""
        if not self.api_key or not self.api_key.isalnum():
            raise FIRMSAuthenticationError(
                "A valid NASA FIRMS MAP_KEY (alphanumeric) is required. "
                "Set FIRMS_API_KEY in your environment/.env or pass it explicitly. "
                "Get a free MAP_KEY at: https://firms.modaps.eosdis.nasa.gov/api/area/"
            )

    def validate_source(self, source: str) -> str:
        """Validate satellite source identifier."""
        normalized = source.strip().upper()
        if normalized not in VALID_SOURCES:
            valid_list = ", ".join(VALID_SOURCES)
            raise FIRMSValidationError(
                f"Invalid FIRMS source '{source}'. Must be one of: {valid_list}"
            )
        return normalized

    def validate_days(self, days: int) -> int:
        """Validate days parameter (NASA FIRMS accepts 1 to 10 days)."""
        if not isinstance(days, int) or days < 1 or days > 10:
            raise FIRMSValidationError(f"Invalid days '{days}'. NASA FIRMS supports 1 to 10 days.")
        return days

    def validate_date(self, target_date: Optional[Union[str, date, datetime]]) -> Optional[str]:
        """Validate optional target date string (YYYY-MM-DD)."""
        if target_date is None:
            return None
        if isinstance(target_date, (date, datetime)):
            return target_date.strftime("%Y-%m-%d")
        if isinstance(target_date, str):
            s = target_date.strip()
            if not s:
                return None
            try:
                parsed = datetime.strptime(s, "%Y-%m-%d")
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                raise FIRMSValidationError(
                    f"Invalid date format '{target_date}'. Expected ISO format 'YYYY-MM-DD'."
                )
        raise FIRMSValidationError(f"Unsupported date type: {type(target_date)}")

    def validate_bbox(self, bbox: Sequence[Union[int, float]]) -> Tuple[float, float, float, float]:
        """
        Validate bounding box coordinates: (min_lon, min_lat, max_lon, max_lat) / (W, S, E, N).
        """
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise FIRMSValidationError(
                f"Bounding box must contain exactly 4 coordinates (min_lon, min_lat, max_lon, max_lat). Got: {bbox}"
            )
        try:
            min_lon, min_lat, max_lon, max_lat = (float(c) for c in bbox)
        except (ValueError, TypeError) as err:
            raise FIRMSValidationError(f"Bounding box coordinates must be numeric: {err}") from err

        if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
            raise FIRMSValidationError(
                f"Longitude must be within [-180, 180]. Got min_lon={min_lon}, max_lon={max_lon}"
            )
        if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
            raise FIRMSValidationError(
                f"Latitude must be within [-90, 90]. Got min_lat={min_lat}, max_lat={max_lat}"
            )
        if min_lon > max_lon:
            raise FIRMSValidationError(
                f"min_lon ({min_lon}) cannot be greater than max_lon ({max_lon})"
            )
        if min_lat > max_lat:
            raise FIRMSValidationError(
                f"min_lat ({min_lat}) cannot be greater than max_lat ({max_lat})"
            )

        return (min_lon, min_lat, max_lon, max_lat)

    def validate_country(self, country: str) -> str:
        """Validate country code (e.g. 'IND', 'USA')."""
        c = country.strip().upper()
        if not c or not re.match(r"^[A-Z]{2,3}$", c):
            raise FIRMSValidationError(
                f"Invalid country code '{country}'. Expected ISO 2 or 3 letter code (e.g., 'IND')."
            )
        return c

    def build_area_url(
        self,
        source: str,
        bbox: Sequence[Union[int, float]],
        days: int = 1,
        target_date: Optional[Union[str, date, datetime]] = None,
    ) -> str:
        """
        Build URL for FIRMS Area (Bounding Box) CSV endpoint.
        Format: {base_url}/api/area/csv/{MAP_KEY}/{source}/{W,S,E,N}/{days}[/{date}]
        """
        self.validate_api_key()
        v_source = self.validate_source(source)
        w, s, e, n = self.validate_bbox(bbox)
        v_days = self.validate_days(days)
        v_date = self.validate_date(target_date)

        bbox_str = f"{w},{s},{e},{n}"
        if v_date:
            return f"{self.base_url}/api/area/csv/{self.api_key}/{v_source}/{bbox_str}/{v_days}/{v_date}"
        return f"{self.base_url}/api/area/csv/{self.api_key}/{v_source}/{bbox_str}/{v_days}"

    def build_country_url(
        self,
        source: str,
        country: str = "IND",
        days: int = 1,
        target_date: Optional[Union[str, date, datetime]] = None,
    ) -> str:
        """
        Build URL for FIRMS Country CSV endpoint.
        Format: {base_url}/api/country/csv/{MAP_KEY}/{source}/{country}/{days}[/{date}]
        """
        self.validate_api_key()
        v_source = self.validate_source(source)
        v_country = self.validate_country(country)
        v_days = self.validate_days(days)
        v_date = self.validate_date(target_date)

        if v_date:
            return f"{self.base_url}/api/country/csv/{self.api_key}/{v_source}/{v_country}/{v_days}/{v_date}"
        return f"{self.base_url}/api/country/csv/{self.api_key}/{v_source}/{v_country}/{v_days}"

    def _inspect_response_for_errors(self, status_code: int, text: str) -> None:
        """
        Detect FIRMS error bodies. NASA FIRMS sometimes returns error messages with 200/400/401/403.
        """
        lower_text = text.lower().strip()

        if status_code in (401, 403) or "invalid map_key" in lower_text or "bad key" in lower_text:
            raise FIRMSAuthenticationError(
                f"NASA FIRMS Authentication Failed: {text.strip()}",
                status_code=status_code,
                response_body=text,
            )

        if status_code == 429 or "transaction limit exceeded" in lower_text or "rate limit" in lower_text:
            raise FIRMSQuotaExceededError(
                f"NASA FIRMS Rate or Transaction Limit Exceeded: {text.strip()}",
                status_code=status_code,
                response_body=text,
            )

        if status_code >= 400:
            raise FIRMSAPIError(
                f"NASA FIRMS API Error (HTTP {status_code}): {text.strip()}",
                status_code=status_code,
                response_body=text,
            )

        # Some FIRMS errors return status 200 with error text body (e.g. "Error: ...")
        if lower_text.startswith("error:") or lower_text.startswith("invalid "):
            raise FIRMSAPIError(
                f"NASA FIRMS API returned error message: {text.strip()}",
                status_code=status_code,
                response_body=text,
            )

    def parse_csv_response(self, csv_text: str) -> List[Dict[str, Any]]:
        """
        Parse raw CSV text returned by FIRMS API into a list of structured dictionary records.
        """
        if not csv_text or not csv_text.strip():
            return []

        # Check for error message before parsing
        self._inspect_response_for_errors(200, csv_text)

        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        records: List[Dict[str, Any]] = []

        for row in reader:
            # Clean string keys and values
            cleaned_row = {
                (k.strip().lower() if k else ""): (v.strip() if v else "")
                for k, v in row.items()
                if k
            }
            if cleaned_row:
                records.append(cleaned_row)

        return records

    async def _execute_request_async(self, url: str) -> str:
        """
        Execute asynchronous HTTP request with exponential backoff and timeout handling.
        """
        masked_url = url.replace(self.api_key, self._mask_key()) if self.api_key else url
        logger.info(f"Initiating FIRMS API request: {masked_url}")

        attempt = 0
        backoff = 1.0

        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        timeout_config = httpx.Timeout(self.timeout, connect=10.0)

        async with httpx.AsyncClient(limits=limits, timeout=timeout_config) as client:
            while True:
                attempt += 1
                try:
                    response = await client.get(url)
                    self._inspect_response_for_errors(response.status_code, response.text)
                    logger.info(
                        f"FIRMS request succeeded (HTTP {response.status_code}, {len(response.text)} bytes)"
                    )
                    return response.text

                except (FIRMSAuthenticationError, FIRMSValidationError):
                    # Do not retry fatal client/auth errors
                    raise

                except FIRMSQuotaExceededError as err:
                    if attempt >= self.max_retries:
                        logger.error(f"Quota exceeded after {attempt} attempts: {err}")
                        raise
                    sleep_time = backoff * (self.retry_backoff ** attempt)
                    logger.warning(
                        f"Rate limit / quota encountered. Retrying in {sleep_time:.1f}s (Attempt {attempt}/{self.max_retries})..."
                    )
                    await asyncio.sleep(sleep_time)

                except (httpx.TimeoutException, FIRMSTimeoutError) as err:
                    if attempt >= self.max_retries:
                        raise FIRMSTimeoutError(
                            f"FIRMS API request timed out after {self.timeout}s on attempt {attempt}: {err}"
                        ) from err
                    sleep_time = backoff * (self.retry_backoff ** attempt)
                    logger.warning(
                        f"Request timed out. Retrying in {sleep_time:.1f}s (Attempt {attempt}/{self.max_retries})..."
                    )
                    await asyncio.sleep(sleep_time)

                except (httpx.NetworkError, httpx.TransportError) as err:
                    if attempt >= self.max_retries:
                        raise FIRMSNetworkError(
                            f"Network error connecting to NASA FIRMS on attempt {attempt}: {err}"
                        ) from err
                    sleep_time = backoff * (self.retry_backoff ** attempt)
                    logger.warning(
                        f"Network error ({err}). Retrying in {sleep_time:.1f}s (Attempt {attempt}/{self.max_retries})..."
                    )
                    await asyncio.sleep(sleep_time)

                except FIRMSAPIError as err:
                    # Retry 5xx server errors
                    if err.status_code and err.status_code >= 500 and attempt < self.max_retries:
                        sleep_time = backoff * (self.retry_backoff ** attempt)
                        logger.warning(
                            f"Server error HTTP {err.status_code}. Retrying in {sleep_time:.1f}s..."
                        )
                        await asyncio.sleep(sleep_time)
                    else:
                        raise

    def _execute_request_sync(self, url: str) -> str:
        """
        Execute synchronous HTTP request with retry logic (for CLI/scripts).
        """
        import time

        masked_url = url.replace(self.api_key, self._mask_key()) if self.api_key else url
        logger.info(f"Initiating FIRMS API sync request: {masked_url}")

        attempt = 0
        backoff = 1.0
        timeout_config = httpx.Timeout(self.timeout, connect=10.0)

        with httpx.Client(timeout=timeout_config) as client:
            while True:
                attempt += 1
                try:
                    response = client.get(url)
                    self._inspect_response_for_errors(response.status_code, response.text)
                    logger.info(
                        f"FIRMS sync request succeeded (HTTP {response.status_code}, {len(response.text)} bytes)"
                    )
                    return response.text

                except (FIRMSAuthenticationError, FIRMSValidationError):
                    raise

                except FIRMSQuotaExceededError as err:
                    if attempt >= self.max_retries:
                        raise
                    sleep_time = backoff * (self.retry_backoff ** attempt)
                    logger.warning(
                        f"Quota encountered. Retrying in {sleep_time:.1f}s (Attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(sleep_time)

                except httpx.TimeoutException as err:
                    if attempt >= self.max_retries:
                        raise FIRMSTimeoutError(
                            f"FIRMS API request timed out after {self.timeout}s on attempt {attempt}: {err}"
                        ) from err
                    sleep_time = backoff * (self.retry_backoff ** attempt)
                    logger.warning(
                        f"Request timed out. Retrying in {sleep_time:.1f}s (Attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(sleep_time)

                except (httpx.NetworkError, httpx.TransportError) as err:
                    if attempt >= self.max_retries:
                        raise FIRMSNetworkError(
                            f"Network error connecting to NASA FIRMS on attempt {attempt}: {err}"
                        ) from err
                    sleep_time = backoff * (self.retry_backoff ** attempt)
                    logger.warning(
                        f"Network error ({err}). Retrying in {sleep_time:.1f}s (Attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(sleep_time)

                except FIRMSAPIError as err:
                    if err.status_code and err.status_code >= 500 and attempt < self.max_retries:
                        sleep_time = backoff * (self.retry_backoff ** attempt)
                        time.sleep(sleep_time)
                    else:
                        raise

    # -------------------------------------------------------------------------
    # Public Async API Methods
    # -------------------------------------------------------------------------

    async def fetch_area_fires(
        self,
        bbox: Sequence[Union[int, float]],
        source: Optional[str] = None,
        days: int = 1,
        target_date: Optional[Union[str, date, datetime]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch active fire observations within a geographic bounding box asynchronously.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat) / (West, South, East, North)
            source: Satellite source (e.g. 'VIIRS_SNPP_NRT', 'MODIS_NRT')
            days: Number of days (1 to 10)
            target_date: Optional date (YYYY-MM-DD)

        Returns:
            List of parsed dictionary records.
        """
        src = source or settings.firms_default_source
        url = self.build_area_url(source=src, bbox=bbox, days=days, target_date=target_date)
        raw_csv = await self._execute_request_async(url)
        return self.parse_csv_response(raw_csv)

    async def fetch_country_fires(
        self,
        country: Optional[str] = None,
        source: Optional[str] = None,
        days: int = 1,
        target_date: Optional[Union[str, date, datetime]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch active fire observations for a country asynchronously.

        Args:
            country: ISO country code (e.g. 'IND')
            source: Satellite source (e.g. 'VIIRS_SNPP_NRT', 'MODIS_NRT')
            days: Number of days (1 to 10)
            target_date: Optional date (YYYY-MM-DD)

        Returns:
            List of parsed dictionary records.
        """
        c = country or settings.firms_default_country
        src = source or settings.firms_default_source
        url = self.build_country_url(source=src, country=c, days=days, target_date=target_date)
        raw_csv = await self._execute_request_async(url)
        return self.parse_csv_response(raw_csv)

    async def fetch_active_fires(
        self,
        country: str = "IND",
        days: int = 1,
        source: Optional[str] = None,
        target_date: Optional[Union[str, date, datetime]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convenience alias for country-based fire fetching (backward compatible).
        """
        return await self.fetch_country_fires(
            country=country,
            source=source,
            days=days,
            target_date=target_date,
        )

    # -------------------------------------------------------------------------
    # Public Synchronous API Methods (for CLI and batch jobs)
    # -------------------------------------------------------------------------

    def fetch_area_fires_sync(
        self,
        bbox: Sequence[Union[int, float]],
        source: Optional[str] = None,
        days: int = 1,
        target_date: Optional[Union[str, date, datetime]] = None,
    ) -> str:
        """
        Fetch raw CSV for bounding box synchronously.
        """
        src = source or settings.firms_default_source
        url = self.build_area_url(source=src, bbox=bbox, days=days, target_date=target_date)
        return self._execute_request_sync(url)

    def fetch_country_fires_sync(
        self,
        country: Optional[str] = None,
        source: Optional[str] = None,
        days: int = 1,
        target_date: Optional[Union[str, date, datetime]] = None,
    ) -> str:
        """
        Fetch raw CSV for country synchronously.
        """
        c = country or settings.firms_default_country
        src = source or settings.firms_default_source
        url = self.build_country_url(source=src, country=c, days=days, target_date=target_date)
        return self._execute_request_sync(url)
