/* Curator tool. Browse every raw Overpass element for a city, cross-check it
   against bus stops, and build up a CURATED / MUST_SEE / GEMS draft that
   exports as Python ready to paste into scripts/cities/<slug>.py.

   The draft is the full desired state (pre-existing curation + edits), kept
   in localStorage per city — this is a personal tool run on localhost, so
   per-browser storage is the right amount of persistence, nothing fancier. */

const WALK_M = 300;

let CITY_INDEX = [];
let BUNDLE = null;
let DRAFT = {};       // norm(name) -> {name, description, category, must_see, gem}
let SELECTED = null;  // the raw_pois entry currently shown in the edit panel
let map, rawLayer, stopLayer, highlightLayer;

const $ = (id) => document.getElementById(id);

function norm(s) {
  return String(s).toLowerCase().trim().replace(/\s+/g, ' ');
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function haversineM(lat1, lon1, lat2, lon2) {
  const r = 6371000;
  const p1 = (lat1 * Math.PI) / 180, p2 = (lat2 * Math.PI) / 180;
  const dp = p2 - p1, dl = ((lon2 - lon1) * Math.PI) / 180;
  const a = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * r * Math.asin(Math.sqrt(a));
}

function categoryGuess(tags) {
  if (tags.tourism === 'zoo' || tags.tourism === 'aquarium') return 'attraction';
  if (tags.tourism === 'museum') return 'museum';
  if (tags.tourism === 'viewpoint') return 'viewpoint';
  if (tags.amenity === 'place_of_worship' || tags.building === 'cathedral' || tags.building === 'church') return 'church';
  if (tags.natural === 'beach') return 'beach';
  if (tags.amenity === 'marketplace') return 'market';
  if (tags.leisure === 'park' || tags.leisure === 'garden') return 'park';
  if (tags.leisure === 'stadium') return 'stadium';
  if (tags.historic === 'castle' || tags.historic === 'city_gate' || tags.historic === 'fort') return 'castle';
  if (tags.historic) return 'historic';
  if (tags.tourism === 'attraction') return 'attraction';
  return 'landmark';
}

/* -------------------------------------------------------------- draft */

function draftKey(slug) { return `curator-draft-${slug}`; }

function loadDraft(slug) {
  try {
    const saved = localStorage.getItem(draftKey(slug));
    if (saved) return JSON.parse(saved);
  } catch (e) { /* fall through to seed */ }
  const seeded = {};
  for (const c of BUNDLE.curated) {
    seeded[c.key] = {
      name: c.name, description: c.description, category: 'landmark',
      must_see: !!c.must_see, gem: false,
    };
  }
  return seeded;
}

function saveDraft() {
  try {
    localStorage.setItem(draftKey(BUNDLE.slug), JSON.stringify(DRAFT));
  } catch (e) { console.warn('localStorage unavailable', e); }
  renderExport();
  renderRows();
  if (SELECTED) renderMarkers();
}

function pyStr(s) {
  return '"' + String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
}

function renderExport() {
  const entries = Object.entries(DRAFT).sort((a, b) => a[1].name.localeCompare(b[1].name));
  $('draftCount').textContent = entries.length;
  const curatedLines = entries
    .map(([key, v]) => `    ${pyStr(key)}: (\n        ${pyStr(v.name)},\n        ${pyStr(v.description || '')},\n    ),`)
    .join('\n');
  // MUST_SEE / GEMS are sets of *display* names in the real Python files, and
  // several raw-name keys often share one display name (a sight tagged under
  // two OSM aliases) — dedupe or the exported set literal repeats itself.
  const dedupeNames = (pred) => [...new Set(entries.filter(([, v]) => pred(v)).map(([, v]) => v.name))].map(pyStr);
  const mustSee = dedupeNames((v) => v.must_see);
  const gems = dedupeNames((v) => v.gem);
  const wrap = (arr) => (arr.length ? `{\n    ${arr.join(',\n    ')},\n}` : 'set()');
  $('exportBox').value =
    `MUST_SEE = ${wrap(mustSee)}\n\n` +
    `GEMS = ${wrap(gems)}\n\n` +
    `CURATED = {\n${curatedLines}\n}\n`;
}

/* -------------------------------------------------------------- map */

function initMap() {
  map = L.map('map', { zoomControl: true }).setView([20, 0], 2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);
  rawLayer = L.layerGroup().addTo(map);
  stopLayer = L.layerGroup().addTo(map);
  highlightLayer = L.layerGroup().addTo(map);
}

function markerFor(poi, draftEntry) {
  let color = '#b8bfc9', radius = 4;
  if (draftEntry) {
    color = draftEntry.gem ? '#2f9e6e' : draftEntry.must_see ? '#e8a33d' : '#1c7ed6';
    radius = 6;
  }
  return L.circleMarker([poi.lat, poi.lon], {
    radius, color, weight: draftEntry ? 2 : 1, fillColor: color, fillOpacity: draftEntry ? 0.85 : 0.5,
  });
}

function renderMarkers() {
  rawLayer.clearLayers();
  stopLayer.clearLayers();
  highlightLayer.clearLayers();

  BUNDLE.bus_stops.forEach((s) => {
    L.circleMarker([s.lat, s.lon], { radius: 3, color: '#8a94a6', weight: 1.5, fillColor: '#fff', fillOpacity: 1 })
      .bindPopup(`<b>${esc(s.name)}</b><br>${s.lines.map(esc).join(', ')}`)
      .addTo(stopLayer);
  });

  const visibleIds = new Set(currentFiltered().map((p) => p.id));
  BUNDLE.raw_pois.forEach((poi) => {
    if (!visibleIds.has(poi.id)) return;
    const draftEntry = DRAFT[norm(poi.name)];
    const m = markerFor(poi, draftEntry);
    m.bindTooltip(esc(poi.name), { direction: 'top', offset: [0, -4] });
    m.on('click', () => selectPoi(poi));
    m.addTo(rawLayer);
  });

  if (SELECTED) {
    L.circle([SELECTED.lat, SELECTED.lon], {
      radius: WALK_M, color: '#1c7ed6', weight: 1.5, dashArray: '4 5', fillOpacity: 0.05,
    }).addTo(highlightLayer);
    L.circleMarker([SELECTED.lat, SELECTED.lon], {
      radius: 9, color: '#d6336c', weight: 3, fillColor: '#fff', fillOpacity: 1,
    }).addTo(highlightLayer);
  }
}

/* -------------------------------------------------------------- list */

function currentFiltered() {
  const q = norm($('search').value);
  const onlyCurated = $('fCurated').checked;
  const onlyUncurated = $('fUncurated').checked;
  const onlyWiki = $('fNoWiki').checked;
  return BUNDLE.raw_pois.filter((poi) => {
    if (q && !norm(poi.name).includes(q)) return false;
    const inDraft = !!DRAFT[norm(poi.name)];
    if (onlyCurated && !inDraft) return false;
    if (onlyUncurated && inDraft) return false;
    if (onlyWiki && !poi.tags.wikidata) return false;
    return true;
  });
}

function renderRows() {
  const list = currentFiltered().slice(0, 400); // keep the DOM light on 2000+ element cities
  const host = $('rows');
  host.innerHTML = list.map((poi) => {
    const d = DRAFT[norm(poi.name)];
    const star = d && d.must_see ? '<span class="star">★</span>' : '';
    const gem = d && d.gem ? '<span class="gem">✦</span>' : '';
    const active = SELECTED && SELECTED.id === poi.id ? ' is-active' : '';
    const curatedCls = d ? ' is-curated' : '';
    return (
      `<li class="cur-row${active}${curatedCls}" data-id="${esc(poi.id)}">` +
      `<div class="cur-row-name">${star}${gem}${esc(d ? d.name : poi.name)}</div>` +
      `<div class="cur-row-meta">${esc(categoryGuess(poi.tags))}${poi.tags.wikidata ? ' · wikidata' : ''}</div>` +
      `</li>`
    );
  }).join('');
  host.querySelectorAll('.cur-row').forEach((row) => {
    row.onclick = () => {
      const poi = BUNDLE.raw_pois.find((p) => p.id === row.dataset.id);
      if (poi) selectPoi(poi);
    };
  });
  $('counts').textContent = `${BUNDLE.raw_pois.length} raw · ${Object.keys(DRAFT).length} in draft`;
}

/* -------------------------------------------------------------- edit panel */

function nearestStop(poi) {
  let best = null, bestD = Infinity;
  for (const s of BUNDLE.bus_stops) {
    const d = haversineM(poi.lat, poi.lon, s.lat, s.lon);
    if (d < bestD) { bestD = d; best = s; }
  }
  return best ? { stop: best, dist: Math.round(bestD) } : null;
}

function selectPoi(poi) {
  SELECTED = poi;
  $('editEmpty').hidden = true;
  $('editForm').hidden = false;
  $('editRawName').textContent = poi.name;

  const tagRows = Object.entries(poi.tags).map(([k, v]) => {
    if (k === 'wikidata') return `wikidata: <a href="https://www.wikidata.org/wiki/${esc(v)}" target="_blank" rel="noopener">${esc(v)}</a>`;
    if (k === 'wikipedia') return `wikipedia: ${esc(v)}`;
    return `${esc(k)}: ${esc(v)}`;
  });
  $('editTags').innerHTML = tagRows.join('<br>') || '<em>no tags captured</em>';

  const near = nearestStop(poi);
  const nEl = $('editNearest');
  if (near) {
    nEl.className = 'cur-nearest' + (near.dist > WALK_M ? ' is-far' : '');
    nEl.innerHTML = `Nearest bus stop: <b>${near.dist} m</b> — ${esc(near.stop.name)} (${near.stop.lines.map(esc).join(', ')})` +
      (near.dist > WALK_M ? ' — outside 300 m' : '');
  } else {
    nEl.className = 'cur-nearest is-far';
    nEl.textContent = 'No bus stop data for this city.';
  }

  const existing = DRAFT[norm(poi.name)];
  $('fName').value = existing ? existing.name : poi.name;
  $('fDesc').value = existing ? existing.description : '';
  $('fCategory').value = existing ? existing.category : categoryGuess(poi.tags);
  $('fMustSee').checked = !!(existing && existing.must_see);
  $('fGem').checked = !!(existing && existing.gem);

  map.panTo([poi.lat, poi.lon]);
  renderRows();
  renderMarkers();
}

$('editForm').addEventListener('submit', (e) => {
  e.preventDefault();
  if (!SELECTED) return;
  DRAFT[norm(SELECTED.name)] = {
    name: $('fName').value.trim() || SELECTED.name,
    description: $('fDesc').value.trim(),
    category: $('fCategory').value,
    must_see: $('fMustSee').checked,
    gem: $('fGem').checked,
  };
  saveDraft();
});

$('btnRemove').addEventListener('click', () => {
  if (!SELECTED) return;
  delete DRAFT[norm(SELECTED.name)];
  saveDraft();
});

$('btnCopy').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText($('exportBox').value);
    $('btnCopy').textContent = 'Copied';
    setTimeout(() => { $('btnCopy').textContent = 'Copy'; }, 1200);
  } catch (e) {
    $('exportBox').select();
  }
});

