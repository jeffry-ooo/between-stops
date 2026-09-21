"""Florence, Italy — Ataf&Linea. PROBE STUB: bbox + mirror only, no hand curation
yet. Run with fetch_pois.py --probe / build_routes.py --probe to get a
bus-reachability estimate before deciding whether to curate this city properly.
"""

CITY = {
    "slug": "florence",
    "name": "Florence",
    "country": "Italy",
    "operator": "Ataf&Linea",
    "operator_url": "https://www.at-bus.it",
    "bbox": (43.760, 11.240, 43.780, 11.270),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/it-toscana-azienda-trasporti-area-fiorentina-ataf-gtfs-1263.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
