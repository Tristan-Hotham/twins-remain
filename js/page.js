/* Twinned with Europe, voted Remain? Every twinning of a British town or council recorded in Wikidata, coloured by
 * whether its partners are in the EU, over 2010 constituencies shaded by the estimated 2016 Leave share.
 * Plain OpenFreeMap Positron base map. Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const START = small ? [[-6.4, 50.0], [1.8, 58.7]] : [[-8.0, 49.9], [2.2, 58.9]];
  const WORLD = small ? [[-14, 34], [32, 64]] : [[-20, 33], [42, 63]];
  const COL = { eu: '#1F4E9A', mix: '#7A4E8E', non: '#C2332B' };
  const TYPE = { lad: 'a council area (its twinnings count for every seat mostly inside it)', settlement: 'a town, village or parish' };
  let map = null, H = null, S = null, popup = null;

  document.getElementById('theme').addEventListener('click', () => {
    const r = document.documentElement, dark = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    r.dataset.theme = dark ? 'light' : 'dark';
  });
  const ct = document.getElementById('cartouche');
  const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function show(h, ll) { if (popup) popup.remove(); popup = new maplibregl.Popup({ maxWidth: '330px', offset: 8 }).setLngLat(ll).setHTML(h).addTo(map); }
  function hostPopup(h, ll) {
    const eu = h.p.filter(p => p[2]).length;
    let s = `<b class="t">${esc(h.n)}</b><div class="nt">${esc(TYPE[h.t] || h.t)}${h.lad ? ' (' + esc(h.lad) + ')' : ''}</div>`;
    s += `<table><tr><td>Partners</td><td><b>${h.p.length}</b>: ${eu} in other EU states, ${h.p.length - eu} outside the EU</td></tr></table><ul class="plist">`;
    h.p.forEach(p => { s += `<li class="${p[2] ? 'eu' : 'ne'}"><a href="https://www.wikidata.org/wiki/${esc(p[5])}" target="_blank" rel="noopener">${esc(p[0])}</a>, ${esc(p[1].replace("People's Republic of China", 'China'))}${p[3] ? ', from ' + esc(p[3]) : ''}${p[4] ? ', ended ' + esc(p[4]) : ''}</li>`; });
    s += `</ul><p class="nt">Source: Wikidata "twinned administrative body" (P190). A missing twinning means not recorded, not necessarily none.</p>`;
    s += `<div class="lk"><a href="https://www.wikidata.org/wiki/${esc(h.q)}" target="_blank" rel="noopener">Wikidata ${esc(h.q)}</a></div>`;
    show(s, ll);
  }
  function seatPopup(p, ll) {
    let s = `<b class="t">${esc(p.seat)}</b><table><tr><td>Leave share</td><td><b>${p.leave.toFixed(1)}%</b> (estimate, 2016)</td></tr>`;
    s += `<tr><td>EU partners</td><td><b>${p.n_eu}</b></td></tr><tr><td>Non-EU partners</td><td><b>${p.n_noneu}</b></td></tr></table>`;
    s += `<p class="nt">Partners of towns in the seat and of councils covering most of it. Leave estimate: Hanretty (2017); constituency on 2010 boundaries.</p>`;
    show(s, ll);
  }

  // true town-to-town arcs: each partner's own Wikidata point (P625)
  function lineFeatures() {
    const f = [];
    H.forEach(h => h.p.forEach(p => { if (p.length > 7) f.push({ type: 'Feature', properties: { eu: p[2] }, geometry: { type: 'LineString', coordinates: arc([h.lon, h.lat], [p[6], p[7]]) } }); }));
    return { type: 'FeatureCollection', features: f };
  }
  function partnerFeatures() {
    const f = [];
    H.forEach((h, i) => h.p.forEach((p, j) => { if (p.length > 7) f.push({ type: 'Feature', properties: { eu: p[2], i, j }, geometry: { type: 'Point', coordinates: [p[6], p[7]] } }); }));
    return { type: 'FeatureCollection', features: f };
  }
  function partnerPopup(h, p, ll) {
    let s = `<b class="t">${esc(p[0])}</b><div class="nt">${esc(p[1].replace("People's Republic of China", 'China'))}${p[2] ? ', in the EU in 2016' : ', outside the EU'}</div>`;
    s += `<table><tr><td>Twinned with</td><td><b>${esc(h.n)}</b>${p[3] ? ', from ' + esc(p[3]) : ''}${p[4] ? ', ended ' + esc(p[4]) : ''}</td></tr></table>`;
    s += `<p class="nt">Partner location: Wikidata coordinate (P625).</p><div class="lk"><a href="https://www.wikidata.org/wiki/${esc(p[5])}" target="_blank" rel="noopener">Wikidata ${esc(p[5])}</a></div>`;
    show(s, ll);
  }
  function arc(a, b) {
    const n = 32, mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, dx = b[0] - a[0], dy = b[1] - a[1];
    const cx = mx - dy * 0.18, cy = my + dx * 0.18, out = [];
    for (let i = 0; i <= n; i++) { const t = i / n; out.push([(1 - t) * (1 - t) * a[0] + 2 * (1 - t) * t * cx + t * t * b[0], (1 - t) * (1 - t) * a[1] + 2 * (1 - t) * t * cy + t * t * b[1]]); }
    return out;
  }

  let only = '';
  function apply() {
    const on = id => document.getElementById(id).checked;
    const kinds = [['eu', on('ckEU')], ['mix', on('ckMix')], ['non', on('ckNon')]].filter(k => k[1] && (!only || (only === 'eu' ? k[0] === 'eu' : k[0] !== 'eu'))).map(k => k[0]);
    map.setFilter('hosts', ['in', ['get', 'k'], ['literal', kinds]]);
    const vis = (id, v) => map.getLayer(id) && map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none');
    vis('seats', on('ckLeave')); vis('seatline', on('ckBound')); vis('lines', on('ckLines')); vis('pdots', on('ckLines'));
    const lf = only === 'eu' ? ['==', ['get', 'eu'], 1] : only === 'non' ? ['==', ['get', 'eu'], 0] : null;
    map.setFilter('lines', lf); map.setFilter('pdots', lf);
    map.getStyle().layers.filter(l => l.type === 'symbol' && !['hostlab'].includes(l.id)).forEach(l => map.setLayoutProperty(l.id, 'visibility', on('ckNames') ? 'visible' : 'none'));
    document.querySelectorAll('.chip[data-k]').forEach(c => c.setAttribute('aria-pressed', String(c.dataset.k === 'lines' ? on('ckLines') : c.dataset.k === only)));
  }

  function setupLayers() {
    const firstSym = (map.getStyle().layers.find(l => l.type === 'symbol') || {}).id;
    map.addSource('seats', { type: 'geojson', data: S, attribution: 'Boundaries: ONS (OGL); Leave: Hanretty (2017)' });
    map.addLayer({ id: 'seats', type: 'fill', source: 'seats', paint: { 'fill-color': ['interpolate', ['linear'], ['get', 'leave'], 20, '#FFFFFF', 34, '#ECE7DC', 48, '#CFC6B4', 62, '#A99F8B', 76, '#7F7563'], 'fill-opacity': 0.72 } }, firstSym);
    map.addLayer({ id: 'seatline', type: 'line', source: 'seats', paint: { 'line-color': '#FFFFFF', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.3, 10, 1.4] } }, firstSym);
    map.addSource('lines', { type: 'geojson', data: lineFeatures() });
    map.addLayer({ id: 'lines', type: 'line', source: 'lines', layout: { visibility: 'none' }, paint: { 'line-color': ['case', ['==', ['get', 'eu'], 1], COL.eu, COL.non], 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 0.6, 8, 1.2], 'line-opacity': 0.28 } });
    map.addSource('partners', { type: 'geojson', data: partnerFeatures() });
    map.addLayer({ id: 'pdots', type: 'circle', source: 'partners', layout: { visibility: 'none' }, paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 3, 2.5, 8, 4.5, 12, 6.5], 'circle-color': ['case', ['==', ['get', 'eu'], 1], COL.eu, COL.non],
      'circle-opacity': 0.85, 'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 1 } });
    const feats = H.map((h, i) => ({ type: 'Feature', properties: { i, k: h.k, n: h.p.length, name: h.n }, geometry: { type: 'Point', coordinates: [h.lon, h.lat] } }));
    map.addSource('hosts', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Twinnings: <a href="https://www.wikidata.org/" target="_blank">Wikidata</a> (CC0)' });
    map.addLayer({ id: 'hosts', type: 'circle', source: 'hosts', layout: { 'circle-sort-key': ['get', 'n'] }, paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, ['+', 3, ['*', 0.8, ['sqrt', ['get', 'n']]]], 8, ['+', 4.5, ['*', 1.8, ['sqrt', ['get', 'n']]]], 12, ['+', 7, ['*', 3, ['sqrt', ['get', 'n']]]]],
      'circle-color': ['match', ['get', 'k'], 'eu', COL.eu, 'mix', COL.mix, COL.non], 'circle-opacity': 0.9,
      'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 4, 0.8, 10, 1.6] } });
    map.addLayer({ id: 'hostlab', type: 'symbol', source: 'hosts', minzoom: 9,
      layout: { 'text-field': ['get', 'name'], 'text-font': ['Noto Sans Regular'], 'text-size': 12, 'text-offset': [0, 1.0], 'text-anchor': 'top', 'text-optional': true },
      paint: { 'text-color': '#2B2119', 'text-halo-color': 'rgba(255,255,255,0.95)', 'text-halo-width': 1.6 } });
    map.on('click', e => {
      const box = [[e.point.x - 6, e.point.y - 6], [e.point.x + 6, e.point.y + 6]];
      const f = map.queryRenderedFeatures(box, { layers: ['hosts'] })[0];
      if (f) return hostPopup(H[f.properties.i], f.geometry.coordinates);
      const pf = map.getLayoutProperty('pdots', 'visibility') !== 'none' ? map.queryRenderedFeatures(box, { layers: ['pdots'] })[0] : null;
      if (pf) return partnerPopup(H[pf.properties.i], H[pf.properties.i].p[pf.properties.j], pf.geometry.coordinates);
      const s = map.getLayer('seats') && map.getLayoutProperty('seats', 'visibility') !== 'none' ? map.queryRenderedFeatures(e.point, { layers: ['seats'] })[0] : null;
      if (s) seatPopup(s.properties, e.lngLat);
    });
    ['hosts', 'seats', 'pdots'].forEach(l => { map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    ['ckEU', 'ckMix', 'ckNon', 'ckLines', 'ckLeave', 'ckBound', 'ckNames'].forEach(id => document.getElementById(id).addEventListener('change', apply));
    document.querySelectorAll('.chip[data-k]').forEach(b => b.addEventListener('click', () => {
      if (b.dataset.k === 'lines') { const c = document.getElementById('ckLines'); c.checked = !c.checked; if (c.checked) { fold(true); if (map.getZoom() > 4.6) map.fitBounds(WORLD, { padding: 10, duration: 1000 }); } }
      else only = only === b.dataset.k ? '' : b.dataset.k;
      apply();
    }));
    document.querySelectorAll('a[data-t]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); flyHost(a.dataset.t); document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); }));
    if (qs.get('lines')) document.getElementById('ckLines').checked = true;
    apply();
  }
  function flyHost(n) {
    const i = H.findIndex(h => h.n === n); if (i < 0) return; const h = H[i]; fold(true);
    map.flyTo({ center: [h.lon, h.lat], zoom: 10, duration: 1200 });
    map.once('moveend', () => hostPopup(h, [h.lon, h.lat]));
  }

  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug');
    let items = [], k = -1;
    const hs = H.map(h => ({ t: 'h', name: h.n, sub: h.p.length + ' partners', lon: h.lon, lat: h.lat, h }));
    const ss = S.features.map(f => { let x0 = 99, x1 = -99, y0 = 99, y1 = -99; const walk = c => typeof c[0] === 'number' ? (x0 = Math.min(x0, c[0]), x1 = Math.max(x1, c[0]), y0 = Math.min(y0, c[1]), y1 = Math.max(y1, c[1])) : c.forEach(walk); walk(f.geometry.coordinates);
      return { t: 's', name: f.properties.seat, sub: 'constituency · Leave ' + f.properties.leave.toFixed(0) + '%', b: [[x0, y0], [x1, y1]], p: f.properties }; });
    const showS = () => {
      const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1;
      if (v.length < 2) { sug.style.display = 'none'; return; }
      const m = arr => arr.filter(p => norm(p.name).startsWith(v)).concat(arr.filter(p => !norm(p.name).startsWith(v) && v.length > 2 && norm(p.name).includes(v)));
      items = m(hs).slice(0, 7).concat(m(ss).slice(0, 5));
      items.forEach((p, i) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(p.name)} <span>${esc(p.sub)}</span>`;
        li.addEventListener('mousedown', e => { e.preventDefault(); pick(i); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none';
    };
    const pick = i => {
      const p = items[i]; if (!p) return; q.value = p.name; sug.style.display = 'none'; fold(true);
      if (p.t === 'h') { map.flyTo({ center: [p.lon, p.lat], zoom: 10.5, duration: 1200 }); map.once('moveend', () => hostPopup(p.h, [p.lon, p.lat])); }
      else { map.fitBounds(p.b, { padding: 40, duration: 1200 }); map.once('moveend', () => seatPopup(p.p, map.getCenter())); }
    };
    q.addEventListener('input', showS);
    q.addEventListener('keydown', e => {
      const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) showS(); pick(k < 0 ? 0 : k); }
      else if (e.key === 'Escape') sug.style.display = 'none';
    });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
  }

  Promise.all([fetch('data/hosts.json').then(r => r.json()), fetch('data/seats.geojson').then(r => r.json())]).then(([h, s]) => {
    H = h.hosts; S = s;
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: START, fitBoundsOptions: { padding: 6 } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 16 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(m => {
    map = m; window.__map = m;
    m.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(a => { a.classList.remove('maplibregl-compact-show'); a.removeAttribute('open'); });
    m.once('idle', foldAt); setTimeout(foldAt, 1500);
    setupLayers(); setupSearch();
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov,.lp,.keys,.mfs-btn,.maplibregl-ctrl,.maplibregl-popup')) return; fold(true); }, { capture: true, passive: true, once: true });
    if (qs.get('place')) flyHost(qs.get('place'));
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
