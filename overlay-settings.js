const overlayForm = document.getElementById("overlay-form");
const overlayFields = {
  enabled: document.getElementById("overlay-enabled"),
  showInMatch: document.getElementById("overlay-in-match"),
  position: document.getElementById("overlay-position"),
  scale: document.getElementById("overlay-scale"),
  playlist: document.getElementById("overlay-playlist"),
  renderer: document.getElementById("overlay-renderer"),
};
const overlayFeedback = document.getElementById("overlay-feedback");
let overlayFieldsLoaded = false;
let overlayDirty = false;
let overlayRequestPending = false;

function renderOverlaySettings(data, force = false) {
  if (force || !overlayFieldsLoaded || (!overlayDirty && document.activeElement === document.body)) {
    for (const [key, field] of Object.entries(overlayFields)) {
      if (field.type === "checkbox") field.checked = data.settings[key];
      else field.value = data.settings[key];
    }
    document.getElementById("overlay-scale-label").textContent = `${data.settings.scale}%`;
    overlayFieldsLoaded = true;
  }
  document.getElementById("overlay-status").textContent = data.settings.renderer === "gamebar" ? (data.settings.enabled ? data.gamebarConnected ? "Game Bar tilkoblet" : "Åpne RL Hub i Win + G" : "Avslått") : data.nativeError || (data.nativeReady ? data.settings.enabled ? data.visible ? "Overlay vises" : "Klart for spillet" : "Avslått" : "Starter…");
  document.getElementById("overlay-source-status").textContent = data.connected ? "Kampdata tilkoblet" : "Venter på kampdata";
  document.getElementById("overlay-hotkey").textContent = data.hotkey ? "Ctrl + Shift + O skjuler eller viser overlayet." : "Hurtigtasten er opptatt. Bruk bryteren i denne fanen.";
  document.getElementById("overlay-session").textContent = `${data.name} · ${data.playlist} · ${data.mmr ?? "—"} MMR · ${data.wins}W / ${data.losses}L denne økten`;
}

async function overlayAction(action, payload = {}) {
  if (overlayRequestPending) return;
  overlayRequestPending = true;
  try {
    const response = await fetch(`./api/overlay/${action}`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Kunne ikke oppdatere overlayet.");
    overlayDirty = false;
    renderOverlaySettings(data, true);
    overlayFeedback.textContent = action === "preview" ? data.settings.renderer === "gamebar" ? "Forhåndsvisningen vises i RL Hub-widgeten i 20 sekunder. Åpne den med Win + G." : "Forhåndsvisningen vises i 20 sekunder, også utenfor spillet." : action === "reset" ? "En ny økt er startet." : "Overlay-innstillingene er lagret.";
  } catch (error) {
    overlayFeedback.textContent = error.message;
  } finally {
    overlayRequestPending = false;
  }
}

function readOverlaySettings() {
  return {enabled: overlayFields.enabled.checked, showInMatch: overlayFields.showInMatch.checked, position: overlayFields.position.value, scale: Number(overlayFields.scale.value), playlist: overlayFields.playlist.value, renderer: overlayFields.renderer.value};
}
overlayForm.addEventListener("input", () => {
  overlayDirty = true;
  document.getElementById("overlay-scale-label").textContent = `${overlayFields.scale.value}%`;
});
overlayForm.addEventListener("submit", (event) => { event.preventDefault(); overlayAction("settings", readOverlaySettings()); });
document.getElementById("overlay-preview").addEventListener("click", async () => {
  if (overlayDirty) await overlayAction("settings", readOverlaySettings());
  if (!overlayDirty) await overlayAction("preview");
});
document.getElementById("overlay-reset").addEventListener("click", () => overlayAction("reset"));
async function pollOverlaySettings() {
  try {
    const response = await fetch("./api/overlay");
    if (!response.ok) throw new Error("Overlayet svarer ikke.");
    renderOverlaySettings(await response.json());
  } catch (error) {
    document.getElementById("overlay-status").textContent = error.message;
  } finally {
    window.setTimeout(pollOverlaySettings, 1500);
  }
}
pollOverlaySettings();
