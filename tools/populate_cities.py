import json
import logging
import zipfile
import io
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_geonames_cities():
    """Fetches the cities15000.txt from Geonames, which contains cities > 15k population."""
    url = "https://download.geonames.org/export/dump/cities15000.zip"
    logger.info(f"Downloading {url}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Geonames provides a zip containing cities15000.txt
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            with z.open("cities15000.txt") as f:
                content = f.read().decode('utf-8')
                
        cities = []
        # The file is tab-separated. 
        # Column 1: geonameid
        # Column 2: name (standard name)
        # Column 9: country code
        # Column 15: population
        
        for line in content.splitlines():
            if not line.strip():
                continue
                
            parts = line.split('\t')
            if len(parts) >= 15:
                name = parts[1]
                country_code = parts[8]
                try:
                    population = int(parts[14])
                except ValueError:
                    continue
                    
                # The user asked for > 100k population to keep the list lean and fast
                if population > 100000:
                    cities.append(f"{name}, {country_code}")
                    
        # Sort alphabetically for a nicer file
        cities.sort()
        return cities

    except Exception as e:
        logger.exception(f"Failed to fetch or parse Geonames data: {e}")
        return []

def main():
    logger.info("Starting city list generation...")
    cities = fetch_geonames_cities()
    
    if not cities:
        logger.error("No cities fetched. Exiting.")
        return
        
    logger.info(f"Successfully extracted {len(cities)} cities with >100,000 population.")
    
    # Write to cities.txt in the root directory
    output_path = "cities.txt"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for city in cities:
                f.write(f"{city}\n")
        logger.info(f"Wrote {len(cities)} cities to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write to {output_path}: {e}")

if __name__ == "__main__":
    main()
