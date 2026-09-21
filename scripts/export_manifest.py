#!/usr/bin/env python3
"""Generate site/cities.json — the single manifest that drives both the
gallery (site/index.html) and the in-city switcher (site/city.html).

LAUNCH_LIST is the explicit decision from the multi-city discussion: every
candidate city discussed, minus the ones confirmed "small enough to just
walk" (Antwerp, Florence, Amsterdam all matched that profile on probing).
Cities that failed for a different reason — Prague/Porto/Stockholm have no
bus line running often enough at all, which is not the same finding — are
still listed here per that decision, flagged `viable: false` so the curator
tool can warn about them, but not silently dropped from the public list.

Run this any time a city moves from probed to fully curated (i.e. whenever
site/routes.<slug>.json appears or changes), so the gallery picks it up.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cities  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DATA = ROOT / "data"

LAUNCH_LIST = [
    "barcelona", "rome", "paris", "london", "madrid", "budapest", "dublin",
    "munich", "copenhagen", "krakow", "porto", "prague", "stockholm",
]

# Cities discussed but excluded as "small enough to just walk" — kept out of
# the manifest entirely rather than shown with a badge, since that finding is
# about the city, not about curation status.
EXCLUDED_WALKABLE = {"antwerp", "florence", "amsterdam"}


def main():
    entries = []
    for slug in LAUNCH_LIST:
        if slug in EXCLUDED_WALKABLE:
            continue
        city = cities.load(slug)
        route_file = SITE / f"routes.{slug}.json"
        probe_file = DATA / slug / "probe_result.json"

        entry = {
            "slug": slug,
            "name": city["name"],
            "country": city["country"],
            "operator": city["operator"],
        }

        if route_file.exists() and city["curated"]:
            doc = json.loads(route_file.read_text())
            entry.update({
                "status": "live",
                "file": route_file.name,
                "loops": len(doc["loops"]),
                "sights": doc["stats"]["pois_bus_reachable"],
            })
        else:
            entry["status"] = "coming_soon"
            if probe_file.exists():
                probe = json.loads(probe_file.read_text())
                has_viable_line = any(
                    l.get("trips_per_day", 0) for l in probe.get("loops_preview", [])
                )
                entry["probe_reach_pct"] = probe["reachability_pct"]
                entry["probe_viable"] = has_viable_line
        entries.append(entry)

    # live cities first, then coming-soon alphabetically
    entries.sort(key=lambda e: (e["status"] != "live", e["name"]))
    (SITE / "cities.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1))
    live = [e["name"] for e in entries if e["status"] == "live"]
    soon = [e["name"] for e in entries if e["status"] != "live"]
    print(f"wrote site/cities.json — {len(entries)} cities", file=sys.stderr)
    print(f"  live: {', '.join(live) or '(none)'}", file=sys.stderr)
    print(f"  coming soon: {', '.join(soon)}", file=sys.stderr)


if __name__ == "__main__":
    main()
