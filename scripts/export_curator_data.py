#!/usr/bin/env python3
"""Build the data bundle the curator tool (site/curator.html) reads.

    python3 scripts/export_curator_data.py --city rome

Writes site/curator-data/<slug>.json:
  raw_pois   every named Overpass element in the bbox (from osm_pois.raw.json,
             already fetched by fetch_pois.py) with its tags, so the curator
             can browse the full universe, not just what got auto-selected
  bus_stops  every stop inside the bbox that a bus actually calls at, with
             which lines serve it and roughly how often, so "is this walkable
             from a real bus stop" is a lookup, not a guess
  curated    the city's current CURATED dict + MUST_SEE set, so already-picked
             sights show up flagged in the browser rather than looking new

This duplicates a slice of build_routes.py's GTFS parsing rather than
importing it — the two scripts read the same feed for different purposes
(one picks routes, this one just wants "what serves this stop"), and keeping
them independent means a change to route-picking logic can't silently break
the curator's stop lookup.
"""

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cities  # noqa: E402
from build_routes import is_bus_route, base_line  # reuse the one tricky bit

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"

TAG_KEYS = (
    "tourism", "historic", "amenity", "leisure", "building", "natural",
    "man_made", "place", "shop", "religion", "heritage", "architect",
    "start_date", "wikidata", "wikipedia", "website", "contact:website",
)

csv.field_size_limit(1 << 24)


def rows(zf, name):
    with zf.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.reader(text)
        header = next(reader)
        idx = {col.strip(): i for i, col in enumerate(header)}
        yield idx
        yield from reader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True, choices=cities.ALL)
    args = ap.parse_args()
    city = cities.load(args.city)
    slug = city["slug"]
    south, west, north, east = city["bbox"]

    raw_path = DATA / slug / "osm_pois.raw.json"
    if not raw_path.exists():
        raise SystemExit(f"missing {raw_path} — run fetch_pois.py --city {slug} first")
    elements = json.loads(raw_path.read_text()).get("elements", [])

    raw_pois = []
    for el in elements:
        tags = el.get("tags") or {}
        name = tags.get("name")
        if not name:
            continue
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            centre = el.get("center") or {}
            lat, lon = centre.get("lat"), centre.get("lon")
        if lat is None or lon is None or not (south <= lat <= north and west <= lon <= east):
            continue
        raw_pois.append({
            "id": f"{el['type']}/{el['id']}",
            "name": name,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "tags": {k: tags[k] for k in TAG_KEYS if k in tags},
        })
    print(f"[{slug}] {len(raw_pois)} named elements in bbox", file=sys.stderr)

    # --- bus stops: which lines serve each one, how often --------------------
    bus_stops = []
    gtfs = DATA / slug / "gtfs.zip"
    if gtfs.exists():
        zf = zipfile.ZipFile(gtfs)

        agency_filter = city.get("agency_filter")
        allowed_agencies = None
        if agency_filter and "agency.txt" in zf.namelist():
            it = rows(zf, "agency.txt")
            idx = next(it)
            allowed_agencies = {
                r[idx["agency_id"]] for r in it
                if r[idx["agency_name"]].strip().lower() == agency_filter.lower()
            }

        routes = {}
        it = rows(zf, "routes.txt")
        idx = next(it)
        for r in it:
            if not is_bus_route(r[idx["route_type"]]):
                continue
            if allowed_agencies is not None:
                aid = r[idx["agency_id"]] if "agency_id" in idx and idx["agency_id"] < len(r) else ""
                if aid not in allowed_agencies:
                    continue
            routes[r[idx["route_id"]]] = r[idx["route_short_name"]] or r[idx["route_long_name"]]

        stops = {}
        it = rows(zf, "stops.txt")
        idx = next(it)
        for r in it:
            try:
                lat, lon = float(r[idx["stop_lat"]]), float(r[idx["stop_lon"]])
            except (ValueError, IndexError):
                continue
            if south <= lat <= north and west <= lon <= east:
                stops[r[idx["stop_id"]]] = {"name": r[idx["stop_name"]], "lat": lat, "lon": lon}

        trip_route = {}
        it = rows(zf, "trips.txt")
        idx = next(it)
        for r in it:
            trip_route[r[idx["trip_id"]]] = r[idx["route_id"]]

        stop_lines = defaultdict(set)
        it = rows(zf, "stop_times.txt")
        idx = next(it)
        for r in it:
            sid = r[idx["stop_id"]]
            if sid not in stops:
                continue
            rid = trip_route.get(r[idx["trip_id"]])
            if rid in routes:
                stop_lines[sid].add(base_line(routes[rid]))

        for sid, st in stops.items():
            lines = sorted(stop_lines.get(sid, []))
            if lines:
                bus_stops.append({
                    "name": st["name"], "lat": round(st["lat"], 6), "lon": round(st["lon"], 6),
                    "lines": lines,
                })
        print(f"[{slug}] {len(bus_stops)} bus stops in bbox", file=sys.stderr)
    else:
        print(f"[{slug}] no gtfs.zip — skipping bus stop overlay", file=sys.stderr)

    curated = [
        {"key": k, "name": v[0], "description": v[1], "must_see": v[0] in city["must_see"]}
        for k, v in sorted(city["curated"].items())
    ]

    out_dir = SITE / "curator-data"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{slug}.json").write_text(json.dumps({
        "slug": slug, "name": city["name"], "country": city["country"],
        "bbox": {"south": south, "west": west, "north": north, "east": east},
        "raw_pois": raw_pois,
        "bus_stops": bus_stops,
        "curated": curated,
    }, ensure_ascii=False, indent=1))
    print(f"[{slug}] wrote site/curator-data/{slug}.json", file=sys.stderr)

    # keep an index of what's available, so curator.html doesn't need to
    # guess or hardcode which cities have been exported
    index_path = out_dir / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else []
    index = [c for c in index if c["slug"] != slug]
    index.append({
        "slug": slug, "name": city["name"], "country": city["country"],
        "raw_count": len(raw_pois), "curated_count": len(curated),
    })
    index.sort(key=lambda c: c["name"])
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
