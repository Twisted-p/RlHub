# Dashboard rank lanyard

## React Bits registry

The public `@react-bits` registry is configured in `components.json` in this
React project's root. `jsconfig.json` and both Vite configs resolve `@/` to
`src/`. Install JS-CSS components from this directory, for example:

```sh
npx shadcn@latest add @react-bits/StarBorder-JS-CSS
```

The registry URL is `https://reactbits.dev/r/{name}.json`. No license key is
needed for this public registry. Pro registries are separate. Components
installed later must be wired into an entry point and their production bundle
rebuilt before shipping the desktop app. `src/registry.css` is the dedicated
registry stylesheet path; current JS-CSS components import their own CSS.

## Goals StarBorder

`src/StarBorder.jsx` and `.css` use the React Bits JS-CSS source supplied by the
user. `src/goals-star-border.jsx` mounts it around each of the three existing
Goals cards without recreating inputs or their listeners. Uses the existing React
dependencies, cyan `#55efd5`, 5s animation, 2px thickness and the app's dark surface.
CSS selectors are scoped to the component; the gradient centers are positioned
on the top/bottom edges for tall goal cards. Reduced motion removes the animated
gradients and retains a static accent; hidden pages pause them.

Build with `npm run build:goals`. Output is the committed standalone JS/CSS bundle
in `assets/goals-star-border/`, registered in the host allowlist and PyInstaller
spec and loaded only by Goals. No new runtime dependencies or remote assets.
Validation: `tests/goals_ui_smoke.py`, including selection persistence, focus,
three component instances, reduced motion and card-content overflow checks.

React island mounted only by `dashboard.html`; existing pages remain plain HTML/JS.

## Page effects

`npm run build:polish` produces `assets/app-polish/`. The desktop host loads this
local bundle on Dashboard, Garage, Settings and Training Packs. Registry sources
for CountUp, TiltedCard, SpotlightCard and Aurora live in `src/components/`;
`motion` and `ogl` are locked in `package-lock.json` and bundled for offline use.
CountUp has an optional formatter for elapsed training time. Original numeric text
remains accessible and authoritative; the animated layer is decorative.
Spotlight preserves the existing controls and TiltedCard animates Garage images.
Reduced motion disables counters and tilt, and touch uses ordinary car images.
Aurora is a subtle Dashboard header background. Its WebGL component unmounts
(cancelling animation and releasing its context) on blur, document hiding,
offscreen header or reduced motion, and resumes when visible and focused.
Rendering failure falls back to a static gradient. No extra stats polling is added.
Run `tests/app_polish_ui_smoke.py` for actual WebView2 rendering, pause/resume,
dynamic collections, counter updates and reduced-motion checks.

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
