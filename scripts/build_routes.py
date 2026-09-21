#!/usr/bin/env python3
"""Steps 1, 3, 4 — parse a city's GTFS, match POIs to bus stops, rank and curate loops.

    python3 scripts/build_routes.py --city barcelona

Reads   data/<slug>/gtfs.zip      (streamed, never fully extracted)
        data/<slug>/pois.json     (from fetch_pois.py)
Writes  site/routes.<slug>.json   (the curated output the site consumes)
        data/<slug>/route_scores.csv  (every bus line scored, for inspection)

Feeds vary wildly in size — De Lijn's covers all of Flanders (2.5 GB unzipped,
a 2 GB stop_times.txt), TMB's is one city (52 MB) — so everything streams out of
the zip and filters on stop_id before allocating anything.
"""

import argparse
import csv
import datetime as dt
import io
import json
import math
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cities  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"

# Standard GTFS route_type 3 = Bus. Several European operators instead use the
# extended hierarchical vehicle types (Munich/MVG: 704 local bus, 702 express
# bus) or tag trolleybuses as 11 — electric, but on ordinary streets, boarded
# with the same ticket as a diesel bus, so they count for this product too.
def is_bus_route(route_type: str) -> bool:
    return route_type == "3" or route_type == "11" or (
        len(route_type) == 3 and route_type[0] == "7")
WALK_M = 300     # POI counts as "served" by a stop within this crow-flies distance
GRID_M = 700     # district cell size used for the geographic-spread score
MUST_SEE_WEIGHT = 2.5  # a headline sight is worth more than a minor one
SERVICE_HOURS = 18  # assumed span of a service day, for the headway estimate

csv.field_size_limit(1 << 24)

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def base_line(short_name: str) -> str:
    """18a / 18b / 18c are service variants of bus 18 — a tourist boards '18'."""
    return re.sub(r"^(\d+)[a-z]$", r"\1", short_name)


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def rows(zf, name):
    """Stream a GTFS csv as (header_index_map, row_iterator)."""
    with zf.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.reader(text)
        header = next(reader)
        idx = {col.strip(): i for i, col in enumerate(header)}
        yield idx
        yield from reader


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def service_calendar(zf):
    """Active dates per service_id, honouring calendar.txt, calendar_dates.txt or both.

    De Lijn ships only calendar_dates; TMB ships a four-row calendar plus 26k
    date exceptions. Both shapes have to work.
    """
    names = set(zf.namelist())
    days = defaultdict(set)

    if "calendar.txt" in names:
        it = rows(zf, "calendar.txt")
        idx = next(it)
        for r in it:
            sid = r[idx["service_id"]]
            start = dt.datetime.strptime(r[idx["start_date"]], "%Y%m%d").date()
            end = dt.datetime.strptime(r[idx["end_date"]], "%Y%m%d").date()
            mask = [r[idx[d]] == "1" for d in WEEKDAYS]
            day = start
            while day <= end:
                if mask[day.weekday()]:
                    days[sid].add(day)
                day += dt.timedelta(days=1)

    if "calendar_dates.txt" in names:
        it = rows(zf, "calendar_dates.txt")
        idx = next(it)
        for r in it:
            sid = r[idx["service_id"]]
            day = dt.datetime.strptime(r[idx["date"]], "%Y%m%d").date()
            if r[idx["exception_type"]] == "1":
                days[sid].add(day)
            else:
                days[sid].discard(day)

    counts = {sid: len(d) for sid, d in days.items()}
    all_days = set().union(*days.values()) if days else set()
    return counts, max(len(all_days), 1)


