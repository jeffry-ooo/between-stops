#!/usr/bin/env bash
# Step 1 — download a city's static GTFS feed.
#
#     ./scripts/fetch_gtfs.sh antwerp
#     ./scripts/fetch_gtfs.sh rome
#
# Every operator we've checked publishes its feed only behind a free-but-
# mandatory registration (see each city's `gtfs_official` block in
# scripts/cities/<slug>.py for the portal + env var names), so by default
# this pulls MobilityData's public mirror of the same feed instead — no key,
# same data. Antwerp and Barcelona also support going direct to the official
# API if you set their key env vars; the rest currently only fetch the mirror
# (nobody has registered for the other 14 operators' APIs yet).
set -euo pipefail
cd "$(dirname "$0")/.."

CITY="${1:-antwerp}"
OUT="data/$CITY/gtfs.zip"
mkdir -p "data/$CITY"

# Pull the mirror URL (and, for Antwerp/Barcelona, the official-API wiring)
# out of the single source of truth: scripts/cities/<slug>.py.
read -r MIRROR OFFICIAL_ENDPOINT AUTH_HEADER ENV_VAR <<PYEOF
$(cd scripts && python3 -c "
import cities
c = cities.load('$CITY')
off = c.get('gtfs_official') or {}
print(c.get('gtfs_mirror') or '-', off.get('endpoint') or '-', off.get('auth_header') or '-', off.get('env_var') or '-')
")
PYEOF

if [ "$MIRROR" = "-" ]; then
  echo "no gtfs_mirror configured for '$CITY' in scripts/cities/$CITY.py" >&2
  exit 1
fi

# Only Antwerp (DELIJN_KEY) and Barcelona (TMB_APP_ID + TMB_APP_KEY) have
# their official-API request wired up below; every other city's official
# portal is documented in gtfs_official but not yet scripted, since no key
# has been requested for them.
case "$CITY" in
  antwerp)
    if [ -n "${DELIJN_KEY:-}" ]; then
      echo "Fetching Antwerp from De Lijn's official API..."
      curl -fSL --progress-bar -H "Ocp-Apim-Subscription-Key: ${DELIJN_KEY}" \
        "$OFFICIAL_ENDPOINT" -o "$OUT"
      exit 0
    fi
    ;;
  barcelona)
    if [ -n "${TMB_APP_ID:-}" ] && [ -n "${TMB_APP_KEY:-}" ]; then
      echo "Fetching Barcelona from TMB's official API..."
      curl -fSL --progress-bar \
        "$OFFICIAL_ENDPOINT?app_id=${TMB_APP_ID}&app_key=${TMB_APP_KEY}" -o "$OUT"
      exit 0
    fi
    ;;
esac

echo "Fetching $CITY from the MobilityData mirror ($MIRROR)..."
curl -fSL --progress-bar "$MIRROR" -o "$OUT"
ls -lh "$OUT"
