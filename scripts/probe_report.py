#!/usr/bin/env python3
"""Aggregate every data/<city>/probe_result.json into one ranked comparison.

Run after fetch_pois.py --probe and build_routes.py --probe have produced a
probe_result.json for each candidate city. Prints a table sorted by
reachability, worst-to-best-verified.
"""

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def main():
    rows = []
    for f in sorted(DATA.glob("*/probe_result.json")):
        rows.append(json.loads(f.read_text()))
    rows.sort(key=lambda r: -r["reachability_pct"])

    w = max(len(r["name"]) for r in rows) if rows else 10
    print(f"{'City':<{w}}  {'Reach%':>7}  {'Reachable':>10}  {'BusStops':>9}  {'BestLine':>9}  {'/day':>5}")
    for r in rows:
        s = r["stats"]
        best = r["top_lines"][0] if r["top_lines"] else None
        print(
            f"{r['name']:<{w}}  {r['reachability_pct']:>6.1f}%  "
            f"{s['pois_bus_reachable']:>4}/{s['pois_total']:<5}  "
            f"{s['bbox_bus_stops']:>4}/{s['bbox_stops']:<4}  "
            f"{(best['line'] if best else '-'):>9}  "
            f"{(round(best['trips_per_day']) if best else 0):>5}"
        )


if __name__ == "__main__":
    main()
