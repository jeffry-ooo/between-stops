"""Amsterdam, Netherlands — GVB. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "amsterdam",
    "name": "Amsterdam",
    "country": "Netherlands",
    "operator": "GVB",
    "operator_url": "https://www.gvb.nl",
    "bbox": (52.354, 4.865, 52.383, 4.910),
    "gtfs_mirror": "http://gtfs.ovapi.nl/nl/gtfs-nl.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
    "agency_filter": "GVB",
}

CURATED = {}
MUST_SEE = set()
