# RL Hub Overwolf Setup

RL Hub now has the basic Overwolf Native wrapper in place.

## Files

- `manifest.json` declares the Overwolf app, permissions and windows.
- `overwolf/background.html` is the hidden startup window.
- `overwolf/background.js` opens the dashboard on desktop and the overlay when Rocket League is running.
- `overwolf/overlay.html` is the in-game HUD shell.
- `overwolf/overlay.js` listens to Rocket League game events and switches between lobby, training/freeplay, post-match and hidden states.
- `dashboard.html` listens to `overwolf.games.events` for Rocket League live data.

## Test Locally

1. Open Overwolf.
2. Open the Overwolf developer tools or development app loader.
3. Load this folder as an unpacked Overwolf app:
   Velg mappen der du har klonet dette repoet.
4. If RL Hub was already loaded, disable/reload the unpacked app so Overwolf rereads `manifest.json`.
5. Start Rocket League.
6. The small RL Hub overlay should appear in-game automatically.
7. Open RL Hub from Overwolf if you also want the desktop dashboard.

When the app runs inside Overwolf, the dashboard and overlay should switch from local fallback mode to Overwolf live mode.

## Overlay Notes

- Rocket League game id: `10798`.
- `manifest.json` uses `game_targeting`, `game_events` and `launch_events` so Overwolf can inject the in-game overlay and auto-launch RL Hub.
- The overlay is click-through/passive, so it should not steal mouse or keyboard focus while playing.
- During an active match, RL Hub stays hidden so it does not cover native Rocket League UI.
- In lobby, it shows 2v2 session MMR from the last saved Tracker profile when available.
- In freeplay/training, it shows a timer for the current training session.
- After a match ends, it shows a short post-match summary.
- If it does not appear, reload the unpacked app in Overwolf and restart Rocket League after reloading.