def trip_multiplier(zf):
    """Runs per service day for frequency-defined trips (1 for ordinary trips)."""
    if "frequencies.txt" not in zf.namelist():
        return {}
    mult = defaultdict(int)
    it = rows(zf, "frequencies.txt")
    idx = next(it)

    def secs(t):
        h, m, s = (int(x) for x in t.split(":"))
        return h * 3600 + m * 60 + s

    for r in it:
        head = int(r[idx["headway_secs"]] or 0)
        if head <= 0:
            continue
        span = secs(r[idx["end_time"]]) - secs(r[idx["start_time"]])
        mult[r[idx["trip_id"]]] += max(1, span // head)
    return dict(mult)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="antwerp", choices=cities.ALL)
    ap.add_argument("--probe", action="store_true",
                     help="write a compact reachability summary to "
                          "data/<city>/probe_result.json instead of the full "
                          "site output, and skip updating site/cities.json")
    args = ap.parse_args()
    city = cities.load(args.city)
    slug = city["slug"]
    min_per_day = city["min_trips_per_day"]
    min_gain = city["min_marginal_gain"]
    top_n = city.get("top_n", 3)

    city_dir = DATA / slug
    gtfs = city_dir / "gtfs.zip"
    if not gtfs.exists():
        raise SystemExit(f"missing {gtfs} — run ./scripts/fetch_gtfs.sh {slug}")
    # A calibration --probe on an already-curated city (Antwerp, Barcelona)
    # reads its throwaway pois.probe.json rather than the hand-written pois.json.
    poi_file = city_dir / "pois.probe.json" if args.probe and (city_dir / "pois.probe.json").exists() \
        else city_dir / "pois.json"
    pois = json.loads(poi_file.read_text())["pois"]
    log(f"[{slug}] {len(pois)} POIs loaded")

    south, west, north, east = city["bbox"]
    zf = zipfile.ZipFile(gtfs)

    feed = {}
    if "feed_info.txt" in zf.namelist():
        it = rows(zf, "feed_info.txt")
        idx = next(it)
        for r in it:
            feed = {k: r[i] for k, i in idx.items() if i < len(r)}
            break

    # --- agency.txt: for national/regional feeds, restrict to one operator ---
    # Amsterdam/Copenhagen/Stockholm only publish a whole-country feed mixing
    # every operator (trains, ferries, dozens of regional bus companies) —
    # agency_filter picks out just the city operator (GVB / Movia / SL) before
    # anything else runs, the same way the bbox picks out just the city stops.
    agency_filter = city.get("agency_filter")
    allowed_agencies = None
    if agency_filter and "agency.txt" in zf.namelist():
        it = rows(zf, "agency.txt")
        idx = next(it)
        # exact match, not substring: "SL" as a substring also matches
        # "Tåg i Bergslagen", an unrelated regional rail operator
        allowed_agencies = {
            r[idx["agency_id"]] for r in it
            if r[idx["agency_name"]].strip().lower() == agency_filter.lower()
        }
        log(f"agency_filter {agency_filter!r}: matched agency_id(s) {sorted(allowed_agencies)}")

    # --- routes.txt: bus lines only -------------------------------------
    routes = {}
    it = rows(zf, "routes.txt")
    idx = next(it)
    n_all = 0
    for r in it:
        n_all += 1
        if not is_bus_route(r[idx["route_type"]]):
            continue
        if allowed_agencies is not None:
            aid = r[idx["agency_id"]] if "agency_id" in idx and idx["agency_id"] < len(r) else ""
            if aid not in allowed_agencies:
                continue
        routes[r[idx["route_id"]]] = {
            "short_name": r[idx["route_short_name"]] or r[idx["route_long_name"]],
            "long_name": r[idx["route_long_name"]],
            "color": (r[idx["route_color"]] if "route_color" in idx else "") or "3C6E9F",
            "url": r[idx["route_url"]] if "route_url" in idx else "",
        }
    log(f"routes.txt: {n_all} routes, {len(routes)} are buses (route_type=3)")

    # --- stops.txt: only stops inside the bounding box -------------------
    stops = {}
    it = rows(zf, "stops.txt")
    idx = next(it)
    n_all = 0
    for r in it:
        n_all += 1
        try:
            lat = float(r[idx["stop_lat"]])
            lon = float(r[idx["stop_lon"]])
        except (ValueError, IndexError):
            continue
        if not (south <= lat <= north and west <= lon <= east):
            continue
        stops[r[idx["stop_id"]]] = {
            "id": r[idx["stop_id"]],
            "name": r[idx["stop_name"]],
            "lat": lat,
            "lon": lon,
        }
    log(f"stops.txt: {n_all} stops, {len(stops)} inside the bbox")

    # --- stop_times.txt: the big pass, filtered on stop_id ---------------
    trip_stops = defaultdict(list)
    it = rows(zf, "stop_times.txt")
    idx = next(it)
    i_trip, i_stop, i_seq = idx["trip_id"], idx["stop_id"], idx["stop_sequence"]
    n_all = n_kept = 0
    for r in it:
        n_all += 1
        if n_all % 5_000_000 == 0:
            log(f"  stop_times: {n_all/1e6:.0f}M rows scanned, {n_kept} kept")
        sid = r[i_stop]
        if sid not in stops:
            continue
        n_kept += 1
        trip_stops[sys.intern(r[i_trip])].append((int(r[i_seq]), sid))
    log(f"stop_times.txt: {n_all} rows, {n_kept} in bbox across {len(trip_stops)} trips")

    # --- trips.txt: resolve only the trips that touched the bbox ---------
    trip_meta = {}
    it = rows(zf, "trips.txt")
    idx = next(it)
    n_all = 0
    for r in it:
        n_all += 1
        tid = r[idx["trip_id"]]
        if tid not in trip_stops:
            continue
        rid = r[idx["route_id"]]
        if rid not in routes:  # tram / metro / funicular
            continue
        trip_meta[tid] = {
            "route_id": rid,
            "service_id": r[idx["service_id"]],
            "shape_id": r[idx["shape_id"]] if "shape_id" in idx else "",
            "headsign": r[idx["trip_headsign"]] if "trip_headsign" in idx else "",
            "direction_id": r[idx["direction_id"]] if "direction_id" in idx else "0",
        }
    log(f"trips.txt: {n_all} trips, {len(trip_meta)} are bus trips touching the bbox")

    for tid in list(trip_stops):
        if tid not in trip_meta:
            del trip_stops[tid]

    service_days, n_days = service_calendar(zf)
    freq_mult = trip_multiplier(zf)
    log(f"calendar: {len(service_days)} services over {n_days} dates"
        + (f"; {len(freq_mult)} frequency-defined trips" if freq_mult else ""))

    # --- POI <-> stop matching (step 3) ----------------------------------
    # Only stops a bus actually calls at count. Matching against every stop in
    # the box would silently count tram and metro stops and overstate reach.
    bus_stop_ids = {sid for tid in trip_stops for _, sid in trip_stops[tid]}
    log(f"{len(bus_stop_ids)} of {len(stops)} bbox stops are served by a bus")

    stop_pois = defaultdict(list)
    poi_stops = defaultdict(list)
    for poi in pois:
        nearest_any = nearest_bus = 1e9
        for sid, st in stops.items():
            d = haversine_m(poi["lat"], poi["lon"], st["lat"], st["lon"])
            nearest_any = min(nearest_any, d)
            if sid in bus_stop_ids:
                nearest_bus = min(nearest_bus, d)
                if d <= WALK_M:
                    stop_pois[sid].append((poi["name"], round(d)))
                    poi_stops[poi["name"]].append((sid, round(d)))
        poi["nearest_stop_m"] = round(nearest_any)
        poi["nearest_bus_stop_m"] = round(nearest_bus)
        poi["bus_reachable"] = bool(poi_stops[poi["name"]])
    for v in stop_pois.values():
        v.sort(key=lambda x: x[1])
    reachable = [p for p in pois if p["bus_reachable"]]
    near_any = [p for p in pois if p["nearest_stop_m"] <= WALK_M]
    log(f"matching: {len(reachable)}/{len(pois)} POIs within {WALK_M} m of a BUS stop "
        f"({len(near_any)} within {WALK_M} m of any stop incl. tram/metro)")

    # --- aggregate per LINE (both directions) ----------------------------
    line_stops = defaultdict(set)
    line_variants = defaultdict(set)
    line_trips = defaultdict(list)
    line_runs = defaultdict(int)
    for tid, meta in trip_meta.items():
        line = base_line(routes[meta["route_id"]]["short_name"])
        line_stops[line].update(s for _, s in trip_stops[tid])
        line_variants[line].add(routes[meta["route_id"]]["short_name"])
        line_trips[line].append(tid)
        line_runs[line] += service_days.get(meta["service_id"], 0) * freq_mult.get(tid, 1)

    poi_by_name = {p["name"]: p for p in pois}

    def weight(name):
        return MUST_SEE_WEIGHT if poi_by_name[name].get("must_see") else 1.0

    def cell(poi):
        lat_m = poi["lat"] * 111_320
        lon_m = poi["lon"] * 111_320 * math.cos(math.radians(poi["lat"]))
        return (int(lat_m // GRID_M), int(lon_m // GRID_M))

    scored = []
    for line, sids in line_stops.items():
        served = sorted({name for sid in sids for name, _ in stop_pois.get(sid, [])})
        if not served:
            continue
        cells = {cell(poi_by_name[n]) for n in served}
        pts = [(poi_by_name[n]["lat"], poi_by_name[n]["lon"]) for n in served]
        spread_km = 0.0
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                spread_km = max(spread_km, haversine_m(*pts[i], *pts[j]) / 1000)
        per_day = line_runs[line] / n_days
        # A line hitting 5 POIs on one street scores 5 + 1.5; one hitting 4 POIs
        # in 4 different districts scores 4 + 6.0. Spread can outrank raw count.
        scored.append({
            "line": line,
            "variants": sorted(line_variants[line]),
            "trips_per_day": round(per_day, 1),
            "frequent_enough": per_day >= min_per_day,
            "score": round(sum(weight(n) for n in served) + 1.5 * len(cells), 2),
            "poi_count": len(served),
            "must_see_count": sum(1 for n in served if poi_by_name[n].get("must_see")),
            "districts": len(cells),
            "spread_km": round(spread_km, 2),
            "bbox_stops": len(sids),
            "pois": served,
        })

    scored.sort(key=lambda x: (-x["score"], -x["spread_km"], x["line"]))
    with (city_dir / "route_scores.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["line", "variants", "trips_per_day", "frequent_enough", "score",
                    "poi_count", "districts", "spread_km", "bbox_stops", "pois"])
        for s in scored:
            w.writerow([s["line"], "/".join(s["variants"]), s["trips_per_day"],
                        s["frequent_enough"], s["score"], s["poi_count"], s["districts"],
                        s["spread_km"], s["bbox_stops"], "; ".join(s["pois"])])
    log(f"scored {len(scored)} bus lines -> data/{slug}/route_scores.csv")
    for s in scored[:10]:
        flag = "" if s["frequent_enough"] else "  [too infrequent]"
        log(f"  {s['line']:>5}  score {s['score']:>5}  {s['poi_count']} POIs "
            f"({s['must_see_count']} must-see)  "
            f"{s['districts']} districts  spread {s['spread_km']} km  "
            f"{s['trips_per_day']}/day{flag}")

    # --- pick the loops (step 4) -----------------------------------------
    # Greedy max-coverage, not simply the top N: after the best line is taken,
    # each remaining line is re-scored on the sights it *adds*, so the loops
    # complement each other instead of all serving the same famous cluster.
    eligible = [s for s in scored if s["frequent_enough"]]
    chosen, covered = [], set()
    while eligible and len(chosen) < top_n:
        def marginal(cand):
            fresh = [n for n in cand["pois"] if n not in covered]
            return (sum(weight(n) for n in fresh)
                    + 1.5 * len({cell(poi_by_name[n]) for n in fresh}),
                    cand["spread_km"])

        best = max(eligible, key=marginal)
        gain = marginal(best)[0]
        if chosen and gain < min_gain:
            log(f"  stopping at {len(chosen)} loops — best remaining adds only {gain:.1f}")
            break
        chosen.append(dict(best, marginal_score=round(gain, 2),
                           new_pois=[n for n in best["pois"] if n not in covered]))
        covered.update(best["pois"])
        eligible = [e for e in eligible if e["line"] != best["line"]]
    log(f"picked {[c['line'] for c in chosen]} covering {len(covered)} distinct sights")

    want_shapes = set()
    itineraries = []
    for s in chosen:
        line = s["line"]

        def trip_value(tid):
            sids = {sid for _, sid in trip_stops[tid]}
            npoi = len({n for sid in sids for n, _ in stop_pois.get(sid, [])})
            return (npoi, len(sids))

        best_tid = max(line_trips[line], key=trip_value)
        meta = trip_meta[best_tid]
        seq = sorted(set(trip_stops[best_tid]))

        ordered = []
        for _, sid in seq:
            st = stops[sid]
            entry = {
                "stop_id": sid, "stop_name": st["name"], "lat": st["lat"], "lon": st["lon"],
                "pois": [{
                    "name": n, "walk_m": d,
                    "description": poi_by_name[n]["description"],
                    "category": poi_by_name[n]["category"],
                    "lat": poi_by_name[n]["lat"], "lon": poi_by_name[n]["lon"],
                } for n, d in stop_pois.get(sid, [])],
            }
            # Operators split a stop into one id per direction/platform, and a
            # terminus loop can pass the same place twice — collapse the repeat.
            if ordered and ordered[-1]["stop_name"] == entry["stop_name"]:
                merged = {p["name"]: p for p in entry["pois"]}
                for p in ordered[-1]["pois"]:
                    if p["name"] not in merged or p["walk_m"] < merged[p["name"]]["walk_m"]:
                        merged[p["name"]] = p
                ordered[-1]["pois"] = sorted(merged.values(), key=lambda p: p["walk_m"])
                continue
            ordered.append(entry)

        # List each sight once, at the stop you'd actually get off at, so the
        # itinerary reads as instructions rather than a repeating catalogue.
        nearest = {}
        for i, st in enumerate(ordered):
            for p in st["pois"]:
                if p["name"] not in nearest or p["walk_m"] < nearest[p["name"]][0]:
                    nearest[p["name"]] = (p["walk_m"], i)
        for i, st in enumerate(ordered):
            st["pois"] = [p for p in st["pois"] if nearest[p["name"]][1] == i]

        rm = routes[meta["route_id"]]
        want_shapes.add(meta["shape_id"])
        itineraries.append({
            "line": line, "variants": s["variants"], "trips_per_day": s["trips_per_day"],
            "route_id": meta["route_id"], "shape_id": meta["shape_id"],
            "headsign": meta["headsign"] or rm["long_name"], "long_name": rm["long_name"],
            "color": "#" + rm["color"], "url": rm["url"],
            "score": s["score"], "marginal_score": s["marginal_score"],
            "new_pois": s["new_pois"], "poi_count": s["poi_count"],
            "districts": s["districts"], "spread_km": s["spread_km"],
            "stops": ordered, "shape": [],
        })

    # --- shapes.txt, filtered to the chosen shape_ids --------------------
    shape_pts = defaultdict(list)
    if "shapes.txt" in zf.namelist() and want_shapes:
        it = rows(zf, "shapes.txt")
        idx = next(it)
        i_sid, i_lat, i_lon, i_seq = (idx["shape_id"], idx["shape_pt_lat"],
                                      idx["shape_pt_lon"], idx["shape_pt_sequence"])
        n_all = 0
        for r in it:
            n_all += 1
            if r[i_sid] not in want_shapes:
                continue
            shape_pts[r[i_sid]].append((int(r[i_seq]), float(r[i_lat]), float(r[i_lon])))
        log(f"shapes.txt: {n_all} points, kept {sum(len(v) for v in shape_pts.values())}")

    for itin in itineraries:
        pts = sorted(shape_pts.get(itin["shape_id"], []))
        itin["shape"] = [[round(la, 6), round(lo, 6)] for _, la, lo in pts]

    out = {
        "city": {k: city.get(k, "") for k in
                 ("slug", "name", "country", "operator", "operator_url",
                  "tour_price_eur", "ticket_note")},
        "generated_from": {
            "gtfs_publisher": feed.get("feed_publisher_name", city["operator"]),
            "gtfs_version": feed.get("feed_version", ""),
            "gtfs_valid_from": feed.get("feed_start_date", ""),
            "gtfs_valid_to": feed.get("feed_end_date", ""),
            "pois": "OpenStreetMap via Overpass API (ODbL)",
        },
        "bbox": {"south": south, "west": west, "north": north, "east": east},
        "walk_radius_m": WALK_M,
        "service_hours": SERVICE_HOURS,
        "min_trips_per_day": min_per_day,
        "scoring": (f"score = sum of POI weights (must-see sights count {MUST_SEE_WEIGHT}x) "
                    "+ 1.5 x distinct 700 m district cells those POIs fall in, so both "
                    "geographic spread and headline sights can outrank raw count"),
        "stats": {
            "bus_routes": len(routes),
            "bbox_stops": len(stops),
            "bbox_bus_stops": len(bus_stop_ids),
            "pois_total": len(pois),
            "pois_bus_reachable": len(reachable),
        },
        "all_pois": pois,
        "unreachable_pois": sorted(
            ({"name": p["name"], "description": p["description"], "category": p["category"],
              "lat": p["lat"], "lon": p["lon"], "nearest_bus_stop_m": p["nearest_bus_stop_m"]}
             for p in pois if not p["bus_reachable"]),
            key=lambda p: p["nearest_bus_stop_m"]),
        "ranking": scored[:15],
        "loops": itineraries,
    }
    if args.probe:
        # Just the headline reachability number and a look at the strongest
        # lines — not a shippable page. Full curation only happens once this
        # says the city is worth the writing effort.
        probe_out = {
            "slug": slug, "name": city["name"], "country": city["country"],
            "operator": city["operator"],
            "stats": out["stats"],
            "reachability_pct": round(
                100 * out["stats"]["pois_bus_reachable"] / max(out["stats"]["pois_total"], 1), 1),
            "top_lines": scored[:6],
            "loops_preview": [
                {"line": l["line"], "poi_count": l["poi_count"],
                 "trips_per_day": l["trips_per_day"]} for l in itineraries
            ],
        }
        (city_dir / "probe_result.json").write_text(
            json.dumps(probe_out, ensure_ascii=False, indent=1))
        log(f"[{slug}] PROBE: {probe_out['reachability_pct']}% reachable "
            f"({out['stats']['pois_bus_reachable']}/{out['stats']['pois_total']} notable POIs) "
            f"-> data/{slug}/probe_result.json")
        return

    SITE.mkdir(exist_ok=True)
    (SITE / f"routes.{slug}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    log(f"wrote site/routes.{slug}.json — {len(itineraries)} loops")
    log("run scripts/export_manifest.py to refresh site/cities.json")


if __name__ == "__main__":
    main()
