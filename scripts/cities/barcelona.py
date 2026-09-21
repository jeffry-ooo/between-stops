"""Barcelona, Spain — TMB (Transports Metropolitans de Barcelona).

The interesting case for this idea. Barcelona's sights are genuinely spread out
— Park Güell, Montjuïc and the Sagrada Família are kilometres apart and uphill —
and TMB's bus network was rebuilt in the 2010s into a high-frequency orthogonal
grid (the H/V/D lines) that actually reaches them. The Bus Turístic costs ~€33.

Keys are matched case-insensitively against name / name:ca / name:es / name:en.
"""

CITY = {
    "slug": "barcelona",
    "name": "Barcelona",
    "country": "Spain",
    "operator": "TMB",
    "operator_url": "https://www.tmb.cat",
    # Ciutat Vella, Eixample, Gràcia/Park Güell, Montjuïc, Barceloneta, Les Corts
    "bbox": (41.35, 2.11, 41.43, 2.22),
    "gtfs_mirror": (
        "https://storage.googleapis.com/mdb-latest/"
        "es-barcelona-transports-metropolitans-de-barcelona-tmb-gtfs-2359.zip"
    ),
    "gtfs_official": {
        "portal": "https://developer.tmb.cat",
        "dataset": "https://www.tmb.cat/en/about-tmb/tools-for-developers",
        "endpoint": "https://api.tmb.cat/v1/static/datasets/gtfs.zip",
        "auth_header": "query params app_id / app_key",
        "env_var": "TMB_APP_ID / TMB_APP_KEY",
        "note": "free registration required; create a Public API Application",
    },
    "tour_price_eur": 33,
    "ticket_note": "a T-casual gives 10 rides for about €12.55",
    # TMB is a city feed, not a regional one, so the frequency floor can be
    # higher: a Barcelona city bus that runs less than this is a marginal route.
    "min_trips_per_day": 70,  # relaxed: a bus every ~20-30 min is fine
    "min_marginal_gain": 4.0,
    "top_n": 4,
    "extra_selectors": [
        'nwr["place"="square"]["name"]({bbox});',
        'nwr["building"~"^(cathedral|church)$"]["name"]({bbox});',
        'nwr["leisure"="stadium"]["name"]({bbox});',
        'nwr["natural"="beach"]["name"]({bbox});',
        'nwr["amenity"~"^(marketplace|theatre|arts_centre)$"]["name"]({bbox});',
        'nwr["man_made"="tower"]["name"]({bbox});',
    ],
}

# The sights a first-time visitor would be annoyed to miss. Explicit editorial
# judgement, not a data signal — every one of these has a wikidata tag, so OSM
# offers nothing to discriminate on. Weighted 2.5x in ranking so a line serving
# the Sagrada Família outranks one serving five minor squares in the old town.
MUST_SEE = {
    "Sagrada Família", "Park Güell", "Casa Batlló", "Casa Milà (La Pedrera)",
    "Barcelona Cathedral", "La Rambla", "La Boqueria", "Santa Maria del Mar",
    "Museu Picasso", "MNAC", "Montjuïc Castle", "Palau de la Música Catalana",
    "Camp Nou", "Recinte Modernista de Sant Pau",
}

