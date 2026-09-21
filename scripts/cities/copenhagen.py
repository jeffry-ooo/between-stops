"""Copenhagen, Denmark — Movia. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "copenhagen",
    "name": "Copenhagen",
    "country": "Denmark",
    "operator": "Movia",
    "operator_url": "https://www.moviatrafik.dk",
    "bbox": (55.665, 12.555, 55.700, 12.610),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/dk-unknown-rejseplanen-gtfs-1292.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
    "agency_filter": "Movia",
}

CURATED = {}
MUST_SEE = set()
