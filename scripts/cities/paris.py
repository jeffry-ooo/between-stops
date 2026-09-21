"""Paris, France — RATP. PROBE STUB: bbox + mirror only, no hand curation yet.
"""

CITY = {
    "slug": "paris",
    "name": "Paris",
    "country": "France",
    "operator": "RATP",
    "operator_url": "https://www.ratp.fr",
    "bbox": (48.845, 2.275, 48.888, 2.375),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/fr-ile-de-france-regie-autonome-des-transports-parisiens-gtfs-1291.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
