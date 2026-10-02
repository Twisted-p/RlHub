(() => {
  if (bodyPage !== "garage") return;
  const catalog = window.RL_GARAGE_CATALOG;
  const favoriteKey = "rlhub:garageFavorites";
  const feature = document.getElementById("garage-feature");
  const grid = document.getElementById("garage-grid");
  const editor = document.getElementById("garage-editor");
  const form = document.getElementById("garage-custom-form");
  const imageDialog = document.getElementById("garage-image-dialog");
  let view = "discover", carFilter = "all", selected = "pro:" + catalog[0].id;
  let editing = null, reference = null, feedbackTimer;
  const escape = value => String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
  const lookup = key => key.startsWith("pro:") ? catalog.find(p => "pro:" + p.id === key) : presets.find(p => "mine:" + p.id === key);
  const sourceFor = preset => catalog.find(p => p.id === (preset.referenceId || preset.catalogId)) || (catalog.includes(preset) ? preset : null);
  const keyFor = preset => (catalog.includes(preset) ? "pro:" : "mine:") + preset.id;
  const feedback = text => { clearTimeout(feedbackTimer); document.getElementById("garage-feedback").textContent = text; feedbackTimer = setTimeout(() => document.getElementById("garage-feedback").textContent = "", 4500); };
  function readFavorites() {
    try { const saved = JSON.parse(localStorage.getItem(favoriteKey)); return new Set(Array.isArray(saved) ? saved.filter(id => typeof id === "string") : []); }
    catch (_) { return new Set(); }
  }
  let favorites = readFavorites();
  function imageMarkup(preset, large = false) {
    const source = sourceFor(preset);
    return source ? `<img src="./${source.image}" alt="${escape(source.player + ' – ' + source.name + (catalog.includes(preset) ? '' : ', referansebilde'))}" ${large ? 'fetchpriority="high"' : 'loading="lazy"'} />` : `<span class="garage-no-image"><strong>${escape(preset.car)}</strong><small>Eget preset · uten bilde</small></span>`;
  }
  function favoriteButton(preset) {
    const key = keyFor(preset), saved = favorites.has(key);
    return `<button class="garage-favorite" type="button" data-favorite="${escape(key)}" aria-pressed="${saved}" aria-label="${saved ? 'Fjern favoritt' : 'Lagre favoritt'}: ${escape(preset.player || preset.name)}">${saved ? '♥' : '♡'}</button>`;
  }
  function parts(preset) {
    return [["Bil",preset.body || preset.car],["Dekal",preset.decal],["Hjul",preset.wheels],["Boost",preset.boost]];
  }
  function renderFeature() {
    const preset = lookup(selected) || catalog[0];
    selected = keyFor(preset);
    const pro = catalog.includes(preset), source = sourceFor(preset);
    const active = !pro && presets[state.selectedPreset]?.id === preset.id;
    feature.innerHTML = `<div class="garage-feature-visual">${imageMarkup(preset, true)}${source ? '<button class="garage-image-zoom" data-action="zoom" type="button">Se hele bildet ↗</button>' : ''}</div>
      <div class="garage-feature-info"><div class="garage-feature-topline"><p class="eyebrow">${pro ? 'Proff-inspirert / ' + escape(preset.car) : active ? 'Ditt aktive preset' : 'Din samling'}</p>${favoriteButton(preset)}</div>
      <h2>${escape(pro ? preset.player : preset.name)}</h2><p class="garage-feature-name">${escape(pro ? preset.name : preset.theme)}</p>
      <dl class="garage-parts">${parts(preset).map(([label,value]) => `<div><dt>${label}</dt><dd>${escape(value || 'Ikke oppgitt')}</dd></div>`).join('')}</dl>
      <div class="garage-feature-actions">${pro ? '<button class="primary-button compact-button" data-action="save" type="button">+ Lagre preset</button>' : `<button class="primary-button compact-button" data-action="activate" type="button" ${active ? 'disabled' : ''}>${active ? 'Aktivt i RL Hub ✓' : 'Bruk i RL Hub'}</button>`}
      <button class="secondary-button compact-button" data-action="copy" type="button">Kopier deleliste</button><button class="ghost-button compact-button" data-action="edit" type="button">${pro ? 'Lag egen variant' : 'Rediger'}</button>${!pro && presets.length > 1 ? '<button class="ghost-button compact-button" data-action="delete" type="button">Slett</button>' : ''}</div>
      ${source ? `<p class="garage-source-line">${pro ? 'Gjenskapt' : 'Referansebilde'} av ${escape(source.creator)} · <a href="${source.source}" target="_blank" rel="noopener noreferrer">Se kilde ↗</a></p>` : ''}
      <details class="garage-detail-note"><summary>${pro ? 'Farger og oppsettsdetaljer' : 'Om dette presetet'}</summary><p>${escape(preset.vibe || '')}</p>${pro ? `<p>Blå side: ${escape(preset.blue)}<br>Oransje side: ${escape(preset.orange)}<br>Primær / sekundær finish: ${escape(preset.finish)}<br>Trail: ${escape(preset.trail)}</p><p>${escape(preset.era)}. Kilde sjekket 02.10.2026. Ikke bekreftet som spillerens nåværende oppsett.</p><p>Gold Rush er et Alpha Reward-item. Bruk for eksempel Standard som egen erstatning hvis du mangler det; da blir det en variant av designet.</p>` : source ? '<p>Bildet viser originalreferansen. Egne endringer vises ikke i bildet.</p>' : ''}<p>Lagres i RL Hub. Delene velges manuelt i Rocket League.</p></details></div>`;
  }
  function items() {
    let list = view === "mine" ? presets : view === "favorites" ? [...catalog, ...presets].filter(p => favorites.has(keyFor(p))) : catalog;
    const query = document.getElementById("garage-search").value.trim().toLocaleLowerCase("nb-NO");
    return list.filter(p => (carFilter === "all" || (carFilter === "other" ? !["Fennec","Octane"].includes(p.car) : p.car === carFilter)) && [p.name,p.player,p.car,p.decal,p.wheels,p.theme,...(p.tags || [])].join(' ').toLocaleLowerCase("nb-NO").includes(query));
  }
  function renderGrid() {
    const list = items();
    grid.innerHTML = list.length ? list.map(preset => {
      const key = keyFor(preset), source = sourceFor(preset), pro = catalog.includes(preset);
      const active = !pro && presets[state.selectedPreset]?.id === preset.id;
      return `<article class="garage-card${key === selected ? ' is-selected' : ''}"><button class="garage-card-open" type="button" data-open="${escape(key)}" aria-label="Vis ${escape((preset.player ? preset.player + ' – ' : '') + preset.name)}"><span class="garage-card-image${source?.id === 'retals-anodized' ? ' is-portrait' : ''}">${imageMarkup(preset)}</span><span class="garage-card-info"><span class="garage-card-player">${escape(pro ? preset.player : active ? 'Aktivt i RL Hub' : 'Eget preset')}</span><span class="garage-card-title">${escape(preset.name)}</span><span class="garage-card-meta">${escape(preset.car)} · ${escape(preset.decal)}</span><span class="garage-card-footer"><span>${escape(pro ? preset.era : preset.theme)}</span><span class="garage-card-arrow">Se oppsett ↗</span></span></span></button>${favoriteButton(preset)}</article>`;
    }).join('') : `<div class="garage-empty"><strong>${view === 'favorites' ? 'Ingen favoritter i dette utvalget' : 'Ingen presets funnet'}</strong>${view === 'favorites' ? 'Trykk på hjertet på et preset for å lagre det her.' : 'Prøv et annet søk eller bilfilter.'}</div>`;
    document.getElementById("garage-result-count").textContent = `${list.length} presets`;
    document.getElementById("garage-favorite-count").textContent = [...catalog,...presets].filter(p => favorites.has(keyFor(p))).length;
    document.getElementById("garage-mine-count").textContent = presets.length;
    document.getElementById("garage-active-name").textContent = presets[state.selectedPreset]?.name || "Ingen aktive presets";
    document.querySelectorAll('.garage-tab').forEach(tab => { const on = tab.dataset.view === view; tab.classList.toggle('active',on); tab.setAttribute('aria-selected',on); tab.tabIndex = on ? 0 : -1; });
    document.querySelectorAll('.garage-filter').forEach(button => { const on = button.dataset.car === carFilter; button.classList.toggle('active',on); button.setAttribute('aria-pressed',on); });
  }
  function render() { renderFeature(); renderGrid(); }
  function persist(change) {
    const previous = JSON.parse(JSON.stringify(presets)), index = state.selectedPreset;
    try { change(); saveGaragePresets(); saveUiState(); renderAppState(); return true; }
    catch (_) { presets = previous; state.selectedPreset = index; feedback('Kunne ikke lagre. Kontroller ledig plass og prøv igjen.'); return false; }
  }
  function openEditor(preset = null) {
    editing = preset && !catalog.includes(preset) ? preset.id : null;
    reference = preset ? sourceFor(preset)?.id : null;
    form.reset();
    form.elements.car.querySelectorAll('[data-custom-car]').forEach(option => option.remove());
    if (preset && ![...form.elements.car.options].some(option => option.value === preset.car)) {
      const option = new Option(preset.car, preset.car); option.dataset.customCar = 'true'; form.elements.car.add(option);
    }
    for (const key of ['name','car','wheels','decal','boost','theme','vibe']) if (preset) form.elements[key].value = key === 'name' && catalog.includes(preset) ? `${preset.player} – min variant` : preset[key] || '';
    document.getElementById('garage-editor-title').textContent = editing ? 'Rediger preset' : preset ? 'Lag din egen variant' : 'Nytt preset';
    editor.showModal();
  }
  document.querySelector('.garage-main').addEventListener('click', async event => {
    const button = event.target.closest('button');
    if (!button) return;
    if (button.dataset.favorite) {
      const key = button.dataset.favorite, wasSaved = favorites.has(key);
      if (wasSaved) favorites.delete(key); else favorites.add(key);
      try { localStorage.setItem(favoriteKey,JSON.stringify([...favorites])); }
      catch (_) { if (wasSaved) favorites.add(key); else favorites.delete(key); feedback('Kunne ikke lagre favoritten.'); return; }
      render();
      const focusButton = [...document.querySelectorAll('[data-favorite]')].find(b => b.dataset.favorite === key && (event.target.closest('.garage-card') ? b.closest('.garage-card') : b.closest('.garage-feature')));
      focusButton?.focus({preventScroll:true});
      return;
    }
    if (button.dataset.view) { view = button.dataset.view; renderGrid(); return; }
    if (button.dataset.car) { carFilter = button.dataset.car; renderGrid(); return; }
    if (button.dataset.open) { selected = button.dataset.open; render(); feature.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',block:'nearest'}); return; }
    if (button.id === 'garage-new') { openEditor(); return; }
    if (button.id === 'garage-close-editor') { editor.close(); return; }
    if (button.id === 'garage-close-image') { imageDialog.close(); return; }
    const preset = lookup(selected);
    if (!preset) return;
    switch (button.dataset.action) {
      case 'save': {
        let saved = presets.find(p => p.catalogId === preset.id);
        if (!saved) {
          saved = {...preset,id:crypto.randomUUID(),catalogId:preset.id,referenceId:preset.id,custom:true,stats:cloneDefaultPresets()[0].stats};
          if (!persist(() => presets.push(saved))) return;
        }
        selected = 'mine:' + saved.id; view = 'mine'; carFilter = 'all'; document.getElementById('garage-search').value = ''; render(); feedback('Preset lagret i din samling.'); break;
      }
      case 'activate':
        if (persist(() => { state.selectedPreset = presets.findIndex(p => p.id === preset.id); })) { render(); feedback('Aktivt preset i RL Hub. Sett delene manuelt i spillet.'); }
        break;
      case 'edit': openEditor(preset); break;
      case 'delete': {
        const index = presets.findIndex(p => p.id === preset.id);
        if (presets.length <= 1 || index < 0) return;
        if (persist(() => { presets.splice(index,1); if (state.selectedPreset > index) state.selectedPreset--; else if (state.selectedPreset === index) state.selectedPreset = Math.min(index,presets.length-1); })) { selected = 'mine:' + presets[state.selectedPreset].id; render(); feedback('Preset slettet.'); }
        break;
      }
      case 'copy': {
        const text = [(preset.player ? preset.player + ' – ' : '') + preset.name,...parts(preset).map(([k,v]) => `${k}: ${v || 'Ikke oppgitt'}`),`Farger: ${preset.theme || 'Ikke oppgitt'}`,preset.finish ? `Finish: ${preset.finish}` : '',preset.blue ? `Blå side: ${preset.blue}` : '',preset.orange ? `Oransje side: ${preset.orange}` : '',sourceFor(preset) ? `Referanse: ${sourceFor(preset).source}` : '', 'Velg delene manuelt i Rocket League.'].filter(Boolean).join('\n');
        try { await navigator.clipboard.writeText(text); feedback('Delelisten er kopiert.'); } catch (_) { feedback('Kunne ikke kopiere. Prøv igjen.'); }
        break;
      }
      case 'zoom': {
        const source = sourceFor(preset); if (!source) return;
        const image = document.getElementById('garage-large-image'); image.src = './' + source.image; image.alt = source.player + ' – ' + source.name;
        document.getElementById('garage-image-credit').textContent = `Bilde: ${source.creator} / BakkesPlugins · ${catalog.includes(preset) ? 'community-gjenskaping' : 'originalreferanse'}`;
        imageDialog.showModal(); break;
      }
    }
  });
  document.querySelector('.garage-tabs').addEventListener('keydown', event => {
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
    event.preventDefault(); const tabs = [...document.querySelectorAll('.garage-tab')]; const i = tabs.findIndex(t => t.dataset.view === view);
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length-1 : (i + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    view = tabs[next].dataset.view; renderGrid(); tabs[next].focus();
  });
  document.getElementById('garage-search').addEventListener('input', renderGrid);
  form.addEventListener('submit', event => {
    event.preventDefault(); if (!form.reportValidity()) return;
    const values = Object.fromEntries(new FormData(form));
    for (const key of Object.keys(values)) values[key] = values[key].trim();
    if (!values.name) { form.elements.name.focus(); return; }
    const existing = editing ? presets.find(p => p.id === editing) : null;
    const preset = {...existing,...values,body:existing?.car === values.car ? existing.body || values.car : values.car,id:existing?.id || crypto.randomUUID(),custom:true,referenceId:reference || '',catalogId:'',tags:['Eget preset',values.car],stats:existing?.stats || cloneDefaultPresets()[0].stats};
    if (persist(() => { const index = presets.findIndex(p => p.id === editing); if (index >= 0) presets[index] = preset; else presets.push(preset); })) {
      selected = 'mine:' + preset.id; view = 'mine'; carFilter = 'all'; document.getElementById('garage-search').value = ''; editor.close(); render(); feedback('Preset lagret.');
    }
  });
  window.addEventListener('storage', event => { if ([GARAGE_PRESETS_STORAGE_KEY,UI_STATE_STORAGE_KEY,favoriteKey].includes(event.key)) { favorites = readFavorites(); render(); } });
  // Broken images degrade to an explicit empty state, never to a different car.
  document.addEventListener('error', event => { if (event.target.tagName === 'IMG' && event.target.closest('.garage-feature,.garage-card')) { const fallback = document.createElement('span'); fallback.className='garage-no-image'; fallback.textContent='Bildet kunne ikke lastes'; event.target.replaceWith(fallback); } }, true);
  render();
})();
