// Codes checked against the linked articles on 2026-10-02; not tested in-game.
(function(root) {
  const rank = 'https://dignitas.gg/articles/best-training-packs-for-every-rank-in-rocket-league';
  const practice = 'https://dignitas.gg/articles/training-packs-you-can-utilize-today-in-rocket-league';
  const packs = [
    ['Ground Shots', '6EB1-79B2-33B8-681C', 'Skudd', 'Silver', rank],
    ['Basic Aerials', 'F0BD-E416-D47D-AF28', 'Aerials', 'Platinum', rank],
    ['Saves', '2E23-ABD5-20C6-DBD4', 'Forsvar', 'Varierende nivå', practice],
    ['Powershots', '7028-5E10-88EF-E83E', 'Skudd', 'Silver', rank],
    ['Dribble Training', '04C1-42C8-6E5D-6F75', 'Ballkontroll', 'Platinum', rank],
    ['Shadow Defense', '5CCE-FB29-7B05-A0B1', 'Forsvar', 'Diamond', rank],
    ['The Ultimate Warm-Up', 'FA24-B2B7-2E8E-193B', 'Oppvarming', 'Variert trening', practice],
    ['Aerial Shots – Pass', 'C7E0-9E0B-B739-A899', 'Aerials', 'Nivå ikke oppgitt', practice],
    ['Backboard Saves', 'D7F8-FD53-98D1-DAFE', 'Forsvar', 'Champion', rank],
    ['Basic Rebound Practice', '3DBA-229E-745C-429C', 'Skudd', 'Gold', rank],
    ['Wall Shots', '9F6D-4387-4C57-2E4B', 'Veggspill', 'Platinum', rank],
    ['Speed Flip', '936E-C293-5DF5-2D5C', 'Kickoff', 'Diamond', rank],
    ['Ground Shots 2', '1B69-2B20-19E0-CFEF', 'Skudd', 'Videre fra Ground Shots', practice],
    ['Aerial Shots – Pass 2', '8B11-F7CF-A64C-229C', 'Aerials', 'Videre fra Pass', practice],
    ['Shadow Defense', '6726-51F1-6B0D-9540', 'Forsvar', 'Champion', rank],
    ['Bronze/Silver Training', '2D89-9321-42D2-48BA', 'Grunntrening', 'Silver', rank],
    ['Fast Aerials', '97B9-5B48-5277-8A85', 'Aerials', 'Diamond', rank],
    ['Aerial Shots – Redirects', '8D93-C997-0ACD-8416', 'Presisjon', 'Avansert', practice]
  ].map(([name, code, category, level, source]) => ({name, code, category, level, source}));
  if (typeof module !== 'undefined' && module.exports) module.exports = packs;
  else root.RLTrainingPacks = packs;
})(typeof window !== 'undefined' ? window : globalThis);
