"""Dublin, Ireland — Dublin Bus. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "dublin",
    "name": "Dublin",
    "country": "Ireland",
    "operator": "Dublin Bus",
    "operator_url": "https://www.dublinbus.ie",
    "bbox": (53.335, -6.295, 53.355, -6.245),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/ie-dublin-dublin-bus-gtfs-2635.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