CURATED = {
    # --- Gaudí & modernisme ----------------------------------------------
    "basílica de la sagrada família": (
        "Sagrada Família",
        "Gaudí's unfinished basilica — a forest of stone columns under stained glass, topped out in 2026.",
    ),
    "temple expiatori de la sagrada família": (
        "Sagrada Família",
        "Gaudí's unfinished basilica — a forest of stone columns under stained glass, topped out in 2026.",
    ),
    "park güell": (
        "Park Güell",
        "Gaudí's failed housing estate turned mosaic terrace, with the whole city laid out below.",
    ),
    "casa batlló": (
        "Casa Batlló",
        "The dragon-backed house on Passeig de Gràcia — no straight lines, bone-like balconies.",
    ),
    "casa milà": (
        "Casa Milà (La Pedrera)",
        "Gaudí's wave-fronted apartment block; the roof is a garden of chimney warriors.",
    ),
    "la pedrera": (
        "Casa Milà (La Pedrera)",
        "Gaudí's wave-fronted apartment block; the roof is a garden of chimney warriors.",
    ),
    "palau güell": (
        "Palau Güell",
        "Gaudí's early mansion off the Rambla, with a parabolic hall and 20 tiled roof chimneys.",
    ),
    "casa vicens": (
        "Casa Vicens",
        "Gaudí's first house — green tiles and Moorish geometry, opened to visitors only in 2017.",
    ),
    "palau de la música catalana": (
        "Palau de la Música Catalana",
        "Domènech i Montaner's concert hall: an inverted stained-glass skylight over the stalls.",
    ),
    "hospital de la santa creu i sant pau": (
        "Recinte Modernista de Sant Pau",
        "A hospital built as a garden village of mosaic pavilions — the largest art nouveau site in Europe.",
    ),
    "recinte modernista de sant pau": (
        "Recinte Modernista de Sant Pau",
        "A hospital built as a garden village of mosaic pavilions — the largest art nouveau site in Europe.",
    ),
    "casa amatller": (
        "Casa Amatller",
        "Puig i Cadafalch's stepped Flemish gable, next door to Casa Batlló in the Block of Discord.",
    ),
    "torre bellesguard": (
        "Torre Bellesguard",
        "A little-visited Gaudí castle on the slope of Tibidabo, built over a medieval royal ruin.",
    ),
    # --- Ciutat Vella ------------------------------------------------------
    "catedral de barcelona": (
        "Barcelona Cathedral",
        "The Gothic cathedral of Santa Eulàlia, with 13 white geese in its cloister — one per year of her life.",
    ),
    "catedral de la santa creu i santa eulàlia": (
        "Barcelona Cathedral",
        "The Gothic cathedral of Santa Eulàlia, with 13 white geese in its cloister — one per year of her life.",
    ),
    "basílica de santa maria del mar": (
        "Santa Maria del Mar",
        "Catalan Gothic at its purest — built in 55 years by the porters of the Born, and it shows.",
    ),
    "parròquia basílica de santa maria del pi": (
        "Santa Maria del Pi",
        "One vast nave and a rose window the size of a room, on a square of the same name.",
    ),
    "basílica de santa maria del pi": (
        "Santa Maria del Pi",
        "One vast nave and a rose window the size of a room, on a square of the same name.",
    ),
    "plaça reial": (
        "Plaça Reial",
        "Palm-shaded arcaded square off the Rambla; the lampposts are an early Gaudí commission.",
    ),
    "plaça de sant jaume": (
        "Plaça de Sant Jaume",
        "Where the city hall faces the Catalan government across the old Roman crossroads.",
    ),
    "la rambla": (
        "La Rambla",
        "The 1.2 km promenade down a filled-in stream bed, from Catalunya to the sea.",
    ),
    "mercat de sant josep - la boqueria": (
        "La Boqueria",
        "The Rambla's cathedral of food, under a wrought-iron roof of 1914.",
    ),
    "mercat de la boqueria": (
        "La Boqueria",
        "The Rambla's cathedral of food, under a wrought-iron roof of 1914.",
    ),
    "museu picasso": (
        "Museu Picasso",
        "Five medieval palaces holding the painter's youth — the work before he became Picasso.",
    ),
    "el born": (
        "El Born CCM",
        "A market hall built over the streets flattened in 1714, now excavated beneath your feet.",
    ),
    "el born centre de cultura i memòria": (
        "El Born CCM",
        "A market hall built over the streets flattened in 1714, now excavated beneath your feet.",
    ),
    "palau de la generalitat de catalunya": (
        "Palau de la Generalitat",
        "Seat of Catalan government since 1400 — one of the oldest working government buildings anywhere.",
    ),
    "museu marítim de barcelona": (
        "Maritime Museum",
        "The medieval royal shipyards, where galleys were built indoors under stone arches.",
    ),
    "monument a colom": (
        "Columbus Monument",
        "A 60 m column at the foot of the Rambla; the lift to the top is the cheapest view in town.",
    ),
    "mirador de colom": (
        "Columbus Monument",
        "A 60 m column at the foot of the Rambla; the lift to the top is the cheapest view in town.",
    ),
    "macba": (
        "MACBA",
        "Richard Meier's white box of contemporary art, its plaza colonised by skateboarders.",
    ),
    "museu d'art contemporani de barcelona": (
        "MACBA",
        "Richard Meier's white box of contemporary art, its plaza colonised by skateboarders.",
    ),
    "centre de cultura contemporània de barcelona": (
        "CCCB",
        "A former workhouse turned exhibition hall, with a mirrored wall reflecting the skyline.",
    ),
    # --- Montjuïc ----------------------------------------------------------
    "museu nacional d'art de catalunya": (
        "MNAC",
        "Romanesque frescoes rescued from Pyrenean churches, in a palace above the Magic Fountain.",
    ),
    "font màgica de montjuïc": (
        "Magic Fountain",
        "The 1929 fountain that still does its light-and-water show below the MNAC steps.",
    ),
    "castell de montjuïc": (
        "Montjuïc Castle",
        "The fortress that shelled the city more than it defended it; now the best 360° viewpoint.",
    ),
    "fundació joan miró": (
        "Fundació Joan Miró",
        "Miró's own foundation in a white Sert building full of Mediterranean light.",
    ),
    "poble espanyol": (
        "Poble Espanyol",
        "An open-air village of replica Spanish architecture, built for the 1929 Expo and never removed.",
    ),
    "estadi olímpic lluís companys": (
        "Olympic Stadium",
        "The 1929 stadium reworked for 1992; the Anella Olímpica around it is free to wander.",
    ),
    "pavelló mies van der rohe": (
        "Mies van der Rohe Pavilion",
        "The Barcelona Pavilion — travertine, onyx and a chair that defined a century.",
    ),
    "jardí botànic de barcelona": (
        "Botanical Garden",
        "Mediterranean-climate plants from five continents, terraced down the Montjuïc slope.",
    ),
    "plaça d'espanya": (
        "Plaça d'Espanya",
        "The Venetian-towered gateway to Montjuïc, and one of the city's great traffic circles.",
    ),
    "arenas de barcelona": (
        "Arenas de Barcelona",
        "A Moorish-revival bullring turned shopping centre, with a free rooftop walkway.",
    ),
    # --- Waterfront & Ciutadella -------------------------------------------
    "parc de la ciutadella": (
        "Parc de la Ciutadella",
        "The city's central park, with a cascade the young Gaudí helped design.",
    ),
    "arc de triomf": (
        "Arc de Triomf",
        "Red-brick arch built as the gateway to the 1888 World Fair — Moorish, not Roman.",
    ),
    "platja de la barceloneta": (
        "Barceloneta Beach",
        "The city beach that did not exist before 1992, when the Olympics opened the seafront.",
    ),
    "zoo de barcelona": (
        "Barcelona Zoo",
        "Inside the Ciutadella park; once home to Snowflake, the only known albino gorilla.",
    ),
    "port vell": (
        "Port Vell",
        "The old harbour, reclaimed from container yards into a marina and boardwalk.",
    ),
    # --- Eixample & beyond --------------------------------------------------
    "plaça de catalunya": (
        "Plaça de Catalunya",
        "The hinge between the old city and the Eixample grid, and everyone's meeting point.",
    ),
    "passeig de gràcia": (
        "Passeig de Gràcia",
        "The boulevard where the bourgeoisie competed by architect; Gaudí won twice.",
    ),
    "torre glòries": (
        "Torre Glòries",
        "Nouvel's iridescent bullet over the Diagonal — a lift to the viewing deck opened in 2022.",
    ),
    "spotify camp nou": (
        "Camp Nou",
        "Europe's largest football stadium, rebuilt around the club's museum.",
    ),
    "camp nou": (
        "Camp Nou",
        "Europe's largest football stadium, rebuilt around the club's museum.",
    ),
    "temple expiatori del sagrat cor": (
        "Tibidabo — Sagrat Cor",
        "The church crowning the city's highest hill, beside a working 1901 funfair.",
    ),
    "mercat de sant antoni": (
        "Mercat de Sant Antoni",
        "A cast-iron market on a Greek-cross plan, reopened in 2018 over Roman road remains.",
    ),
}
