const bodyPage = document.body.dataset.page || "home";
const revealNodes = document.querySelectorAll(".reveal");
const splashOverlay = document.getElementById("splash-overlay");
const splashBrand = document.getElementById("splash-brand");
const modulesSection = document.getElementById("modules-section");
const modulesButton = document.getElementById("modules-button");
const homeConnectForm = document.getElementById("home-connect-form");
const homeDisplayName = document.getElementById("home-display-name");
const homePlatform = document.getElementById("home-platform");
const homeGamertag = document.getElementById("home-gamertag");
const homeConnectStatus = document.getElementById("home-connect-status");

const presetList = document.getElementById("preset-list");
const presetPreview = document.getElementById("preset-preview");
const garageAction = document.getElementById("garage-action");
const garageForm = document.getElementById("garage-form");
const presetNameInput = document.getElementById("preset-name-input");
const presetCarInput = document.getElementById("preset-car-input");
const presetThemeInput = document.getElementById("preset-theme-input");
const presetWheelsInput = document.getElementById("preset-wheels-input");
const presetBoostInput = document.getElementById("preset-boost-input");
const presetDecalInput = document.getElementById("preset-decal-input");
const presetNoteInput = document.getElementById("preset-note-input");

const routineList = document.getElementById("routine-list");
const sessionTimer = document.getElementById("session-timer");
const sessionState = document.getElementById("session-state");
const timerToggle = document.getElementById("timer-toggle");
const timerReset = document.getElementById("timer-reset");
const trainingLog = document.getElementById("training-log");
const flowScore = document.getElementById("flow-score");
const liveSource = document.getElementById("live-source");
const liveMode = document.getElementById("live-mode");
const liveRank = document.getElementById("live-rank");
const overwolfStatusNote = document.getElementById("overwolf-status-note");
const trainingStreak = document.getElementById("training-streak");
const trainingMinutes = document.getElementById("training-minutes");
const trainingFocus = document.getElementById("training-focus");

const profileForm = document.getElementById("profile-form");
const profilePlatform = document.getElementById("profile-platform");
const profileGamertag = document.getElementById("profile-gamertag");
const profileSubmit = document.getElementById("profile-submit");
const profileSource = document.getElementById("profile-source");
const profileStatus = document.getElementById("profile-status");
const trackerProfileLink = document.getElementById("tracker-profile-link");
const profileAvatar = document.getElementById("profile-avatar");
const profileName = document.getElementById("profile-name");
const profileTagline = document.getElementById("profile-tagline");
const profileStats = document.getElementById("profile-stats");
const rankList = document.getElementById("rank-list");
const activityFeed = document.getElementById("activity-feed");

const statusTitle = document.getElementById("status-title");
const statusCopy = document.getElementById("status-copy");
const statusFlow = document.getElementById("status-flow");
const statusRoutine = document.getElementById("status-routine");
const statusPreset = document.getElementById("status-preset");
const statusFlowBar = document.getElementById("status-flow-bar");
const statusRoutineBar = document.getElementById("status-routine-bar");
const statusPresetBar = document.getElementById("status-preset-bar");

