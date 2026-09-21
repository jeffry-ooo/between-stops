CITY ?= barcelona
CITIES = antwerp barcelona

.PHONY: all every pois routes manifest curator-data serve clean help
all: routes                        ## build one city (CITY=barcelona by default)

every:                             ## build every city end to end, then refresh cities.json
	@for c in $(CITIES); do $(MAKE) --no-print-directory CITY=$$c routes; done
	$(MAKE) --no-print-directory manifest

data/$(CITY)/gtfs.zip:
	./scripts/fetch_gtfs.sh $(CITY)

data/$(CITY)/pois.json:
	python3 scripts/fetch_pois.py --city $(CITY)

pois:                              ## re-fetch POIs from OpenStreetMap
	python3 scripts/fetch_pois.py --city $(CITY)

routes: data/$(CITY)/gtfs.zip data/$(CITY)/pois.json  ## build site/routes.$(CITY).json
	python3 scripts/build_routes.py --city $(CITY)
	$(MAKE) --no-print-directory manifest

manifest:                          ## rebuild site/cities.json (gallery + switcher)
	python3 scripts/export_manifest.py

curator-data:                      ## refresh site/curator-data/$(CITY).json for the curator tool
	python3 scripts/export_curator_data.py --city $(CITY)

serve:                             ## preview at http://localhost:8000 (gallery at /, curator at /curator.html)
	cd site && python3 -m http.server 8000

clean:
	rm -f site/routes.*.json site/cities.json data/*/route_scores.csv data/*/pois.json

help:
	@grep -E '^[a-z/$$().%-]+:.*?## .*$$' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'
