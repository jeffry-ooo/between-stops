#!/usr/bin/env python3
"""Step 2 — fetch tourist POIs for a city's bounding box from OpenStreetMap.

    python3 scripts/fetch_pois.py --city barcelona

Writes data/<slug>/osm_pois.raw.json (everything Overpass returned, for
inspection) and data/<slug>/pois.json (the curated shortlist the site uses).

No API key needed. Overpass is a free community service — be gentle with it.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cities  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# Two kinds of selector in one union:
#  1. the tag families we care about everywhere (attraction / museum / viewpoint
#     / historic / place_of_worship / park), plus whatever extra families that
#     city's config adds — headline sights are tagged inconsistently across
#     countries (a market hall, a beach, a stadium, a square);
#  2. an exact-name pass built from the curated list, which catches anything the
#     tag families miss regardless of how it happens to be tagged.
BASE_SELECTORS = [
    'nwr["tourism"~"^(attraction|museum|viewpoint|gallery|zoo|aquarium)$"]["name"]({bbox});',
    'nwr["historic"]["name"]({bbox});',
    'nwr["amenity"="place_of_worship"]["name"]({bbox});',
    'nwr["leisure"="park"]["name"]({bbox});',
]

QUERY_TMPL = "[out:json][timeout:180];\n(\n{selectors}\n);\nout center tags;"


def overpass(query: str) -> dict:
    body = urllib.parse.urlencode({"data": query}).encode()
    last = None
    for endpoint in ENDPOINTS:
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=body,
                    headers={
                        "User-Agent": "sightseeing-by-bus/0.1 (open-source spike; non-commercial)",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )
                with urllib.request.urlopen(req, timeout=200) as resp:
                    print(f"  ok via {endpoint}", file=sys.stderr)
                    return json.loads(resp.read().decode())
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                last = exc
                print(f"  {endpoint} attempt {attempt + 1} failed: {exc}", file=sys.stderr)
                time.sleep(5)
    raise SystemExit(f"all Overpass endpoints failed: {last}")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


def curated_match(tags: dict, curated: dict):
    """Return (display_name, description) if this feature is on the shortlist."""
    for key in ("name", "name:nl", "name:en", "name:ca", "name:es", "short_name", "alt_name",
                "official_name"):
        cand = tags.get(key)
        if not cand:
            continue
        n = norm(cand)
        if n in curated:
            return curated[n]
        # tolerate a trailing qualifier, e.g. "Stadhuis van Antwerpen"
        for ckey, val in curated.items():
            if n.startswith(ckey + " "):
                return val
    return None


def category_of(tags: dict) -> str:
    if tags.get("tourism") in {"zoo", "aquarium"}:
        return "attraction"
    if tags.get("tourism") == "museum":
        return "museum"
    if tags.get("tourism") == "viewpoint":
        return "viewpoint"
    if tags.get("amenity") == "place_of_worship" or tags.get("building") in {"cathedral", "church"}:
        return "church"
    if tags.get("natural") == "beach":
        return "beach"
    if tags.get("amenity") == "marketplace":
        return "market"
    if tags.get("leisure") in {"park", "garden"}:
        return "park"
    if tags.get("leisure") == "stadium":
        return "stadium"
    if tags.get("historic") in {"castle", "city_gate", "fort"}:
        return "castle"
    if tags.get("historic"):
        return "historic"
    if tags.get("tourism") == "attraction":
        return "attraction"
    return "landmark"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="antwerp", choices=cities.ALL)
    ap.add_argument("--probe", action="store_true",
                     help="skip hand curation; auto-select wikidata-tagged POIs "
                          "for a quick bus-reachability estimate")
    args = ap.parse_args()
    city = cities.load(args.city)
    curated = city["curated"]
    probe = args.probe or not curated
    bbox_t = city["bbox"]

    out_dir = DATA / city["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)

    bbox = ",".join(str(v) for v in bbox_t)
    names = ""
    selectors = BASE_SELECTORS + list(city.get("extra_selectors", []))
    if curated:
        names = "|".join(re.escape(k) for k in sorted(curated))
        selectors = selectors + ['nwr["name"~"^({names})$",i]({bbox});']
    body = "\n".join("  " + s for s in selectors)
    query = QUERY_TMPL.format(selectors=body).format(bbox=bbox, names=names)

    mode = "probe (wikidata-tagged, auto-named)" if probe else "curated"
    print(f"Querying Overpass for {city['name']} bbox {bbox} [{mode}] ...", file=sys.stderr)
    raw = overpass(query)
    (out_dir / "osm_pois.raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1))
    elements = raw.get("elements", [])
    print(f"  {len(elements)} raw elements", file=sys.stderr)

    south, west, north, east = bbox_t
    best = {}
    for el in elements:
        tags = el.get("tags") or {}
        if probe:
            # No hand curation yet: a notability filter stands in for editorial
            # judgement. wikidata is a reasonable proxy — it excludes the
            # hundreds of memorial plaques and neighbourhood chapels Overpass
            # otherwise returns, without pretending to replace real curation.
            name = tags.get("name")
            if not name or not tags.get("wikidata"):
                continue
            desc = ""
        else:
            hit = curated_match(tags, curated)
            if not hit:
                continue
            name, desc = hit
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            centre = el.get("center") or {}
            lat, lon = centre.get("lat"), centre.get("lon")
        if lat is None or lon is None:
            continue
        if not (south <= lat <= north and west <= lon <= east):
            continue

        # prefer the richest-tagged element when several match one sight
        score = (1 if tags.get("wikidata") else 0, 1 if tags.get("wikipedia") else 0, len(tags))
        rec = {
            "id": f"{el['type']}/{el['id']}",
            "name": name,
            "osm_name": tags.get("name", ""),
            "description": desc,
            "category": category_of(tags),
            "must_see": name in city["must_see"],
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "wikidata": tags.get("wikidata"),
            "website": tags.get("website") or tags.get("contact:website"),
            "_score": score,
        }
        prev = best.get(name)
        if prev is None or score > prev["_score"]:
            best[name] = rec

    pois = sorted(best.values(), key=lambda r: r["name"])
    for p in pois:
        p.pop("_score")

    # Probe runs never touch pois.json: a city already promoted to full
    # curation (Antwerp, Barcelona) can still be re-probed for calibration
    # without clobbering its hand-written shortlist.
    out_name = "pois.probe.json" if probe else "pois.json"
    (out_dir / out_name).write_text(json.dumps(
        {
            "city": city["slug"],
            "bbox": {"south": south, "west": west, "north": north, "east": east},
            "source": "OpenStreetMap via Overpass API (ODbL)",
            "probe": probe,
            "count": len(pois),
            "pois": pois,
        }, ensure_ascii=False, indent=1))
    print(f"Kept {len(pois)} POIs -> data/{city['slug']}/{out_name}", file=sys.stderr)

    unmatched = sorted({v[0] for v in curated.values()} - {p["name"] for p in pois})
    if unmatched:
        print(f"  not found in OSM extract ({len(unmatched)}): {', '.join(unmatched)}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
