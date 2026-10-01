const OVERLAY_FEATURES = [
  "gep_internal",
  "stats",
  "match",
  "roster",
  "me",
  "match_info",
  "death",
  "game_info",
  "training",
];

const GARAGE_PRESETS_STORAGE_KEY = "rlhub:garagePresets";
const UI_STATE_STORAGE_KEY = "rlhub:uiState";
const TRACKER_PROFILE_STORAGE_KEY = "rlhub:trackerProfile";
const PROFILE_QUERY_STORAGE_KEY = "rlhub:lastProfileQuery";
const SESSION_STORAGE_KEY = "rlhub:overlaySession";
const TRACKER_PROXY_URL = "http://127.0.0.1:8765";
const ROCKET_LEAGUE_GAME_ID = 10798;
const POST_MATCH_VISIBLE_MS = 35000;
const TRACKER_REFRESH_DELAYS_MS = [4000, 12000, 25000];
const TRAINING_SIGNAL_TTL_MS = 120000;
const INFO_POLL_MS = 2500;
const FEATURE_RETRY_MS = 2000;
const FEATURE_RETRY_LIMIT = 15;
const GEP_DIAGNOSTICS_STORAGE_KEY = "rlhub:gepDiagnostics";
const RANKED_PLAYLISTS = ["1v1", "2v2", "3v3"];
const PLAYLIST_BY_MAX_PLAYERS = { 2: "1v1", 4: "2v2", 6: "3v3" };

const overlayCard = document.getElementById("overlay-card");
const storedSessionState = readOverlaySessions();

const overlayState = {
  connected: false,
  phase: "hidden",
  inActiveMatch: false,
  score: 0,
  goals: 0,
  assists: 0,
  saves: 0,
  shots: 0,
  teamScore: 0,
  playerTeam: 0,
  team1Score: null,
  team2Score: null,
  result: "",
  matchType: "",
  gameMode: "",
  gameState: "",
  currentArena: "",
  offlineArenaActive: false,
  rankedMatch: false,
  maxPlayers: 0,
  trackedMatch: false,
  trackedPlaylist: "",
  currentMatchId: "",
  activeMatchId: "",
  lastFinishedMatchId: "",
  pendingResult: "",
  resultCommitted: false,
  matchFinished: false,
  matchStartMmr: null,
  matchMmrDelta: null,
  trackerRefreshStatus: "idle",
  trackerRefreshGeneration: 0,
  trainingMode: false,
  trainingPack: "",
  trainingStartedAt: null,
  lastTrainingSignalAt: 0,
  postMatchUntil: 0,
  activePlaylist: storedSessionState.activePlaylist,
  sessions: storedSessionState.playlists,
  session: storedSessionState.playlists[storedSessionState.activePlaylist],
};

function readJsonStorage(key) {
  try {
    return JSON.parse(localStorage.getItem(key));
  } catch (error) {
    return null;
  }
}

function writeJsonStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn("RL Hub could not write local storage", key, error);
  }
}

function summarizeGepPayload(kind, payload) {
  if (kind === "events") {
    return {
      events: Array.isArray(payload && payload.events)
        ? payload.events.map((eventItem) => ({ name: eventItem.name, data: eventItem.data }))
        : [],
    };
  }

  if (kind === "info") {
    const source = (payload && (payload.res || payload.info)) || {};
    return {
      success: payload && payload.success,
      match_info: source.match_info,
      matchInfo: source.matchInfo,
      matchState: source.matchState,
      me: source.me,
      teamsScore: source.teamsScore,
      training: source.training,
    };
  }

  return payload;
}

function recordGepDiagnostic(kind, payload) {
  const diagnostics = readJsonStorage(GEP_DIAGNOSTICS_STORAGE_KEY);
  let entries = Array.isArray(diagnostics) ? diagnostics : [];
  const summary = summarizeGepPayload(kind, payload);

  if (JSON.stringify(entries).length > 100000) {
    entries = [];
  }

  entries.push({
    at: new Date().toISOString(),
    kind,
    payload: summary,
  });

  writeJsonStorage(GEP_DIAGNOSTICS_STORAGE_KEY, entries.slice(-40));
  console.log(`[RL Hub GEP] ${kind}`, summary);
}

function createPlaylistSession(playlist) {
  return {
    playlist,
    startMmr: null,
    currentMmr: null,
    wins: 0,
    losses: 0,
    streakType: "neutral",
    streakCount: 0,
    nextRank: null,
  };
}

