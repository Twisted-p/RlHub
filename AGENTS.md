# Working on RL Hub

The main product is the standalone Windows app. Read README.md and STANDALONE_SETUP.md before changing its startup, rank lookup or Performance collection.

- Run `desktop_app.py` with Python 3.13 and the dependencies in `requirements-desktop.txt`. Build using `requirements-build.txt` and `RL Hub.spec`.
- Keep the local UI/API on one origin. Port 18765 preserves existing WebView storage; use an ephemeral port for isolated service tests.
- When adding a runtime asset, update both `desktop_app.py`'s `UI_FILES` allowlist and `RL Hub.spec`'s asset list. Keep subdirectories intact in the bundle.
- The splash should play on each app launch, finish within seven seconds and support skipping. The host supplies a fresh session ID so it does not repeat on navigation. Do not automatically skip it based on `prefers-reduced-motion`; use the skip button.
- Stats API `Data` may contain JSON-encoded text. Match-ended events can lack a GUID. Preserve replay/freeplay filtering, deduplication and abandoned-match handling.
- Only public player identity is read from game logs. Never collect authentication tokens or commit logs, personal account data or `%LOCALAPPDATA%/RL Hub` storage.
- Preserve the older Overwolf files for future work, but do not introduce an Overwolf dependency into the standalone app.
- Verify changes with the relevant tests in `tests`. Unit tests are independent of live Rocket League; WebView smoke tests require Windows. Use isolated storage and avoid interrupting the user's running app.
- Generated builds belong in ignored `dist`/`build` directories. Distribute executables through GitHub Releases.