$('btnClear').addEventListener('click', () => {
  if (!confirm('Clear the whole draft for this city? This does not touch the exported .py file.')) return;
  DRAFT = {};
  saveDraft();
});

['search', 'fCurated', 'fUncurated', 'fNoWiki'].forEach((id) =>
  $(id).addEventListener('input', () => { renderRows(); renderMarkers(); })
);

/* -------------------------------------------------------------- city load */

async function loadCity(slug) {
  BUNDLE = await fetch(`curator-data/${slug}.json`, { cache: 'no-cache' }).then((r) => r.json());
  DRAFT = loadDraft(slug);
  SELECTED = null;
  $('editEmpty').hidden = false;
  $('editForm').hidden = true;
  history.replaceState(null, '', `?city=${slug}`);
  renderRows();
  renderMarkers();
  renderExport();
  if (BUNDLE.raw_pois.length) {
    const lats = BUNDLE.raw_pois.map((p) => p.lat), lons = BUNDLE.raw_pois.map((p) => p.lon);
    map.fitBounds([[Math.min(...lats), Math.min(...lons)], [Math.max(...lats), Math.max(...lons)]],
      { padding: [30, 30] });
  }
}

async function main() {
  initMap();
  CITY_INDEX = await fetch('curator-data/index.json', { cache: 'no-cache' }).then((r) => r.json());
  const sel = $('citySelect');
  sel.innerHTML = CITY_INDEX.map((c) =>
    `<option value="${esc(c.slug)}">${esc(c.name)} (${c.curated_count}/${c.raw_count})</option>`
  ).join('');
  sel.onchange = () => loadCity(sel.value);

  const want = new URLSearchParams(location.search).get('city');
  const startSlug = CITY_INDEX.some((c) => c.slug === want) ? want : CITY_INDEX[0].slug;
  sel.value = startSlug;
  await loadCity(startSlug);
}

main().catch((err) => {
  console.error(err);
  document.body.insertAdjacentHTML('beforeend',
    `<div style="position:fixed;bottom:12px;left:12px;background:#c92a2a;color:#fff;padding:8px 12px;border-radius:8px;font:13px sans-serif">Curator failed to load: ${esc(err.message)}</div>`);
});