function normalizePlaylistSession(value, playlist) {
  const source = value && typeof value === "object" ? value : {};
  const startMmr = source.startMmr === null || source.startMmr === undefined ? null : Number(source.startMmr);
  const currentMmr = source.currentMmr === null || source.currentMmr === undefined ? null : Number(source.currentMmr);

  return {
    playlist,
    startMmr: Number.isFinite(startMmr) ? startMmr : null,
    currentMmr: Number.isFinite(currentMmr) ? currentMmr : null,
    wins: Number.isFinite(Number(source.wins)) ? Number(source.wins) : 0,
    losses: Number.isFinite(Number(source.losses)) ? Number(source.losses) : 0,
    streakType: source.streakType || "neutral",
    streakCount: Number.isFinite(Number(source.streakCount)) ? Number(source.streakCount) : 0,
    nextRank: source.nextRank || null,
  };
}

function readOverlaySessions() {
  const stored = readJsonStorage(SESSION_STORAGE_KEY);
  const activePlaylist = stored && RANKED_PLAYLISTS.includes(stored.activePlaylist)
    ? stored.activePlaylist
    : "2v2";
  const playlists = {};

  RANKED_PLAYLISTS.forEach((playlist) => {
    const savedPlaylist = stored && stored.playlists ? stored.playlists[playlist] : null;
    playlists[playlist] = normalizePlaylistSession(savedPlaylist, playlist);
  });

  if (stored && !stored.playlists) {
    playlists["2v2"] = normalizePlaylistSession(stored, "2v2");
  }

  return {
    activePlaylist,
    playlists,
  };
}

function saveOverlaySession() {
  writeJsonStorage(SESSION_STORAGE_KEY, {
    version: 2,
    activePlaylist: overlayState.activePlaylist,
    playlists: overlayState.sessions,
  });
}

function setActivePlaylist(playlist) {
  if (!RANKED_PLAYLISTS.includes(playlist)) {
    return;
  }

  overlayState.activePlaylist = playlist;
  overlayState.session = overlayState.sessions[playlist];
  saveOverlaySession();
}

function reloadRankedSessions() {
  const stored = readOverlaySessions();
  overlayState.activePlaylist = stored.activePlaylist;
  overlayState.sessions = stored.playlists;
  overlayState.session = stored.playlists[stored.activePlaylist];
  overlayState.trackedMatch = false;
  overlayState.trackedPlaylist = "";
  overlayState.pendingResult = "";
  overlayState.resultCommitted = false;
  overlayState.matchFinished = false;
  overlayState.matchStartMmr = null;
  overlayState.matchMmrDelta = null;
  overlayState.postMatchUntil = 0;
  clearTrainingMode();
  syncSessionFromTracker();
  renderOverlay();
}

function parseMaybeNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function parseNullableNumber(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function isTrueValue(value) {
  return value === true || value === 1 || String(value).toLowerCase() === "true";
}

function parseMaybeJson(value) {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value !== "string") {
    return value;
  }

  let candidate = value;

  try {
    candidate = decodeURI(candidate);
  } catch (error) {
    candidate = value;
  }

  try {
    return JSON.parse(candidate);
  } catch (error) {
    return candidate;
  }
}

function getBaseGameId(gameInfo) {
  if (!gameInfo) {
    return 0;
  }

  const classId = Number(gameInfo.classId);
  const instanceId = Number(gameInfo.id);

  if (Number.isFinite(classId)) {
    return classId;
  }

  if (Number.isFinite(instanceId)) {
    return Math.floor(instanceId / 10);
  }

  return 0;
}

function isRocketLeagueRunning(gameInfo) {
  return Boolean(gameInfo && gameInfo.isRunning && getBaseGameId(gameInfo) === ROCKET_LEAGUE_GAME_ID);
}

function getActivePresetName() {
  const presets = readJsonStorage(GARAGE_PRESETS_STORAGE_KEY);
  const uiState = readJsonStorage(UI_STATE_STORAGE_KEY);
  const selectedPreset = uiState && Number.isInteger(uiState.selectedPreset) ? uiState.selectedPreset : 0;

  if (Array.isArray(presets) && presets[selectedPreset] && presets[selectedPreset].name) {
    return presets[selectedPreset].name;
  }

  return "Aktiv preset ikke valgt";
}

function getTrackerProfile() {
  const profile = readJsonStorage(TRACKER_PROFILE_STORAGE_KEY);
  return profile && typeof profile === "object" ? profile : null;
}

function getTrackerLookup() {
  const lookup = readJsonStorage(PROFILE_QUERY_STORAGE_KEY);
  if (!lookup || !lookup.gamertag) {
    return null;
  }

  return {
    platform: (lookup.platform || "epic").trim().toLowerCase(),
    gamertag: lookup.gamertag.trim(),
  };
}

