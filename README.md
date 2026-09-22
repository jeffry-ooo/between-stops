# Between Stops

Public spike: https://jeffry-ooo.github.io/between-stops/

Free, open-source, bus-only sightseeing. This is an early prototype using
generated timetable snapshots, not live arrivals. The current public gallery
has Barcelona available; Antwerp's generated bundle remains a development fixture.

## GitHub Pages hosting

Pushes to `main` run `.github/workflows/pages.yml`. It packages the public
files from `site/` with `python3 scripts/prepare_pages.py` and deploys `_site/`
to GitHub Pages. The local curator and its large data bundles are not deployed.
Hosting uses the free GitHub Pages address and standard Actions runner.

The same workflow refreshes Barcelona daily at **03:17 UTC**, on pushes to
`main`, and on manual runs. It downloads the public MobilityData GTFS mirror,
checks ZIP integrity, required tables, validity through the next seven days,
bus-only route/trip/stop references, geometry and sight coverage, then rebuilds
and commits the compact JSON before deploying. No API key or paid service is needed.

The existing bus lines, sights, descriptions and fares are preserved. Trip
selection and frequency averages use service in the next seven days. These
remain approximate timetable summaries, not real-time arrivals or guarantees
that the illustrated trip runs at the visitor's chosen time.

A failed download, validation, test or build stops deployment; the last successful
Pages release stays live. A concurrent source change makes the snapshot push
fail rather than overwrite newer work. See Actions for the failure and enable
GitHub Actions failure emails in your personal notification settings. The city
page shows the last successful check and warns after three days or feed expiry.

GitHub schedules are best effort and public-repository schedules can be disabled
after 60 days without activity. Check Actions if freshness becomes overdue;
manual Run workflow is always available. No raw feed or growing daily artifact
archive is committed; Pages artifacts expire after one day.

