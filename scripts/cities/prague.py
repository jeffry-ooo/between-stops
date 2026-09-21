"""Prague, Czechia — PID. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "prague",
    "name": "Prague",
    "country": "Czechia",
    "operator": "PID",
    "operator_url": "https://pid.cz",
    "bbox": (50.078, 14.388, 50.098, 14.435),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/cz-praha-prazska-integrovana-doprava-pid-gtfs-767.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