function syncSessionFromTracker() {
  const profile = getTrackerProfile();
  if (!profile) {
    return;
  }

  const trackerRanks = Array.isArray(profile.ranks) ? profile.ranks : [];

  trackerRanks.forEach((rank) => {
    if (!rank || !RANKED_PLAYLISTS.includes(rank.playlist)) {
      return;
    }

    const session = overlayState.sessions[rank.playlist];
    const currentMmr = parseNullableNumber(rank.mmr);

    if (currentMmr !== null) {
      if (session.startMmr === null) {
        session.startMmr = currentMmr;
      }

      session.currentMmr = currentMmr;
    }

    if (rank.nextRank) {
      session.nextRank = rank.nextRank;
    }
  });

  const legacySession = profile.session;
  const doubles = overlayState.sessions["2v2"];
  const legacyMmr = legacySession ? parseNullableNumber(legacySession.currentMmr) : null;

  if (legacyMmr !== null && doubles.currentMmr === null) {
    if (doubles.startMmr === null) {
      doubles.startMmr = legacyMmr;
    }

    doubles.currentMmr = legacyMmr;
  }

  if (legacySession && legacySession.nextRank && !doubles.nextRank) {
    doubles.nextRank = legacySession.nextRank;
  }

  saveOverlaySession();
}

function formatSigned(value) {
  if (!Number.isFinite(value) || value === 0) {
    return "0";
  }

  return value > 0 ? `+${value}` : String(value);
}

function getMmrDelta() {
  const start = parseNullableNumber(overlayState.session.startMmr);
  const current = parseNullableNumber(overlayState.session.currentMmr);

  if (start === null || current === null) {
    return null;
  }

  return current - start;
}

function getPlaylistFromMaxPlayers() {
  return PLAYLIST_BY_MAX_PLAYERS[overlayState.maxPlayers] || "";
}

function isTrackedRankedMatch() {
  const type = (overlayState.matchType || "").toLowerCase();
  const mode = (overlayState.gameMode || "").toLowerCase();

  return (
    type.includes("online") &&
    overlayState.rankedMatch &&
    mode === "soccar" &&
    Boolean(getPlaylistFromMaxPlayers())
  );
}

function activateTrackedPlaylist() {
  const playlist = getPlaylistFromMaxPlayers();
  if (!playlist || !isTrackedRankedMatch()) {
    return false;
  }

  setActivePlaylist(playlist);
  overlayState.trackedMatch = true;
  overlayState.trackedPlaylist = playlist;

  if (!Number.isFinite(overlayState.matchStartMmr)) {
    overlayState.matchStartMmr = parseNullableNumber(overlayState.session.currentMmr);
  }

  return true;
}

function beginTrackedMatch() {
  if (!isTrackedRankedMatch()) {
    return false;
  }

  const matchId = overlayState.currentMatchId || `ranked-${Date.now()}`;
  if (
    overlayState.activeMatchId === matchId &&
    !overlayState.matchFinished
  ) {
    return true;
  }

  if (overlayState.lastFinishedMatchId === matchId) {
    return false;
  }

  overlayState.activeMatchId = matchId;
  overlayState.inActiveMatch = true;
  overlayState.postMatchUntil = 0;
  overlayState.result = "";
  overlayState.score = 0;
  overlayState.goals = 0;
  overlayState.assists = 0;
  overlayState.saves = 0;
  overlayState.shots = 0;
  overlayState.playerTeam = 0;
  overlayState.team1Score = null;
  overlayState.team2Score = null;
  overlayState.pendingResult = "";
  overlayState.resultCommitted = false;
  overlayState.matchFinished = false;
  overlayState.trackedMatch = false;
  overlayState.trackedPlaylist = "";
  overlayState.matchStartMmr = null;
  overlayState.matchMmrDelta = null;
  overlayState.trackerRefreshStatus = "idle";
  activateTrackedPlaylist();
  return true;
}

function wasTrackedRankedMatch() {
  return overlayState.trackedMatch || isTrackedRankedMatch();
}

