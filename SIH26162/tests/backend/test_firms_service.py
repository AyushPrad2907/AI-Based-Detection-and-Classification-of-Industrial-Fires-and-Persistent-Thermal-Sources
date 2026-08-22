"""
SIH26162 — Unit & Integration Tests for NASA FIRMS Service.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.firms_service import (
    FIRMSAPIError,
    FIRMSAuthenticationError,
    FIRMSException,
    FIRMSNetworkError,
    FIRMSQuotaExceededError,
    FIRMSService,
    FIRMSTimeoutError,
    FIRMSValidationError,
    VALID_SOURCES,
)


@pytest.fixture
def mock_service():
    """Create FIRMSService instance with test credentials."""
    return FIRMSService(
        api_key="abcdef1234567890abcdef1234567890",
        base_url="https://firms.modaps.eosdis.nasa.gov",
        timeout=5.0,
        max_retries=2,
        retry_backoff=1.1,
    )


class TestFIRMSServiceValidation:
    """Test parameter validation rules."""

    def test_validate_api_key_valid(self, mock_service):
        mock_service.validate_api_key()  # Should not raise

    def test_validate_api_key_missing(self):
        service = FIRMSService(api_key="")
        with pytest.raises(FIRMSAuthenticationError, match="valid NASA FIRMS MAP_KEY"):
            service.validate_api_key()

    def test_validate_source_valid(self, mock_service):
        for src in VALID_SOURCES:
            assert mock_service.validate_source(src) == src
            assert mock_service.validate_source(src.lower()) == src

    def test_validate_source_invalid(self, mock_service):
        with pytest.raises(FIRMSValidationError, match="Invalid FIRMS source"):
            mock_service.validate_source("INVALID_SATELLITE_NAME")

    def test_validate_days_valid(self, mock_service):
        for d in range(1, 11):
            assert mock_service.validate_days(d) == d

    def test_validate_days_invalid(self, mock_service):
        with pytest.raises(FIRMSValidationError):
            mock_service.validate_days(0)
        with pytest.raises(FIRMSValidationError):
            mock_service.validate_days(11)
        with pytest.raises(FIRMSValidationError):
            mock_service.validate_days("1")  # type: ignore

    def test_validate_date_valid(self, mock_service):
        assert mock_service.validate_date(None) is None
        assert mock_service.validate_date("2024-05-18") == "2024-05-18"
        assert mock_service.validate_date(date(2024, 5, 18)) == "2024-05-18"

    def test_validate_date_invalid(self, mock_service):
        with pytest.raises(FIRMSValidationError, match="Invalid date format"):
            mock_service.validate_date("18-05-2024")
        with pytest.raises(FIRMSValidationError, match="Invalid date format"):
            mock_service.validate_date("not-a-date")

    def test_validate_bbox_valid(self, mock_service):
        bbox = (68.0, 6.0, 97.0, 37.0)
        w, s, e, n = mock_service.validate_bbox(bbox)
        assert (w, s, e, n) == (68.0, 6.0, 97.0, 37.0)

    def test_validate_bbox_invalid_ranges(self, mock_service):
        # Lat out of range
        with pytest.raises(FIRMSValidationError, match="Latitude must be within"):
            mock_service.validate_bbox((68.0, -95.0, 97.0, 37.0))
        # Lon out of range
        with pytest.raises(FIRMSValidationError, match="Longitude must be within"):
            mock_service.validate_bbox((-190.0, 6.0, 97.0, 37.0))
        # West > East
        with pytest.raises(FIRMSValidationError, match="cannot be greater than max_lon"):
            mock_service.validate_bbox((100.0, 6.0, 70.0, 37.0))
        # South > North
        with pytest.raises(FIRMSValidationError, match="cannot be greater than max_lat"):
            mock_service.validate_bbox((68.0, 40.0, 97.0, 10.0))
        # Invalid length
        with pytest.raises(FIRMSValidationError, match="exactly 4 coordinates"):
            mock_service.validate_bbox((68.0, 6.0, 97.0))

    def test_validate_country_valid(self, mock_service):
        assert mock_service.validate_country("ind") == "IND"
        assert mock_service.validate_country("USA") == "USA"

    def test_validate_country_invalid(self, mock_service):
        with pytest.raises(FIRMSValidationError):
            mock_service.validate_country("INDIA_LONG")
        with pytest.raises(FIRMSValidationError):
            mock_service.validate_country("1")


class TestFIRMSURLBuilder:
    """Test official NASA FIRMS URL construction."""

    def test_build_area_url(self, mock_service):
        url = mock_service.build_area_url(
            source="VIIRS_SNPP_NRT",
            bbox=(68.0, 6.0, 97.0, 37.0),
            days=2,
            target_date="2024-05-18",
        )
        expected = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/abcdef1234567890abcdef1234567890/VIIRS_SNPP_NRT/68.0,6.0,97.0,37.0/2/2024-05-18"
        assert url == expected

    def test_build_country_url(self, mock_service):
        # Known country with bounding box mapping (e.g. IND)
        url_ind = mock_service.build_country_url(
            source="MODIS_NRT",
            country="IND",
            days=1,
        )
        expected_ind = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/abcdef1234567890abcdef1234567890/MODIS_NRT/68.0,6.0,97.0,37.0/1"
        assert url_ind == expected_ind

        # Fallback country without pre-defined bounding box
        url_other = mock_service.build_country_url(
            source="MODIS_NRT",
            country="XYZ",
            days=1,
        )
        expected_other = "https://firms.modaps.eosdis.nasa.gov/api/country/csv/abcdef1234567890abcdef1234567890/MODIS_NRT/XYZ/1"
        assert url_other == expected_other


    def test_key_masking(self, mock_service):
        masked = mock_service._mask_key()
        assert masked == "abcd...7890"
        assert "1234567890abcdef" not in masked


class TestFIRMSResponseParsing:
    """Test parsing and error inspection of FIRMS CSV payloads."""

    def test_parse_valid_viirs_csv(self, mock_service):
        raw_csv = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight
28.6139,77.2090,345.2,0.38,0.36,2024-05-18,0730,N,VIIRS,nominal,2.0NRT,298.4,12.5,D
19.0760,72.8777,330.1,0.40,0.37,2024-05-18,0730,N,VIIRS,high,2.0NRT,295.0,8.2,D
"""
        records = mock_service.parse_csv_response(raw_csv)
        assert len(records) == 2
        assert records[0]["latitude"] == "28.6139"
        assert records[0]["longitude"] == "77.2090"
        assert records[0]["bright_ti4"] == "345.2"
        assert records[0]["confidence"] == "nominal"
        assert records[1]["confidence"] == "high"

    def test_parse_empty_csv(self, mock_service):
        assert mock_service.parse_csv_response("") == []
        assert mock_service.parse_csv_response("   \n  ") == []

    def test_parse_invalid_key_error_in_body(self, mock_service):
        with pytest.raises(FIRMSAuthenticationError, match="Authentication Failed"):
            mock_service.parse_csv_response("Invalid MAP_KEY")

    def test_parse_quota_exceeded_error_in_body(self, mock_service):
        with pytest.raises(FIRMSQuotaExceededError, match="Limit Exceeded"):
            mock_service.parse_csv_response("Transaction limit exceeded for today.")

    def test_inspect_response_http_errors(self, mock_service):
        with pytest.raises(FIRMSAuthenticationError):
            mock_service._inspect_response_for_errors(401, "Unauthorized")

        with pytest.raises(FIRMSQuotaExceededError):
            mock_service._inspect_response_for_errors(429, "Too Many Requests")

        with pytest.raises(FIRMSAPIError):
            mock_service._inspect_response_for_errors(500, "Internal Server Error")


