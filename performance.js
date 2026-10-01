const performanceStatus = document.getElementById("performance-status");
const performanceConnection = document.getElementById("performance-connection");
const performanceSetup = document.getElementById("performance-setup");
const performanceEnable = document.getElementById("performance-enable");
const performanceDetail = document.getElementById("performance-detail");
const performanceHistory = document.getElementById("performance-history");
let selectedMatchId = null;
let followLatestMatch = true;
let performanceData = null;
let setupMessage = "";
const modeFilter = document.getElementById("performance-mode");
const resultFilter = document.getElementById("performance-result");
const sortFilter = document.getElementById("performance-sort");
const rangeFilter = document.getElementById("performance-range");
let performanceView = "matches";
let lastModeOptions = "";
let lastTrendRender = "";
const chartMetrics = [["shots", "Skudd", "#59f0d4"], ["goals", "Mål", "#8bc9ff"], ["saves", "Saves", "#ffb478"], ["assists", "Assists", "#ba9bff"]];
const formatPerformanceNumber = value => value === null ? "–" : value.toLocaleString("nb-NO", {maximumFractionDigits: 1});

function safePerformanceText(value) {
  const element = document.createElement("span");
  element.textContent = value == null ? "–" : String(value);
  return element.innerHTML.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function matchPlayer(match) {
  const lookup = readProfileQuery();
  const cached = readStoredTrackerProfile();
  const playerId = (lookup && lookup.playerId) ||
    (cached && lookup && cached.name.toLowerCase() === (lookup.gamertag || "").toLowerCase() && cached.playerId) ||
    (performanceData.localPlayer && performanceData.localPlayer.playerId);
  const name = (lookup && lookup.gamertag) || (performanceData.localPlayer && performanceData.localPlayer.name) || "";
  return playerId ? match.players.find(row => row.playerId === playerId) :
    match.players.find(row => row.name.toLowerCase() === name.toLowerCase());
}

function matchResult(match, player) {
  const result = performanceAnalytics.result(match, player);
  return result === "win" ? "Seier" : result === "loss" ? "Tap" : "Kamp avsluttet";
}

function renderModeOptions() {
  const selected = modeFilter.value;
  const modes = new Map(performanceData.matches.map(match => [String(match.playlist), match.mode || "Annen modus"]));
  const key = JSON.stringify([...modes]);
  if (key === lastModeOptions) return;
  lastModeOptions = key;
  modeFilter.innerHTML = '<option value="all">Alle gamemodes</option>' + [...modes].sort((a, b) => a[1].localeCompare(b[1], "nb-NO")).map(([value, label]) => `<option value="${safePerformanceText(value)}">${safePerformanceText(label)}</option>`).join("");
  modeFilter.value = modes.has(selected) ? selected : "all";
}

function renderTrendChart(matches, key, label, color) {
  const values = matches.map(match => performanceAnalytics.number(matchPlayer(match), key));
  const ceiling = Math.max(1, ...values.filter(value => value !== null));
  const width = 600, height = 210, left = 38, top = 20, bottom = 173, plotWidth = 545;
  const step = plotWidth / matches.length;
  const bars = matches.map((match, index) => {
    const value = values[index];
    const x = left + step * (index + .5);
    const barHeight = value === null ? 0 : value / ceiling * (bottom - top);
    const tooltip = `${new Date(match.endedAt).toLocaleString("nb-NO")} · ${match.mode} · ${label}: ${formatPerformanceNumber(value)}${match.partial ? " · Delvis innsamlet" : ""}`;
    return `<g class="performance-chart-point" tabindex="0" role="img" aria-label="${safePerformanceText(tooltip)}"><title>${safePerformanceText(tooltip)}</title><rect x="${x - Math.min(26, step * .65) / 2}" y="${bottom - Math.max(2, barHeight)}" width="${Math.min(26, step * .65)}" height="${Math.max(2, barHeight)}" rx="3" fill="${value === null ? '#66788c' : color}" opacity="${value === null ? '.3' : '.9'}"/><text x="${x}" y="${Math.max(top + 12, bottom - barHeight - 7)}" text-anchor="middle">${formatPerformanceNumber(value)}</text><text x="${x}" y="195" text-anchor="middle">${index + 1}</text></g>`;
  }).join("");
  return `<article class="glass module is-active performance-chart"><div class="module-header"><h3>${label}</h3><span class="live-pill">Per kamp</span></div><svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${label} i ${matches.length} kamper, eldste først"><line x1="${left}" y1="${bottom}" x2="583" y2="${bottom}"/><line x1="${left}" y1="${top}" x2="583" y2="${top}" class="chart-grid"/><text x="28" y="${top + 5}" text-anchor="end">${ceiling}</text><text x="28" y="${bottom + 5}" text-anchor="end">0</text>${bars}</svg><p class="module-note">Kampnummer · eldste → nyeste</p></article>`;
}

function renderPerformanceTrends(filtered) {
  const count = Number(rangeFilter.value);
  const renderKey = JSON.stringify([count, modeFilter.value, resultFilter.value, filtered.map(match => [match, matchPlayer(match)])]);
  if (renderKey === lastTrendRender) return;
  lastTrendRender = renderKey;
  const matches = performanceAnalytics.recent(filtered, matchPlayer, count);
  const omitted = filtered.filter(match => !matchPlayer(match)).length;
  const partial = matches.filter(match => match.partial).length;
  const summary = document.getElementById("performance-trends-summary");
  const metrics = document.getElementById("performance-trend-metrics");
  const charts = document.getElementById("performance-charts");
  const table = document.getElementById("performance-trend-table");
  if (!matches.length) {
    summary.textContent = filtered.length ? "Ingen personlige kampdata for dette utvalget. Koble kontoen din i Profile." : "Ingen kamper i dette utvalget. Spill en kamp eller endre filtrene.";
    metrics.innerHTML = charts.innerHTML = table.innerHTML = "";
    return;
  }
  summary.textContent = `Viser ${matches.length} av opptil ${count} siste kamper etter filtrering, fra eldste til nyeste.${omitted ? ` ${omitted} kamper uten din spiller er utelatt.` : ""}${partial ? ` ${partial} kamper er delvis innsamlet.` : ""} Manglende tall vises som –.`;
  const totals = performanceAnalytics.summary(matches, matchPlayer);
  metrics.innerHTML = chartMetrics.map(([key, label]) => `<div class="profile-stat"><span>${label} totalt</span><strong>${formatPerformanceNumber(totals[key].total)}</strong><small>${formatPerformanceNumber(totals[key].average)} per kamp${totals[key].count < matches.length ? ` · tall fra ${totals[key].count} kamper` : ""}</small></div>`).join("") + `<div class="profile-stat"><span>Skuddprosent samlet</span><strong>${totals.accuracy === null ? "–" : formatPerformanceNumber(totals.accuracy) + "%"}</strong><small>Mål / skudd med tilgjengelige tall</small></div><div class="profile-stat"><span>Resultater</span><strong>${totals.wins}W / ${totals.losses}L</strong><small>Av ${matches.length} kamper</small></div>`;
  charts.innerHTML = chartMetrics.map(([key, label, color]) => renderTrendChart(matches, key, label, color)).join("");
  table.innerHTML = `<table class="performance-table"><thead><tr><th>Kamp</th><th>Gamemode</th><th>Resultat</th><th>Skudd</th><th>Mål</th><th>Saves</th><th>Assists</th></tr></thead><tbody>${matches.map((match, index) => `<tr><td><button class="performance-open-match" type="button" data-open-match="${safePerformanceText(match.id)}">${index + 1} · ${safePerformanceText(new Date(match.endedAt).toLocaleString("nb-NO", {day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"}))}</button></td><td>${safePerformanceText(match.mode)}${match.partial ? " · Delvis" : ""}</td><td>${safePerformanceText(matchResult(match, matchPlayer(match)))}</td>${["shots", "goals", "saves", "assists"].map(key => `<td>${formatPerformanceNumber(performanceAnalytics.number(matchPlayer(match), key))}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}

function matchScore(match) {
  const blue = match.teams.find((row) => row.team === 0);
  const orange = match.teams.find((row) => row.team === 1);
  return `${blue ? blue.score : "–"} : ${orange ? orange.score : "–"}`;
}

function renderPerformance() {
  const data = performanceData;
  if (data.connected) setupMessage = "";
  performanceSetup.hidden = data.enabled;
  performanceConnection.textContent = data.connected
    ? (data.activeMatch ? "Kamp pågår" : data.lastEvent ? "Tilkoblet" : "Venter på kampdata")
    : "Venter på spillet";
  performanceStatus.textContent = setupMessage || (data.connected
    ? data.activeMatch
      ? "Mottar kampdata fra Rocket League. Oppsummeringen lagres når kampen er ferdig."
      : data.lastEvent
        ? "Rocket League er koblet til. Neste avsluttede kamp lagres automatisk."
        : "Forbindelsen til Rocket League er åpen. Venter på de første kampdataene."
    : data.enabled
      ? "Åpne Rocket League og spill en kamp med RL Hub åpen. Har du nettopp aktivert funksjonen, start spillet på nytt."
      : "Aktiver kampoppsummeringer for å komme i gang.");
  renderModeOptions();
  const filtered = performanceAnalytics.filter(data.matches, matchPlayer, modeFilter.value, resultFilter.value);
  const matches = performanceAnalytics.sort(filtered, matchPlayer, sortFilter.value);
  document.getElementById("performance-filter-summary").textContent = `${filtered.length} av ${data.matches.length} lagrede kamper matcher filtrene.`;
  if (performanceView === "trends") renderPerformanceTrends(filtered);
  if (!matches.length) {
    selectedMatchId = null;
    performanceHistory.innerHTML = '<p class="module-note">Ingen kamper i dette utvalget.</p>';
    performanceDetail.innerHTML = data.matches.length ? '<h3>Ingen kamper matcher filtrene</h3><p class="module-note">Velg en annen gamemode eller nullstill filtrene.</p>' : '<h3>Ingen kamper lagret ennå</h3><p class="module-note">Spill en kamp med RL Hub åpen. Oppsummeringen vises når kampen er ferdig.</p>';
    return;
  }
  if (followLatestMatch || !selectedMatchId || !matches.some((match) => match.id === selectedMatchId)) selectedMatchId = matches[0].id;
  performanceHistory.innerHTML = matches.map((match) => {
    const result = matchResult(match, matchPlayer(match));
    const time = new Date(match.endedAt).toLocaleString("nb-NO", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
    return `<button class="performance-match ${match.id === selectedMatchId ? "active" : ""}" type="button" data-match-id="${safePerformanceText(match.id)}"><span>${safePerformanceText(result)} · ${safePerformanceText(matchScore(match))}</span><small>${safePerformanceText(match.mode)} · ${safePerformanceText(time)}</small></button>`;
  }).join("");
  const match = matches.find((row) => row.id === selectedMatchId);
  const player = matchPlayer(match);
  const result = matchResult(match, player);
  const metrics = player ? [["Score", player.score], ["Mål", player.goals], ["Assists", player.assists], ["Saves", player.saves], ["Skudd", player.shots], ["Skuddprosent", player.accuracy == null ? "–" : `${player.accuracy}%`]] : [];
  const observations = [];
  if (player) {
    if (player.goals != null && player.assists != null) observations.push(`Du bidro med ${player.goals} mål og ${player.assists} assists.`);
    if (player.saves > 0) observations.push(`Du stoppet ${player.saves} skudd med saves.`);
    if (player.accuracy != null) observations.push(`${player.goals} av ${player.shots} skudd ble mål (${player.accuracy}%).`);
  }
  performanceDetail.innerHTML = `<div class="module-header"><div><p class="eyebrow">${safePerformanceText(match.mode)}</p><h3>${safePerformanceText(result)}</h3></div><strong class="performance-score">${safePerformanceText(matchScore(match))}</strong></div>
    <p class="module-note">${player ? safePerformanceText(player.name) : "Hele kampen"}${match.overtime ? " · Overtime" : ""} · ${safePerformanceText(new Date(match.endedAt).toLocaleString("nb-NO"))}</p>
    ${match.partial ? '<p class="module-note">RL Hub koblet til underveis. Oppsummeringen bygger på tilgjengelige kampdata.</p>' : ""}
    <div class="performance-metrics">${metrics.map(([label, value]) => `<div class="profile-stat"><span>${safePerformanceText(label)}</span><strong>${safePerformanceText(value)}</strong></div>`).join("")}</div>
    ${observations.length ? `<div class="performance-observations"><h3>Ditt bidrag</h3>${observations.map((text) => `<p>${safePerformanceText(text)}</p>`).join("")}</div>` : '<p class="module-note">Din spiller ble ikke gjenkjent i denne kampen. Velg kontoen din i Profile for personlige tall.</p>'}
    <h3>Scoreboard</h3><div class="performance-table-wrap"><table class="performance-table"><thead><tr><th>Spiller</th><th>Score</th><th>Mål</th><th>Assists</th><th>Saves</th><th>Skudd</th></tr></thead><tbody>${match.players.map((row) => `<tr class="${row.team === 0 ? "team-blue" : "team-orange"}"><td>${safePerformanceText(row.name)}${player && row.playerId === player.playerId ? " · deg" : ""}</td>${[row.score, row.goals, row.assists, row.saves, row.shots].map((value) => `<td>${safePerformanceText(value)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
    <p class="module-note">Kilde: Rocket League Stats API. Blått lag vises først i resultatet.</p>`;
}

async function refreshPerformance() {
  try {
    const response = await fetch("/api/performance");
    if (!response.ok) throw new Error();
    performanceData = await response.json();
    renderPerformance();
  } catch (error) {
    performanceConnection.textContent = "Ikke tilkoblet";
    performanceStatus.textContent = "Kampoppsummeringer er tilgjengelig i Windows-appen. Hvis appen er åpen, prøv å starte den på nytt.";
  }
}

performanceHistory.addEventListener("click", (event) => {
  const button = event.target.closest("[data-match-id]");
  if (button) { followLatestMatch = false; selectedMatchId = button.dataset.matchId; renderPerformance(); }
});
performanceEnable.addEventListener("click", async () => {
  performanceEnable.disabled = true;
  try {
    const response = await fetch("/api/performance/setup", { method: "POST" });
    const payload = await response.json();
    setupMessage = response.ok ? payload.message : payload.error;
    await refreshPerformance();
  } catch (error) {
    performanceStatus.textContent = "Kunne ikke aktivere kampoppsummeringer. Prøv igjen.";
  } finally { performanceEnable.disabled = false; }
});
refreshPerformance();
const performanceRefreshTimer = window.setInterval(refreshPerformance, 2000);
window.addEventListener("pagehide", () => window.clearInterval(performanceRefreshTimer));

function switchPerformanceView(view, focus = false) {
  performanceView = view;
  for (const name of ["matches", "trends"]) {
    const selected = name === view;
    const tab = document.getElementById(`performance-tab-${name}`);
    tab.classList.toggle("active", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    document.getElementById(`performance-${name}-panel`).hidden = !selected;
    if (selected && focus) tab.focus();
  }
  document.getElementById("performance-sort-field").hidden = view !== "matches";
  document.getElementById("performance-range-field").hidden = view !== "trends";
  if (performanceData) renderPerformance();
}
for (const view of ["matches", "trends"]) {
  const tab = document.getElementById(`performance-tab-${view}`);
  tab.addEventListener("click", () => switchPerformanceView(view));
  tab.addEventListener("keydown", event => {
    if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      switchPerformanceView(event.key === "Home" ? "matches" : event.key === "End" ? "trends" : performanceView === "matches" ? "trends" : "matches", true);
    }
  });
}
for (const field of [modeFilter, resultFilter, sortFilter, rangeFilter]) field.addEventListener("change", () => {
  followLatestMatch = true;
  if (performanceData) renderPerformance();
});
document.getElementById("performance-reset-filters").addEventListener("click", () => {
  modeFilter.value = resultFilter.value = "all";
  sortFilter.value = "newest";
  rangeFilter.value = "10";
  followLatestMatch = true;
  if (performanceData) renderPerformance();
});
document.getElementById("performance-trend-table").addEventListener("click", event => {
  const button = event.target.closest("[data-open-match]");
  if (!button) return;
  selectedMatchId = button.dataset.openMatch;
  followLatestMatch = false;
  switchPerformanceView("matches", true);
  performanceDetail.scrollIntoView({behavior: "smooth", block: "start"});
});