async function refreshTrackerProfile(generation) {
  if (generation !== overlayState.trackerRefreshGeneration || overlayState.trackerRefreshStatus === "updated") {
    return;
  }

  const lookup = getTrackerLookup();
  if (!lookup) {
    overlayState.trackerRefreshStatus = "unavailable";
    renderOverlay();
    return;
  }

  try {
    const params = new URLSearchParams(lookup);
    params.set("refresh", String(Date.now()));
    const response = await fetch(`${TRACKER_PROXY_URL}/api/profile?${params.toString()}`);
    const payload = await response.json().catch(() => ({}));

    if (!response.ok || !payload.profile) {
      throw new Error(payload.error || "Tracker svarte ikke");
    }

    writeJsonStorage(TRACKER_PROFILE_STORAGE_KEY, payload.profile);

    const playlist = overlayState.trackedPlaylist || overlayState.activePlaylist;
    const ranks = Array.isArray(payload.profile.ranks) ? payload.profile.ranks : [];
    const refreshedRank = ranks.find((rank) => rank && rank.playlist === playlist);
    const trackerSession = playlist === "2v2" ? payload.profile.session : null;
    const refreshedMmr = refreshedRank
      ? parseNullableNumber(refreshedRank.mmr)
      : trackerSession
        ? parseNullableNumber(trackerSession.currentMmr)
        : null;

    if (refreshedMmr !== null) {
      overlayState.session.currentMmr = refreshedMmr;

      const nextRank = refreshedRank ? refreshedRank.nextRank : trackerSession && trackerSession.nextRank;
      if (nextRank) {
        overlayState.session.nextRank = nextRank;
      }

      if (Number.isFinite(overlayState.matchStartMmr)) {
        overlayState.matchMmrDelta = refreshedMmr - overlayState.matchStartMmr;
      }

      if (Number.isFinite(overlayState.matchMmrDelta) && overlayState.matchMmrDelta !== 0) {
        if (!overlayState.resultCommitted) {
          overlayState.pendingResult = overlayState.matchMmrDelta > 0 ? "win" : "loss";
          commitPendingResult();
        }

        overlayState.trackerRefreshStatus = "updated";
      }

      saveOverlaySession();
    }

    renderOverlay();
  } catch (error) {
    recordGepDiagnostic("trackerRefreshError", error.message || String(error));
    overlayState.trackerRefreshStatus = "unavailable";
    renderOverlay();
  }
}

function scheduleTrackerRefresh() {
  overlayState.trackerRefreshGeneration += 1;
  const generation = overlayState.trackerRefreshGeneration;
  overlayState.trackerRefreshStatus = getTrackerLookup() ? "updating" : "unavailable";

  TRACKER_REFRESH_DELAYS_MS.forEach((delay) => {
    window.setTimeout(() => refreshTrackerProfile(generation), delay);
  });
}

function getStreakLabel() {
  const { streakType, streakCount } = overlayState.session;
  if (!streakCount || streakType === "neutral") {
    return "Ingen streak";
  }

  return streakType === "win" ? `${streakCount}W` : `${streakCount}L`;
}

function getNextRankText() {
  const nextRank = overlayState.session.nextRank;
  if (!nextRank || nextRank.missing === null || nextRank.missing === undefined) {
    return "Ukjent";
  }

  const prefix = nextRank.estimated ? "ca. " : "";
  return `${prefix}${nextRank.missing} MMR til ${nextRank.label}`;
}

function secondsToClock(seconds) {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(safeSeconds / 60);
  const rest = safeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
}

function getTrainingSeconds() {
  if (!overlayState.trainingStartedAt) {
    return 0;
  }

  return Math.floor((Date.now() - overlayState.trainingStartedAt) / 1000);
}

function getTrainingLabel(value) {
  const parsed = parseMaybeJson(value);

  if (parsed && typeof parsed === "object") {
    return (
      parsed.pack_name ||
      parsed.name ||
      parsed.training_pack ||
      parsed.download_code ||
      parsed.code ||
      "Training pack"
    );
  }

  if (typeof parsed === "string" && parsed.trim()) {
    return parsed;
  }

  return "Freeplay / Training";
}

function setTrainingMode(label) {
  overlayState.trainingMode = true;
  overlayState.trainingPack = label || overlayState.trainingPack || "Freeplay / Training";
  overlayState.lastTrainingSignalAt = Date.now();
  overlayState.inActiveMatch = false;
  overlayState.postMatchUntil = 0;

  if (!overlayState.trainingStartedAt) {
    overlayState.trainingStartedAt = Date.now();
  }
}

function clearTrainingMode() {
  overlayState.trainingMode = false;
  overlayState.trainingPack = "";
  overlayState.trainingStartedAt = null;
  overlayState.lastTrainingSignalAt = 0;
}

function hasFreshTrainingSignal() {
  return (
    overlayState.trainingMode &&
    overlayState.lastTrainingSignalAt > 0 &&
    Date.now() - overlayState.lastTrainingSignalAt < TRAINING_SIGNAL_TTL_MS
  );
}

