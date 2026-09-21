/* City gallery — the home page. Reads cities.json (written by
   scripts/export_manifest.py) and renders one card per city. */

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

async function main() {
  const cities = await fetch('cities.json', { cache: 'no-cache' }).then((r) => r.json());
  const host = document.getElementById('galleryGrid');
  host.innerHTML = cities.map((c) => {
    const isLive = c.status === 'live';
    const stats = isLive
      ? `${c.loops} route${c.loops === 1 ? '' : 's'} &middot; ${c.sights} sights`
      : '';
    const tag = isLive ? 'a' : 'div';
    const href = isLive ? ` href="city.html?city=${encodeURIComponent(c.slug)}"` : '';
    return (
      `<${tag} class="city-card${isLive ? '' : ' is-soon'}"${href}>` +
      (isLive ? '' : '<span class="badge-soon">Coming soon</span>') +
      `<div class="city-card-name">${esc(c.name)}</div>` +
      `<div class="city-card-country">${esc(c.country)}</div>` +
      (stats ? `<div class="city-card-stats">${stats}</div>` : '') +
      `</${tag}>`
    );
  }).join('');
}

main().catch((err) => {
  document.getElementById('galleryGrid').textContent = `Could not load cities — ${err.message}`;
  console.error(err);
});
