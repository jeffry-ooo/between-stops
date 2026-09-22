"""Refresh Barcelona atomically, preserving the published editorial selections.

Only stdlib and curl are needed. Work happens in a temporary copy; a failed
download/build/validation never changes the checked-in public bundle.
"""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

from build_routes import is_bus_route, service_calendar
from cities import load

ROOT = Path(__file__).resolve().parent.parent


def records(zf, name):
    with zf.open(name) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))


def validate_feed(path, today):
    with zipfile.ZipFile(path) as zf:
        if sum(i.file_size for i in zf.infolist()) > 500_000_000:
            raise ValueError("Barcelona feed exceeds the 500 MB expanded limit")
        if zf.testzip():
            raise ValueError("Corrupt GTFS archive")
        required = {
            "routes.txt": {"route_id", "route_type"},
            "stops.txt": {"stop_id", "stop_lat", "stop_lon"},
            "trips.txt": {"trip_id", "route_id", "service_id"},
            "stop_times.txt": {"trip_id", "stop_id", "stop_sequence"},
            "feed_info.txt": {"feed_start_date", "feed_end_date"},
        }
        for name, columns in required.items():
            row = next(records(zf, name), None)
            if not row or not columns <= row.keys():
                raise ValueError(f"Missing/empty GTFS table or columns: {name}")
        info = next(records(zf, "feed_info.txt"))
        start, end = [dt.datetime.strptime(info[k], "%Y%m%d").date()
                      for k in ("feed_start_date", "feed_end_date")]
        if not start <= today <= end:
            raise ValueError(f"Feed not valid today: {start} to {end}")
        if end < today + dt.timedelta(days=6):
            raise ValueError("Feed must cover the next seven days")
        active, _ = service_calendar(zf, today)
        if not any(active.values()):
            raise ValueError("No service during the next seven days")
        return active


def validate_bundle(bundle, previous, feed, active):
    if bundle["city"]["slug"] != "barcelona":
        raise ValueError("Unexpected city")
    if [r["line"] for r in bundle["loops"]] != [r["line"] for r in previous["loops"]]:
        raise ValueError("Editorial bus selections changed")
    if {p["name"] for p in bundle["all_pois"]} != {p["name"] for p in previous["all_pois"]}:
        raise ValueError("Editorial sight selections changed")
    with zipfile.ZipFile(feed) as zf:
        buses = {r["route_id"] for r in records(zf, "routes.txt") if is_bus_route(r["route_type"])}
        stops = {r["stop_id"] for r in records(zf, "stops.txt")}
        trips = {r["trip_id"]: r for r in records(zf, "trips.txt")}
        selected = {r["trip_id"] for r in bundle["loops"]}
        calls = {tid: set() for tid in selected}
        for r in records(zf, "stop_times.txt"):
            if r["trip_id"] in calls:
                calls[r["trip_id"]].add(r["stop_id"])
        for loop, old in zip(bundle["loops"], previous["loops"]):
            trip = trips[loop["trip_id"]]
            if loop["route_id"] not in buses or trip["route_id"] != loop["route_id"]:
                raise ValueError("Selected route is not a bus")
            if not active.get(trip["service_id"]):
                raise ValueError("Selected trip has no upcoming service")
            if len(loop["stops"]) < 2 or len(loop["shape"]) < 2:
                raise ValueError("Empty route geometry/stops")
            for st in loop["stops"]:
                if st["stop_id"] not in stops or st["stop_id"] not in calls[loop["trip_id"]]:
                    raise ValueError("Stop does not belong to the selected bus trip")
            points = loop["shape"] + [[s["lat"], s["lon"]] for s in loop["stops"]]
            for lat, lon in points:
                if not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Invalid coordinates")
            count = lambda r: len({p["name"] for s in r["stops"] for p in s["pois"]})
            if count(loop) < max(1, count(old) * 0.75):
                raise ValueError(f"Bus {loop['line']} lost more than 25% of its sights; review required")


def refresh(root=ROOT, feed_path=None):
    target = root / "site/routes.barcelona.json"
    previous = json.loads(target.read_text())
    today = dt.datetime.now(ZoneInfo("Europe/Madrid")).date()
    source = load("barcelona")["gtfs_mirror"]
    with tempfile.TemporaryDirectory(prefix="between-stops-refresh-") as tmp:
        work = Path(tmp)
        shutil.copytree(root / "scripts", work / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        data = work / "data/barcelona"
        data.mkdir(parents=True)
        feed = data / "gtfs.zip"
        if feed_path:
            shutil.copyfile(feed_path, feed)
        else:
            subprocess.run(["curl", "--fail", "--location", "--retry", "3",
                            "--connect-timeout", "20", "--max-time", "180",
                            "--max-filesize", "100000000", source, "--output", str(feed)], check=True)
        active = validate_feed(feed, today)
        # Published POIs are the editorial source; no automatic rewriting of copy.
        (data / "pois.json").write_text(json.dumps({"pois": previous["all_pois"]}))
        subprocess.run([sys.executable, str(work / "scripts/build_routes.py"),
                        "--city", "barcelona", "--lines", ",".join(r["line"] for r in previous["loops"]),
                        "--service-date", today.isoformat()], check=True, timeout=300)
        result = json.loads((work / "site/routes.barcelona.json").read_text())
        validate_bundle(result, previous, feed, active)
        # Preserve reviewed fares and editorial city copy, too.
        result["city"] = previous["city"]
        result["generated_from"].update({
            "refreshed_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "gtfs_source": source,
            "gtfs_sha256": hashlib.sha256(feed.read_bytes()).hexdigest(),
            "service_window_start": today.isoformat(),
            "service_window_end": (today + dt.timedelta(days=6)).isoformat(),
        })
        encoded = json.dumps(result, ensure_ascii=False, indent=1, allow_nan=False) + "\n"
        pending = target.with_suffix(".json.tmp")
        pending.write_text(encoded)
        pending.replace(target)
        print(f"Validated and refreshed {len(result['loops'])} Barcelona bus routes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed", type=Path, help="Use a local GTFS ZIP for an offline verification")
    args = parser.parse_args()
    refresh(feed_path=args.feed)
