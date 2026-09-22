/* Sightseeing by Bus — Antwerp
   Reads routes.json (produced by scripts/build_routes.py) and draws it. */

const LOOP_COLORS = ['#d6336c', '#1c7ed6', '#f08c00'];

const CAT_GLYPH = {
  museum: '\u{1F3DB}', church: '†', park: '\u{1F332}', castle: '\u{1F3F0}',
  viewpoint: '\u{1F441}', attraction: '★', historic: '⚑', landmark: '◆',
};

const $ = (id) => document.getElementById(id);

let DATA = null;
let map = null;
let layer = null;          // everything for the current loop
let gapLayer = null;       // sights no bus reaches
let active = 0;
let poiMarkers = new Map(); // poi name -> marker
let CITIES = [];
let activeCity = null;
let fitTarget = null;       // bounds of the loop currently drawn
let userMoved = false;      // once the visitor pans/zooms, stop re-fitting on them

/* ---------------------------------------------------------------- map */

function initMap() {
  map = L.map('map', { zoomControl: true, scrollWheelZoom: true })
    .setView([51.2194, 4.4025], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' +
      ' &middot; transit data &copy; <a href="https://www.delijn.be">De Lijn</a>',
  }).addTo(map);
  layer = L.layerGroup().addTo(map);
  gapLayer = L.layerGroup();

  const el = map.getContainer();
  ['mousedown', 'wheel', 'touchstart'].forEach((ev) =>
    el.addEventListener(ev, () => { userMoved = true; }, { passive: true }));

  // The container can still be 0-height when the first loop is drawn (a pane
  // mid-open, a slow stylesheet), and Leaflet would then compute the zoom from
  // an empty box and slam to maxZoom. Re-fit whenever the box actually changes.
  new ResizeObserver(() => {
    map.invalidateSize();
    if (!userMoved) fitCurrent();
  }).observe(el);
}

function fitCurrent() {
  if (!fitTarget || !fitTarget.isValid()) return;
  const { x, y } = map.getSize();
  if (x < 50 || y < 50) return;  // not laid out yet — the observer will call back
  map.fitBounds(fitTarget, { padding: [40, 40] });
}

/* Split a route shape into the parts inside the study area and the parts that
   run off into the suburbs, so the tail can be drawn as a hint rather than
   dominating the view. Boundary points join both segments to keep it unbroken. */
function splitByBbox(shape, bbox) {
  const inside = (p) =>
    p[0] >= bbox.south && p[0] <= bbox.north && p[1] >= bbox.west && p[1] <= bbox.east;
  const segs = [];
  let cur = null;
  shape.forEach((p) => {
    const isIn = inside(p);
    if (!cur || cur.inside !== isIn) {
      if (cur) cur.pts.push(p);          // close the previous run on this point
      cur = { inside: isIn, pts: cur ? [cur.pts[cur.pts.length - 1], p] : [p] };
      segs.push(cur);
    } else {
      cur.pts.push(p);
    }
  });
  return segs.filter((s) => s.pts.length > 1);
}

const MUST_SEE_COLOR = '#e8a33d';

