# `populate_cities.py` Documentation Summary

This script automates the generation of a curated list of global cities with populations exceeding 100,000 by fetching and parsing data from the GeoNames database.

## Overview

The script downloads the `cities15000.zip` dataset from [GeoNames](https://download.geonames.org/export/dump/), filters the entries based on population, and produces a sorted text file containing city names and their respective country codes.

## Requirements

- **Python 3.x**
- **External Libraries**: `requests` (for downloading the dataset).
- **Standard Libraries**: `json`, `logging`, `zipfile`, `io`.

## Functions

### `fetch_geonames_cities()`
*   **Purpose**: Downloads and parses the GeoNames "cities15000" dataset.
*   **Mechanism**:
    1.  Fetches the ZIP file via HTTP.
    2.  Extracts `cities15000.txt` in memory.
    3.  Parses the tab-separated values (TSV).
    4.  Filters for cities where **Population > 100,000**.
    5.  Returns a list of strings formatted as `"{City Name}, {Country Code}"`.
*   **Returns**: `List[str]` (Sorted alphabetically).

### `main()`
*   **Purpose**: Orchestrates the execution flow.
*   **Action**: Calls the fetcher and writes the resulting list to a local file named `cities.txt`.

## Usage

Run the script directly using Python:

```bash
python populate_cities.py
```

## Output

- **File**: `cities.txt`
- **Format**: One city per line (e.g., `New York City, US`).
- **Location**: Root directory of the execution context.