const IS_STANDALONE = window.RL_HUB_STANDALONE === true;
const TRACKER_PROXY_URL = IS_STANDALONE ? window.location.origin : "http://127.0.0.1:8765";
const PROFILE_QUERY_STORAGE_KEY = "rlhub:lastProfileQuery";
const TRACKER_PROFILE_STORAGE_KEY = "rlhub:trackerProfile";
const USER_PROFILE_STORAGE_KEY = "rlhub:userProfile";
const UI_STATE_STORAGE_KEY = "rlhub:uiState";
const GARAGE_PRESETS_STORAGE_KEY = "rlhub:garagePresets";
const TRAINING_STATE_STORAGE_KEY = "rlhub:trainingState";
const OVERWOLF_FEATURES = [
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

const defaultPresets = [
  {
    id: "neo-tokyo",
    name: "Neo Tokyo Fennec",
    car: "Fennec",
    theme: "Cobalt / Orange",
    vibe: "Aggressive but clean ranked preset",
    wheels: "Alpha Rim",
    boost: "Standard Blue",
    decal: "Sharp edge finish",
    tags: ["Ranked", "Clean", "Main"],
    stats: [
      { label: "Style", value: 92 },
      { label: "Comfort", value: 96 },
      { label: "Speed feel", value: 89 },
    ],
  },
  {
    id: "octane-storm",
    name: "Octane Storm",
    car: "Octane",
    theme: "Sunset / Black",
    vibe: "Fast corner reads and aerial confidence",
    wheels: "Cristiano",
    boost: "Flamethrower",
    decal: "Minimal storm stripe",
    tags: ["Aerials", "Fast", "Tournament"],
    stats: [
      { label: "Style", value: 87 },
      { label: "Comfort", value: 84 },
      { label: "Speed feel", value: 94 },
    ],
  },
  {
    id: "ice-circuit",
    name: "Ice Circuit",
    car: "Dominus",
    theme: "Frost / White",
    vibe: "Long flicks, clean lines and smart positioning",
    wheels: "Zomba",
    boost: "Ion",
    decal: "Cold shine setup",
    tags: ["Control", "1v1", "Showcase"],
    stats: [
      { label: "Style", value: 90 },
      { label: "Comfort", value: 79 },
      { label: "Speed feel", value: 82 },
    ],
  },
];

let presets = readGaragePresets();

const drills = [
  {
    id: "aerial-ladder",
    name: "Fast aerial ladder",
    category: "Aerials",
    duration: 12,
    note: "Reaksjon, høyde og recovery",
    focus: "Launch speed",
  },
  {
    id: "wall-reads",
    name: "Wall reads",
    category: "Reads",
    duration: 18,
    note: "Timing fra sidevegg og backboard",
    focus: "Ball tracking",
  },
  {
    id: "consistency",
    name: "Shot consistency",
    category: "Shooting",
    duration: 20,
    note: "Lav boost, raske touch og rebound",
    focus: "Placement",
  },
  {
    id: "recoveries",
    name: "Recovery loops",
    category: "Recovery",
    duration: 10,
    note: "Landinger, wave dashes og turn speed",
    focus: "Control",
  },
];

const defaultProfile = {
  name: "RL Hub Player",
  tagline: "Smart grinding, clean presets og full oversikt.",
  avatarText: "RL",
  sourceLabel: "Kilde: RL Hub demo",
  stats: [
    { label: "Peak rank", value: "C3 div 3" },
    { label: "Main car", value: "Fennec" },
    { label: "Sessions", value: "18 this week" },
  ],
  ranks: [
    { playlist: "2v2", rank: "Champ 2", trend: "+32 MMR" },
    { playlist: "3v3", rank: "Champ 1", trend: "+11 MMR" },
    { playlist: "1v1", rank: "Diamond 3", trend: "Stable" },
  ],
  activity: [
    "Best session this week: 6 wins in 2v2",
    "Most used preset: Neo Tokyo Fennec",
    "Current focus: reads into fast counterattack",
  ],
};

function readUiState() {
  try {
    const stored = JSON.parse(localStorage.getItem(UI_STATE_STORAGE_KEY));
    if (!stored || typeof stored !== "object") {
      return null;
    }
    return stored;
  } catch (error) {
    return null;
  }
}

function saveUiState() {
  localStorage.setItem(
    UI_STATE_STORAGE_KEY,
    JSON.stringify({
      selectedPreset: state.selectedPreset,
      completedDrills: Array.from(state.completedDrills),
    })
  );
}

const savedUiState = readUiState();

const state = {
  selectedPreset:
    savedUiState && Number.isInteger(savedUiState.selectedPreset)
      ? normalizePresetIndex(savedUiState.selectedPreset)
      : 0,
  completedDrills: new Set(
    savedUiState && Array.isArray(savedUiState.completedDrills)
      ? savedUiState.completedDrills
      : IS_STANDALONE ? [] : ["aerial-ladder", "consistency"]
  ),
  training: readTrainingState(),
  profile: IS_STANDALONE ? readStoredTrackerProfile() || {
    name: "RL Hub Player",
    tagline: "Legg til gamertagen din for å hente rank og MMR.",
    avatarText: "RL",
    sourceLabel: "Ingen rank-profil hentet",
    stats: [], ranks: [], activity: [],
  } : defaultProfile,
  overwolf: {
    available: false,
    connected: false,
    running: false,
    sourceLabel: "Lokal modus",
    modeLabel: "Ikke i kamp",
    rankLabel: "Venter på Overwolf",
    sessionStart: null,
    lastEventAt: null,
    score: 0,
    goals: 0,
    teamScore: 0,
    matchType: "",
    gameMode: "",
    trainingPack: "",
    rankText: "",
    error: "",
  },
};

function getAvatarText(value) {
  const letters = (value || "RL").replace(/[^a-zæøå0-9]/gi, "").toUpperCase();
  return (letters.slice(0, 2) || "RL").padEnd(2, "L");
}

function saveProfileQuery(lookup) {
  localStorage.setItem(PROFILE_QUERY_STORAGE_KEY, JSON.stringify(lookup));
}

function saveTrackerProfile(profile) {
  localStorage.setItem(TRACKER_PROFILE_STORAGE_KEY, JSON.stringify(profile));
}

function readStoredTrackerProfile() {
  try {
    const profile = JSON.parse(localStorage.getItem(TRACKER_PROFILE_STORAGE_KEY));
    return profile && typeof profile.name === "string" &&
      Array.isArray(profile.stats) && Array.isArray(profile.ranks) && Array.isArray(profile.activity)
      ? profile : null;
  } catch (error) {
    return null;
  }
}

function saveUserProfile(profile) {
  localStorage.setItem(USER_PROFILE_STORAGE_KEY, JSON.stringify(profile));
}

function readUserProfile() {
  try {
    return JSON.parse(localStorage.getItem(USER_PROFILE_STORAGE_KEY));
  } catch (error) {
    return null;
  }
}

function readProfileQuery() {
  try {
    return JSON.parse(localStorage.getItem(PROFILE_QUERY_STORAGE_KEY));
  } catch (error) {
    return null;
  }
}

function initHomeConnect() {
  if (!homeConnectForm || !homeDisplayName || !homePlatform || !homeGamertag) {
    return;
  }

  const savedUser = readUserProfile();
  const savedLookup = readProfileQuery();

  if (savedUser && savedUser.displayName) {
    homeDisplayName.value = savedUser.displayName;
  }

  if (savedLookup && savedLookup.platform) {
    homePlatform.value = savedLookup.platform;
  }

  if (savedLookup && savedLookup.gamertag) {
    homeGamertag.value = savedLookup.gamertag;
  }

  homeConnectForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const action = event.submitter ? event.submitter.dataset.connectAction : "link";
    const displayName = homeDisplayName.value.trim() || "RL Hub Player";
    const platform = homePlatform.value;
    const gamertag = homeGamertag.value.trim();

    saveUserProfile({
      displayName,
      createdAt: new Date().toISOString(),
    });

    if (action === "link") {
      if (!gamertag) {
        homeConnectStatus.textContent = "Skriv inn gamertag for å koble spilleren din.";
        homeConnectStatus.classList.add("is-error");
        return;
      }

      saveProfileQuery({ platform, gamertag });
      window.location.href = "./profile.html";
      return;
    }

    homeConnectStatus.textContent = "Bruker opprettet lokalt.";
    homeConnectStatus.classList.remove("is-error");
    homeConnectStatus.classList.add("is-success");

    window.setTimeout(() => {
      window.location.href = "./dashboard.html";
    }, 450);
  });
}

