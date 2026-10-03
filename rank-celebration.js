/* Original RL Hub milestone card. No external scripts or paid component source. */
(() => {
  let active = null, busy = false, previousFocus = null;
  const dismissed = new Set();
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const dialog = document.createElement('dialog');
  dialog.className = 'rank-celebration';
  dialog.setAttribute('aria-labelledby', 'milestone-title');
  dialog.innerHTML = `<div class="milestone-intro"><span class="milestone-eyebrow">EN NY MILEPÆL</span><h2 id="milestone-title">Du har løftet spillet ditt.</h2><p>Et nytt nivå. Samme driv.</p></div>
    <div class="milestone-stage"><article class="milestone-card"><div class="milestone-grain"></div><div class="milestone-orbit"></div>
    <header class="milestone-brand"><span class="milestone-card-type">Rank Card</span><span>RL<span class="milestone-brand-light">HUB</span></span></header>
    <div class="milestone-chip-row" aria-hidden="true"><svg class="milestone-chip" viewBox="0 0 60 44"><defs><linearGradient id="chip-gold" x2="1" y2="1"><stop stop-color="#f3df9c"/><stop offset=".45" stop-color="#ad8140"/><stop offset=".7" stop-color="#e6c782"/><stop offset="1" stop-color="#8a632f"/></linearGradient></defs><rect x="1" y="1" width="58" height="42" rx="9" fill="url(#chip-gold)" stroke="#f7df9c"/><g fill="none" stroke="#705528" stroke-width="1.2"><rect x="21" y="10" width="18" height="24" rx="5"/><path d="M1 14h20M1 30h20M39 14h20M39 30h20M21 1v9M39 1v9M21 34v9M39 34v9M1 22h20M39 22h20"/></g></svg><svg class="milestone-contactless" viewBox="0 0 28 36"><g fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M5 14q4 4 0 8M10 10q8 8 0 16M15 6q12 12 0 24M20 2q16 16 0 32"/></g></svg></div>
    <div class="milestone-content"><div class="milestone-identity"><span class="milestone-label">NY RANK</span><h3 id="milestone-family"></h3><p id="milestone-rank"></p><div class="milestone-path"><span id="milestone-previous"></span><span aria-hidden="true"> ↗ </span><strong id="milestone-mode"></strong></div></div><div class="milestone-emblem"><div class="milestone-halo"></div><img id="milestone-icon" alt=""></div></div>
    <footer class="milestone-footer"><div><span class="milestone-label">GAMERTAG</span><strong id="milestone-name"></strong></div><div class="milestone-date-block"><span class="milestone-label" title="Datoen RL Hub først registrerte denne ranken">OPPNÅDD</span><strong id="milestone-date"></strong></div></footer>
    </article></div><div class="milestone-stats"><div><strong id="milestone-mmr"></strong><span>MMR</span></div><div><strong id="milestone-wins"></strong><span>SEIERE</span></div><div><strong id="milestone-losses"></strong><span>TAP</span></div><div><strong id="milestone-matches"></strong><span>KAMPER</span></div></div>
    <p class="milestone-stat-note">Kampresultater registrert av RL Hub siste 24 timer.</p><button type="button" class="milestone-dismiss">Videre mot neste mål <span aria-hidden="true">↗</span></button><p class="milestone-hint">Esc for å lukke</p>`;
  document.body.append(dialog);
  const card = dialog.querySelector('.milestone-card');
  const button = dialog.querySelector('button');
  const put = (id, value) => { dialog.querySelector(`#milestone-${id}`).textContent = value; };
  async function ack(id) {
    try {
      const response = await fetch('./api/rank-promotions/ack', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})});
      if (response.ok && (await response.json()).acknowledged) dismissed.delete(id);
    } catch (_) { /* Retry on the next poll without showing it twice this page. */ }
  }
  function dismiss() {
    if (!active) return;
    const id = active.id;
    dismissed.add(id);
    active = null;
    dialog.close();
    if (previousFocus?.isConnected) previousFocus.focus({preventScroll:true});
    ack(id);
  }
  button.addEventListener('click', dismiss);
  dialog.addEventListener('cancel', event => { event.preventDefault(); dismiss(); });
  card.addEventListener('pointermove', event => {
    if (reduced.matches || event.pointerType === 'touch') return;
    const box = card.getBoundingClientRect();
    const x = Math.max(-.5, Math.min(.5, (event.clientX-box.left)/box.width-.5));
    const y = Math.max(-.5, Math.min(.5, (event.clientY-box.top)/box.height-.5));
    card.style.setProperty('--tilt-x', `${-y*12}deg`);
    card.style.setProperty('--tilt-y', `${x*14}deg`);
    card.style.setProperty('--shine-x', `${(x+.5)*100}%`);
    card.style.setProperty('--shine-y', `${(y+.5)*100}%`);
  });
  card.addEventListener('pointerleave', () => {card.style.setProperty('--tilt-x','0deg');card.style.setProperty('--tilt-y','0deg');});
  async function poll() {
    if (busy || document.hidden || document.body.classList.contains('splash-active')) return;
    busy = true;
    try {
      const response = await fetch('./api/rank-promotions');
      if (!response.ok) return;
      const {events} = await response.json();
      for (const id of dismissed) ack(id);
      if (active) {
        if (!events.some(event => event.id === active.id)) {active=null;dialog.close();}
        return;
      }
      const event = events.find(event => !dismissed.has(event.id));
      if (!event) return;
      active = event;
      const digits = {I:'1', II:'2', III:'3', IV:'4'};
      const cardRank = event.rank.replace(/\b(IV|III|II|I)\b/g, roman => digits[roman]).replace(' Division ', ' · DIV ');
      put('family', cardRank);put('rank', `${event.mmr} MMR`);put('previous', `Fra ${event.previousFamily}`);
      put('mode', event.playlist);put('name', event.name);put('mmr', event.mmr);
      put('date', new Intl.DateTimeFormat('nb-NO', {day:'2-digit',month:'short',year:'numeric',timeZone:'Europe/Oslo'}).format(new Date(event.observedAt)));
      put('wins',event.stats.wins24h);put('losses',event.stats.losses24h);put('matches',event.stats.matches24h);
      card.style.setProperty('--rank-accent', event.color);
      dialog.querySelector('img').src = `./assets/ranks/${event.icon}.png`;
      previousFocus = document.activeElement;
      dialog.showModal();
      button.focus({preventScroll:true});
    } catch (_) { /* Rank retrieval never blocks the rest of the app. */ }
    finally {busy=false;}
  }
  document.addEventListener('visibilitychange', poll);
  window.setInterval(poll, 2500);
  poll();
})();
