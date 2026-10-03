(function(root) {
  const interval = 15 * 60 * 1000;
  function rotation(packs, now = Date.now()) {
    const slot = Math.floor(now / interval);
    const start = ((slot * 3) % packs.length + packs.length) % packs.length;
    return {slot, remaining: (slot + 1) * interval - now,
      packs: Array.from({length: Math.min(3, packs.length)}, (_, i) => packs[(start + i) % packs.length])};
  }
  const api = {interval, rotation};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.RLTrainingRotation = api;
})(typeof window !== 'undefined' ? window : globalThis);