function classifyPhase() {
  if (Date.now() < overlayState.postMatchUntil) {
    return "post-match";
  }

  const type = (overlayState.matchType || "").toLowerCase();
  const state = (overlayState.gameState || "").toLowerCase();
  const mode = (overlayState.gameMode || "").toLowerCase();
  const inOnlineMatch = type.includes("online") || type.includes("private");
  const inTraining =
    hasFreshTrainingSignal() ||
    overlayState.offlineArenaActive ||
    type.includes("offline") ||
    mode.includes("training") ||
    mode.includes("freeplay");
  const inLobby = type.includes("lobby") || state.includes("waiting") || state === "";
  const inMatch = ["active", "countdown", "postgoalscored", "replayplayback", "podiumspotlight"].some((item) =>
    state.includes(item.toLowerCase())
  );

  if (inTraining) {
    return "training";
  }

  if (overlayState.inActiveMatch || (inMatch && inOnlineMatch)) {
    return "hidden";
  }

  if (inMatch && type && !inOnlineMatch) {
    setTrainingMode(overlayState.trainingPack || "Freeplay / Training");
    return "training";
  }

  if (inMatch) {
    return "hidden";
  }

  if (inLobby) {
    return "lobby";
  }

  return "hidden";
}

function renderLobbyOverlay() {
  syncSessionFromTracker();

  const delta = getMmrDelta();
  const deltaClass = delta === null || delta === 0 ? "" : delta > 0 ? "is-positive" : "is-negative";
  const startMmr = overlayState.session.startMmr !== null ? overlayState.session.startMmr : "-";
  const currentMmr = overlayState.session.currentMmr !== null ? overlayState.session.currentMmr : "-";

  overlayCard.className = "overlay-card is-lobby";
  overlayCard.innerHTML = `
    <div class="overlay-top">
      <div class="overlay-brand">
        <img src="../App Logo.png" alt="RL Hub" />
        <div class="overlay-title">
          <span class="eyebrow">Lobby | ${overlayState.activePlaylist} session</span>
          <strong>Ranked session tracker</strong>
        </div>
      </div>
      <span class="overlay-pill">${getStreakLabel()}</span>
    </div>

    <section class="metric-grid">
      <div class="metric-card">
        <span>Start MMR</span>
        <strong>${startMmr}</strong>
      </div>
      <div class="metric-card">
        <span>Nåværende</span>
        <strong>${currentMmr}</strong>
      </div>
      <div class="metric-card">
        <span>Økt</span>
        <strong class="${deltaClass}">${delta === null ? "-" : `${formatSigned(delta)} MMR`}</strong>
      </div>
    </section>

    <section class="session-row">
      <div class="session-delta">
        <span>Win / loss</span>
        <strong>${overlayState.session.wins}W / ${overlayState.session.losses}L</strong>
      </div>
      <div class="session-delta">
        <span>Neste rank</span>
        <strong>${getNextRankText()}</strong>
      </div>
    </section>
  `;
}

function renderTrainingOverlay() {
  overlayCard.className = "overlay-card is-training";
  overlayCard.innerHTML = `
    <div class="overlay-top">
      <div class="overlay-brand">
        <img src="../App Logo.png" alt="RL Hub" />
        <div>
          <span class="eyebrow">Freeplay / Training</span>
          <strong>Training timer</strong>
        </div>
      </div>
    </div>
    <div class="timer-value">${secondsToClock(getTrainingSeconds())}</div>
    <p class="overlay-copy">${overlayState.trainingPack || "Tid brukt i freeplay/training denne økten."}</p>
  `;
}

function renderPostMatchOverlay() {
  const sessionDelta = getMmrDelta();
  const matchDelta = overlayState.matchMmrDelta;
  const resultLabel = overlayState.result || "Match ferdig";
  const matchDeltaClass = matchDelta === null || matchDelta === 0 ? "" : matchDelta > 0 ? "is-positive" : "is-negative";
  let mmrLabel = "Venter på Tracker";

  if (Number.isFinite(matchDelta) && matchDelta !== 0) {
    mmrLabel = `${formatSigned(matchDelta)} MMR denne kampen`;
  } else if (overlayState.trackerRefreshStatus === "unavailable") {
    mmrLabel = "Tracker-proxy er ikke tilgjengelig";
  }

  overlayCard.className = "overlay-card is-post-match";
  overlayCard.innerHTML = `
    <div class="overlay-top">
      <div class="overlay-brand">
        <img src="../App Logo.png" alt="RL Hub" />
        <div class="overlay-title">
          <span class="eyebrow">Post-match</span>
          <strong>${resultLabel}</strong>
        </div>
      </div>
      <span class="overlay-pill">${getStreakLabel()}</span>
    </div>

    <section class="metric-grid">
      <div class="metric-card">
        <span>Score</span>
        <strong>${overlayState.score}</strong>
      </div>
      <div class="metric-card">
        <span>Goals</span>
        <strong>${overlayState.goals}</strong>
      </div>
      <div class="metric-card">
        <span>Saves</span>
        <strong>${overlayState.saves}</strong>
      </div>
    </section>

    <div class="wide-stat">
      <span>Ranked ${overlayState.trackedPlaylist || overlayState.activePlaylist}</span>
      <strong class="${matchDeltaClass}">${mmrLabel}</strong>
      <p class="overlay-copy">Session: ${sessionDelta === null ? "-" : `${formatSigned(sessionDelta)} MMR`} | ${getNextRankText()}</p>
    </div>
  `;
}

