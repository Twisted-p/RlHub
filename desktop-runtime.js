// Loaded by the desktop host before the shared application script.
window.RL_HUB_STANDALONE = true;
document.body.classList.add("desktop-app");

function applyMotionPause() {
  window.RL_HUB_MOTION_PAUSED = Boolean(window.RL_HUB_GAME_BUSY || document.hidden);
  document.body.classList.toggle("app-motion-paused", window.RL_HUB_MOTION_PAUSED);
  window.dispatchEvent(new CustomEvent("rlhub:motion", {detail: window.RL_HUB_MOTION_PAUSED}));
}
window.RL_HUB_SET_GAME_ACTIVITY = function (busy) {
  window.RL_HUB_GAME_BUSY = Boolean(busy);
  applyMotionPause();
};
document.addEventListener("visibilitychange", applyMotionPause);
applyMotionPause();
const connectButton = document.querySelector('[data-connect-action="link"]');
if (connectButton) connectButton.textContent = "Koble spiller";
document.querySelectorAll("a[href]").forEach((link) => {
  const url = new URL(link.getAttribute("href"), window.location.href);
  if (url.origin === window.location.origin) {
    link.removeAttribute("target");
  }
});

const desktopNav = document.querySelector(".nav");
if (desktopNav) {
  if (!desktopNav.querySelector('a[href="./training-packs.html"]')) {
    const link = document.createElement("a");
    link.className = "nav-link" + (document.body.dataset.page === "training-packs" ? " active" : "");
    link.href = "./training-packs.html";
    link.textContent = "Training Packs";
    const training = desktopNav.querySelector('a[href="./training.html"]');
    desktopNav.insertBefore(link, training ? training.nextSibling : null);
  }
  if (!desktopNav.querySelector('a[href="./settings.html"]')) {
    const settingsLink = document.createElement("a");
    settingsLink.className = "nav-link";
    settingsLink.href = "./settings.html";
    settingsLink.textContent = "Settings";
    const garageLink = desktopNav.querySelector('a[href="./garage.html"]');
    desktopNav.insertBefore(settingsLink, garageLink ? garageLink.nextSibling : desktopNav.firstChild);
  }
  if (!desktopNav.querySelector('a[href="./goals.html"]')) {
    const goalsLink = document.createElement("a");
    goalsLink.className = "nav-link";
    goalsLink.href = "./goals.html";
    goalsLink.textContent = "Goals";
    desktopNav.insertBefore(goalsLink, desktopNav.querySelector('a[href="./profile.html"]'));
  }
  const overlayLink = document.createElement("a");
  overlayLink.className = "nav-link" + (document.body.dataset.page === "overlay" ? " active" : "");
  overlayLink.href = "./overlay.html";
  overlayLink.textContent = "Overlay";
  desktopNav.append(overlayLink);
}

let sentOverlayProfile = "";
async function syncOverlayProfile() {
  try {
    const profile = JSON.parse(localStorage.getItem("rlhub:trackerProfile"));
    const lookup = JSON.parse(localStorage.getItem("rlhub:lastProfileQuery"));
    if (!profile || !profile.playerId || !Array.isArray(profile.ranks)) return;
    const payload = JSON.stringify({profile, lookup});
    if (payload === sentOverlayProfile) return;
    const response = await fetch("./api/overlay/profile", {method: "POST", headers: {"Content-Type": "application/json"}, body: payload});
    if (response.ok) sentOverlayProfile = payload;
  } catch (_) { /* The main app continues to work if the overlay is unavailable. */ }
}
window.addEventListener("storage", syncOverlayProfile);
window.addEventListener("DOMContentLoaded", syncOverlayProfile);
window.setInterval(syncOverlayProfile, 4000);
