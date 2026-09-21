import requests
import json
import math
import re

# --- CONFIGURATION ---
BBOX = "44.0, -94.0, 46.0, -92.0"  # coordinates bounding box
OUTPUT_PATH = "ui/runwaysnew.json"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# This was all written by AI.  The point is just that it makes a json file with the airports names, coordinates, and heading if possible, outputs to runwaysnew.json

def parse_value(val_str, default=1000.0):
    if not val_str: return default
    s = str(val_str).lower().strip()
    try:
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", s)
        if not nums: return default
        val = float(nums[0])
        return round(val * 0.3048, 2) if ('ft' in s or "'" in s) else val
    except: return default

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculates the bearing between two points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_lon = math.radians(lon2 - lon1)
    y = math.sin(d_lon) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lon)
    return round((math.degrees(math.atan2(y, x)) + 360) % 360, 2)

def fetch_runways():
    # 'out geom' provides the lat/lon of all points in the way
    query = f"""
    [out:json][timeout:60];
    (way["aeroway"="runway"]({BBOX}););
    out geom;
    """
    
    print(f"Fetching runway geometries...")
    try:
        response = requests.post(OVERPASS_URL, data={'data': query}, timeout=70)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Failed: {e}")
        return

    runways = []
    for element in data.get('elements', []):
        if element['type'] == 'way' and 'geometry' in element:
            tags = element.get('tags', {})
            geom = element['geometry']
            
            if len(geom) < 2: continue

            # 1. Heading Math (Start to End)
            p1, p2 = geom[0], geom[-1]
            true_heading = calculate_bearing(p1['lat'], p1['lon'], p2['lat'], p2['lon'])
            
            # 2. Position (Exact Midpoint of the line)
            mid_lat = (p1['lat'] + p2['lat']) / 2
            mid_lon = (p1['lon'] + p2['lon']) / 2

            # 3. Check if heading is likely valid
            heading_valid = True if true_heading != 0 else False

            runways.append({
                "type": "runway",
                "ref": tags.get('ref', "UNK"),
                "lat": mid_lat,
                "lon": mid_lon,
                "heading": true_heading,
                "heading_found": heading_valid,
                "length": parse_value(tags.get('length'), 1500.0),
                "width": parse_value(tags.get('width'), 30.48),
                "surface": tags.get('surface', "asphalt")
            })

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(runways, f, indent=4)
    
    print(f"Saved {len(runways)} runways. Check {OUTPUT_PATH} for results.")

if __name__ == "__main__":
    fetch_runways()