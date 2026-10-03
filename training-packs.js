(() => {
  const grid = document.getElementById('packs-grid');
  const feedback = document.getElementById('packs-feedback');
  let shownSlot;
  function update() {
    const state = RLTrainingRotation.rotation(RLTrainingPacks);
    const seconds = Math.ceil(state.remaining / 1000);
    document.getElementById('packs-countdown').textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
    if (shownSlot === state.slot) return;
    const first = shownSlot === undefined;
    shownSlot = state.slot;
    grid.replaceChildren(...state.packs.map((pack, index) => {
      const card = document.createElement('article');
      card.className = 'pack-card';
      card.innerHTML = `<div class="pack-top"><span class="eyebrow"></span><span class="pack-number">0${index + 1}</span></div><h2></h2><p class="pack-level"></p><code></code><button class="primary-button" type="button">Kopier kode</button><a target="_blank" rel="noopener noreferrer">Se kilde ↗</a>`;
      card.querySelector('.eyebrow').textContent = pack.category;
      card.querySelector('h2').textContent = pack.name;
      card.querySelector('.pack-level').textContent = pack.level;
      card.querySelector('code').textContent = pack.code;
      card.querySelector('a').href = pack.source;
      card.querySelector('button').addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(pack.code);
          feedback.textContent = `Kopiert: ${pack.code}`;
        } catch (_) {
          const field = document.getElementById('packs-copy-text');
          field.value = pack.code;
          const dialog = document.getElementById('packs-copy-dialog');
          if (!dialog.open) dialog.showModal();
          field.focus(); field.select();
        }
      });
      return card;
    }));
    if (!first) feedback.textContent = 'Tre nye treningspakker er klare.';
  }
  document.getElementById('packs-close-dialog').addEventListener('click', () => document.getElementById('packs-copy-dialog').close());
  document.addEventListener('visibilitychange', update);
  window.addEventListener('focus', update);
  window.addEventListener('pageshow', update);
  update();
  setInterval(update, 1000);
})();
