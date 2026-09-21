"""Antwerp, Belgium — De Lijn.

The historic core is pedestrianised and tram-served, so bus reach is genuinely
limited here; see the README. Descriptions are hand-written, geometry is OSM's.
"""

CITY = {
    "slug": "antwerp",
    "name": "Antwerp",
    "country": "Belgium",
    "operator": "De Lijn",
    "operator_url": "https://www.delijn.be",
    # historic core, Zuid, Eilandje, Zoo / Centraal Station
    "bbox": (51.19, 4.38, 51.25, 4.45),
    "gtfs_mirror": "https://storage.googleapis.com/mdb-latest/be-vlaams-gewest-de-lijn-gtfs-684.zip",
    "gtfs_official": {
        "portal": "https://data.delijn.be",
        "dataset": "https://transportdata.be/dataset/de-lijn-gtfs-static",
        "endpoint": "https://api.delijn.be/gtfs/v3/static",
        "auth_header": "Ocp-Apim-Subscription-Key",
        "env_var": "DELIJN_KEY",
        "note": "free registration required; returns 404 without a key",
    },
    "tour_price_eur": 25,
    "ticket_note": "one De Lijn ticket also covers the trams",
    # De Lijn's feed is all of Flanders, so these are tuned for a big feed
    "min_trips_per_day": 70,  # relaxed: a bus every ~20-30 min is fine
    "min_marginal_gain": 4.0,
    "top_n": 3,
    # extra Overpass tag families beyond the brief's, for locally-tagged sights
    "extra_selectors": [
        'nwr["amenity"~"^(courthouse|theatre|arts_centre)$"]["name"]({bbox});',
        'nwr["place"="square"]["name"]({bbox});',
        'nwr["building"~"^(cathedral|church)$"]["name"]({bbox});',
    ],
}

# See barcelona.py — the sights a first-time visitor would be annoyed to miss.
MUST_SEE = {
    "Cathedral of Our Lady", "Rubens House", "Grote Markt", "Het Steen",
    "MAS | Museum aan de Stroom", "Plantin-Moretus Museum",
    "Royal Museum of Fine Arts (KMSKA)", "Antwerp Central Station",
    "Red Star Line Museum",
}

