# Sample Data

This directory will contain sample datasets for development and testing.

## How to Obtain NASA FIRMS Data

1. **Get an API Key**: Register at [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/api/area/) to get a free MAP_KEY.

2. **Download via API**:
   ```
   https://firms.modaps.eosdis.nasa.gov/api/country/csv/{MAP_KEY}/VIIRS_SNPP_NRT/IND/1
   ```

3. **Data Fields**: latitude, longitude, brightness, scan, track, acq_date, acq_time, satellite, confidence, version, bright_t31, frp, daynight

4. **Place downloaded CSV files in `data/raw/`** for preprocessing.

> **Note**: Do not commit real FIRMS data to this repository. Use `.gitignore` to exclude `data/raw/` contents.