function renderOverlay() {
  overlayState.phase = classifyPhase();

  if (overlayState.phase === "lobby") {
    renderLobbyOverlay();
    return;
  }

  if (overlayState.phase === "training") {
    renderTrainingOverlay();
    return;
  }

  if (overlayState.phase === "post-match") {
    renderPostMatchOverlay();
    return;
  }

  overlayCard.className = "overlay-card is-hidden";
  overlayCard.innerHTML = "";
}

function updateSessionResult(result) {
  overlayState.result = result === "win" ? "Seier" : result === "loss" ? "Tap" : "Kamp ferdig";

  if (result === "win") {
    overlayState.session.wins += 1;
    overlayState.session.streakCount = overlayState.session.streakType === "win" ? overlayState.session.streakCount + 1 : 1;
    overlayState.session.streakType = "win";
  }

  if (result === "loss") {
    overlayState.session.losses += 1;
    overlayState.session.streakCount = overlayState.session.streakType === "loss" ? overlayState.session.streakCount + 1 : 1;
    overlayState.session.streakType = "loss";
  }

  saveOverlaySession();
}

function inferResultFromScore() {
  if (overlayState.pendingResult || ![1, 2].includes(overlayState.playerTeam)) {
    return;
  }

  const ownScore = overlayState.playerTeam === 1 ? overlayState.team1Score : overlayState.team2Score;
  const opponentScore = overlayState.playerTeam === 1 ? overlayState.team2Score : overlayState.team1Score;

  if (ownScore === null || opponentScore === null || ownScore === opponentScore) {
    return;
  }

  overlayState.pendingResult = ownScore > opponentScore ? "win" : "loss";
}

function commitPendingResult() {
  if (overlayState.resultCommitted || !overlayState.pendingResult || !wasTrackedRankedMatch()) {
    return;
  }

  updateSessionResult(overlayState.pendingResult);
  overlayState.resultCommitted = true;
}

function finishTrackedMatch() {
  overlayState.inActiveMatch = false;

  if (overlayState.matchFinished) {
    inferResultFromScore();
    commitPendingResult();
    return;
  }

  if (!wasTrackedRankedMatch()) {
    overlayState.postMatchUntil = 0;
    return;
  }

  overlayState.matchFinished = true;
  overlayState.lastFinishedMatchId = overlayState.activeMatchId || overlayState.currentMatchId;
  overlayState.postMatchUntil = Date.now() + POST_MATCH_VISIBLE_MS;
  inferResultFromScore();
  commitPendingResult();
  scheduleTrackerRefresh();
}