function normalizePresetIndex(index) {
  if (!Number.isInteger(index) || index < 0 || index >= presets.length) {
    return 0;
  }

  return index;
}

function cloneDefaultPresets() {
  return defaultPresets.map((preset) => ({
    ...preset,
    tags: [...preset.tags],
    stats: preset.stats.map((stat) => ({ ...stat })),
  }));
}

function readGaragePresets() {
  try {
    const stored = JSON.parse(localStorage.getItem(GARAGE_PRESETS_STORAGE_KEY));
    if (Array.isArray(stored) && stored.length > 0) {
      return stored.map((preset, index) => normalizePreset(preset, index));
    }
  } catch (error) {
    return cloneDefaultPresets();
  }

  return cloneDefaultPresets();
}

function saveGaragePresets() {
  localStorage.setItem(GARAGE_PRESETS_STORAGE_KEY, JSON.stringify(presets));
}

function normalizePreset(preset, index) {
  const fallback = defaultPresets[index % defaultPresets.length];

  return {
    id: preset.id || `preset-${Date.now()}-${index}`,
    name: preset.name || fallback.name,
    car: preset.car || fallback.car,
    theme: preset.theme || fallback.theme,
    vibe: preset.vibe || fallback.vibe,
    wheels: preset.wheels || fallback.wheels,
    boost: preset.boost || fallback.boost,
    decal: preset.decal || fallback.decal,
    tags: Array.isArray(preset.tags) ? preset.tags : ["Custom"],
    stats: Array.isArray(preset.stats) ? preset.stats : fallback.stats,
    custom: preset.custom === true,
  };
}

function readTrainingState() {
  try {
    const stored = JSON.parse(localStorage.getItem(TRAINING_STATE_STORAGE_KEY));
    if (stored && typeof stored === "object") {
      return {
        elapsedSeconds: Number.isFinite(stored.elapsedSeconds) ? stored.elapsedSeconds : 0,
        runningSince: Number.isFinite(stored.runningSince) ? stored.runningSince : null,
        history: Array.isArray(stored.history) ? stored.history.slice(0, 10) : [],
      };
    }
  } catch (error) {
    return { elapsedSeconds: 0, runningSince: null, history: [] };
  }

  return { elapsedSeconds: 0, runningSince: null, history: [] };
}

function saveTrainingState() {
  localStorage.setItem(TRAINING_STATE_STORAGE_KEY, JSON.stringify(state.training));
}

function getTrainingElapsedSeconds() {
  const runningSeconds = state.training.runningSince
    ? Math.max(0, Math.floor((Date.now() - state.training.runningSince) / 1000))
    : 0;

  return state.training.elapsedSeconds + runningSeconds;
}

