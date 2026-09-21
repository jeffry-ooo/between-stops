"""London, UK — red buses run by contracted private operators (Arriva London,
Go-Ahead, Metroline, Stagecoach London...) all under the TfL brand, not one
filed operator. There's no single-operator GTFS for this; the only source
that has them is the UK national aggregate feed, so the whole bbox is kept
without an agency_filter -- unlike Amsterdam/Copenhagen/Stockholm there is no
single agency name to filter down to.
"""

CITY = {
    "slug": "london",
    "name": "London",
    "country": "United Kingdom",
    "operator": "TfL (contracted bus operators)",
    "operator_url": "https://tfl.gov.uk",
    # Kensington museums to Tower Bridge, South Bank to Euston/British Museum
    "bbox": (51.495, -0.200, 51.525, -0.070),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/gb-unknown-uk-aggregate-feed-gtfs-2014.zip",
    "min_trips_per_day": 70,  # a bus every ~20-30 min, both directions combined
    "min_marginal_gain": 4.0,
    "top_n": 3,
}

CURATED = {}
MUST_SEE = set()
