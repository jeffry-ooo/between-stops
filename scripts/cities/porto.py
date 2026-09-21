"""Porto, Portugal — STCP. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "porto",
    "name": "Porto",
    "country": "Portugal",
    "operator": "STCP",
    "operator_url": "https://www.stcp.pt",
    "bbox": (41.128, -8.630, 41.152, -8.595),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/pt-porto-sociedade-de-transportes-colectivos-do-porto-gtfs-2148.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
