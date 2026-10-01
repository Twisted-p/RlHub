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
  return match.players.find((row) => row.playerId === playerId) ||
    match.players.find((row) => row.name.toLowerCase() === name.toLowerCase());
}

function matchResult(match, player) {
  if (!player || ![0, 1].includes(player.team)) return "Kamp avsluttet";
  return player.team === match.winnerTeam ? "Seier" : "Tap";
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
  const matches = data.matches;
  if (!matches.length) return;
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
