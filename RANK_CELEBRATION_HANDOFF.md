# Rank celebration

Original RL Hub component with local JavaScript and CSS, created at the user's
request. No React Bits Pro code, license key or extra dependencies are required.

`rank_promotion_service.py` runs on accepted profile updates in
`OverlayService.set_profile`. It records first observed family promotions per
account and playlist in local `rank-promotions.json`. Existing rank history and
the first valid ranked lookup establish a baseline. Subtiers, divisions,
downgrades, stale timestamps, unranked/unknown labels, account switches and
regaining an already observed family do not produce a new milestone.

Events contain player name, full rank label, family, previous highest family,
rank icon, accent color, observed timestamp, MMR and recorded ranked wins/losses
in the preceding 24 hours. These are collected observations, not lifetime
statistics. The date is when the source reported the new rank, displayed in
Europe/Oslo, not a reconstructed achievement time.

`rank-celebration.js` and `.css` show a modal card across desktop app pages.
The card uses the proportions of a bank card, a gold chip, a contactless symbol,
embossed text and a glowing rank emblem. The card-number position contains
the rank in text and numbers (for example `CHAMPION 1 · DIV 1`), the cardholder
position contains the gamertag, and the date position contains the first observed
promotion date. Match statistics sit below the card.
CSS provides the spring entrance, brushed metal, orbit engraving, rank glow and
pointer tilt. Reduced motion removes entrance/tilt. The native dialog traps
keyboard focus; the action or Escape dismisses it and restores focus. There is
no timed dismissal. Pending events wait while the page is hidden or the intro
is playing and persist until acknowledged. An account change closes a different
player's card. The main window is not activated over the game: this feature
displays in RL Hub, not the native/Game Bar overlay.

GET `/api/rank-promotions` exposes events only for the active account.
POST `/api/rank-promotions/ack` requires the local app Origin and an event ID;
it acknowledges only the active account's event. Network failures retry without
redisplaying within the current page. Runtime assets are included in both
`desktop_app.py` and `RL Hub.spec`.

`assets/ranks/` uses the same genuine rank icons as the Dashboard Lanyard.
Their source and revision are documented in `frontend/lanyard/README.md`.

Validation: Python unit suite including `tests/test_rank_promotions.py`, plus
`tests/rank_celebration_ui_smoke.py` for actual events, content, icons, keyboard
focus, reduced motion, narrow layout, Escape, persistent dismissal and delivery
on Settings and Dashboard. Tests use isolated storage. Build via `RL Hub.spec`
and verify the executable with `tests/packaged_smoke.py`.