function applyInfoSection(key, value) {
  if (!value || typeof value !== "object") {
    return;
  }

  if (key === "me") {
    if (value.score !== undefined) {
      overlayState.score = parseMaybeNumber(value.score);
    }

    if (value.goals !== undefined) {
      overlayState.goals = parseMaybeNumber(value.goals);
    }

    if (value.assists !== undefined) {
      overlayState.assists = parseMaybeNumber(value.assists);
    }

    if (value.saves !== undefined) {
      overlayState.saves = parseMaybeNumber(value.saves);
    }

    if (value.shots !== undefined) {
      overlayState.shots = parseMaybeNumber(value.shots);
    }

    if (value.team_score !== undefined) {
      overlayState.teamScore = parseMaybeNumber(value.team_score);
    }

    if (value.team !== undefined) {
      overlayState.playerTeam = parseMaybeNumber(value.team);
    }
  }

  if (key === "teamsScore" || key === "teams_score") {
    if (value.team1_score !== undefined) {
      overlayState.team1Score = parseNullableNumber(value.team1_score);
    }

    if (value.team2_score !== undefined) {
      overlayState.team2Score = parseNullableNumber(value.team2_score);
    }

    if (overlayState.matchFinished) {
      inferResultFromScore();
      commitPendingResult();
    }
  }

  if (key === "match_info") {
    const arena = value.arena ? String(value.arena) : "";
    const serverInfo = value.server_info ? String(value.server_info).toLowerCase() : "";
    const isMenuArena = arena.toLowerCase().startsWith("menu_");

    if (arena) {
      overlayState.currentArena = arena;
    }

    if (value.pseudo_match_id) {
      overlayState.currentMatchId = String(value.pseudo_match_id);
    }

    if (isMenuArena) {
      overlayState.offlineArenaActive = false;
      clearTrainingMode();
    } else if (arena && serverInfo.includes("offline")) {
      overlayState.offlineArenaActive = true;
      setTrainingMode(overlayState.trainingPack || "Freeplay");
    }
  }

  if (key === "matchInfo" || key === "match") {
    const matchType = value.matchType || value.match_type;
    const gameMode = value.gameMode || value.game_mode;
    const gameState = value.gameState || value.game_state;

    if (matchType) {
      overlayState.matchType = matchType;
    }

    if (gameMode) {
      overlayState.gameMode = gameMode;
    }

    if (gameState) {
      overlayState.gameState = gameState;
    }

    if (value.ranked !== undefined) {
      overlayState.rankedMatch = isTrueValue(value.ranked);
    }

    if (value.maxPlayers !== undefined || value.max_players !== undefined) {
      const maxPlayers = value.maxPlayers !== undefined ? value.maxPlayers : value.max_players;
      overlayState.maxPlayers = parseMaybeNumber(maxPlayers);
    }

    if (overlayState.inActiveMatch && isTrackedRankedMatch()) {
      activateTrackedPlaylist();
    }

    const normalizedMatchType = matchType ? String(matchType).toLowerCase() : "";

    const normalizedGameState = gameState ? String(gameState).toLowerCase() : "";
    const isWaitingForPlayers = normalizedGameState.includes("waitingforplayers");

    if (isTrackedRankedMatch() && normalizedGameState !== "finished") {
      beginTrackedMatch();
    }

    if (isTrackedRankedMatch() && normalizedGameState === "finished") {
      beginTrackedMatch();
      finishTrackedMatch();
    }

    if (isWaitingForPlayers) {
      clearTrainingMode();
    }

    if (
      (normalizedMatchType.includes("online") || normalizedMatchType.includes("private")) &&
      !overlayState.inActiveMatch
    ) {
      clearTrainingMode();
    }

    if (normalizedMatchType.includes("lobby") && !overlayState.offlineArenaActive) {
      clearTrainingMode();
    }

    if (normalizedMatchType.includes("offline")) {
      setTrainingMode(overlayState.trainingPack || "Freeplay / Training");
    }
  }

  if (key === "matchState" || key === "match_state") {
    const matchEnded = isTrueValue(value.ended);

    if (value.started !== undefined) {
      overlayState.inActiveMatch = isTrueValue(value.started) && !matchEnded;

      if (overlayState.inActiveMatch) {
        overlayState.postMatchUntil = 0;

        const type = (overlayState.matchType || "").toLowerCase();
        if ((type.includes("online") || type.includes("private")) && !hasFreshTrainingSignal()) {
          clearTrainingMode();
        }
      } else {
        const type = (overlayState.matchType || "").toLowerCase();
        if (
          !overlayState.offlineArenaActive &&
          (type.includes("online") || type.includes("private") || type.includes("lobby"))
        ) {
          clearTrainingMode();
        }
      }
    }

    if (matchEnded && (overlayState.gameState || "").toLowerCase() === "finished") {
      finishTrackedMatch();
    }
  }

  if (key === "game_info" || key === "training") {
    if (value.training_pack !== undefined) {
      setTrainingMode(getTrainingLabel(value.training_pack));
    }

    if (
      value.training_round !== undefined ||
      value.training_round_result !== undefined ||
      value.training_shuffle_mode !== undefined
    ) {
      setTrainingMode(overlayState.trainingPack || "Training pack");
    }
  }

  Object.keys(value).forEach((childKey) => {
    const childValue = parseMaybeJson(value[childKey]);
    if (childValue && typeof childValue === "object") {
      applyInfoSection(childKey, childValue);
    }
  });
}

function applyInfoPayload(payload) {
  overlayState.connected = true;
  recordGepDiagnostic("info", payload);

  if (payload && payload.category && payload.key) {
    const section = {};
    section[payload.key] = payload.value !== undefined ? payload.value : payload.data;
    applyInfoSection(payload.category, section);
    renderOverlay();
    return;
  }

  applyInfoSection("root", payload && payload.info ? payload.info : payload);
  renderOverlay();
}

