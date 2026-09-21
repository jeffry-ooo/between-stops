"""Budapest, Hungary — BKK. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "budapest",
    "name": "Budapest",
    "country": "Hungary",
    "operator": "BKK",
    "operator_url": "https://bkk.hu",
    "bbox": (47.488, 19.030, 47.518, 19.085),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/hu-budapest-budapesti-kozlekedesi-kozpont-bkk-gtfs-990.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