function formatDuration(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function todayKey() {
  return new Date().toISOString().slice(0, 10);
}

function recordTrainingHistory() {
  const minutes = Math.round(getTrainingElapsedSeconds() / 60);
  const completed = state.completedDrills.size;

  if (minutes < 1 && completed === 0) {
    return;
  }

  const entry = {
    date: todayKey(),
    minutes,
    completed,
    total: drills.length,
  };
  const rest = state.training.history.filter((item) => item.date !== entry.date);
  state.training.history = [entry, ...rest].slice(0, 10);
}

function calculateTrainingStreak() {
  const loggedDates = new Set(
    state.training.history
      .filter((entry) => entry.completed > 0 || entry.minutes > 0)
      .map((entry) => entry.date)
  );

  let streak = 0;
  const cursor = new Date();

  while (loggedDates.has(cursor.toISOString().slice(0, 10))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }

  return streak;
}

function parseMaybeNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
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

function formatRankLabel(entry) {
  if (!entry || typeof entry !== "object") {
    return "";
  }

  const tier = entry.tier || entry.rank || entry.tierName || "";
  const division = entry.division || entry.div || "";

  if (tier && division) {
    return `${tier} Div ${division}`;
  }

  return tier;
}

function touchOverwolfSession() {
  if (!state.overwolf.sessionStart) {
    state.overwolf.sessionStart = Date.now();
  }

  state.overwolf.lastEventAt = Date.now();
}

function refreshOverwolfLabels() {
  const ow = state.overwolf;

  if (!ow.available) {
    ow.sourceLabel = "Ikke i Overwolf";
  } else if (!ow.connected) {
    ow.sourceLabel = "Starter Overwolf...";
  } else if (ow.running) {
    ow.sourceLabel = "Overwolf live";
  } else {
    ow.sourceLabel = "Overwolf klar";
  }

  if (ow.trainingPack) {
    ow.modeLabel = `Training: ${ow.trainingPack}`;
  } else {
    const modeParts = [];
    if (ow.gameMode) {
      modeParts.push(ow.gameMode);
    }
    if (ow.matchType) {
      modeParts.push(ow.matchType);
    }
    ow.modeLabel = modeParts.length > 0 ? modeParts.join(" | ") : "Ikke i kamp";
  }

  ow.rankLabel = ow.rankText || "Ingen rank-data enda";
}

function applyOverwolfSection(key, value) {
  if (!value || typeof value !== "object") {
    return;
  }

  if (key === "me") {
    if (value.score !== undefined) {
      state.overwolf.score = parseMaybeNumber(value.score);
      state.overwolf.running = true;
      touchOverwolfSession();
    }

    if (value.goals !== undefined) {
      state.overwolf.goals = parseMaybeNumber(value.goals);
      state.overwolf.running = true;
    }

    if (value.team_score !== undefined) {
      state.overwolf.teamScore = parseMaybeNumber(value.team_score);
    }

    if (value.playlists_rank) {
      const parsedRanks = parseMaybeJson(value.playlists_rank);
      if (Array.isArray(parsedRanks) && parsedRanks.length > 0) {
        state.overwolf.rankText = formatRankLabel(parsedRanks[0]);
      }
    }
  }

  if (key === "matchInfo" || key === "match") {
    if (value.matchType) {
      state.overwolf.matchType = value.matchType;
    }

    if (value.gameMode) {
      state.overwolf.gameMode = value.gameMode;
    }

    if (value.started === "true" || value.matchState === "true") {
      state.overwolf.running = true;
      touchOverwolfSession();
    }

    if (value.ended === "true") {
      state.overwolf.running = false;
    }
  }

  if (key === "game_info" || key === "training") {
    if (value.training_pack) {
      state.overwolf.trainingPack = value.training_pack;
      state.overwolf.running = true;
      touchOverwolfSession();
    }

    if (value.gameMode && !state.overwolf.gameMode) {
      state.overwolf.gameMode = value.gameMode;
    }
  }

  Object.keys(value).forEach((childKey) => {
    const childValue = value[childKey];
    if (childValue && typeof childValue === "object") {
      applyOverwolfSection(childKey, childValue);
    }
  });
}

function applyOverwolfSingleUpdate(update) {
  if (!update || !update.category || !update.key) {
    return false;
  }

  const value = update.value !== undefined ? update.value : update.data;
  const section = {};
  section[update.key] = value;
  applyOverwolfSection(update.category, section);
  return true;
}

function applyOverwolfInfoPayload(payload) {
  if (!payload) {
    return;
  }

  if (applyOverwolfSingleUpdate(payload)) {
    refreshOverwolfLabels();
    renderAppState();
    return;
  }

  const infoPayload = payload.info ? payload.info : payload;
  applyOverwolfSection("root", infoPayload);
  refreshOverwolfLabels();
  renderAppState();
}

function applyOverwolfEvents(eventPayload) {
  if (!eventPayload || !Array.isArray(eventPayload.events)) {
    return;
  }

  eventPayload.events.forEach((eventItem) => {
    const name = eventItem.name || "";
    const data = parseMaybeJson(eventItem.data);

    if (name === "goal" || name === "score") {
      if (data && typeof data === "object") {
        if (data.score !== undefined) {
          state.overwolf.score = parseMaybeNumber(data.score);
        }
        if (data.goals !== undefined) {
          state.overwolf.goals = parseMaybeNumber(data.goals);
        }
      }
      state.overwolf.running = true;
      touchOverwolfSession();
    }

    if (name === "teamGoal" || name === "opposingTeamGoal") {
      state.overwolf.running = true;
      touchOverwolfSession();
    }
  });

  refreshOverwolfLabels();
  renderAppState();
}

function calculateSessionSnapshot() {
  const completed = state.completedDrills.size;
  const total = drills.length;
  const localMinutes = drills
    .filter((drill) => state.completedDrills.has(drill.id))
    .reduce((sum, drill) => sum + drill.duration, 0);
  const focusPreset = presets[state.selectedPreset];
  const nextDrill = drills.find((drill) => !state.completedDrills.has(drill.id));
  const timerMinutes = Math.round(getTrainingElapsedSeconds() / 60);
  const liveMinutes = state.overwolf.sessionStart
    ? Math.max(1, Math.round((Date.now() - state.overwolf.sessionStart) / 60000))
    : 0;
  const minutes = Math.max(localMinutes || 0, timerMinutes || 0, liveMinutes || 0);
  const liveScoreBonus = Math.min(18, Math.round(state.overwolf.score / 60));
  const liveGoalsBonus = Math.min(12, state.overwolf.goals * 4);
  const warmupBonus = Math.min(14, Math.round(minutes / 3));
  const livePresenceBonus = state.overwolf.connected ? 6 : 0;
  const liveMatchBonus = state.overwolf.running ? 8 : 0;
  const trainingPackBonus = state.overwolf.trainingPack ? 5 : 0;
  const flow = Math.min(
    98,
    34 +
      completed * 10 +
      warmupBonus +
      Math.round(focusPreset.stats[1].value / 8) +
      liveScoreBonus +
      liveGoalsBonus +
      livePresenceBonus +
      liveMatchBonus +
      trainingPackBonus
  );

  return {
    completed,
    total,
    minutes,
    focusPreset,
    nextFocus: nextDrill ? nextDrill.category : "Review",
    flow,
  };
}

function renderPresetList() {
  if (!presetList) {
    return;
  }

  presetList.innerHTML = "";

  presets.forEach((preset, index) => {
    const button = document.createElement("button");
    const isSelected = index === state.selectedPreset;
    button.className = `preset-option${isSelected ? " is-selected is-active" : ""}`;
    button.type = "button";
    button.dataset.index = String(index);
    button.innerHTML = `
      <span class="preset-option-top">
        <strong>${preset.name}</strong>
        <span class="preset-option-theme">${preset.theme}${isSelected ? " | Aktiv" : ""}</span>
      </span>
      <span class="preset-option-note">${preset.vibe}</span>
    `;
    presetList.appendChild(button);
  });
}

function renderPresetPreview() {
  if (!presetPreview) {
    return;
  }

  const preset = presets[state.selectedPreset];
  const statMarkup = preset.stats
    .map((stat) => `<div class="mini-stat"><span>${stat.label}</span><strong>${stat.value}</strong></div>`)
    .join("");
  const tagMarkup = preset.tags.map((tag) => `<span class="tag">${tag}</span>`).join("");

  presetPreview.innerHTML = `
    <p class="eyebrow">Selected build</p>
    <h4>${preset.name}</h4>
    <p class="detail-note">${preset.vibe}</p>
    <div class="preview-meta">
      <div><span>Car</span><strong>${preset.car}</strong></div>
      <div><span>Wheels</span><strong>${preset.wheels}</strong></div>
      <div><span>Boost</span><strong>${preset.boost}</strong></div>
      <div><span>Decal</span><strong>${preset.decal}</strong></div>
    </div>
    <div class="tag-row">${tagMarkup}</div>
    <div class="metric-grid">${statMarkup}</div>
    <div class="timer-actions">
      <button class="primary-button compact-button" id="set-active-preset" type="button">Bruk som aktiv</button>
      <button class="ghost-button compact-button" id="delete-preset" type="button">Slett preset</button>
    </div>
  `;
}

function buildPresetFromForm() {
  const name = presetNameInput.value.trim();
  const car = presetCarInput.value.trim();
  const theme = presetThemeInput.value.trim() || "Custom colors";
  const wheels = presetWheelsInput.value.trim() || "Not set";
  const boost = presetBoostInput.value.trim() || "Not set";
  const decal = presetDecalInput.value.trim() || "Not set";
  const vibe = presetNoteInput.value.trim() || "Custom build for ranked sessions";

  if (!name) {
    presetNameInput.focus();
    return null;
  }

  return {
    id: `custom-${Date.now()}`,
    name,
    car,
    theme,
    vibe,
    wheels,
    boost,
    decal,
    tags: ["Custom", car, "Active-ready"],
    stats: [
      { label: "Style", value: 88 },
      { label: "Comfort", value: 86 },
      { label: "Speed feel", value: 84 },
    ],
    custom: true,
  };
}

function clearGarageForm() {
  if (!garageForm) {
    return;
  }

  garageForm.reset();
}

function deleteSelectedPreset() {
  if (presets.length <= 1) {
    return;
  }

  presets.splice(state.selectedPreset, 1);
  state.selectedPreset = normalizePresetIndex(Math.max(0, state.selectedPreset - 1));
  saveGaragePresets();
  saveUiState();
  renderAppState();
}

function renderRoutineList() {
  if (!routineList) {
    return;
  }

  routineList.innerHTML = "";

  drills.forEach((drill) => {
    const done = state.completedDrills.has(drill.id);
    const item = document.createElement("button");
    item.className = `routine-item${done ? " is-done" : ""}`;
    item.type = "button";
    item.dataset.id = drill.id;
    item.innerHTML = `
      <span class="routine-copy">
        <strong>${drill.name}</strong>
        <span>${drill.note}</span>
      </span>
      <span class="routine-meta">
        <span>${drill.duration} min</span>
        <span class="check-toggle">${done ? "Done" : drill.focus}</span>
      </span>
    `;
    routineList.appendChild(item);
  });
}

function renderTrainingTimer() {
  if (!sessionTimer || !sessionState || !timerToggle) {
    return;
  }

  const elapsed = getTrainingElapsedSeconds();
  sessionTimer.textContent = formatDuration(elapsed);
  sessionState.textContent = state.training.runningSince ? "Timeren går" : elapsed > 0 ? "Pauset" : "Klar";
  timerToggle.textContent = state.training.runningSince ? "Pause" : "Start";
}

function renderTrainingLog() {
  if (!trainingLog) {
    return;
  }

  if (state.training.history.length === 0) {
    trainingLog.innerHTML = `
      <div class="log-item">
        <strong>Ingen økter logget enda</strong>
        <span>Start timeren eller fullfør drills</span>
      </div>
    `;
    return;
  }

  trainingLog.innerHTML = state.training.history
    .slice(0, 4)
    .map(
      (entry) => `
        <div class="log-item">
          <strong>${entry.date}</strong>
          <span>${entry.minutes} min | ${entry.completed} / ${entry.total} drills</span>
        </div>
      `
    )
    .join("");
}

function renderProfile() {
  if (!profileName || !profileStats || !rankList || !activityFeed) {
    return;
  }

  const currentProfile = state.profile;

  if (profileAvatar) {
    profileAvatar.textContent = currentProfile.avatarText || getAvatarText(currentProfile.name);
  }

  profileName.textContent = currentProfile.name;
  profileTagline.textContent = currentProfile.tagline;

  if (profileSource) {
    profileSource.textContent = currentProfile.sourceLabel || "Kilde: RL Hub";
  }

  profileStats.innerHTML = currentProfile.stats
    .map(
      (stat) => `
        <div class="profile-stat">
          <span>${stat.label}</span>
          <strong>${stat.value}</strong>
        </div>
      `
    )
    .join("");

  rankList.innerHTML = currentProfile.ranks
    .map(
      (rank) => `
        <div class="rank-tile">
          <span>${rank.playlist}</span>
          <strong>${rank.rank}</strong>
          <small>${rank.trend}</small>
        </div>
      `
    )
    .join("");

  activityFeed.innerHTML = currentProfile.activity
    .map(
      (item) => `
        <div class="activity-item">
          <span></span>
          <p>${item}</p>
        </div>
      `
    )
    .join("");
}

function updateDashboardSummary() {
  const snapshot = calculateSessionSnapshot();
  const hasOverwolfSignal = state.overwolf.available && state.overwolf.connected;

  if (flowScore) {
    flowScore.textContent = `${snapshot.flow}%`;
  }

  if (liveSource) {
    liveSource.textContent = hasOverwolfSignal ? state.overwolf.sourceLabel : "Garage + Training";
  }

  if (liveMode) {
    liveMode.textContent =
      hasOverwolfSignal && state.overwolf.running
        ? state.overwolf.modeLabel
        : `${snapshot.minutes} min warmup`;
  }

  if (liveRank) {
    liveRank.textContent =
      hasOverwolfSignal && state.overwolf.rankText ? state.overwolf.rankLabel : snapshot.focusPreset.name;
  }

  if (overwolfStatusNote) {
    if (!state.overwolf.available) {
      overwolfStatusNote.textContent =
        "Lokal readiness: basert på Training-progress, warmup-tid og aktiv Garage-preset. Ikke en offisiell Rocket League-stat.";
    } else if (state.overwolf.error) {
      overwolfStatusNote.textContent = state.overwolf.error;
    } else if (state.overwolf.connected && state.overwolf.running) {
      overwolfStatusNote.textContent =
        "Overwolf leverer live match- og treningsdata akkurat nå.";
    } else if (state.overwolf.connected) {
      overwolfStatusNote.textContent =
        "Overwolf er koblet, men Rocket League sender ingen aktiv live-feed akkurat nå.";
    } else {
      overwolfStatusNote.textContent =
        "Prøver å koble til Overwolf live data. Start Rocket League for å fylle denne boksen.";
    }
  }

  if (trainingStreak) {
    trainingStreak.textContent = `${calculateTrainingStreak()}d`;
  }

  if (trainingMinutes) {
    trainingMinutes.textContent = String(snapshot.minutes);
  }

  if (trainingFocus) {
    trainingFocus.textContent = snapshot.nextFocus;
  }
}

function renderSidebarStatus() {
  if (!statusTitle || !statusCopy || !statusFlow || !statusRoutine || !statusPreset) {
    return;
  }

  const snapshot = calculateSessionSnapshot();
  const statusContent = {
    home: {
      title: "Hub oversikt",
      copy: "Velg hvilken del av RL Hub du vil åpne i en egen side.",
    },
    dashboard: {
      title: "Lokal readiness",
      copy: "Basert på Training-progress, warmup-tid og aktiv Garage-preset. Dette er ikke en offisiell Rocket League-stat.",
    },
    garage: {
      title: "Aktivt biloppsett",
      copy: "Denne visningen holder fokus på presetet du bruker akkurat nå og hvor komfortabelt det føles.",
    },
    training: {
      title: "Treningsflyt",
      copy: "Her får du oversikt over hvor mye av dagens rutine som er gjort og hva som gjenstår.",
    },
    profile: {
      title: "Spillerbilde",
      copy: "Denne boksen gir deg en rask oppsummering mens du ser på rank, vaner og progresjon.",
    },
  };

  const currentStatus = statusContent[bodyPage] || statusContent.home;

  statusTitle.textContent = currentStatus.title;
  statusCopy.textContent = currentStatus.copy;
  statusFlow.textContent = `${snapshot.flow}%`;
  statusRoutine.textContent = `${snapshot.completed} / ${snapshot.total}`;
  statusPreset.textContent = snapshot.focusPreset.name;
  statusFlowBar.style.setProperty("--fill", `${snapshot.flow}%`);
  statusRoutineBar.style.setProperty(
    "--fill",
    `${Math.round((snapshot.completed / snapshot.total) * 100)}%`
  );
  statusPresetBar.style.setProperty("--fill", `${Math.min(100, snapshot.focusPreset.stats[1].value)}%`);
}

function renderAppState() {
  renderPresetList();
  renderPresetPreview();
  renderRoutineList();
  renderTrainingTimer();
  renderTrainingLog();
  renderProfile();
  updateDashboardSummary();
  renderSidebarStatus();
}

function setProfileStatus(message, tone = "neutral") {
  if (!profileStatus) {
    return;
  }

  profileStatus.textContent = message;
  profileStatus.classList.remove("is-loading", "is-success", "is-error");

  if (tone === "loading") {
    profileStatus.classList.add("is-loading");
  }

  if (tone === "success") {
    profileStatus.classList.add("is-success");
  }

  if (tone === "error") {
    profileStatus.classList.add("is-error");
  }
}

async function fetchTrackerProfile(lookup) {
  if (!profileSubmit) {
    return;
  }

  const platform = (lookup.platform || "epic").trim().toLowerCase();
  const gamertag = (lookup.gamertag || "").trim();
  const savedLookup = readProfileQuery();
  const playerId = IS_STANDALONE && savedLookup &&
    savedLookup.platform === platform &&
    (savedLookup.gamertag || "").trim().toLowerCase() === gamertag.toLowerCase()
    ? (savedLookup.playerId || "").trim() : "";

  if (!gamertag) {
    if (trackerProfileLink) trackerProfileLink.hidden = true;
    setProfileStatus("Skriv inn en gamertag for å hente spillerdata.", "error");
    return;
  }

  profileSubmit.disabled = true;
  saveProfileQuery({ platform, gamertag, playerId });
  updateTrackerProfileLink();
  setProfileStatus(IS_STANDALONE ? "Henter rank og MMR..." : "Henter data fra Tracker Network...", "loading");

  try {
    const params = new URLSearchParams({ platform, gamertag, playerId });
    const response = await fetch(`${TRACKER_PROXY_URL}/api/profile?${params.toString()}`);
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.error || "Klarte ikke hente Tracker-data akkurat nå.");
    }

    state.profile = payload.profile;
    renderProfile();
    saveProfileQuery({ platform, gamertag, playerId: payload.profile.playerId || playerId });
    saveTrackerProfile(payload.profile);
    setProfileStatus(`Viser ${IS_STANDALONE ? "rank og MMR" : "Tracker-data"} for ${payload.profile.name}.`, "success");
  } catch (error) {
    const message =
      error instanceof TypeError
        ? IS_STANDALONE
          ? "Oppslagstjenesten svarer ikke. Lukk og åpne RL Hub igjen."
          : "Lokal Tracker-proxy svarer ikke. Start tracker_proxy.py og prøv igjen."
        : error.message;
    setProfileStatus(state.profile.ranks.length > 0
      ? `${message} Viser sist lagrede statistikk; den er ikke oppdatert.`
      : message, "error");
  } finally {
    profileSubmit.disabled = false;
  }
}

