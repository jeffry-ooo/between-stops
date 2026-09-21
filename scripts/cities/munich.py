"""Munich, Germany — MVG. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "munich",
    "name": "Munich",
    "country": "Germany",
    "operator": "MVG",
    "operator_url": "https://www.mvg.de",
    "bbox": (48.125, 11.550, 48.155, 11.605),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/de-bavaria-munchner-verkehrsgesellschaft-mvg-gtfs-2335.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
