"""
SIH26162 — NASA FIRMS Data Service (Placeholder).

Will handle fetching and processing active fire data from the
NASA FIRMS (Fire Information for Resource Management System) API.

Data sources:
    - MODIS (Moderate Resolution Imaging Spectroradiometer)
    - VIIRS (Visible Infrared Imaging Radiometer Suite)

API Documentation: https://firms.modaps.eosdis.nasa.gov/api/area/

NOT YET IMPLEMENTED — will be built in Phase 1.
"""

import httpx
from app.config import settings


class FIRMSService:
    """
    Service for interacting with the NASA FIRMS API.

    Will provide methods to:
    - Fetch active fire data for a given region and time range
    - Parse FIRMS CSV/JSON responses into structured data
    - Store fetched data in the database
    """

    def __init__(self):
        self.api_key = settings.firms_api_key
        self.base_url = settings.firms_base_url

    async def fetch_active_fires(self, country: str = "IND", days: int = 1):
        """
        Fetch active fire data from NASA FIRMS.

        Args:
            country: ISO 3166-1 alpha-3 country code (default: India)
            days: Number of days of data to fetch (1, 2, or 10)

        Returns:
            Parsed fire detection data.

        NOT YET IMPLEMENTED.
        """
        # TODO: Implement FIRMS API call
        # URL pattern: {base_url}/api/country/csv/{api_key}/VIIRS_SNPP_NRT/{country}/{days}
        raise NotImplementedError("FIRMS data fetching will be implemented in Phase 1")