function updateTrackerProfileLink() {
  if (!trackerProfileLink || !profilePlatform || !profileGamertag) return;
  if (IS_STANDALONE) {
    trackerProfileLink.hidden = true;
    return;
  }
  const gamertag = profileGamertag.value.trim();
  trackerProfileLink.hidden = !gamertag;
  if (gamertag) {
    trackerProfileLink.href = `https://rocketleague.tracker.network/rocket-league/profile/${encodeURIComponent(profilePlatform.value)}/${encodeURIComponent(gamertag)}/overview`;
  } else {
    trackerProfileLink.removeAttribute("href");
  }
}

async function initTrackerProfile() {
  if (!profileForm || !profilePlatform || !profileGamertag) {
    return;
  }

  profilePlatform.addEventListener("change", updateTrackerProfileLink);
  profileGamertag.addEventListener("input", updateTrackerProfileLink);
  if (IS_STANDALONE) {
    profileSubmit.textContent = "Hent rank";
  }

  const savedLookup = readProfileQuery();

  if (savedLookup && savedLookup.platform) {
    profilePlatform.value = savedLookup.platform;
  }

  if (savedLookup && savedLookup.gamertag) {
    profileGamertag.value = savedLookup.gamertag;
    await fetchTrackerProfile(savedLookup);
    return;
  }

  try {
    const response = await fetch(`${TRACKER_PROXY_URL}/health`);
    if (!response.ok) {
      throw new Error("Proxy health check feilet.");
    }
    setProfileStatus(IS_STANDALONE
      ? "Velg plattform, skriv gamertagen din og trykk Hent rank."
      : "Oppslagstjenesten er klar. Automatisk import kan bli avvist av Tracker; du kan også åpne profilen i nettleseren.", "success");
  } catch (error) {
    setProfileStatus(IS_STANDALONE
      ? "Oppslagstjenesten svarer ikke. Lukk og åpne RL Hub igjen."
      : "Lokal Tracker-proxy er ikke aktiv enda. Start tracker_proxy.py for live data.", "error");
  }
}