class TestFIRMSServiceNetworkCalls:
    """Test async and sync execution with mocked network transport."""

    @pytest.mark.anyio
    async def test_fetch_country_fires_async_success(self, mock_service):
        csv_data = "latitude,longitude,bright_ti4,acq_date,acq_time,confidence\n28.61,77.20,340.0,2024-05-18,0600,n\n"

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = csv_data
            mock_get.return_value = mock_resp

            records = await mock_service.fetch_country_fires(country="IND", days=1)
            assert len(records) == 1
            assert records[0]["latitude"] == "28.61"
            assert records[0]["confidence"] == "n"

    def test_fetch_area_fires_sync_success(self, mock_service):
        csv_data = "latitude,longitude,brightness,acq_date,acq_time,confidence\n22.57,88.36,315.0,2024-05-18,0500,85\n"

        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = csv_data
            mock_get.return_value = mock_resp

            result_csv = mock_service.fetch_area_fires_sync(
                bbox=(68.0, 6.0, 97.0, 37.0), days=1
            )
            assert "22.57,88.36,315.0" in result_csv

    def test_fetch_sync_timeout_error(self, mock_service):
        with patch("httpx.Client.get", side_effect=httpx.TimeoutException("Read timed out")):
            with pytest.raises(FIRMSTimeoutError, match="timed out"):
                mock_service.fetch_country_fires_sync(country="IND")

    def test_fetch_sync_network_error(self, mock_service):
        with patch("httpx.Client.get", side_effect=httpx.ConnectError("Connection refused")):
            with pytest.raises(FIRMSNetworkError, match="Network error"):
                mock_service.fetch_country_fires_sync(country="IND")
