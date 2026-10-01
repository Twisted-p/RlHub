(() => {
  const cards = document.getElementById('goals-cards');
  const status = document.getElementById('goals-status');
  const nodes = new Map();
  let pending = false;
  function createCard(mode, catalog) {
    const card = document.createElement('section'); card.className = 'goal-card'; card.dataset.mode = mode;
    const header = document.createElement('h3'); header.textContent = mode;
    const current = document.createElement('p'); current.className = 'module-note';
    const label = document.createElement('label'); label.className = 'field-group';
    const text = document.createElement('span'); text.textContent = 'Ranken du vil oppnå';
    const select = document.createElement('select'); select.className = 'profile-input'; select.id = `goal-${mode}`;
    select.add(new Option('Velg rankmål', ''));
    catalog.forEach(row => select.add(new Option(row.rank, String(row.tier))));
    select.addEventListener('change', () => save(mode, select.value ? Number(select.value) : null));
    label.append(text, select);
    const target = document.createElement('p'); target.className = 'goal-target';
    const metrics = document.createElement('div'); metrics.className = 'goal-metrics';
    const gap = document.createElement('strong'), wins = document.createElement('strong');
    for (const [value, caption] of [[gap,'MMR igjen'],[wins,'Seiere på rad, ca.']]) {
      const stat = document.createElement('div'), note = document.createElement('span'); note.textContent = caption;
      stat.append(value, note); metrics.append(stat);
    }
    const note = document.createElement('p'); note.className = 'module-note goal-message';
    card.append(header, current, label, target, metrics, note); cards.append(card);
    nodes.set(mode, {card, select, current, target, gap, wins, note});
  }
  function render(data) {
    document.getElementById('goals-player').textContent = data.name ? `Rankmål for ${data.name}` : 'Dine rankmål';
    const stamp = new Date(data.fetchedAt);
    document.getElementById('goals-updated').textContent = data.fetchedAt && !Number.isNaN(stamp.getTime()) ? `MMR sist hentet ${stamp.toLocaleString('nb-NO')}. Rank-kilden kan være forsinket.` : data.name ? 'Bruker sist hentede MMR. Oppdater rank i Profile ved behov.' : 'Hent rank i Profile for å se din MMR og avstand til målene.';
    data.goals.forEach(row => {
      if (!nodes.has(row.playlist)) createCard(row.playlist, data.catalog);
      const n = nodes.get(row.playlist);
      n.select.value = row.tier === null ? '' : String(row.tier);
      n.select.disabled = pending;
      n.current.textContent = row.currentMmr === null ? 'Ingen MMR hentet for denne modusen' : `${row.currentRank} · ${row.currentMmr} MMR`;
      n.target.textContent = row.targetMmr === null ? 'Velg målet ditt over' : `${row.targetRank} · ca. ${row.targetMmr} MMR`;
      n.gap.textContent = row.remaining === null ? '—' : String(row.remaining);
      n.wins.textContent = row.wins === null ? '—' : String(row.wins);
      n.note.textContent = row.tier === null ? 'Du kan ha ulike rankmål i hver modus.' : row.currentMmr === null ? 'Målet er lagret. Hent rank i Profile for å beregne avstanden.' : row.reached ? 'MMR-målet nådd! Velg et nytt mål når du er klar.' : `Med ${row.wins} seiere på rad à +9 MMR blir du omtrent ${row.currentMmr + row.wins * 9} MMR.`;
      n.card.classList.toggle('goal-reached', row.reached);
    });
  }
  async function refresh() {
    if (pending) return;
    try {
      const response = await fetch('./api/goals'); if (!response.ok) throw new Error();
      const data = await response.json(); if (!pending) render(data);
    } catch (_) { status.textContent = 'Kunne ikke hente målene. Åpne siden i RL Hub-appen og prøv igjen.'; }
  }
  async function save(playlist, tier) {
    pending = true; nodes.forEach(n => n.select.disabled = true);
    try {
      const response = await fetch('./api/goals', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({playlist, tier})});
      const data = await response.json(); if (!response.ok) throw new Error(data.error);
      pending = false; render(data); status.textContent = tier === null ? `Målet for ${playlist} er fjernet.` : `Målet for ${playlist} er lagret.`;
    } catch (error) { status.textContent = error.message || 'Kunne ikke lagre målet.'; }
    finally { pending = false; nodes.forEach(n => n.select.disabled = false); await refresh(); }
  }
  refresh(); setInterval(refresh, 4000);
})();
