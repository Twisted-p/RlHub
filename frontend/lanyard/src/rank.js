export const tiers = ['Unranked', ...['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Champion', 'Grand Champion'].flatMap(f => ['I', 'II', 'III'].map(n => `${f} ${n}`)), 'Supersonic Legend'];
export function selectRank(profile, playlist) {
  const row = profile?.ranks?.find(r => r.playlist === playlist);
  const rank = typeof row?.rank === 'string' ? row.rank : '';
  const tier = tiers.indexOf(rank.replace(/ Division (I|II|III|IV)$/, ''));
  return {name: typeof profile?.name === 'string' ? profile.name : '', playlist,
    rank: tier >= 0 ? rank : 'Hent rank i Profile', tier: Math.max(tier, 0),
    known: tier >= 0, mmr: Number.isFinite(row?.mmr) ? row.mmr : null};
}
