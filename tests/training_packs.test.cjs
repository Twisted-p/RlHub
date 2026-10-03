const assert = require('node:assert/strict');
const packs = require('../training-packs-data.js');
const {interval, rotation} = require('../training-packs-rotation.js');
assert.equal(interval, 900000);
assert.equal(new Set(packs.map(p => p.code)).size, packs.length);
for (const pack of packs) assert.match(pack.code, /^[A-F0-9]{4}(-[A-F0-9]{4}){3}$/);
const codes = time => rotation(packs, time).packs.map(p => p.code);
const base = Math.floor(Date.now() / interval) * interval;
const seen = new Set();
for (let i = 0; i < packs.length / 3; i++) {
  const time = base + i * interval;
  const current = codes(time);
  assert.equal(current.length, 3);
  assert.equal(new Set(current).size, 3);
  assert.deepEqual(codes(time + interval - 1), current);
  assert.equal(rotation(packs, time).remaining, interval);
  assert.equal(rotation(packs, time + interval - 1).remaining, 1);
  assert.ok(codes(time + interval).every(code => !current.includes(code)));
  current.forEach(code => seen.add(code));
}
assert.equal(seen.size, packs.length);
assert.deepEqual(codes(base + packs.length / 3 * interval), codes(base));
assert.deepEqual(codes(base + 23 * interval + 5678), codes(base + 23 * interval));
console.log('Training packs: unique catalog, three per slot, exact quarter-hour boundary, full cycle, reload stability and sleep catch-up OK');