function applyEventPayload(eventPayload) {
  if (!eventPayload || !Array.isArray(eventPayload.events)) {
    return;
  }

  overlayState.connected = true;
  recordGepDiagnostic("events", eventPayload);

  eventPayload.events.forEach((eventItem) => {
    const name = eventItem.name || "";
    const data = parseMaybeJson(eventItem.data);

    if (name === "matchStart") {
      beginTrackedMatch();

      const type = (overlayState.matchType || "").toLowerCase();
      if ((type.includes("online") || type.includes("private")) && !hasFreshTrainingSignal()) {
        clearTrainingMode();
      }
    }

    if (name === "victory") {
      overlayState.pendingResult = "win";
      commitPendingResult();
    }

    if (name === "defeat") {
      overlayState.pendingResult = "loss";
      commitPendingResult();
    }

    if (name === "matchEnd") {
      finishTrackedMatch();
    }

    if (name.startsWith("training_") || name.toLowerCase().includes("training")) {
      setTrainingMode(getTrainingLabel(data));
    }

    if (data && typeof data === "object") {
      if (data.score !== undefined) {
        overlayState.score = parseMaybeNumber(data.score);
      }

      if (data.goals !== undefined) {
        overlayState.goals = parseMaybeNumber(data.goals);
      }

      if (data.saves !== undefined) {
        overlayState.saves = parseMaybeNumber(data.saves);
      }

      if (data.team_score !== undefined) {
        overlayState.teamScore = parseMaybeNumber(data.team_score);
      }
    }
  });

  renderOverlay();
}

function registerOverlayFeatures(attempt = 0) {
  window.overwolf.games.events.setRequiredFeatures(OVERLAY_FEATURES, (result) => {
    recordGepDiagnostic("setRequiredFeatures", result);

    if (!result || result.success !== true) {
      overlayState.connected = false;
      renderOverlay();

      if (attempt < FEATURE_RETRY_LIMIT) {
        window.setTimeout(() => registerOverlayFeatures(attempt + 1), FEATURE_RETRY_MS);
      }
      return;
    }

    overlayState.connected = true;

    window.overwolf.games.events.getInfo((info) => {
      applyInfoPayload(info);
    });

    window.setInterval(() => {
      window.overwolf.games.events.getInfo((info) => {
        applyInfoPayload(info);
      });
    }, INFO_POLL_MS);
  });
}

function initOverlayEvents() {
  if (!window.overwolf || !window.overwolf.games || !window.overwolf.games.events) {
    overlayState.matchType = "Lobby";
    overlayState.session.startMmr = overlayState.session.startMmr !== null ? overlayState.session.startMmr : 1214;
    overlayState.session.currentMmr = overlayState.session.currentMmr !== null ? overlayState.session.currentMmr : 1236;
    overlayState.session.wins = overlayState.session.wins || 3;
    overlayState.session.losses = overlayState.session.losses || 1;
    overlayState.session.streakType = overlayState.session.streakType === "neutral" ? "win" : overlayState.session.streakType;
    overlayState.session.streakCount = overlayState.session.streakCount || 2;
    overlayState.session.nextRank = overlayState.session.nextRank || {
      label: "Champion 2",
      missing: 60,
      estimated: true,
    };
    renderOverlay();
    return;
  }

  window.overwolf.games.events.onInfoUpdates2.addListener(applyInfoPayload);
  window.overwolf.games.events.onNewEvents.addListener(applyEventPayload);
  window.overwolf.games.events.onError.addListener((error) => {
    recordGepDiagnostic("error", error);
  });

  registerOverlayFeatures();
}

function initGameVisibility() {
  if (!window.overwolf || !window.overwolf.games) {
    return;
  }

  window.overwolf.games.getRunningGameInfo((result) => {
    if (result && result.success !== false && !isRocketLeagueRunning(result.gameInfo || result)) {
      overlayCard.className = "overlay-card is-hidden";
    }
  });
}

window.addEventListener("storage", (event) => {
  if (event.key === SESSION_STORAGE_KEY) {
    reloadRankedSessions();
    return;
  }

  if ([GARAGE_PRESETS_STORAGE_KEY, UI_STATE_STORAGE_KEY, TRACKER_PROFILE_STORAGE_KEY].includes(event.key)) {
    syncSessionFromTracker();
    renderOverlay();
  }
});

window.setInterval(() => {
  if (overlayState.phase === "training" || overlayState.phase === "post-match") {
    renderOverlay();
  }
}, 1000);

syncSessionFromTracker();
renderOverlay();
initGameVisibility();
initOverlayEvents();