CURATED = {
    # --- Historic core ---------------------------------------------------
    "onze-lieve-vrouwekathedraal": (
        "Cathedral of Our Lady",
        "Belgium's tallest cathedral — 123m of Brabantine Gothic, with four Rubens altarpieces inside.",
    ),
    "grote markt": (
        "Grote Markt",
        "The guildhall-lined main square, with the Brabo fountain flinging a severed hand at its centre.",
    ),
    "stadhuis": (
        "City Hall",
        "1560s Renaissance city hall on the Grote Markt, a UNESCO-listed civic landmark.",
    ),
    "het steen": (
        "Het Steen",
        "The 13th-century riverside castle — Antwerp's oldest building, now the visitor centre.",
    ),
    "vleeshuis": (
        "Vleeshuis",
        "The butchers' guildhall of 1504, striped like streaky bacon; now a music museum.",
    ),
    "sint-carolus borromeuskerk": (
        "St. Charles Borromeo Church",
        "Baroque church whose façade Rubens helped design; the ceiling paintings burned in 1718.",
    ),
    "sint-pauluskerk": (
        "St. Paul's Church",
        "Gothic Dominican church with a startling baroque calvary garden tucked beside it.",
    ),
    "sint-jacobskerk": (
        "St. James' Church",
        "Rubens' burial place, and the richest church interior in the city.",
    ),
    "sint-andrieskerk": (
        "St. Andrew's Church",
        "Parish church of the old Sint-Andries quarter, with a memorial to Mary, Queen of Scots.",
    ),
    "handelsbeurs": (
        "Handelsbeurs",
        "The world's first purpose-built commodity exchange, reopened after a long restoration.",
    ),
    "rubenshuis": (
        "Rubens House",
        "The painter's own home and studio, with an Italianate portico he designed himself.",
    ),
    "plantin-moretusmuseum": (
        "Plantin-Moretus Museum",
        "UNESCO-listed printing house with the two oldest surviving printing presses in the world.",
    ),
    "maagdenhuis": (
        "Maagdenhuis",
        "Former foundling girls' orphanage, now a small museum of Flemish masters and food bowls.",
    ),
    "rockoxhuis": (
        "Snijders&Rockox House",
        "The patrician home of Rubens' patron, hung as a 17th-century collector would have had it.",
    ),
    "sint-annatunnel": (
        "St. Anna Pedestrian Tunnel",
        "1933 tunnel under the Scheldt, reached by the original wooden escalators.",
    ),
    "ruihuis": (
        "Ruihuis",
        "Entrance to the Ruien — the covered medieval canals running under the old town.",
    ),
    # --- Zuid ------------------------------------------------------------
    "koninklijk museum voor schone kunsten antwerpen": (
        "Royal Museum of Fine Arts (KMSKA)",
        "Reopened in 2022 after eleven years — Van Eyck, Memling, Ensor and Rubens at full scale.",
    ),
    "museum voor hedendaagse kunst antwerpen": (
        "M HKA",
        "Antwerp's contemporary art museum, in a converted grain silo on the Zuid waterfront.",
    ),
    "fotomuseum antwerpen": (
        "FOMU (Photo Museum)",
        "One of Europe's serious photography museums, with a 3-million-image collection.",
    ),
    "koning albertpark": (
        "Koning Albertpark",
        "Green wedge along the southern ring, good for a breather between museums.",
    ),
    "zuiderpershuis": (
        "Zuiderpershuis",
        "Neo-Gothic hydraulic power station of 1882, now a world-music venue.",
    ),
    # --- Eilandje / docks -------------------------------------------------
    "mas": (
        "MAS | Museum aan de Stroom",
        "Ten stacked red-sandstone boxes; the free rooftop spiral is the best view in Antwerp.",
    ),
    "museum aan de stroom": (
        "MAS | Museum aan de Stroom",
        "Ten stacked red-sandstone boxes; the free rooftop spiral is the best view in Antwerp.",
    ),
    "red star line museum": (
        "Red Star Line Museum",
        "In the sheds where two million emigrants were deloused before sailing to New York.",
    ),
    "havenhuis": (
        "Port House",
        "Zaha Hadid's glass diamond balanced on a replica Hanseatic fire station.",
    ),
    "sint-felixpakhuis": (
        "Sint-Felixpakhuis",
        "Vast 1860s warehouse split by a covered street; now the city archive.",
    ),
    "loodswezen": ("Loodswezen", "Neo-Gothic pilotage building on the quay, a Scheldt-front landmark."),
    "loodsgebouw": ("Loodswezen", "Neo-Gothic pilotage building on the quay, a Scheldt-front landmark."),
    "park spoor noord": (
        "Park Spoor Noord",
        "A 24-hectare park laid over a demolished railway yard — the city's favourite new green space.",
    ),
    # --- Centraal Station / Zoo / Diamond quarter -------------------------
    "antwerpen-centraal": (
        "Antwerp Central Station",
        "The 'railway cathedral' — a stone-and-iron dome over four levels of platforms.",
    ),
    "antwerpen centraal": (
        "Antwerp Central Station",
        "The 'railway cathedral' — a stone-and-iron dome over four levels of platforms.",
    ),
    "zoo antwerpen": (
        "Antwerp Zoo",
        "Founded 1843, right beside Central Station — one of the oldest zoos in the world.",
    ),
    "stadspark": (
        "Stadspark",
        "Romantic 19th-century park on the line of the old Spanish ramparts.",
    ),
    "sint-joriskerk": ("St. George's Church", "Neo-Gothic parish church on the line of the old city walls."),
    "hendrik conscienceplein": (
        "Hendrik Conscienceplein",
        "Antwerp's most complete baroque square, car-free and lit by gas lamps.",
    ),
    "bourlaschouwburg": (
        "Bourla Theatre",
        "1834 neoclassical playhouse, the last surviving continental theatre of its type.",
    ),
    "koningin astridplein": (
        "Koningin Astridplein",
        "The square in front of Central Station, gateway to the zoo and the diamond quarter.",
    ),
    "de koninck": (
        "De Koninck City Brewery",
        "The bolleke brewery, with a tasting room and food hall in the old stables.",
    ),
    "justitiepaleis": (
        "Law Courts",
        "Richard Rogers' 'sails' over the southern approach — a modern city gate.",
    ),
    "brouwershuis": (
        "Brewers' House",
        "16th-century water house that pumped the city's brewing water, with machinery intact.",
    ),
    "sint-augustinuskerk": (
        "AMUZ (St. Augustine's Church)",
        "Deconsecrated baroque church turned concert hall for early music.",
    ),
    "koninklijk paleis": (
        "Royal Palace (Paleis op de Meir)",
        "Napoleon's Antwerp residence on the shopping street, with a chocolate salon downstairs.",
    ),
    "paleis op de meir": (
        "Royal Palace (Paleis op de Meir)",
        "Napoleon's Antwerp residence on the shopping street, with a chocolate salon downstairs.",
    ),
    "diamantwijk": (
        "Diamond District",
        "Four streets behind the station through which most of the world's rough diamonds pass.",
    ),
    "boerentoren": (
        "Boerentoren",
        "Europe's first skyscraper (1932), an art-deco slab over the Meir.",
    ),
    "museum plantin-moretus": (
        "Plantin-Moretus Museum",
        "UNESCO-listed printing house with the two oldest surviving printing presses in the world.",
    ),
    "m hka": (
        "M HKA",
        "Antwerp's contemporary art museum, in a converted grain silo on the Zuid waterfront.",
    ),
    "muhka": (
        "M HKA",
        "Antwerp's contemporary art museum, in a converted grain silo on the Zuid waterfront.",
    ),
    "felixarchief": (
        "Sint-Felixpakhuis",
        "Vast 1860s warehouse split by a covered street; now the city archive.",
    ),
    "snijders & rockoxhuis": (
        "Snijders&Rockox House",
        "The patrician home of Rubens' patron, hung as a 17th-century collector would have had it.",
    ),
    "diamantkwartier": (
        "Diamond District",
        "Four streets behind the station through which most of the world's rough diamonds pass.",
    ),
    "momu": (
        "MoMu (Fashion Museum)",
        "Belgium's fashion museum — home turf of the Antwerp Six, reopened in 2021.",
    ),
    "diva": (
        "DIVA",
        "Museum of diamonds, silver and jewellery, in a townhouse off the Grote Markt.",
    ),
    "koninklijke zoo van antwerpen": (
        "Antwerp Zoo",
        "Founded 1843, right beside Central Station — one of the oldest zoos in the world.",
    ),
}