function syncStateFromStorage() {
  const latestUiState = readUiState();
  if (!latestUiState) {
    return;
  }

  if (Number.isInteger(latestUiState.selectedPreset)) {
    state.selectedPreset = latestUiState.selectedPreset;
  }

  if (Array.isArray(latestUiState.completedDrills)) {
    state.completedDrills = new Set(latestUiState.completedDrills);
  }

  renderAppState();
}

function syncGarageFromStorage() {
  presets = readGaragePresets();
  state.selectedPreset = normalizePresetIndex(state.selectedPreset);
  renderAppState();
}

function syncTrainingFromStorage() {
  state.training = readTrainingState();
  renderAppState();
}

function initStorageSync() {
  window.addEventListener("storage", (event) => {
    if (event.key === UI_STATE_STORAGE_KEY) {
      syncStateFromStorage();
    }

    if (event.key === GARAGE_PRESETS_STORAGE_KEY) {
      syncGarageFromStorage();
    }

    if (event.key === TRAINING_STATE_STORAGE_KEY) {
      syncTrainingFromStorage();
    }

    if (event.key === PROFILE_QUERY_STORAGE_KEY && profileGamertag && profilePlatform) {
      const latestLookup = readProfileQuery();
      if (latestLookup && latestLookup.platform) {
        profilePlatform.value = latestLookup.platform;
      }
      if (latestLookup && latestLookup.gamertag) {
        profileGamertag.value = latestLookup.gamertag;
      }
    }
  });
}

