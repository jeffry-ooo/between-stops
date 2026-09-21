"""Madrid, Spain — EMT Madrid. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "madrid",
    "name": "Madrid",
    "country": "Spain",
    "operator": "EMT Madrid",
    "operator_url": "https://www.emtmadrid.es",
    "bbox": (40.405, -3.720, 40.428, -3.675),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/es-madrid-empresa-municipal-de-transportes-de-madrid-emt-madrid-gtfs-793.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
