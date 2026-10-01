// Pure calculations shared by the match list and the trends view.
const performanceAnalytics = {
  timestamp(match) {
    const value = Date.parse(match.endedAt);
    return Number.isFinite(value) ? value : 0;
  },
  number(player, key) {
    const value = player && player[key];
    return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : null;
  },
  result(match, player) {
    if (!player || ![0, 1].includes(player.team) || ![0, 1].includes(match.winnerTeam)) return null;
    return player.team === match.winnerTeam ? "win" : "loss";
  },
  filter(matches, playerFor, mode = "all", result = "all") {
    return matches.filter(match =>
      (mode === "all" || String(match.playlist) === mode) &&
      (result === "all" || this.result(match, playerFor(match)) === result));
  },
  sort(matches, playerFor, order = "newest") {
    return [...matches].sort((a, b) => {
      const time = this.timestamp(b) - this.timestamp(a);
      if (order === "oldest") return -time;
      if (order === "newest") return time;
      const av = this.number(playerFor(a), order);
      const bv = this.number(playerFor(b), order);
      if (av === null && bv === null) return time;
      if (av === null) return 1;
      if (bv === null) return -1;
      return bv - av || time;
    });
  },
  recent(matches, playerFor, count) {
    return this.sort(matches.filter(match => playerFor(match)), playerFor).slice(0, count).reverse();
  },
  summary(matches, playerFor) {
    const summary = {};
    for (const key of ["score", "goals", "assists", "saves", "shots"]) {
      const values = matches.map(match => this.number(playerFor(match), key)).filter(value => value !== null);
      const total = values.reduce((sum, value) => sum + value, 0);
      summary[key] = {total: values.length ? total : null, average: values.length ? total / values.length : null, count: values.length};
    }
    const shotPairs = matches.map(playerFor).filter(player => this.number(player, "shots") !== null && this.number(player, "goals") !== null);
    const shots = shotPairs.reduce((sum, player) => sum + player.shots, 0);
    summary.accuracy = shots ? shotPairs.reduce((sum, player) => sum + player.goals, 0) / shots * 100 : null;
    summary.wins = matches.filter(match => this.result(match, playerFor(match)) === "win").length;
    summary.losses = matches.filter(match => this.result(match, playerFor(match)) === "loss").length;
    return summary;
  }
};
