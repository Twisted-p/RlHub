# Dashboard rank lanyard

React island mounted only by `dashboard.html`; existing pages remain plain HTML/JS.

Install/build from this directory with `npm ci` and `npm run build` (Node 24 used).
The committed production bundle in `assets/dashboard-lanyard/` contains React,
Three, Rapier WASM, rank icons, the card model and band texture. No CDN or React
development server is needed to run the desktop app or build its Python executable.
Regenerate this bundle after changing the source. Both bundle files are registered
in `desktop_app.py` and `RL Hub.spec`.

Source: https://reactbits.dev/r/Lanyard-JS-CSS.json fetched 2026-10-03.
The registry lists no dependencies; the imported packages were installed explicitly
and pinned in `package-lock.json`. `Lanyard.jsx` and `Lanyard.css` came directly from
the JS-CSS registry. Local changes cap DPR to 1.5 and dispose replaced card textures.
Vite includes GLB files and substitutes NODE_ENV for the standalone browser build.

Card model and original band texture:
https://github.com/DavidHDev/react-bits/tree/main/src/assets/lanyard
See `REACT_BITS_LICENSE.md` for the upstream MIT + Commons Clause terms.

Rocket League tier icons (0–22) copied from:
https://github.com/BenTheDan/IngameRank/tree/cb706fc7fc6d77409c3b4349c90c59f5dd96ae31/data/assets/IngameRank/Tiers
These are Rocket League/Psyonix rank graphics; they are used to represent the
player's actual fetched rank, not as a claim of affiliation.

The default mode is 2v2; selection is saved separately as `rlhub:lanyardPlaylist`.
Rank-to-icon mapping uses the exact rank labels from `mmr_provider.py`, stripping
only the division suffix. Unknown data shows a Profile action, not a sample rank.
The local `/api/dashboard-ranks` endpoint reads already-fetched rank data under the
overlay lock; it never performs an additional upstream lookup. The widget polls
it every 10 seconds while visible and keeps the last profile during connection errors.
The 3D scene unmounts when hidden; reduced-motion and rendering errors use a static
icon card. All rank details remain accessible as HTML outside the decorative canvas.

Validation:
`node tests/dashboard_rank.test.mjs` from the repository root,
Python desktop unit tests, and `tests/dashboard_lanyard_ui_smoke.py` in isolated
WebView2 storage. The smoke test covers real WebGL, mode/icon changes, unknown rank,
persistence, a narrow viewport and reduced motion.
