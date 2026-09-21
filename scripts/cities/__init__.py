"""City registry.

Each city module exports CITY (config) and CURATED (name -> (display, blurb)).
Adding a city means adding one module here and listing its slug in ALL.
"""

import importlib

ALL = [
    "antwerp", "barcelona",
    # probe stubs -- bbox + mirror only, awaiting curation
    "rome", "madrid", "prague", "budapest", "munich", "florence",
    "porto", "krakow", "dublin", "amsterdam", "copenhagen", "stockholm",
    "london", "paris",
]


def load(slug: str):
    if slug not in ALL:
        raise SystemExit(f"unknown city {slug!r} — known: {', '.join(ALL)}")
    mod = importlib.import_module(f"cities.{slug}")
    city = dict(mod.CITY)
    city["curated"] = mod.CURATED
    city["must_see"] = getattr(mod, "MUST_SEE", set())
    return city
