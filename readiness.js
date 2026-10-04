// Coaching state is collected by the desktop service on every page.
(() => {
  const el = (id) => document.getElementById(`session-${id}`);
  const duration = (seconds) => `${Math.floor(Math.max(0, seconds) / 60)}:${String(Math.max(0, seconds) % 60).padStart(2, '0')}`;
  const signed = (value) => `${value > 0 ? '+' : value < 0 ? '−' : ''}${Math.abs(value)}`;
  const number = (value) => value === null ? '—' : new Intl.NumberFormat('nb-NO', {maximumFractionDigits: 1}).format(value);
  let busy = false;
  function render(s) {
    const started = Boolean(s.startedAt);
    const score = s.readiness === null ? '—' : `${s.readiness}%`;
    el('score').textContent = el('sidebar-score').textContent = score;
    el('ring').style.setProperty('--readiness', `${s.readiness || 0}%`);
    el('sidebar-bar').style.setProperty('--fill', `${s.readiness || 0}%`);
    el('training').textContent = duration(s.trainingSeconds);
    el('status').textContent = !s.connected ? 'Venter på spillet' : s.resting ? 'Pause' : s.training ? 'Trening' : s.playing ? 'I kamp' : 'I lobby';
    el('note').textContent = started ? 'Din lokale spillform, basert på innsamlede data i denne økten.' : 'Start trening eller en kamp. Aktiver kampoppsummeringer i Performance hvis spillet ikke kobles til.';
    if (s.accountMismatch) el('note').textContent = `Spillet bruker ${s.gamePlayerName || 'en annen konto'} enn rankprofilen. Hent rank for denne kontoen i Profile. MMR fra kontoene blandes ikke.`;
    el('sidebar-copy').textContent = started ? `${s.matchCount} kamper · ${duration(s.trainingSeconds)} trening` : 'Venter på første trenings- eller kampdata.';
    el('sidebar-bracket').textContent = `${s.bracketProgress} / 5`;
    el('bracket-bar').style.setProperty('--fill', `${s.bracketProgress * 20}%`);
    el('focus-clock').textContent = el('sidebar-focus').textContent = duration(s.focusRemaining);
    el('focus-fill').style.width = `${Math.min(100, s.focusSeconds / s.focusLimit * 100)}%`;
    el('focus-bar').style.setProperty('--fill', `${s.focusRemaining / s.focusLimit * 100}%`);
    el('focus-copy').textContent = !started ? 'Timeren starter når du begynner å spille.' : s.focusRemaining === 0 ? '90 minutter er nådd. Ta minst 15 minutter pause og vurder å avslutte økten. Readiness synker videre.' : `${duration(s.focusSeconds)} økttid · −${s.components.fatigue} readiness fra fokustid. Korte pauser nullstiller ikke 90-minuttersrammen.`;
    el('results').textContent = s.recent.length ? `${s.wins} seiere · ${s.losses} tap (${s.recent.length}/5 kamper)` : 'Ingen kamper ennå';
    el('result-dots').replaceChildren(...s.recent.map((match, index) => {
      const dot = document.createElement('span');
      dot.className = match.win ? 'session-win' : 'session-loss';
      dot.textContent = match.win ? 'W' : 'L';
      dot.title = `Kamp ${index + 1}: ${match.win ? 'seier' : 'tap'}${match.partial ? ' · delvis innsamlet' : ''}`;
      return dot;
    }));
    el('mmr').textContent = s.mmr.length ? s.mmr.map(r => `${r.playlist}: ${r.delta === null ? '—' : signed(r.delta)} MMR`).join(' · ') : 'Hent rank i Profile';
    el('mmr').title = `MMR fra siste rank-oppslag. Kilden kan være forsinket. Readiness bruker ${s.playlist}, aktiv eller sist spilte ranked-modus.`;
    el('sample').textContent = `${s.recent.length} av 5 kamper`;
    el('stats').replaceChildren(...[['shots','Skudd'],['goals','Mål'],['saves','Saves'],['assists','Assists'],['score','Poeng']].map(([key, label]) => {
      const card = document.createElement('div'); card.className = 'profile-stat';
      const title = document.createElement('span'); title.textContent = label;
      const value = document.createElement('strong'); value.textContent = number(s.averages[key]);
      card.append(title, value); return card;
    }));
    const a = s.advice;
    let title = 'Én blokk om gangen', copy = `${s.bracketProgress}/5 kamper i neste blokk. Etter fem får du et pauseråd.`;
    el('break-clock').hidden = true;
    if (a.kind) {
      title = a.kind === 'loss' ? 'Ta 15 minutter pause' : a.kind === 'win' ? '5 min pause, så 5 min trening' : 'Ta en pust i bakken';
      copy = a.kind === 'manual' ? 'Bli i lobbyen eller lukk spillet mens RL Hub måler pausen.' : `Blokk ${a.bracket}: ${a.wins} seiere og ${5-a.wins} tap. ${a.kind === 'loss' ? 'Nullstill hodet før neste femkamper.' : 'Behold rytmen med hvile og en kort oppvarming før neste femkamper.'}`;
      if (s.resting) {
        el('break-clock').hidden = false;
        el('break-clock').textContent = `${duration(Math.max(0, a.rest - s.restSeconds))} pause igjen`;
        copy += s.playing ? ' Du spiller nå; pauseklokken starter på nytt når du går ut av trening/kamp.' : ' Pausen teller mens du er ute av trening og kamp. Hold RL Hub åpen.';
      } else if (a.stage === 'warmup') {
        title = 'Pausen er ferdig — tren i 5 minutter';
        copy = 'Gå til freeplay eller trening. Bare faktisk treningstid etter pausen teller.';
        el('break-clock').hidden = false;
        el('break-clock').textContent = `${duration(Math.max(0, a.warmup - s.warmupSeconds))} trening igjen`;
      }
    }
    if (el('coach-title').textContent !== title) el('coach-title').textContent = title;
    el('coach-copy').textContent = copy;
    el('coach').classList.toggle('needs-break', Boolean(a.kind));
    el('break').textContent = s.resting ? 'Pause pågår' : a.stage === 'warmup' ? 'Venter på trening' : `Start ${Math.round((a.rest || 900) / 60)} min pause`;
    el('break').disabled = busy || !started || s.resting || a.stage === 'warmup';
    el('reset').disabled = busy || s.playing;
    el('reset').title = s.playing ? 'Gå til lobbyen før du starter en ny økt.' : 'Nullstiller trening, femkampers blokker, fokustimer og MMR-baseline.';
  }
  async function refresh() {
    try { const response = await fetch('./api/readiness'); if (!response.ok) throw new Error(); render(await response.json()); }
    catch (_) { el('status').textContent = 'Ikke tilkoblet'; el('note').textContent = 'Åpne denne siden i standalone-appen for automatisk måling av spillform.'; }
  }
  async function action(name) {
    busy = true; el('break').disabled = el('reset').disabled = true;
    try {
      const response = await fetch(`./api/readiness/${name}`, {method: 'POST'});
      const result = await response.json(); if (!response.ok) throw new Error(result.error);
      busy = false; render(result); el('action-status').textContent = name === 'reset' ? 'Ny økt klargjort. Timeren starter når du begynner å spille.' : 'Pause startet.';
    } catch (error) { el('action-status').textContent = error.message || 'Kunne ikke oppdatere økten.'; }
    finally { busy = false; await refresh(); }
  }
  el('break').addEventListener('click', () => action('break'));
  el('reset').addEventListener('click', () => action('reset'));
  refresh(); setInterval(refresh, 1000);
})();
