import assert from 'node:assert/strict';
import {selectRank, tiers} from '../frontend/lanyard/src/rank.js';
assert.equal(tiers.length, 23);
for (let tier = 0; tier < 23; tier++) {
  const name = tiers[tier] + (tier > 0 && tier < 22 ? ' Division IV' : '');
  const result = selectRank({name:'Test',ranks:[{playlist:'2v2',rank:name,mmr:1234}]},'2v2');
  assert.equal(result.tier,tier); assert.equal(result.rank,name); assert.equal(result.mmr,1234);
}
const profile = {ranks:[{playlist:'1v1',rank:'Diamond II Division I',mmr:945},{playlist:'2v2',rank:'Champion I Division II',mmr:1234}]};
assert.equal(selectRank(profile,'1v1').tier,14);
assert.equal(selectRank(profile,'2v2').tier,16);
assert.equal(selectRank(profile,'3v3').known,false);
assert.equal(selectRank(null,'2v2').known,false);
assert.equal(selectRank({ranks:[{playlist:'2v2',rank:'invalid',mmr:null}]},'2v2').mmr,null);
console.log('Dashboard rank: all 23 icons, division handling, playlist isolation, unknown and unavailable rank OK');
