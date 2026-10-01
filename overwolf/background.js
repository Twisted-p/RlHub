const DEFAULT_WINDOW = "dashboard";
const WINDOW_NAMES = new Set(["dashboard", "garage", "training", "profile"]);
const OVERLAY_WINDOW = "overlay";
const ROCKET_LEAGUE_GAME_ID = 10798;
const OVERLAY_RETRY_ATTEMPTS = 6;
const OVERLAY_RETRY_DELAY_MS = 2000;
const OVERLAY_INITIAL_DELAY_MS = 8000;
const OVERLAY_POSITION = { left: 48, top: 48 };
const SESSION_STORAGE_KEY = "rlhub:overlaySession";

let activeRocketLeagueSession = null;
let overlayRestoreTimer = null;
let overlayRestoredForSession = false;

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

function syncRankedSessionLifecycle(gameInfo) {
  if (!isRocketLeagueRunning(gameInfo)) {
    activeRocketLeagueSession = null;
    return false;
  }

  const sessionId = String(gameInfo.id || gameInfo.classId || ROCKET_LEAGUE_GAME_ID);
  if (activeRocketLeagueSession === sessionId) {
    return false;
  }

  activeRocketLeagueSession = sessionId;
  localStorage.removeItem(SESSION_STORAGE_KEY);
  return true;
}

function restoreWindow(windowName = DEFAULT_WINDOW) {
  if (!window.overwolf || !window.overwolf.windows) {
    return;
  }

  const target = WINDOW_NAMES.has(windowName) ? windowName : DEFAULT_WINDOW;

  window.overwolf.windows.obtainDeclaredWindow(target, (result) => {
    if (!result || result.status !== "success" || !result.window) {
      console.warn("RL Hub could not obtain window", target, result);
      return;
    }

    window.overwolf.windows.restore(result.window.id, () => {});
  });
}

function minimizeWindow(windowName) {
  if (!windowName || !window.overwolf || !window.overwolf.windows) {
    return;
  }

  window.overwolf.windows.getWindow(windowName, (result) => {
    if (!result || result.status !== "success" || !result.window) {
      return;
    }

    window.overwolf.windows.minimize(result.window.id, () => {});
  });
}

function minimizeDesktopWindows() {
  WINDOW_NAMES.forEach((windowName) => minimizeWindow(windowName));
}

function restoreOverlay(callback) {
  if (!window.overwolf || !window.overwolf.windows) {
    callback(false);
    return;
  }

  window.overwolf.windows.obtainDeclaredWindow(OVERLAY_WINDOW, (result) => {
    if (!result || result.status !== "success" || !result.window) {
      console.warn("RL Hub could not obtain overlay window", result);
      callback(false);
      return;
    }

    window.overwolf.windows.restore(result.window.id, (restoreResult) => {
      positionOverlay(result.window.id);
      callback(
        !restoreResult ||
        restoreResult.status === "success" ||
        restoreResult.success === true
      );
    });
  });
}

function positionOverlay(windowId) {
  if (!windowId || !window.overwolf || !window.overwolf.windows) {
    return;
  }

  if (typeof window.overwolf.windows.changePosition === "function") {
    window.overwolf.windows.changePosition(
      windowId,
      OVERLAY_POSITION.left,
      OVERLAY_POSITION.top,
      () => {}
    );
  }
}

function scheduleOverlayRestore(attempt = 0) {
  if (overlayRestoredForSession || overlayRestoreTimer !== null) {
    return;
  }

  const delay = attempt === 0 ? OVERLAY_INITIAL_DELAY_MS : OVERLAY_RETRY_DELAY_MS;
  overlayRestoreTimer = window.setTimeout(() => {
    overlayRestoreTimer = null;
    restoreOverlay((success) => {
      if (success) {
        overlayRestoredForSession = true;
        return;
      }

      if (attempt < OVERLAY_RETRY_ATTEMPTS) {
        scheduleOverlayRestore(attempt + 1);
      }
    });
  }, delay);
}

function resetOverlayRestoreState() {
  if (overlayRestoreTimer !== null) {
    window.clearTimeout(overlayRestoreTimer);
    overlayRestoreTimer = null;
  }

  overlayRestoredForSession = false;
}

function minimizeOverlay() {
  if (!window.overwolf || !window.overwolf.windows) {
    return;
  }

  window.overwolf.windows.getWindow(OVERLAY_WINDOW, (result) => {
    if (!result || result.status !== "success" || !result.window) {
      return;
    }

    window.overwolf.windows.minimize(result.window.id, () => {});
  });
}

function syncOverlayWithGame(gameInfo) {
  if (isRocketLeagueRunning(gameInfo)) {
    const isNewSession = syncRankedSessionLifecycle(gameInfo);
    if (isNewSession) {
      minimizeDesktopWindows();
    }

    scheduleOverlayRestore();
    return true;
  }

  syncRankedSessionLifecycle(null);
  resetOverlayRestoreState();
  minimizeOverlay();
  return false;
}

function checkRunningGame(restoreDesktopWhenIdle = false, desktopWindow = DEFAULT_WINDOW) {
  if (!window.overwolf || !window.overwolf.games) {
    if (restoreDesktopWhenIdle) {
      restoreWindow(desktopWindow);
    }
    return;
  }

  window.overwolf.games.getRunningGameInfo((result) => {
    const gameInfo = result && result.success !== false ? result.gameInfo || result : null;
    const isRunning = isRocketLeagueRunning(gameInfo);
    if (isRunning) {
      const isNewSession = syncRankedSessionLifecycle(gameInfo);
      if (isNewSession) {
        minimizeDesktopWindows();
      }

      scheduleOverlayRestore();
    } else {
      syncRankedSessionLifecycle(null);
      resetOverlayRestoreState();
      minimizeOverlay();
    }

    if (!isRunning && restoreDesktopWhenIdle) {
      restoreWindow(desktopWindow);
    }
  });
}

function routeLaunch(parameter = DEFAULT_WINDOW, allowDesktopFallback = true) {
  const desktopWindow = WINDOW_NAMES.has(parameter) ? parameter : DEFAULT_WINDOW;
  checkRunningGame(allowDesktopFallback, desktopWindow);
}

function wireLaunchTriggers() {
  if (!window.overwolf) {
    return;
  }

  routeLaunch(DEFAULT_WINDOW, false);

  if (window.overwolf.extensions && window.overwolf.extensions.onAppLaunchTriggered) {
    window.overwolf.extensions.onAppLaunchTriggered.addListener((event) => {
      const parameter = event && event.parameter ? event.parameter : DEFAULT_WINDOW;
      routeLaunch(parameter, false);

      window.setTimeout(() => {
        routeLaunch(parameter, false);
      }, 2000);

      window.setTimeout(() => {
        routeLaunch(parameter, true);
      }, 6000);
    });
  }

  if (window.overwolf.games && window.overwolf.games.onGameInfoUpdated) {
    window.overwolf.games.onGameInfoUpdated.addListener((event) => {
      syncOverlayWithGame(event && event.gameInfo);
    });
  }

  if (window.overwolf.games && window.overwolf.games.onGameLaunched) {
    window.overwolf.games.onGameLaunched.addListener((event) => {
      syncOverlayWithGame(event && event.gameInfo ? event.gameInfo : event);
    });
  }
}

window.addEventListener("load", wireLaunchTriggers);
