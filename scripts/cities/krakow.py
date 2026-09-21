"""Kraków, Poland — MPK Kraków. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "krakow",
    "name": "Kraków",
    "country": "Poland",
    "operator": "MPK Kraków",
    "operator_url": "https://www.mpk.krakow.pl",
    "bbox": (50.044, 19.918, 50.070, 19.958),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/pl-malopolskie-zarzad-transportu-publicznego-w-krakowie-ztp-krakow-gtfs-1326.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