function poiIcon(color, category, mustSee) {
  const glyph = CAT_GLYPH[category] || CAT_GLYPH.landmark;
  const bg = mustSee ? MUST_SEE_COLOR : color;
  const size = mustSee ? 27 : 22;
  return L.divIcon({
    className: '',
    html: `<div class="poi-pin" style="background:${bg};width:${size}px;height:${size}px">` +
          `<span>${glyph}</span></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size - 2],
    popupAnchor: [0, -(size - 4)],
  });
}

function popupHtml(poi, extra) {
  return (
    `<div class="pop-name">${esc(poi.name)}</div>` +
    `<div class="pop-desc">${esc(poi.description)}</div>` +
    (extra ? `<div class="pop-meta">${extra}</div>` : '')
  );
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/* ------------------------------------------------------------- render */

function drawLoop(i) {
  active = i;
  const loop = DATA.loops[i];
  const color = LOOP_COLORS[i % LOOP_COLORS.length];

  layer.clearLayers();
  poiMarkers.clear();

  const segs = splitByBbox(loop.shape, DATA.bbox);
  segs.filter((sg) => !sg.inside).forEach((sg) =>
    L.polyline(sg.pts, { color, weight: 2.5, opacity: 0.4, dashArray: '3 6', lineJoin: 'round' })
      .bindPopup(`<div class="pop-meta">Bus ${esc(loop.line)} continues to ${esc(loop.headsign)}</div>`)
      .addTo(layer));
  segs.filter((sg) => sg.inside).forEach((sg) => {
    // white casing under the route line keeps it legible over busy tiles
    L.polyline(sg.pts, { color: '#fff', weight: 9, opacity: 0.9, lineJoin: 'round' }).addTo(layer);
    L.polyline(sg.pts, { color, weight: 4.5, opacity: 1, lineJoin: 'round' }).addTo(layer);
  });

  const seen = new Set();
  const mustSee = new Set(DATA.all_pois.filter((p) => p.must_see).map((p) => p.name));
  loop.stops.forEach((stop) => {
    const hasPoi = stop.pois.length > 0;
    L.circleMarker([stop.lat, stop.lon], {
      radius: hasPoi ? 6 : 4,
      color: hasPoi ? color : '#8a94a6',
      weight: 2.5,
      fillColor: '#fff',
      fillOpacity: 1,
    })
      .bindPopup(
        `<div class="pop-name">${esc(stop.stop_name)}</div>` +
        `<div class="pop-meta">Bus ${esc(loop.line)} &middot; ` +
        (hasPoi ? `${stop.pois.length} sight${stop.pois.length > 1 ? 's' : ''} within ${DATA.walk_radius_m} m`
                : 'no sights within walking distance') +
        `</div>`
      )
      .addTo(layer);

    stop.pois.forEach((poi) => {
      if (seen.has(poi.name)) return;
      seen.add(poi.name);
      // 300 m walking circle, drawn faintly so the "is it walkable" claim is visible
      L.circle([poi.lat, poi.lon], {
        radius: DATA.walk_radius_m,
        color,
        weight: 1,
        opacity: 0.25,
        fillColor: color,
        fillOpacity: 0.05,
      }).addTo(layer);

      const m = L.marker([poi.lat, poi.lon],
        { icon: poiIcon(color, poi.category, mustSee.has(poi.name)), riseOnHover: true,
          zIndexOffset: mustSee.has(poi.name) ? 1000 : 0 })
        .bindPopup(
          popupHtml(poi, `${poi.walk_m} m from <b>${esc(stop.stop_name)}</b> &middot; bus ${esc(loop.line)}`)
        )
        .addTo(layer);
      poiMarkers.set(poi.name, m);
    });
  });

  fitTarget = L.latLngBounds(
    loop.stops.map((st) => [st.lat, st.lon])
      .concat(loop.stops.flatMap((st) => st.pois.map((p) => [p.lat, p.lon])))
  );
  userMoved = false;
  map.invalidateSize();
  fitCurrent();
  renderTabs();
  renderMeta(loop, color);
  renderItinerary(loop, color);
}

function renderTabs() {
  const host = $('loops');
  host.innerHTML = '';
  DATA.loops.forEach((loop, i) => {
    const color = LOOP_COLORS[i % LOOP_COLORS.length];
    const b = document.createElement('button');
    b.className = 'loop-btn';
    b.style.color = color;
    b.setAttribute('aria-selected', String(i === active));
    const sights = new Set(loop.stops.flatMap((s) => s.pois.map((p) => p.name))).size;
    b.innerHTML =
      `<span class="badge" style="background:${color}">${esc(loop.line)}</span>` +
      `<span class="txt"><span class="t1">${esc(loop.long_name)}</span>` +
      `<span class="t2">${sights} sights &middot; ${Math.round(loop.trips_per_day)} buses/day</span></span>`;
    b.onclick = () => drawLoop(i);
    host.appendChild(b);
  });
}

function renderMeta(loop, color) {
  const names = loop.stops.flatMap((s) => s.pois.map((p) => p.name));
  const sights = new Set(names).size;
  const must = new Set(DATA.all_pois.filter((p) => p.must_see).map((p) => p.name));
  const nMust = new Set(names.filter((n) => must.has(n))).size;
  const headway = Math.round(((DATA.service_hours || 18) * 60) / (loop.trips_per_day / 2));
  $('loopMeta').innerHTML = [
    `<span class="stat"><b>${sights}</b> sights</span>`,
    nMust ? `<span class="stat"><b>${nMust}</b> must-see</span>` : '',
    `<span class="stat"><b>${loop.districts}</b> districts</span>`,
    `<span class="stat"><b>${loop.spread_km}</b> km spread</span>`,
    `<span class="stat">every <b>~${headway}</b> min</span>`,
    `<span class="stat">towards <b>${esc(loop.headsign)}</b></span>`,
  ].join('');
}

function renderItinerary(loop, color) {
  const onlySights = $('onlySights').checked;
  const host = $('itinerary');
  host.innerHTML = '';
  host.style.color = color;

  const must = new Set(DATA.all_pois.filter((p) => p.must_see).map((p) => p.name));
  const stops = onlySights ? loop.stops.filter((s) => s.pois.length) : loop.stops;
  $('stopCount').textContent =
    `${stops.length} of ${loop.stops.length} stops in the centre`;

  stops.forEach((stop) => {
    const li = document.createElement('li');
    li.className = 'stop' + (stop.pois.length ? ' has-poi' : '');

    const name = document.createElement('div');
    name.className = 'stop-name';
    name.textContent = stop.stop_name;
    li.appendChild(name);

    if (stop.pois.length) {
      const ul = document.createElement('ul');
      ul.className = 'poi-list';
      stop.pois.forEach((poi) => {
        const li2 = document.createElement('li');
        const isMust = must.has(poi.name);
        const btn = document.createElement('button');
        btn.className = 'poi' + (isMust ? ' is-must' : '');
        btn.innerHTML =
          `<span class="poi-top">${isMust ? '<span class="star">\u2605</span>' : ''}` +
          `<span class="poi-name">${esc(poi.name)}</span>` +
          `<span class="poi-walk">${poi.walk_m} m</span></span>` +
          `<span class="cat">${esc(poi.category)}</span>` +
          `<div class="poi-desc">${esc(poi.description)}</div>`;
        btn.onclick = () => {
          const m = poiMarkers.get(poi.name);
          if (!m) return;
          userMoved = true;  // don't yank this view away on the next resize
          map.setView([poi.lat, poi.lon], 17, { animate: true });
          m.openPopup();
        };
        li2.appendChild(btn);
        ul.appendChild(li2);
      });
      li.appendChild(ul);
    }
    host.appendChild(li);
  });
}

/* --------------------------------------------------------- why / gaps */

function renderWhy() {
  const picked = new Set(DATA.loops.map((l) => l.line));
  const rows = DATA.ranking
    .slice(0, 10)
    .map(
      (r) =>
        `<tr class="${picked.has(r.line) ? 'picked' : ''}"><td>${esc(r.line)}</td>` +
        `<td>${r.poi_count}</td><td>${r.must_see_count ?? 0}</td><td>${r.districts}</td>` +
        `<td>${r.spread_km}</td><td>${Math.round(r.trips_per_day)}</td><td>${r.score}</td></tr>`
    )
    .join('');
  $('whyBody').innerHTML =
    `<p>${esc(DATA.scoring)}. Lines running fewer than ${DATA.min_trips_per_day} buses a day ` +
    `are dropped — they are peak-only commuter runs, no use for hopping on and off. The loops ` +
    `are then chosen greedily on the sights they <em>add</em>, so they complement rather than ` +
    `repeat each other.</p>` +
    `<table class="rank"><thead><tr><th>Line</th><th>Sights</th><th>★</th><th>Distr.</th>` +
    `<th>km</th><th>Buses/day</th><th>Score</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderGaps() {
  document.querySelectorAll('.gaps').forEach((el) => el.remove());
  gapLayer.clearLayers();
  if (map.hasLayer(gapLayer)) map.removeLayer(gapLayer);

  const gaps = DATA.unreachable_pois || [];
  if (!gaps.length) return;
  const el = document.createElement('details');
  el.className = 'gaps';
  el.innerHTML =
    `<summary>${gaps.length} sight${gaps.length > 1 ? 's' : ''} the bus can't reach</summary>` +
    `<div class="gaps-body"><p>No bus stop within ${DATA.walk_radius_m} m. ` +
    `The same ticket covers the metro and tram, so these are still one ride away.</p>` +
    `<label class="switch"><input type="checkbox" id="showGaps"><span>Show them on the map</span></label>` +
    `<ul>${gaps
      .map((p) => `<li><strong>${esc(p.name)}</strong> — nearest bus stop ${p.nearest_bus_stop_m} m</li>`)
      .join('')}</ul></div>`;
  $('why').after(el);

  gaps.forEach((p) => {
    L.marker([p.lat, p.lon], { icon: poiIcon('#8a94a6', p.category, false) })
      .bindPopup(popupHtml(p,
        `No bus within ${DATA.walk_radius_m} m &middot; nearest is ${p.nearest_bus_stop_m} m &mdash; take the metro or tram`))
      .addTo(gapLayer);
  });

  el.querySelector('#showGaps').onchange = (e) => {
    if (e.target.checked) gapLayer.addTo(map);
    else map.removeLayer(gapLayer);
  };
}

/* ---------------------------------------------------------------- cities */

function renderCityTabs() {
  const host = $('cities');
  host.innerHTML = '';
  CITIES.forEach((c) => {
    const b = document.createElement('button');
    b.className = 'city-btn';
    b.setAttribute('aria-selected', String(c.slug === activeCity));
    b.innerHTML = `${esc(c.name)}<small>${c.loops} loops &middot; ${c.sights} sights</small>`;
    b.onclick = () => loadCity(c.slug);
    host.appendChild(b);
  });
}

async function loadCity(slug) {
  const meta = CITIES.find((c) => c.slug === slug) || CITIES[0];
  const res = await fetch(meta.file, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${meta.file}: ${res.status}`);
  DATA = await res.json();
  activeCity = slug;
  active = 0;
  userMoved = false;
  history.replaceState(null, '', `?city=${slug}`);

  const c = DATA.city;
  document.title = `Sightseeing by Bus — ${c.name}`;
  $('brandSub').textContent = `${c.name}, on one ordinary ticket`;
  $('pitch').innerHTML =
    `A hop-on-hop-off tour costs about <strong>&euro;${c.tour_price_eur}</strong>. These are ` +
    `regular ${esc(c.operator)} city buses that pass the same sights &mdash; ${esc(c.ticket_note)}.`;

  const g = DATA.generated_from;
  const fmt = (d) => (d && d.length === 8 ? `${d.slice(6, 8)}/${d.slice(4, 6)}/${d.slice(0, 4)}` : d);
  const refreshed = g.refreshed_at ? new Date(g.refreshed_at) : null;
  const ageDays = refreshed ? (Date.now() - refreshed.getTime()) / 86400000 : Infinity;
  const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Madrid' }).format(new Date()).replaceAll('-', '');
  const expired = g.gtfs_valid_to && g.gtfs_valid_to < today;
  const freshness = refreshed && Number.isFinite(refreshed.getTime())
    ? `Timetable checked ${esc(refreshed.toLocaleDateString())}. `
    : 'Timetable refresh date unavailable. ';
  const warning = expired ? 'Timetable expired. Check the operator before travelling. '
    : ageDays > 3 ? 'Timetable refresh is overdue. Check the operator before travelling. ' : '';
  $('foot').innerHTML =
    `<strong>${esc(warning)}</strong>${freshness}Scheduled service, not live arrivals. ` +
    `Routes and stops from the <strong>${esc(g.gtfs_publisher)}</strong> GTFS feed` +
    (g.gtfs_valid_from ? ` (valid ${fmt(g.gtfs_valid_from)}&ndash;${fmt(g.gtfs_valid_to)})` : '') +
    `. Sights from <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, ODbL. ` +
    `Walking distances are straight-line, not routed. Always check live times on ` +
    `<a href="${esc(c.operator_url)}">${esc(c.operator_url.replace(/^https?:\/\//, ''))}</a>.`;

  renderCityTabs();
  drawLoop(0);
  renderWhy();
  renderGaps();
}

/* ---------------------------------------------------------------- init */

async function main() {
  initMap();
  // city.html only ever drives a real map view, so filter cities.json down
  // to the ones that actually have a routes.<slug>.json to fetch.
  CITIES = (await fetch('cities.json', { cache: 'no-cache' }).then((r) => r.json()))
    .filter((c) => c.status === 'live');
  const want = new URLSearchParams(location.search).get('city');
  await loadCity(CITIES.some((c) => c.slug === want) ? want : CITIES[0].slug);
  $('onlySights').onchange = () =>
    renderItinerary(DATA.loops[active], LOOP_COLORS[active % LOOP_COLORS.length]);
  $('loading').hidden = true;
}

main().catch((err) => {
  $('loading').innerHTML = `<span style="color:#c92a2a">Could not load &mdash; ${esc(err.message)}</span>`;
  console.error(err);
});