function getOverwolfWindowNameFromHref(href) {
  const fileName = href.split("/").pop().split("#")[0].split("?")[0];
  const windowName = fileName.replace(".html", "");
  return ["dashboard", "garage", "training", "profile"].includes(windowName) ? windowName : "";
}

function minimizeOtherOverwolfWindows() {
  if (!window.overwolf || !window.overwolf.windows) {
    return;
  }

  window.overwolf.windows.getCurrentWindow((currentResult) => {
    const currentWindow = currentResult && currentResult.window;
    if (!currentWindow) {
      return;
    }

    ["dashboard", "garage", "training", "profile"].forEach((windowName) => {
      window.overwolf.windows.getWindow(windowName, (result) => {
        if (
          result &&
          result.status === "success" &&
          result.window &&
          result.window.id !== currentWindow.id
        ) {
          window.overwolf.windows.minimize(result.window.id, () => {});
        }
      });
    });
  });
}

function initOverwolfNavigation() {
  if (!window.overwolf || !window.overwolf.windows) {
    return;
  }

  minimizeOtherOverwolfWindows();

  document.querySelectorAll("a[href$='.html']").forEach((link) => {
    const windowName = getOverwolfWindowNameFromHref(link.getAttribute("href") || "");
    if (!windowName) {
      return;
    }

    link.addEventListener("click", (event) => {
      event.preventDefault();
      minimizeOtherOverwolfWindows();
      window.location.href = link.getAttribute("href");
    });
  });
}

function initOverwolfLiveData() {
  if (!window.overwolf || !window.overwolf.games || !window.overwolf.games.events) {
    state.overwolf.available = false;
    refreshOverwolfLabels();
    renderAppState();
    return;
  }

  state.overwolf.available = true;
  refreshOverwolfLabels();

  window.overwolf.games.events.onError.addListener((event) => {
    state.overwolf.error = event && event.reason ? `Overwolf-feil: ${event.reason}` : "Overwolf rapporterte en feil.";
    renderAppState();
  });

  window.overwolf.games.events.onInfoUpdates2.addListener((event) => {
    state.overwolf.connected = true;
    state.overwolf.error = "";
    applyOverwolfInfoPayload(event);
  });

  window.overwolf.games.events.onNewEvents.addListener((event) => {
    state.overwolf.connected = true;
    state.overwolf.error = "";
    applyOverwolfEvents(event);
  });

  window.overwolf.games.events.setRequiredFeatures(OVERWOLF_FEATURES, (result) => {
    if (!result || result.success !== true) {
      state.overwolf.connected = false;
      state.overwolf.error = "Klarte ikke å registrere Overwolf-features for Rocket League.";
      renderAppState();
      return;
    }

    state.overwolf.connected = true;
    state.overwolf.error = "";
    refreshOverwolfLabels();
    renderAppState();

    window.overwolf.games.events.getInfo((info) => {
      applyOverwolfInfoPayload(info);
    });
  });
}

