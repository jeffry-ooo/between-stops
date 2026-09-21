"""Rome, Italy — ATAC. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "rome",
    "name": "Rome",
    "country": "Italy",
    "operator": "ATAC",
    "operator_url": "https://www.atac.roma.it",
    "bbox": (41.878, 12.445, 41.912, 12.515),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/it-lazio-roma-servizi-per-la-mobilita-gtfs-1294.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
