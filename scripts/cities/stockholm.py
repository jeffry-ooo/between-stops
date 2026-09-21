"""Stockholm, Sweden — SL. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "stockholm",
    "name": "Stockholm",
    "country": "Sweden",
    "operator": "SL",
    "operator_url": "https://sl.se",
    "bbox": (59.315, 18.030, 59.335, 18.110),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/se-trafiklab-gtfs-sverige-2-gtfs-2661.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
    "agency_filter": "SL",
}

CURATED = {}
MUST_SEE = set()
