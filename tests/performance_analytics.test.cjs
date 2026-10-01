const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../performance-analytics.js'), 'utf8') + '\nglobalThis.analytics = performanceAnalytics;', context);
const analytics = context.analytics;
const playerFor = match => match.players.find(player => player.playerId === 'me');
const matches = Array.from({length: 25}, (_, i) => ({
  id: String(i), playlist: i < 15 ? 11 : 13, endedAt: new Date(1700000000000 + i * 60000).toISOString(), winnerTeam: i % 2,
  players: [{playerId: 'me', team: 0, shots: i, goals: i % 3, saves: i % 5, assists: i % 2, score: 100 + i}]
}));
const original = JSON.stringify(matches);
const filtered = analytics.filter(matches, playerFor, '11', 'all');
assert.equal(filtered.length, 15);
assert.equal(analytics.recent(filtered, playerFor, 5).map(row => row.id).join(','), '10,11,12,13,14');
assert.equal(analytics.recent(matches, playerFor, 10).length, 10);
assert.equal(analytics.recent(matches, playerFor, 20).length, 20);
assert.equal(analytics.sort(matches, playerFor, 'shots')[0].id, '24');
assert.equal(analytics.sort(matches, playerFor, 'oldest')[0].id, '0');
assert.equal(analytics.filter(matches, playerFor, 'all', 'win').length, 13);
assert.equal(analytics.filter(matches, playerFor, 'all', 'loss').length, 12);
assert.equal(JSON.stringify(matches), original, 'Calculations must not mutate stored history');
const small = [
  {players: [{playerId: 'me', team: 0, shots: 2, goals: 1, saves: null}], winnerTeam: 0},
  {players: [{playerId: 'me', team: 0, shots: 8, goals: 1, saves: 0}], winnerTeam: null},
  {players: [{playerId: 'someone-else', shots: 20, goals: 10}]}
];
const summary = analytics.summary(small, playerFor);
assert.equal(summary.accuracy, 20, 'Accuracy must be weighted by total shots');
assert.equal(summary.saves.average, 0, 'A missing stat is not a zero-valued observation');
assert.equal(summary.saves.count, 1);
assert.equal(summary.wins, 1);
assert.equal(summary.losses, 0, 'Unknown winners must not be counted as losses');
assert.equal(analytics.recent(small, playerFor, 20).length, 2, 'Other players must be excluded');
assert.equal(analytics.summary([{players: [{playerId: 'me', shots: 0, goals: 0}]}], playerFor).accuracy, null);
assert.equal(analytics.summary([], playerFor).shots.total, null);
assert.equal(analytics.number({shots: NaN}, 'shots'), null);
console.log('Performance analytics: filters, chronology, windows, own player, missing stats and weighted accuracy OK');