Local verification:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/refresh_data.py                 # download, validate, rebuild
python3 scripts/refresh_data.py --feed /path/to/gtfs.zip  # offline rebuild
python3 scripts/prepare_pages.py
```

OSM candidate refresh and editorial changes remain manual (`make pois`), pending
a review flow that can show additions/removals without replacing curated sights.
Only Barcelona is refreshed automatically in this first version.

In repository Settings → Pages, the source must be **GitHub Actions**.
To retry a deployment, use Actions → Deploy GitHub Pages → Run workflow.

Curator bundles are generated locally with `make CITY=barcelona curator-data`
after obtaining the source GTFS and OSM data.

## Original spike notes

A spike: overlay a city's must-see sights onto **ordinary public bus routes**, so a
tourist can ride with one regular ticket instead of paying for a hop-on-hop-off tour.

Static site, no backend, no database, no auth. Open source, non-commercial.
Two cities so far: **Barcelona** and **Antwerp**.

```bash
make every && make serve     # http://localhost:8000
```

---

## Does the GTFS need an API key?

**Both operators: yes — free, but mandatory registration.** Neither publishes a
plain downloadable zip.

| | Antwerp | Barcelona |
|---|---|---|
| Operator | De Lijn | TMB |
| Portal | `data.delijn.be` | `developer.tmb.cat` |
| Auth | `Ocp-Apim-Subscription-Key` header | `app_id` + `app_key` query params |
| Endpoint | `api.delijn.be/gtfs/v3/static` | `api.tmb.cat/v1/static/datasets/gtfs.zip` |
| Env vars | `DELIJN_KEY` | `TMB_APP_ID`, `TMB_APP_KEY` |

`transportdata.be/dataset/de-lijn-gtfs-static` is not a file — its only resource is a
pointer to De Lijn's portal. Without a key the endpoint returns `404`, masking
unauthorised as not-found. Registration is free but it *is* registration, so this spike
does not use it.

**What it uses instead:** MobilityData's public mirrors of the same feeds, no
registration needed. `scripts/fetch_gtfs.sh` prefers the official API whenever the key
env vars are set, so switching is one export.

| City | Mirror | Feed version | Valid |
|---|---|---|---|
| Antwerp | `mdb-latest/be-vlaams-gewest-de-lijn-gtfs-684.zip` | `20260601_20260930_003000` | 2026-06-01 → 09-30 |
| Barcelona | `mdb-latest/es-…-tmb-gtfs-2359.zip` | `084410042026002` | 2026-04-10 → 12-05 |

Two traps worth knowing: the `gtfs.irail.be` mirror that MobilityData still lists as De
Lijn's producer URL is dead (404), and TMB has **two** entries in the registry —
`mdb-1007` is stale from 2019, `mdb-2359` is current.

---

## Run it

```bash
make every                       # both cities, end to end
make CITY=barcelona routes       # one city
make serve                       # http://localhost:8000
```

Individual steps:

```bash
./scripts/fetch_gtfs.sh barcelona          # step 1 — GTFS zip (gitignored)
python3 scripts/fetch_pois.py  --city barcelona   # step 2 — Overpass
python3 scripts/build_routes.py --city barcelona  # steps 3+4
```

No dependencies beyond Python 3 stdlib and `curl`. `site/` is a plain static directory —
drop it on GitHub Pages as-is.

**Adding a city** is one file: `scripts/cities/<slug>.py` with a `CITY` dict (bbox, mirror
URL, thresholds), a `CURATED` name→description map, and a `MUST_SEE` set. Add the slug to
`ALL` in `scripts/cities/__init__.py`. The site's city switcher is generated from
`site/cities.json`, which the build writes — no front-end edit needed.

---

## How it works

**Step 1 — GTFS.** Feeds vary enormously: De Lijn's covers all of Flanders (2.5 GB
unzipped, a 2 GB `stop_times.txt`, 8.9 M shape points) while TMB's is one city (52 MB).
Nothing is ever extracted to disk or read whole — everything streams out of the zip and
filters on `stop_id` first, which discards >99% of the biggest file with a set lookup.

| | Antwerp | Barcelona |
|---|---|---|
| `stop_times.txt` rows | 13.0 M → 965 k in bbox | 1.17 M → 828 k in bbox |
| stops | 30,617 → 507 in bbox | 3,450 → 2,185 in bbox |
| bus routes (`route_type=3`) | 2,040 of 2,090 | 105 of 116 |
| build time | ~15 s | ~1 s |

Service frequency comes from `calendar.txt`, `calendar_dates.txt` or both — De Lijn ships
only the latter, TMB ships a four-row calendar plus 26 k date exceptions — and
`frequencies.txt` is expanded where present.

**Step 2 — POIs.** One Overpass query per city, no key. It unions the brief's tag families
(`tourism`, `historic`, `amenity=place_of_worship`, `leisure=park`) with per-city extras
and an **exact-name pass**, because headline sights are tagged inconsistently: the Grote
Markt is a `place=square`, Barcelona's zoo a `tourism=zoo`, Camp Nou a `leisure=stadium`.
Raw results (590 in Antwerp, 2,462 in Barcelona) are cut to a curated shortlist — OSM
supplies geometry and tags, the one-line descriptions are hand-written.

**Step 3 — matching.** Haversine, 300 m, POI → stop. Crow-flies, not routed, as specified.
Only stops a *bus* actually calls at count; matching against every stop in the box would
silently count tram and metro stops and badly overstate reach.

**Step 4 — ranking.** Four rules:

1. `score = Σ POI weights + 1.5 × distinct 700 m district cells`, so geographic spread can
   outrank raw count — 5 sights on one street scores 6.5, 4 sights in 4 districts scores 10.
2. **Must-see weighting (2.5×).** Explicit editorial judgement, not a data signal — every
   major sight has a `wikidata` tag, so OSM offers nothing to discriminate on. Without it
   Barcelona's ranking put 17 minor old-town squares above the Sagrada Família.
3. **Frequency floor** (80/day Antwerp, 120/day Barcelona). Drops Antwerp's **X19**
   — 3rd on sights, but it is *"Snelbus Antwerpen–Kontich–Rumst"*, a peak-only commuter
   express at 59/day — and Barcelona's **120**, a 39/day neighbourhood minibus.
4. **Greedy complementary selection.** After the best line is taken, the rest are re-scored
   on the sights they *add*. Without it Antwerp's 18 and 22 both won by serving the same
   Groenplaats cluster.

Service variants (`18`, `18a`, `18b`, `18c`) collapse to the line a tourist boards.
`data/<city>/route_scores.csv` has every line scored, for inspection.

---

## What came out

### Barcelona — 4 loops, 43 of 45 sights bus-reachable

| Line | Route | Sights | Buses/day |
|---|---|---|---|
| **59** | Poblenou / Pl. Reina Maria Cristina | 17 | 138 |
| **150** | Pl. Espanya / Castell de Montjuïc | 9 | 121 |
| **V17** | Port Vell / Vall d'Hebron | 11 | 139 |
| **D50** | Paral·lel / Ciutat Meridiana | 8 | 186 |

Line **59** is the waterfront-and-Rambla run: Zoo → Barceloneta Beach → Santa Maria del
Mar → Columbus Monument & Maritime Museum → Palau Güell & Plaça Reial → Santa Maria del Pi
& La Boqueria → Plaça de Catalunya. Line **150** is effectively a museum-hill shuttle
that happens to be a normal city bus — Mies van der Rohe Pavilion (69 m), Magic Fountain,
Poble Espanyol, MNAC, Olympic Stadium, Fundació Joan Miró, Botanical Garden, Montjuïc
Castle. **D50** exists in the set to reach the Sagrada Família; **V17** picks up Casa
Batlló and Casa Milà.

10 of 14 must-sees are covered. The misses: **Park Güell** has no bus stop within 300 m at
all (nearest is 401 m — it is up a steep hill, which is why TMB runs a dedicated Bus Güell
shuttle), and Barcelona Cathedral, Camp Nou and Sant Pau sit on lines that ranked below the
cut. A fifth loop would pick most of them up.

### Antwerp — 2 loops, 21 of 43 sights bus-reachable

| Line | Route | Sights | Buses/day |
|---|---|---|---|
| **17** | Brouwersvliet – Centraal Station – UZA | 11 | 171 |
| **18** | Aartselaar – Antwerpen Groenplaats | 8 | 126 |

A third loop would have added exactly one sight, below the marginal-gain threshold, so the
pipeline stops at two.

### The comparison is the actual result

| | Antwerp | Barcelona |
|---|---|---|
| Sights within 300 m of a bus stop | **21 / 43 (49%)** | **43 / 45 (96%)** |
| Bbox stops served by a bus | 342 / 507 | 1,638 / 2,185 |
| Sights covered by the chosen loops | 18 | 32 |

**Antwerp partly refutes the premise; Barcelona vindicates it.** Antwerp's historic core is
pedestrianised and tram-served — Het Steen, Rubens House, St. Paul's, the Vleeshuis, City
Hall and the Red Star Line Museum have no bus within walking distance — and the whole
centre is walkable anyway, so the bus adds little. Barcelona is the opposite: the sights
are kilometres apart, Montjuïc and Park Güell are uphill, and TMB's post-2012 orthogonal
grid (the H/V/D lines) is high-frequency and reaches almost everything. That is exactly
the situation a paid hop-on-hop-off tour is sold into, and where a free alternative has
something to offer.

Both sites state their gaps rather than hiding them: a panel lists every unreachable sight
with its nearest bus stop and can plot them on the map in grey.

---

## Site

`site/` — `index.html` + `styles.css` + `app.js` + generated `routes.<city>.json` and
`cities.json`. Leaflet 1.9.4 from cdnjs, OSM tiles, no key, no build step, no framework.

City switcher (deep-linkable via `?city=barcelona`), loop switcher, must-see sights starred
and given larger gold pins, an itinerary that reads as instructions — each sight listed
once, at the stop you'd actually get off at — 300 m walk circles so the walkability claim
is visible, out-of-area route tails dashed back, a "why these lines" panel with the full
ranking table, light/dark, and a mobile layout.

---

## Limitations

- Walking distance is straight-line. A 250 m crow-flies hop across a harbour is not a
  250 m walk. Real routing (OSRM/Valhalla foot profile) is the fix, and would change
  Barcelona's Montjuïc numbers most.
- No timetables — "buses/day" is averaged over the feed period, not a departure board.
- One representative trip per line supplies the shape and stop order, so each itinerary is
  one direction of one variant.
- Descriptions and the must-see list are hand-written editorial judgement, not sourced.
- Buses only, by design. Adding tram and metro (`route_type` 0 and 1) is a one-constant
  change and would transform the Antwerp result.

## Licence & attribution

Code MIT. Transit data © [De Lijn](https://www.delijn.be) and © [TMB](https://www.tmb.cat).
Map data and POIs © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
ODbL — derived data here is ODbL too. Tiles from openstreetmap.org, subject to their
[tile usage policy](https://operations.osmfoundation.org/policies/tiles/): fine for a
spike, not for production traffic. Non-commercial.