function finishSplash() {
  if (!splashOverlay) {
    return;
  }

  const video = splashOverlay.querySelector("video");
  if (video) video.pause();
  if (splashOverlay.contains(document.activeElement)) document.activeElement.blur();
  splashOverlay.inert = true;
  splashOverlay.classList.add("is-exiting");
  document.body.classList.remove("splash-active");
  document.body.classList.add("app-ready");
}

function startSplashZoom() {
  if (splashOverlay) {
    splashOverlay.classList.add("is-zooming");
  }
}

function initSplash() {
  if (splashOverlay && window.RL_HUB_STANDALONE) {
    let alreadyShown = false;
    const sessionId = window.RL_HUB_SESSION || "standalone";
    try {
      alreadyShown = sessionStorage.getItem("rlhub-intro-shown") === sessionId;
      sessionStorage.setItem("rlhub-intro-shown", sessionId);
    } catch (_) { /* Playback still works when browser storage is unavailable. */ }
    if (alreadyShown) {
      splashOverlay.hidden = true;
      finishSplash();
      return;
    }
    splashOverlay.classList.add("is-video");
    splashOverlay.replaceChildren();
    const video = document.createElement("video");
    video.className = "splash-video";
    video.muted = true;
    video.playsInline = true;
    video.preload = "auto";
    video.poster = "./App Logo.png";
    video.setAttribute("aria-label", "Octane kjører inn og blir til RL Hub-logoen");
    video.src = "./assets/rlhub-intro.mp4";
    const skip = document.createElement("button");
    skip.className = "splash-skip";
    skip.type = "button";
    skip.textContent = "Hopp over intro";
    splashOverlay.append(video, skip);
    const deadline = window.setTimeout(finishSplash, 6750);
    const done = () => { window.clearTimeout(deadline); finishSplash(); };
    skip.addEventListener("click", done);
    video.addEventListener("ended", done, { once: true });
    video.addEventListener("error", done, { once: true });
    video.play().catch(done);
    return;
  }
  if (!splashOverlay || !splashBrand) {
    return;
  }

  window.setTimeout(() => {
    splashBrand.classList.add("is-visible");
  }, 120);

  window.setTimeout(() => {
    startSplashZoom();
  }, 2100);

  window.setTimeout(() => {
    finishSplash();
  }, 3400);
}

function wireUi() {
  if (modulesButton && modulesSection) {
    modulesButton.addEventListener("click", () => {
      modulesSection.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  if (garageAction) {
    garageAction.addEventListener("click", () => {
      state.selectedPreset = (state.selectedPreset + 1) % presets.length;
      saveUiState();
      renderAppState();
    });
  }

  if (presetList) {
    presetList.addEventListener("click", (event) => {
      const target = event.target.closest(".preset-option");
      if (!target) {
        return;
      }

      state.selectedPreset = Number(target.dataset.index);
      saveUiState();
      renderAppState();
    });
  }

  if (presetPreview) {
    presetPreview.addEventListener("click", (event) => {
      const target = event.target.closest("button");
      if (!target) {
        return;
      }

      if (target.id === "set-active-preset") {
        saveUiState();
        renderAppState();
      }

      if (target.id === "delete-preset") {
        deleteSelectedPreset();
      }
    });
  }

  if (garageForm) {
    garageForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const preset = buildPresetFromForm();
      if (!preset) {
        return;
      }

      presets.push(preset);
      state.selectedPreset = presets.length - 1;
      saveGaragePresets();
      saveUiState();
      clearGarageForm();
      renderAppState();
    });
  }

  if (routineList) {
    routineList.addEventListener("click", (event) => {
      const target = event.target.closest(".routine-item");
      if (!target) {
        return;
      }

      const id = target.dataset.id;
      if (state.completedDrills.has(id)) {
        state.completedDrills.delete(id);
      } else {
        state.completedDrills.add(id);
      }

      recordTrainingHistory();
      saveUiState();
      saveTrainingState();
      renderAppState();
    });
  }

  if (timerToggle) {
    timerToggle.addEventListener("click", () => {
      if (state.training.runningSince) {
        state.training.elapsedSeconds = getTrainingElapsedSeconds();
        state.training.runningSince = null;
        recordTrainingHistory();
      } else {
        state.training.runningSince = Date.now();
      }

      saveTrainingState();
      renderAppState();
    });
  }

  if (timerReset) {
    timerReset.addEventListener("click", () => {
      state.training.elapsedSeconds = 0;
      state.training.runningSince = null;
      saveTrainingState();
      renderAppState();
    });
  }

  if (profileForm) {
    profileForm.addEventListener("submit", (event) => {
      event.preventDefault();
      fetchTrackerProfile({
        platform: profilePlatform.value,
        gamertag: profileGamertag.value,
      });
    });
  }

  if (revealNodes.length > 0) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.2 }
    );

    revealNodes.forEach((node) => observer.observe(node));
  }

  if (sessionTimer) {
    window.setInterval(() => {
      renderTrainingTimer();
      updateDashboardSummary();
      renderSidebarStatus();
    }, 1000);
  }
}

function init() {
  renderAppState();
  wireUi();
  initStorageSync();
  if (!IS_STANDALONE) initOverwolfNavigation();
  initHomeConnect();
  initTrackerProfile();
  if (!IS_STANDALONE) initOverwolfLiveData();
  initSplash();
}

init();
