(() => {
  if (document.body.dataset.page !== 'settings') return;
  const profiles = window.RL_PRO_SETTINGS, storageKey = 'rlhub:proSettings';
  const cameraLabels = ['Camera Shake','FOV','Height','Angle','Distance','Stiffness','Swivel Speed','Transition Speed','Ball Camera'];
  const controlLabels = ['Powerslide','Air Roll','Air Roll Left','Air Roll Right','Boost','Jump','Ball Cam','Brake','Throttle'];
  const deadzoneLabels = ['Controller Deadzone','Dodge Deadzone','Aerial Sensitivity','Steering Sensitivity'];
  const psNames = {Square:'Square (□)',Circle:'Circle (○)',Cross:'Cross (×)',Triangle:'Triangle (△)'};
  const xboxNames = {Square:'X',Circle:'B',Cross:'A',Triangle:'Y',L1:'LB',R1:'RB',L2:'LT',R2:'RT'};
  const escape = value => String(value).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  let player = profiles[0], controller = 'ps', section = 'camera';
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey));
    player = profiles.find(p=>p.id === stored?.player) || player;
    if (stored?.controller === 'xbox') controller = 'xbox';
  } catch (_) { /* Invalid or disabled storage does not block the page. */ }
  const feedback = message => document.getElementById('settings-feedback').textContent = message;
  function saveSelection() {
    try { localStorage.setItem(storageKey,JSON.stringify({player:player.id,controller})); }
    catch (_) { feedback('Valget kunne ikke huskes til neste oppstart. Du kan fortsatt kopiere innstillingene.'); }
  }
  function binding(value) { return value === null ? 'Ikke bundet' : (controller === 'xbox' ? xboxNames[value] : psNames[value]) || value; }
  const date = value => value ? value.split('-').reverse().join('.') : 'dato ikke oppgitt';
  function rows(group) {
    if (group === 'camera') return cameraLabels.map((label,i)=>[label,player.camera[i]]);
    if (group === 'deadzone') return deadzoneLabels.map((label,i)=>[label,player.deadzone[i]]);
    return controlLabels.map((label,i)=>[label,binding(player.controls[i])]);
  }
  function tiles(group) {
    return rows(group).map(([label,value],i)=>`<article class="settings-value${value === 'Ikke bundet' ? ' is-unbound' : ''}"><p>${label}</p><strong>${escape(value)}</strong><button type="button" data-copy="${group}:${i}" aria-label="Kopier ${label}" title="Kopier verdi">⧉</button></article>`).join('');
  }
  function render() {
    document.getElementById('settings-players').innerHTML = profiles.map(p=>`<button type="button" class="settings-player" data-player="${p.id}" aria-pressed="${p === player}">${p.name}</button>`).join('');
    document.getElementById('settings-player-name').textContent = player.name;
    document.getElementById('settings-region').textContent = player.region + ' / proffprofil';
    document.getElementById('settings-source').href = player.source;
    document.getElementById('settings-controller').value = controller;
    document.querySelectorAll('[data-section]').forEach(tab=>{const active = tab.dataset.section === section; tab.setAttribute('aria-selected',active); tab.tabIndex = active ? 0 : -1;});
    document.getElementById('settings-panel').setAttribute('aria-labelledby','settings-tab-' + section);
    document.getElementById('settings-section-note').textContent = section === 'camera' ? 'Kamera i kilden: ' + date(player.cameraUpdated) : (controller === 'ps' ? 'PlayStation-knapper fra kilden.' : 'Tilsvarende knappesteder på Xbox.') + ' Air Roll er vanlig rotasjon; Left og Right er egne bindinger.';
    document.getElementById('settings-copy-section').textContent = section === 'camera' ? 'Kopier kamera' : 'Kopier kontroller';
    document.getElementById('settings-values').innerHTML = tiles(section);
    document.getElementById('settings-deadzones').hidden = section !== 'controls';
    document.getElementById('settings-deadzone-values').innerHTML = tiles('deadzone');
    document.getElementById('settings-shape').textContent = 'Deadzone Shape i kilden: ' + player.shape + '. Dette er en separat kontroller-/inputinnstilling, ikke en verdi i den vanlige spillmenyen.';
    document.getElementById('settings-dates').textContent = 'Kamera: ' + date(player.cameraUpdated) + '. Deadzone/følsomhet: ' + date(player.deadzoneUpdated) + '. Knappebindinger: dato ikke oppgitt.';
  }
  function sectionText(group) {
    const list = rows(group);
    if (group === 'controls') list.push(...rows('deadzone'),['Deadzone Shape (kontroller/input)',player.shape]);
    return list.map(([label,value])=>label + ': ' + value).join('\n');
  }
  function copyText(scope) {
    if (scope.includes(':')) { const [group,index] = scope.split(':'); return rows(group)[Number(index)][1]; }
    const body = scope === 'all' ? 'KAMERA\n' + sectionText('camera') + '\n\nKONTROLLER / ' + (controller === 'ps' ? 'PlayStation' : 'Xbox (tilsvarende knapper)') + '\n' + sectionText('controls') : sectionText(section);
    return player.name + ' – Rocket League\n\n' + body + '\n\nKilde: ' + player.source + '\nKamera: ' + date(player.cameraUpdated) + ' · Deadzone: ' + date(player.deadzoneUpdated) + '\nKnappebindinger: dato ikke oppgitt. Kildeutdrag hentet 02.10.2026.\nSett innstillingene manuelt i Rocket League.';
  }
  document.querySelector('.settings-main').addEventListener('click',async event=>{
    const button = event.target.closest('button'); if (!button) return;
    if (button.dataset.player) { player = profiles.find(p=>p.id === button.dataset.player); feedback(''); saveSelection(); render(); document.querySelector(`[data-player="${player.id}"]`).focus({preventScroll:true}); }
    if (button.dataset.section) { section = button.dataset.section; feedback(''); render(); }
    if (button.dataset.copy) {
      const text = copyText(button.dataset.copy), name = player.name;
      try { await navigator.clipboard.writeText(text); feedback(button.dataset.copy.includes(':') ? 'Verdien er kopiert.' : name + ': innstillingene er kopiert som tekst.'); }
      catch (_) { const dialog = document.getElementById('settings-copy-dialog'), input = document.getElementById('settings-copy-text'); input.value = text; if (!dialog.open) dialog.showModal(); input.focus(); input.select(); feedback('Marker teksten i vinduet for å kopiere manuelt.'); }
    }
    if (button.id === 'settings-close-dialog') document.getElementById('settings-copy-dialog').close();
  });
  document.getElementById('settings-controller').addEventListener('change',event=>{controller = event.target.value; feedback(''); saveSelection(); render();});
  document.querySelector('.settings-tabs').addEventListener('keydown',event=>{
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
    event.preventDefault(); section = event.key === 'Home' ? 'camera' : event.key === 'End' ? 'controls' : section === 'camera' ? 'controls' : 'camera'; render(); document.getElementById('settings-tab-' + section).focus();
  });
  render();
})();
